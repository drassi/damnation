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

    def _get_move_permissions(self):
        if self.user.superuser:
            return ['move']
        target_collection_id = self.request.params['collection_id']
        asset_ids = self.request.params.getall('asset_id[]')
        assets = DBSession.query(Asset).filter(Asset.id.in_(asset_ids)).all()
        source_collection_ids = set([asset.collection_id for asset in assets])
        collection_ids_to_check = source_collection_ids.union([target_collection_id])
        grants = DBSession.query(CollectionGrant) \
                          .filter(CollectionGrant.user_id==self.user.id) \
                          .filter(CollectionGrant.collection_id.in_(collection_ids_to_check)) \
                          .filter(CollectionGrant.grant_type=='admin') \
                          .all()
        for grant in grants:
            collection_ids_to_check.remove(grant.collection_id)
        return ['move'] if not collection_ids_to_check else []

    @property
    def __acl__(self):
        if not self.authenticated:
            return []
        matchdict = self.request.matchdict
        permissions = set()
        if self.matched_route and self.matched_route.name in ['list-collections', 'add-collection']:
            permissions.add('read')
            if self.user.superuser:
                permissions.add('admin')
        elif self.matched_route and self.matched_route.name == 'move-assets':
            permissions.update(self._get_move_permissions())
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
            if grant == 'admin' or self.user.superuser:
                permissions.update(['read', 'write', 'admin'])
            if grant == 'write':
                permissions.update(['read', 'write'])
            elif grant =='read':
                permissions.update(['read'])
        else:
            raise Exception('not sure how to generate ACLs for this request')
        return [(Allow, Everyone, permission) for permission in permissions]
