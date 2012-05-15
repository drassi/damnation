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
    config.add_route('list-collections', '/')
    config.add_route('show-collection', '/collection/{collection_id}')
    config.add_route('show-asset', '/asset/{asset_id}')
    config.add_route('youtube-upload', '/ajax/youtube-upload')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('debug', '/debug')
    config.scan()
    return config.make_wsgi_app()

