import simplejson as json

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
