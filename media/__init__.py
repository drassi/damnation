from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from sqlalchemy import engine_from_config

from .models import DBSession

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    authn_policy = AuthTktAuthenticationPolicy('damnation')
    authz_policy = ACLAuthorizationPolicy()
    config = Configurator(settings=settings, root_factory='.auth.RootFactory')
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('list-collections', '/', request_method='GET')
    config.add_route('show-collection', '/collection/view/{collection_id}', request_method='GET')
    config.add_route('add-collection', '/collection/add', request_method='POST')
    config.add_route('delete-collection', '/collection/delete/${collection_id}', request_method='POST')
    config.add_route('admin-collection', '/collection/admin/{collection_id}', request_method='GET')
    config.add_route('admin-collection-save', '/collection/admin/save/{collection_id}', request_method='POST')

    config.add_route('show-asset', '/asset/view/{asset_id}', request_method='GET')
    config.add_route('modify-asset', '/asset/modify/{asset_id}', request_method='POST')
    config.add_route('move-assets', '/asset/move', request_method='POST')
    config.add_route('save-annotation', '/asset/annotation-save/{asset_id}', request_method='POST')
    config.add_route('delete-annotation', '/annotation/delete/{annotation_id}', request_method='POST')
    config.add_route('upload-asset-to-youtube', '/asset/youtube-upload/{asset_id}', request_method='POST')

    config.add_route('admin-users', '/user/admin', request_method='GET')
    config.add_route('admin-users-save', '/user/admin/save', request_method='POST')

    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('debug', '/debug')

    config.scan()
    return config.make_wsgi_app()

