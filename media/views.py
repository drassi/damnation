import os
import simplejson as json
from redis import Redis

from pyramid.response import Response
from pyramid.view import view_config, forbidden_view_config
from pyramid.security import remember, forget, authenticated_userid
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPSeeOther, HTTPForbidden

from sqlalchemy import func
from sqlalchemy.exc import DBAPIError

from .models import DBSession, User, Asset, DerivativeAsset, Collection, CollectionGrant
from .config import Config

def get_user(request):
    username = authenticated_userid(request)
    user = DBSession.query(User).filter(User.username==username).first()
    return user

@view_config(route_name='list-collections', renderer='list-collections.mako', permission='read')
def list_collections(request):
    user = get_user(request)
    collection_query = DBSession.query(Collection, func.count(Asset.id)) \
                                .join(Asset) \
                                .group_by(Collection.id)
    if not user.superuser:
        collection_query = collection_query.join(CollectionGrant).filter(CollectionGrant.user_id==user.id)
    collection_counts = collection_query.all()
    return {
      'collection_counts' : collection_counts,
      'user' : user,
    }

@view_config(route_name='show-collection', renderer='show-collection.mako', permission='read')
def show_collection(request):
    user = get_user(request)
    id = request.matchdict['collection_id']
    collection = DBSession.query(Collection).get(id)
    assets = collection.assets
    page_assets, page_screenshots = [], {}
    for asset in assets:
        derivatives = asset.derivatives
        transcode_matches = [d.path for d in derivatives if d.derivative_type == 'transcode.360.mp4']
        screenshot_matches = [d.path for d in derivatives if d.derivative_type == 'screenshot.180.gif']
        thumbnail_matches = [d.path for d in derivatives if d.derivative_type == 'thumbnail.180.png']
        if transcode_matches and screenshot_matches and thumbnail_matches:
            transcode = transcode_matches[0]
            screenshot = screenshot_matches[0]
            thumbnail = thumbnail_matches[0]
            page_assets.append(asset)
            asset.screenshot = screenshot
            asset.thumbnail = thumbnail
    grant = DBSession.query(CollectionGrant).filter(CollectionGrant.collection_id==id).filter(CollectionGrant.user_id==user.id).first()
    show_admin_link = user.superuser or (grant is not None and grant.grant_type == 'admin')
    return {
      'collection' : collection,
      'page_assets' : page_assets,
      'base_media_url' : Config.BASE_MEDIA_URL,
      'user' : user,
      'show_admin_link' : show_admin_link,
    }

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

    user = get_user(request)
    id = request.matchdict['collection_id']
    collection = DBSession.query(Collection).get(id)

    collection.name = request.params['collection_name']
    collection.description = request.params['collection_description']
    DBSession.add(collection)

    grants_to_save = dict([(key.replace('grant_', ''), request.params[key]) for key in [key for key in request.params.keys() if key.startswith('grant_')]])
    for grant in collection.grants:
        if grant.user_id in grants_to_save:
            grant_to_save = grants_to_save[grant.user_id]
            if grant_to_save in ['read', 'write', 'admin']:
                grant.grant_type = grant_to_save
                DBSession.add(grant)
            elif grant_to_save == 'revoke':
                DBSession.delete(grant)
            else:
                raise Exception('i dont know about grant %s' % grant_to_save)

    new_grant_username = request.params['new_username'].strip()
    if new_grant_username:
       user = DBSession.query(User).filter(User.username == new_grant_username).first()
       if not user:
           raise Exception('unable to locate user with username %s' % new_grant_username)
       new_grant_type = request.params['new_grant']
       if new_grant_type not in ['read', 'write', 'admin']:
           raise Exception('i dont know about grant %s' % new_grant_type)
       new_grant = CollectionGrant(collection, user, new_grant_type)
       DBSession.add(new_grant)

    return HTTPSeeOther(location = request.route_url('show-collection', collection_id=id))

@view_config(route_name='show-asset', renderer='show-asset.mako', permission='read')
def show_asset(request):
    asset_id = request.matchdict['asset_id']
    asset = DBSession.query(Asset).join(DerivativeAsset).filter(Asset.id==asset_id).first()
    if not asset:
        return HTTPNotFound('No such asset')
    transcode_matches = [d.path for d in asset.derivatives if d.derivative_type == 'transcode.360.mp4']
    youtube_matches = [json.loads(d.path) for d in asset.derivatives if d.derivative_type == 'youtube']
    if not transcode_matches:
        raise Exception('Couldnt locate the proper transcode of this asset')
    transcode = transcode_matches[0]
    asset.transcode = transcode
    asset.youtube = youtube_matches[0] if youtube_matches else None
    logged_in = authenticated_userid(request)
    return {
        'asset' : asset,
        'base_media_url' : Config.BASE_MEDIA_URL,
        'logged_in' : logged_in,
    }

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
