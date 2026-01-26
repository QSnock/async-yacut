from datetime import datetime

from .app import db
from .constants import MAX_SHORT_ID_LENGTH


class URLMap(db.Model):
    __tablename__ = 'url_map'

    id = db.Column(db.Integer, primary_key=True)
    original = db.Column(db.String, nullable=False)
    short = db.Column(
        db.String(MAX_SHORT_ID_LENGTH),
        unique=True,
        nullable=False,
        index=True
    )
    timestamp = db.Column(
        db.DateTime, index=True, default=datetime.utcnow
    )


class File(db.Model):
    __tablename__ = 'file'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    path = db.Column(db.String, nullable=False)
    timestamp = db.Column(
        db.DateTime, index=True, default=datetime.utcnow
    )
    url_map_id = db.Column(
        db.Integer, db.ForeignKey('url_map.id'), nullable=False
    )
    url_map = db.relationship('URLMap', backref='files')
