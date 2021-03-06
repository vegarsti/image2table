from datetime import datetime
from hashlib import md5
from time import time
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import app, db, login
from aws_helpers import get_url, filename_helper


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    images = db.relationship("Image", backref="user", lazy="dynamic")

    def __repr__(self):
        return "<User {}>".format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return "https://www.gravatar.com/avatar/{}?d=identicon&s={}".format(
            digest, size
        )

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            app.config["SECRET_KEY"],
            algorithm="HS256",
        ).decode("utf-8")

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])[
                "reset_password"
            ]
        except:
            return
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(32), nullable=False)  # all uuid hexes are 32 long
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    filename = db.Column(db.String(140), nullable=False)
    MAX_JSON_CHARACTER_COUNT = 10000
    tabular = db.Column(db.String(MAX_JSON_CHARACTER_COUNT))
    num_columns = db.Column(db.Integer)

    def image_url(self):
        filename, file_ending = filename_helper(self.filename)
        return get_url(self.uuid, filename) + "." + file_ending

    def excel_url(self):
        filename, _ = filename_helper(self.filename)
        file_ending = "xlsx"
        return get_url(self.uuid, filename) + "." + file_ending

    def csv_url(self):
        filename, _ = filename_helper(self.filename)
        file_ending = "csv"
        return get_url(self.uuid, filename) + "." + file_ending

    def thumbnail_url(self):
        filename, file_ending = filename_helper(self.filename)
        return get_url(self.uuid, filename) + "_thumbnail" + "." + file_ending

    def __repr__(self):
        return "<Image {}>".format(self.uuid)
