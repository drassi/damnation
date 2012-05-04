import os
import simplejson as json
from redis import Redis

from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from .models import DBSession, Asset, DerivativeAsset
from .config import Config

@view_config(route_name='list-assets', renderer='list-assets.mako')
def list_assets(request):
    assets = DBSession.query(Asset).join(DerivativeAsset).all()
    page_assets, page_screenshots = [], {}
    for asset in assets:
        derivatives = asset.derivatives
        transcode_matches = [d.path for d in derivatives if d.derivative_type == 'transcode.360.flv']
        screenshot_matches = [d.path for d in derivatives if d.derivative_type == 'screenshot.180.gif']
        thumbnail_matches = [d.path for d in derivatives if d.derivative_type == 'thumbnail.180.png']
        if transcode_matches and screenshot_matches and thumbnail_matches:
            transcode = transcode_matches[0]
            screenshot = screenshot_matches[0]
            thumbnail = thumbnail_matches[0]
            page_assets.append(asset)
            asset.screenshot = screenshot
            asset.thumbnail = thumbnail
        if len(page_assets) >= 20:
            break
    return {
      'page_assets' : page_assets,
      'base_media_url' : Config.BASE_MEDIA_URL,
    }

@view_config(route_name='show-asset', renderer='show-asset.mako')
def show_asset(request):
    asset = DBSession.query(Asset).join(DerivativeAsset).filter(Asset.id==request.matchdict['id']).one()
    transcode_matches = [d.path for d in asset.derivatives if d.derivative_type == 'transcode.360.flv']
    youtube_matches = [json.loads(d.path) for d in asset.derivatives if d.derivative_type == 'youtube']
    if not transcode_matches:
        raise Exception('Couldnt locate the proper transcode of this asset')
    transcode = transcode_matches[0]
    asset.transcode = transcode
    asset.youtube = youtube_matches[0] if youtube_matches else None
    return {
        'asset' : asset,
        'base_media_url' : Config.BASE_MEDIA_URL,
    }

@view_config(route_name='youtube-upload', renderer='json')
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
