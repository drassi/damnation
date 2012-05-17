from pyramid.security import Allow, Everyone, authenticated_userid

from .models import DBSession, User, Asset, Collection, CollectionGrant

class RootFactory(object):

    def __init__(self, request):
        self.request = request
        self.username = authenticated_userid(request)
        self.authenticated = self.username is not None
        self.matched_route = request.matched_route
        if self.authenticated:
            self.user = DBSession.query(User).filter(User.username==self.username).one()

    @staticmethod
    def _get_collection_grant(user_id, collection_id):
        grant = DBSession.query(CollectionGrant) \
                          .filter(CollectionGrant.user_id==user_id) \
                          .filter(CollectionGrant.collection_id==collection_id) \
                          .first()
        return grant.grant_type if grant else None

    @property
    def __acl__(self):
        if not self.authenticated:
            return []
        matchdict = self.request.matchdict
        permissions = set()
        if self.matched_route and self.matched_route.name in ['list-collections']:
            permissions.add('read')
        elif 'collection_id' in matchdict:
            grant = self._get_collection_grant(self.user.id, matchdict['collection_id'])
            if grant == 'admin' or self.user.superuser:
                permissions.update(['read', 'write', 'admin'])
            elif grant == 'write':
                permissions.update(['read', 'write'])
            elif grant == 'read':
                permissions.update(['read'])
        elif 'asset_id' in matchdict:
            asset = DBSession.query(Asset).get(matchdict['asset_id'])
            grant = self._get_collection_grant(self.user.id, asset.collection_id)
            if grant == 'write' or self.user.superuser:
                permissions.update(['read', 'write'])
            elif grant =='read':
                permissions.update(['read'])
        else:
            raise Exception('not sure how to generate ACLs for this request')
        return [(Allow, Everyone, permission) for permission in permissions]
