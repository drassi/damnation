from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from .models import Asset, DBSession

@view_config(route_name='list-assets', renderer='list-assets.mako')
def list_assets(request):
    assets = DBSession.query(Asset).all()
    return {
      'assets' : assets
    }
