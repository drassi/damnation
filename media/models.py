from datetime import datetime

from sqlalchemy import Column, Integer, Text, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class Asset(Base):

    __tablename__ = 'assets'

    id = Column(Integer, primary_key=True)
    path = Column(Text, nullable=False)
    md5 = Column(Text, nullable=False)
    size = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)
    original_abspath = Column(Text, nullable=False)
    created = Column(Date, nullable=False)

    def __init__(self, path, md5, size, title, original_abspath):
        self.path = path
        self.md5 = md5
        self.size = size
        self.title = title
        self.original_abspath = original_abspath
        self.created = datetime.utcnow()

class DerivativeAsset(Base):

    __tablename__ = 'derivative_assets'

    id = Column(Integer, primary_key=True)
    path = Column(Text, nullable=False)
    cmd = Column(Text)
    output = Column(Text)
    created = Column(Date, nullable=False)

    def __init__(self, path, cmd, output):
        self.path = path
        self.cmd = cmd
        self.output = output
        self.created = created
