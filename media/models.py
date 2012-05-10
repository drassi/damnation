import simplejson as json
from datetime import datetime

from sqlalchemy import Column, Integer, Text, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from zope.sqlalchemy import ZopeTransactionExtension

from pyramid.security import Allow, Everyone

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class Asset(Base):

    __tablename__ = 'assets'

    id = Column(Integer, primary_key=True)
    asset_type = Column(Text, nullable=False)
    path = Column(Text, nullable=False)
    md5 = Column(Text, nullable=False)
    size = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=False)
    original_abspath = Column(Text, nullable=False)
    created = Column(Date, nullable=False)

    def __init__(self, asset_type, path, md5, size, duration, width, height, title, original_abspath):
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
        self.metadata_json = json.dumps(metadata)

class DerivativeAsset(Base):

    __tablename__ = 'derivative_assets'

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    derivative_type = Column(Text, nullable=False)
    path = Column(Text, nullable=False)
    cmd = Column(Text)
    output = Column(Text)
    created = Column(Date, nullable=False)

    parent = relationship(Asset, backref='derivatives')

    def __init__(self, asset_id, derivative_type, path, cmd):
        self.asset_id = asset_id
        self.derivative_type = derivative_type
        self.path = path
        self.cmd = cmd
        self.output = output
        self.created = datetime.utcnow()

class RootFactory(object):
    __acl__ = [ (Allow, Everyone, 'view'),
                (Allow, 'group:editors', 'edit') ]
    def __init__(self, request):
        pass
