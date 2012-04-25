from datetime import datetime

from sqlalchemy import Column, Integer, Text, Date

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class Asset(Base):

    __tablename__ = 'assets'

    id = Column(Integer, primary_key=True)
    path = Column(Text, nullable=False)
    size = Column(Integer, nullable=False)
    name = Column(Text, nullable=False)
    transcoded360 = Column(Integer, nullable=False)
    created = Column(Date, nullable=False)

    def __init__(self, path, size, name):
        self.path = path
        self.size = size
        self.name = name
        self.created = datetime.utcnow()
        self.transcoded360 = 0
