import os
import simplejson as json
from redis import Redis

from pyramid.response import Response
from pyramid.view import view_config, forbidden_view_config
from pyramid.security import remember, forget, authenticated_userid
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from sqlalchemy.exc import DBAPIError

from .models import DBSession, Asset, DerivativeAsset
from .auth import User
from .config import Config

@view_config(route_name='list-assets', renderer='list-assets.mako', permission='read')
def list_assets(request):
    assets = DBSession.query(Asset).join(DerivativeAsset).all()
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
    logged_in = authenticated_userid(request)
    return {
      'page_assets' : page_assets,
      'base_media_url' : Config.BASE_MEDIA_URL,
      'logged_in' : logged_in,
    }

@view_config(route_name='show-asset', renderer='show-asset.mako', permission='read')
def show_asset(request):
    asset = DBSession.query(Asset).join(DerivativeAsset).filter(Asset.id==request.matchdict['id']).first()
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

@view_config(route_name='youtube-upload', renderer='json', permission='write')
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
@forbidden_view_config(renderer='templates/login.pt')
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
            return HTTPFound(location = came_from, headers = headers)
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
    return HTTPFound(location = request.route_url('list-assets'), headers = headers)
