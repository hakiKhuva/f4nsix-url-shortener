from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, BigInteger, String, Integer, DateTime, Text, ForeignKey, Boolean, Date
from datetime import datetime

from .functions import get_user_ip_address

import uuid
import random

db = SQLAlchemy()


class Base(db.Model):
    __abstract__ = True
    id = Column(BigInteger().with_variant(Integer, 'sqlite'), primary_key=True, autoincrement=True)
    created_date = Column(DateTime(), nullable=False, default=datetime.utcnow)


class ShortenLink(Base):
    __tablename__ = "shorten_links"
    destination = Column(Text(), nullable=False)
    code = Column(String(16), nullable=False, unique=True)
    tracking_id = Column(String(32), nullable=False, unique=True, default=lambda:uuid.uuid4().hex[random.randint(3, 6):random.randint(17,20)].upper()) # changed tracking id length

    user_id = Column(BigInteger().with_variant(Integer, 'sqlite'), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    def __repr__(self):
        return "<ShortenLink:{}>".format(self.code)


class ShortenLinkTransaction(Base):
    __tablename__ = 'shorten_link_transactions'
    device = Column(String(64))
    os = Column(String(64))
    browser = Column(String(64))
    city = Column(String(128))
    region = Column(String(128))
    country = Column(String(128))
    timezone = Column(String(64))
    ipaddress = Column(String(128))
    referrer = Column(String(128))

    shorten_link_id = Column(BigInteger().with_variant(Integer, 'sqlite'), ForeignKey('shorten_links.id', ondelete='CASCADE'))

    def __repr__(self):
        return "<ShortenLinkTransaction>"


class AdminUser(Base):
    __tablename__ = "admin_users"
    name = Column(String(64), nullable=False)
    email_address = Column(String(200), unique=True, nullable=False)
    password = Column(Text(), nullable=False)
    suspended = Column(Boolean(), nullable=False, default=False)

    user_sessions = db.relationship('AdminUserSession', backref='user', uselist=False, passive_deletes=True)
    notifications = db.relationship('Notification', backref='user', uselist=False, passive_deletes=True)

    def __repr__(self):
        return f"<AdminUser:{self.name}>"


class AdminUserSession(Base):
    __tablename__ = "admin_user_sessions"
    session_id = Column(String(200), unique=True, nullable=False, default=lambda:uuid.uuid4().hex+"__-__"+uuid.uuid4().hex)
    ipaddress = Column(String(200))
    city = Column(String(128))
    region = Column(String(128))
    country = Column(String(128))
    allowed = Column(Boolean(), nullable=False, default=True)
    admin_id = Column(BigInteger().with_variant(Integer, 'sqlite'), ForeignKey('admin_users.id', ondelete='CASCADE'))

    def __repr__(self):
        return f"<AdminUserSession:{self.session_id}>"


class BlacklistIP(Base):
    __tablename__ = "blacklist_ip_addresses"
    ipaddress = Column(String(128), nullable=False)

    def __repr__(self):
        return "<BlacklistIP:{}>".format(self.ipaddress)


class UserVisit(db.Model):
    __tablename__ = "_user_visits"
    id = Column(BigInteger(), primary_key=True, autoincrement=True)
    endpoint = Column(String(128), nullable=False)
    user_ip_address = Column(String(128), nullable=False, default=get_user_ip_address)
    created_date = Column(DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return f"<UserVisit:{self.id}:{self.user_ip_address}>"


class User(Base):
    __tablename__ = "users"
    name = Column(String(64), nullable=False)
    avatar_url = Column(Text(), nullable=False)
    username = Column(String(64), nullable=False)
    email_address = Column(String(256), nullable=False, unique=True)
    api_key = Column(String(128), nullable=True, unique=True)
    api_key_created = Column(Date(), nullable=True)
    auth_method = Column(String(32), nullable=False)
    receive_emails = Column(Boolean(), default=True, nullable=True)

    sessions = db.relationship("UserSession", backref="user", cascade="all, delete", passive_deletes=True)
    shorten_links = db.relationship("ShortenLink", backref="user", cascade="all, delete", passive_deletes=True)
    api_requests = db.relationship("APIRequest", backref="user", cascade="all, delete", passive_deletes=True)

    def __repr__(self):
        return "<User:{}>".format(self.name)


class UserSession(Base):
    __tablename__ = "user_sessions"
    session_id = Column(String(128), nullable=False)
    user_id = Column(BigInteger().with_variant(Integer, 'sqlite'), ForeignKey("users.id", ondelete="CASCADE"))

    def __repr__(self):
        return "<UserSession:{}>".format(self.session_id)


class APIRequest(Base):
    __tablename__ = "api_requests"
    ipaddress = Column(String(128), nullable=False, default=get_user_ip_address)
    request_url = Column(Text(), nullable=False)
    return_code = Column(Integer(), nullable=False)
    user_id = Column(BigInteger().with_variant(Integer, 'sqlite'), ForeignKey("users.id", ondelete="CASCADE"))

    def __repr__(self):
        return "<APIRequest:{}>".format(self.id)
    

class Notification(Base):
    __tablename__ = "notifications"
    render_data = Column(Text(), nullable=False)
    from_ = Column(DateTime(), nullable=False)
    to = Column(DateTime(), nullable=False)
    public_id = Column(String(), nullable=False, unique=True, default=uuid.uuid4)

    admin_id = Column(BigInteger().with_variant(Integer, 'sqlite'), ForeignKey("admin_users.id", ondelete="CASCADE"))

    def __repr__(self):
        return f"<Notification:{self.id}>"