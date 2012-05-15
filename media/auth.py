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
    def _get_collection_grants(user_id, collection_ids):
        grants = DBSession.query(CollectionGrant) \
                          .filter(CollectionGrant.user_id==user_id) \
                          .filter(CollectionGrant.collection_id.in_(collection_ids)) \
                          .all()
        return set([grant.grant_type for grant in grants])

    @property
    def __acl__(self):
        if not self.authenticated:
            return []
        matchdict = self.request.matchdict
        permissions = set()
        if self.matched_route and self.matched_route.name in ['list-collections']:
            permissions.add('read')
        elif 'collection_id' in matchdict:
            grants = self._get_collection_grants(self.user.id, [matchdict['collection_id']])
            if 'admin' in grants or self.user.superuser:
                permissions.update(['read', 'write', 'admin'])
            if 'write' in grants:
                permissions.update(['read', 'write'])
            if 'read' in grants:
                permissions.update(['read'])
        elif 'asset_id' in matchdict:
            asset = DBSession.query(Asset).get(matchdict['asset_id'])
            grants = self._get_collection_grants(self.user.id, [collection.id for collection in asset.collections])
            if 'write' in grants or self.user.superuser:
                permissions.update(['read', 'write'])
            if 'read' in grants:
                permissions.update(['read'])
        else:
            raise Exception('not sure how to generate ACLs for this request')
        return [(Allow, Everyone, permission) for permission in permissions]
