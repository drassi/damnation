import random
import string
import simplejson as json
from datetime import datetime
from passlib.hash import bcrypt

from sqlalchemy import Column, Integer, BigInteger, Text, Unicode, Boolean, DateTime, ForeignKey, Table, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from zope.sqlalchemy import ZopeTransactionExtension

from pyramid.security import Allow, Everyone

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class Asset(Base):

    __tablename__ = 'assets'

    id = Column(Text, primary_key=True)
    asset_type = Column(Text, nullable=False)
    path = Column(Text, nullable=False)
    md5 = Column(Text, nullable=False, unique=True)
    size = Column(BigInteger, nullable=False)
    duration = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    title = Column(Unicode, nullable=False)
    description = Column(Unicode, nullable=False)
    original_abspath = Column(Text, nullable=False)
    created = Column(DateTime)
    imported = Column(DateTime, nullable=False)
    collection_id = Column(Text, ForeignKey('collections.id'), nullable=False)
    import_log_id = Column(Text, ForeignKey('import_log.id'), nullable=False)

    collection = relationship('Collection', backref='assets')
    import_log = relationship('ImportLog', backref='assets')

    def __init__(self, id, asset_type, path, md5, size, duration, width, height, title, description, original_abspath, collection, import_log):
        self.id = id
        self.asset_type = asset_type
        self.path = path
        self.md5 = md5
        self.size = size
        self.duration = duration
        self.width = width
        self.height = height
        self.title = title
        self.description = description
        self.original_abspath = original_abspath
        self.imported = datetime.utcnow()
        self.created = None
        self.collection = collection
        self.import_log = import_log

    def size_mb_str(self):
        return '%0.1f' % (self.size * 1.0 / (1024 * 1024))

class DerivativeAsset(Base):

    __tablename__ = 'derivative_assets'
    __table_args__ = (
        UniqueConstraint('asset_id', 'derivative_type', 'part'),
    )

    id = Column(Integer, primary_key=True)
    asset_id = Column(Text, ForeignKey('assets.id'), nullable=False)
    derivative_type = Column(Text, nullable=False)
    part = Column(Integer, nullable=False)
    path = Column(Text, nullable=False)
    cmd = Column(Text)
    output = Column(Text)
    created = Column(DateTime, nullable=False)

    parent = relationship(Asset, backref='derivatives')

    def __init__(self, asset_id, derivative_type, path, cmd, part=0):
        self.asset_id = asset_id
        self.derivative_type = derivative_type
        self.part = part
        self.path = path
        self.cmd = cmd
        self.output = output
        self.created = datetime.utcnow()

class Collection(Base):

    __tablename__ = 'collections'

    id = Column(Text, primary_key=True)
    name = Column(Unicode, nullable=False)
    description = Column(Unicode, nullable=False)
    active = Column(Boolean, nullable=False)
    created = Column(DateTime, nullable=False)

    grants = relationship('CollectionGrant', backref='collection')

    def __init__(self, id, name, description):
        self.id = id
        self.name = name
        self.description = description
        self.active = True
        self.created = datetime.utcnow()

class User(Base):

    __tablename__ = 'users'

    id = Column(Text, primary_key=True)
    username = Column(Unicode, nullable=False, unique=True)
    password = Column(Text, nullable=False)
    active = Column(Boolean, nullable=False)
    superuser = Column(Boolean, nullable=False)
    created = Column(DateTime, nullable=False)

    def __init__(self, username, password):
        self.id = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
        self.username = username
        self.password = bcrypt.encrypt(password)
        self.active = True
        self.superuser = False
        self.created = datetime.utcnow()

    def validate_password(self, password):
        return bcrypt.verify(password, self.password)

class Annotation(Base):

    __tablename__ = 'annotations'

    id = Column(Text, primary_key=True)
    user_id = Column(Text, ForeignKey('users.id'), nullable=False)
    asset_id = Column(Text, ForeignKey('assets.id'), nullable=False)
    time = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    created = Column(DateTime, nullable=False)
    active = Column(Boolean, nullable=False)

    inactive_time = Column(DateTime)
    inactive_user_id = Column(Text, ForeignKey('users.id'))

    asset = relationship(Asset, backref='annotations')
    user = relationship(User, primaryjoin='Annotation.user_id==User.id')
    inactive_user = relationship(User, primaryjoin='Annotation.inactive_user_id==User.id')

    def created_str(self):
        return 'just now'

    def __init__(self, user, asset, time, text):
        self.id = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
        self.user = user
        self.asset = asset
        self.time = time
        self.text = text
        self.created = datetime.utcnow()
        self.active = True

class CollectionGrant(Base):

    __tablename__ = 'collection_grants'

    collection_id = Column(Text, ForeignKey('collections.id'), primary_key=True)
    user_id = Column(Text, ForeignKey('users.id'), primary_key=True)
    grant_type = Column(Text, nullable=False)

    user = relationship(User, backref='grants')

    def __init__(self, collection, user, grant_type):
        self.collection_id = collection.id
        self.user_id = user.id
        self.grant_type = grant_type

class UserLog(Base):

    __tablename__ = 'user_log'

    id = Column(Integer, primary_key=True)
    user_id = Column(Text, ForeignKey('users.id'), nullable=False)
    affected_user_id = Column(Text, ForeignKey('users.id'), nullable=False)
    log_type = Column(Text, nullable=False)
    log_json = Column(Unicode, nullable=False)
    created = Column(DateTime, nullable=False)

    def __init__(self, user, affected_user, log_type, log):
        self.user_id = user.id
        self.affected_user_id = affected_user.id
        self.log_type = log_type
        self.log_json = json.dumps(log)
        self.created = datetime.utcnow()

class CollectionLog(Base):

    __tablename__ = 'collection_log'

    id = Column(Integer, primary_key=True)
    user_id = Column(Text, ForeignKey('users.id'), nullable=False)
    affected_user_id = Column(Text, ForeignKey('users.id'), nullable=True)
    collection_id = Column(Text, ForeignKey('collections.id'), nullable=False)
    log_type = Column(Text, nullable=False)
    log_json = Column(Unicode, nullable=False)
    created = Column(DateTime, nullable=False)

    def __init__(self, user, affected_user, collection, log_type, log):
        self.user_id = user.id
        self.affected_user_id = affected_user.id if affected_user is not None else None
        self.collection_id = collection.id
        self.log_type = log_type
        self.log_json = json.dumps(log)
        self.created = datetime.utcnow()

class AssetLog(Base):

    __tablename__ = 'asset_log'

    id = Column(Integer, primary_key=True)
    user_id = Column(Text, ForeignKey('users.id'), nullable=False)
    asset_id = Column(Text, ForeignKey('assets.id'), nullable=False)
    old_collection_id = Column(Text, ForeignKey('collections.id'), nullable=True)
    new_collection_id = Column(Text, ForeignKey('collections.id'), nullable=True)
    log_type = Column(Text, nullable=False)
    log_json = Column(Unicode, nullable=False)
    created = Column(DateTime, nullable=False)

    def __init__(self, user, asset, log_type, log, old_collection=None, new_collection=None):
        self.user_id = user.id
        self.asset_id = asset.id
        self.old_collection_id = old_collection.id if old_collection is not None else None
        self.new_collection_id = new_collection.id if new_collection is not None else None
        self.log_type = log_type
        self.log_json = json.dumps(log)
        self.created = datetime.utcnow()

class ImportLog(Base):

    __tablename__ = 'import_log'

    id = Column(Text, primary_key=True)
    abspath = Column(Text, nullable=False)
    created = Column(DateTime, nullable=False)
    log = Column(Unicode, nullable=False)

    def __init__(self, id, abspath, log):
        self.id = id
        self.abspath = abspath
        self.log = log
        self.created = datetime.utcnow()
