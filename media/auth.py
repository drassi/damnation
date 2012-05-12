import os
import random
import string
from datetime import datetime
from passlib.hash import bcrypt

from sqlalchemy import Column, Integer, Text, Unicode, DateTime, Boolean

from pyramid.security import Allow, Everyone, authenticated_userid

from .models import Base

class RootFactory(object):

    def __init__(self, request):
        self.request = request
        self.user_id = authenticated_userid(request)

    @property
    def __acl__(self):
        allow_read = True # some logic here
        allow_write = False # some logic here
        acls = []
        if allow_read:
            acls.append((Allow, Everyone, 'read'))
        if allow_write:
            acls.append((Allow, Everyone, 'write'))
        return acls

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
