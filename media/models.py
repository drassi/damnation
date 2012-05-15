import random
import string
import simplejson as json
from datetime import datetime
from passlib.hash import bcrypt

from sqlalchemy import Column, Integer, Text, Unicode, Boolean, DateTime, ForeignKey, Table
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
    md5 = Column(Text, nullable=False)
    size = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    title = Column(Unicode, nullable=False)
    metadata_json = Column(Unicode, nullable=False)
    original_abspath = Column(Text, nullable=False)
    created = Column(DateTime, nullable=False)

    def __init__(self, id, asset_type, path, md5, size, duration, width, height, title, original_abspath):
        self.id = id
        self.asset_type = asset_type
        self.path = path
        self.md5 = md5
        self.size = size
        self.duration = duration
        self.width = width
        self.height = height
        self.title = title
        self.original_abspath = original_abspath
        self.created = datetime.utcnow()
        self.set_metadata({})

    def size_mb_str(self):
        return '%0.1f' % (self.size * 1.0 / (1024 * 1024))

    def get_metadata(self):
        return json.loads(self.metadata_json)

    def set_metadata(self, metadata):
        self.metadata_json = unicode(json.dumps(metadata))

class DerivativeAsset(Base):

    __tablename__ = 'derivative_assets'

    id = Column(Integer, primary_key=True)
    asset_id = Column(Text, ForeignKey('assets.id'), nullable=False)
    derivative_type = Column(Text, nullable=False)
    path = Column(Text, nullable=False)
    cmd = Column(Text)
    output = Column(Text)
    created = Column(DateTime, nullable=False)

    parent = relationship(Asset, backref='derivatives')

    def __init__(self, asset_id, derivative_type, path, cmd):
        self.asset_id = asset_id
        self.derivative_type = derivative_type
        self.path = path
        self.cmd = cmd
        self.output = output
        self.created = datetime.utcnow()

collection_assets = Table(
    'collection_assets',
    Base.metadata,
    Column('collection_id', Text, ForeignKey('collections.id'), primary_key=True),
    Column('asset_id', Text, ForeignKey('assets.id'), primary_key=True)
)

class Collection(Base):

    __tablename__ = 'collections'

    id = Column(Text, primary_key=True)
    name = Column(Unicode, nullable=False)
    description = Column(Unicode, nullable=False)
    frozen = Column(Boolean, nullable=False)
    created = Column(DateTime, nullable=False)

    assets = relationship(Asset, secondary=collection_assets, backref='collections')
    grants = relationship('CollectionGrant', backref='collection')

    def __init__(self, id, name, description, frozen):
        self.id = id
        self.name = name
        self.description = description
        self.frozen = frozen
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

class CollectionGrant(Base):

    __tablename__ = 'collection_grants'

    collection_id = Column(Text, ForeignKey('collections.id'), primary_key=True)
    user_id = Column(Text, ForeignKey('users.id'), primary_key=True)
    grant_type = Column(Text, nullable=False)

    user = relationship(User, backref='grants')

    def __init(self, collection, user, grant_type):
        self.collection_id = collection.id
        self.user_id = user.id
        self.grant_type = grant_type
