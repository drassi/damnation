import bleach
import os
import random
import string
import simplejson as json
from redis import Redis

from pyramid.response import Response
from pyramid.view import view_config, forbidden_view_config
from pyramid.security import remember, forget, authenticated_userid, has_permission
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPSeeOther, HTTPForbidden

from sqlalchemy import func
from sqlalchemy.exc import DBAPIError

from .models import DBSession, User, Asset, DerivativeAsset, Collection, CollectionGrant
from .models import UserLog, CollectionLog, AssetLog
from .config import Config

def get_user(request):
    username = authenticated_userid(request)
    user = DBSession.query(User).filter(User.username==username).first()
    return user

def rand(n):
    return ''.join(random.choice(string.lowercase + string.digits) for i in xrange(n))

@view_config(route_name='list-collections', renderer='list-collections.mako', permission='read')
def list_collections(request):
    user = get_user(request)
    if user.superuser:
        collections = DBSession.query(Collection, func.count(Asset.id)) \
                               .outerjoin(Asset) \
                               .group_by(Collection.id) \
                               .order_by(Collection.name) \
                               .filter(Collection.active==True) \
                               .all()
        collections = [(collection, count, True) for collection, count in collections]
    else:
        collections = DBSession.query(Collection, func.count(Asset.id), func.max(CollectionGrant.grant_type)) \
                               .outerjoin(Asset) \
                               .group_by(Collection.id) \
                               .order_by(Collection.name) \
                               .join(CollectionGrant) \
                               .filter(CollectionGrant.user_id==user.id) \
                               .filter(Collection.active==True) \
                               .all()
        collections = [(collection, count, grant_type=='admin') for collection, count, grant_type in collections]
    return {
      'collections' : collections,
      'user' : user,
      'show_add_collection_link' : has_permission('admin', request.context, request),
      'is_user_admin' : has_permission('admin', request.context, request),
    }

@view_config(route_name='show-collection', renderer='show-collection.mako', permission='read')
def show_collection(request):
    user = get_user(request)
    collection_id = request.matchdict['collection_id']
    collection = DBSession.query(Collection).get(collection_id)
    assets = collection.assets
    page_assets, page_screenshots = [], {}
    for asset in assets:
        derivatives = asset.derivatives
        transcode_matches = [d.path for d in derivatives if d.derivative_type == 'transcode.480.mp4']
        screenshot_matches = [d.path for d in derivatives if d.derivative_type == 'screenshot.180.gif']
        thumbnail_matches = [d.path for d in derivatives if d.derivative_type == 'thumbnail.180.png']
        if transcode_matches and screenshot_matches and thumbnail_matches:
            transcode = transcode_matches[0]
            screenshot = screenshot_matches[0]
            thumbnail = thumbnail_matches[0]
            page_assets.append(asset)
            asset.screenshot = screenshot
            asset.thumbnail = thumbnail
    grant = DBSession.query(CollectionGrant).filter(CollectionGrant.collection_id==collection_id).filter(CollectionGrant.user_id==user.id).first()
    if user.superuser:
        admin_collections = DBSession.query(Collection).filter(Collection.active==True).all()
    else:
        admin_collections = DBSession.query(Collection).join(CollectionGrant).filter(CollectionGrant.user_id==user.id).filter(CollectionGrant.grant_type=='admin').filter(Collection.active==True).all()
    admin_collections = [c for c in admin_collections if c.id != collection_id]
    return {
      'collection' : collection,
      'page_assets' : page_assets,
      'base_media_url' : Config.BASE_MEDIA_URL,
      'user' : user,
      'show_admin_link' : has_permission('admin', request.context, request),
      'show_asset_checkboxes' : has_permission('admin', request.context, request),
      'admin_collections' : admin_collections,
    }

@view_config(route_name='add-collection', permission='admin')
def add_collection(request):
    collection_name = request.params['new_collection_name'].strip()
    if collection_name:
        collection = Collection(rand(6), collection_name, '')
        DBSession.add(collection)
        user = get_user(request)
        DBSession.add(CollectionLog(user, None, collection, 'create', {}))
    return HTTPSeeOther(location=request.route_url('list-collections'))

@view_config(route_name='delete-collection', permission='admin')
def delete_collection(request):
    collection_id = request.matchdict['collection_id']
    collection = DBSession.query(Collection).get(collection_id)
    if len(collection.assets) > 0:
        raise Exception("can't delete a collection with assets")
    collection.active = False
    user = get_user(request)
    DBSession.add(CollectionLog(user, None, collection, 'deactivate', {}))
    return HTTPSeeOther(location=request.route_url('list-collections'))

@view_config(route_name='admin-collection', renderer='admin-collection.mako', permission='admin')
def admin_collection(request):
    user = get_user(request)
    id = request.matchdict['collection_id']
    collection = DBSession.query(Collection).get(id)
    grants = [(grant.user_id, grant.user.username, grant.grant_type) for grant in collection.grants]
    return {
      'collection' : collection,
      'grants' : grants,
      'user' : user,
    }

@view_config(route_name='admin-collection-save', permission='admin')
def admin_collection_save(request):

    collection_id = request.matchdict['collection_id']
    collection = DBSession.query(Collection).get(collection_id)
    user = get_user(request)

    new_name = request.params['collection_name']
    if collection.name != new_name:
        DBSession.add(CollectionLog(user, None, collection, 'modify-name',
                                    {'old' : collection.name, 'new' : new_name}))
    collection.name = new_name

    new_description = request.params['collection_description']
    if collection.description != new_description:
        DBSession.add(CollectionLog(user, None, collection, 'modify-description',
                                    {'old' : collection.description, 'new' : new_description}))
    collection.description = new_description

    grants_to_save = dict([(key.replace('grant_', ''), request.params[key]) for key in [key for key in request.params.keys() if key.startswith('grant_')]])
    for grant in collection.grants:
        if grant.user_id in grants_to_save:
            grant_to_save = grants_to_save[grant.user_id]
            grant_user = DBSession.query(User).filter(User.id==grant.user_id).one()
            if grant_to_save in ['read', 'write', 'admin']:
                if grant.grant_type != grant_to_save:
                    DBSession.add(CollectionLog(user, grant_user, collection, 'modify-grant',
                                  {'old' : grant.grant_type, 'new' : grant_to_save}))
                    grant.grant_type = grant_to_save
            elif grant_to_save == 'revoke':
                DBSession.add(CollectionLog(user, grant_user, collection, 'revoke-grant',
                              {'old' : grant.grant_type}))
                DBSession.delete(grant)
            else:
                raise Exception('i dont know about grant %s' % grant_to_save)

    new_grant_username = request.params['new_username'].strip()
    if new_grant_username:
       grant_user = DBSession.query(User).filter(User.username == new_grant_username).first()
       if not grant_user:
           raise Exception('unable to locate user with username %s' % new_grant_username)
       new_grant_type = request.params['new_grant']
       if new_grant_type not in ['read', 'write', 'admin']:
           raise Exception('i dont know about grant %s' % new_grant_type)
       DBSession.add(CollectionGrant(collection, grant_user, new_grant_type))
       DBSession.add(CollectionLog(user, grant_user, collection, 'add-grant',
                                   {'new' : new_grant_type}))

    return HTTPSeeOther(location = request.route_url('show-collection', collection_id=collection_id))

@view_config(route_name='show-asset', renderer='show-asset.mako', permission='read')
def show_asset(request):
    user = get_user(request)
    asset_id = request.matchdict['asset_id']
    asset = DBSession.query(Asset).join(DerivativeAsset).filter(Asset.id==asset_id).first()
    if not asset:
        return HTTPNotFound('No such asset')
    transcodes = [d.path for d in asset.derivatives if d.derivative_type == 'transcode.480.mp4']
    youtube_matches = [json.loads(d.path) for d in asset.derivatives if d.derivative_type == 'youtube']
    if not transcodes:
        raise Exception('Couldnt locate the proper transcode of this asset')
    asset.playlist = len(transcodes) > 1
    if asset.playlist:
        asset.transcodes = transcodes
    else:
        asset.transcode = transcodes[0]
    asset.youtube = youtube_matches[0] if youtube_matches else None
    return {
        'user' : user,
        'asset' : asset,
        'base_media_url' : Config.BASE_MEDIA_URL,
        'show_modify_asset' : has_permission('write', request.context, request),
    }

@view_config(route_name='move-assets', renderer='json', permission='move')
def move_assets(request):
    user = get_user(request)
    target_collection_id = request.params['collection_id']
    target_collection = DBSession.query(Collection).get(target_collection_id)
    asset_ids = request.params.getall('asset_id[]')
    assets = DBSession.query(Asset).filter(Asset.id.in_(asset_ids)).all()
    for asset in assets:
        old_collection = asset.collection
        asset.collection = target_collection
        DBSession.add(AssetLog(user, asset, 'change-collection', {}, old_collection=old_collection, new_collection=target_collection))
    return {'success' : True}

@view_config(route_name='modify-asset', permission='write')
def modify_asset(request):
    user = get_user(request)
    asset_id = request.matchdict['asset_id']
    asset = DBSession.query(Asset).get(asset_id)
    asset_title = request.params['asset_title']
    if asset.title != asset_title:
        DBSession.add(AssetLog(user, asset, 'modify-title', {'old' : asset.title, 'new' : asset_title}))
        asset.title = asset_title
    asset_description = request.params['asset_description']
    if asset.description != asset_description:
        asset_description = bleach.clean(asset_description, tags=['i', 'em', 'b', 'strong', 'p', 'div', 'a', 'br', 'span', 'ol', 'ul', 'li', 'h1', 'h2'])
        DBSession.add(AssetLog(user, asset, 'modify-description', {'old' : asset.description, 'new' : asset_description}))
        asset.description = asset_description
    return HTTPSeeOther(location=request.route_url('show-asset', asset_id=asset_id))

@view_config(route_name='admin-users', renderer='admin-users.mako', permission='admin')
def admin_users(request):
    user = get_user(request)
    users = DBSession.query(User).order_by(User.username).all()
    return {
        'user' : user,
        'users' : users,
    }

def change_usertype(user, affected_user, superuser, active):
    if affected_user.superuser != superuser:
        affected_user.superuser = superuser
        log_type = 'make-superuser' if superuser else 'revoke-superuser'
        DBSession.add(UserLog(user, affected_user, log_type, {}))
    if affected_user.active != active:
        affected_user.active = active
        log_type = 'activate' if active else 'deactivate'
        DBSession.add(UserLog(user, affected_user, log_type, {}))

@view_config(route_name='admin-users-save', permission='admin')
def admin_users_save(request):

    user = get_user(request)

    new_username = request.params['new_username'].strip()
    if new_username:
        password = request.params['new_password']
        new_user = User(new_username, password)
        DBSession.add(new_user)
        DBSession.flush()
        DBSession.add(UserLog(user, new_user, 'create', {}))

    users = DBSession.query(User).all()
    user_types_to_save = dict([(key.replace('usertype_', ''), request.params[key]) for key in [key for key in request.params.keys() if key.startswith('usertype_')]])
    for affected_user in users:
        if affected_user.id in user_types_to_save:
            user_type = user_types_to_save[affected_user.id]
            if user_type == 'normal':
                change_usertype(user, affected_user, False, True)
            elif user_type == 'superuser':
                change_usertype(user, affected_user, True, True)
            elif user_type == 'inactive':
                change_usertype(user, affected_user, False, False)
            else:
                raise Exception("i don't know about user type %s" % user_type)

    return HTTPSeeOther(location=request.route_url('admin-users'))

@view_config(route_name='upload-asset-to-youtube', renderer='json', permission='write')
def youtube_upload(request):
    asset = DBSession.query(Asset).join(DerivativeAsset).filter(Asset.id==request.params['id']).one()
    youtube_matches = [d.path for d in asset.derivatives if d.derivative_type == 'youtube']
    metadata = asset.get_metadata()
    if metadata.get('youtube-started') or youtube_matches:
        raise Exception('already started youtube for this video')
    metadata['youtube-started'] = True
    asset.set_metadata(metadata)
    DBSession.flush()
    redis = Redis()
    env_dir = os.path.join(os.getcwd(), '..')
    asset_abspath = os.path.join(Config.ASSET_ROOT, asset.path)
    redis.rpush('resque:queue:youtube',
                json.dumps({'class': 'YoutubeUpload',
                            'args': [asset.id, 'youtube', asset_abspath,
                                     'bash %s/youtube/examples/split_video_for_youtube.sh' % env_dir,
                                     '. %s/bin/activate && youtube-upload' % env_dir,
                                     Config.YOUTUBE_USER, Config.YOUTUBE_PASSWORD,
                                     asset.title, 'description', 'Education']}))
    return {'ok': True}

@view_config(route_name='debug', renderer='json')
def debug(request):
    raise Exception()

@view_config(route_name='login', renderer='templates/login.pt')
def login(request):
    login_url = request.route_url('login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/' # never use the login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    message = ''
    username = ''
    if 'form.submitted' in request.params:
        username = request.params['login']
        password = request.params['password']
        user = DBSession.query(User).filter(User.username == username).first()
        if user and user.active and user.validate_password(password):
            headers = remember(request, username)
            return HTTPSeeOther(location = came_from, headers = headers)
        message = 'Failed to authenticate'

    return dict(
        message = message,
        url = request.application_url + '/login',
        came_from = came_from,
        login = username,
    )

@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPSeeOther(location = request.route_url('list-collections'), headers = headers)

@forbidden_view_config()
def forbidden(request):
    if authenticated_userid(request):
        return HTTPForbidden()
    else:
        return HTTPSeeOther(location = request.route_url('login', _query={'came_from' : request.url}))
