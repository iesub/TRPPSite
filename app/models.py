"""
модуль models
"""

import pytz
from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from hashlib import md5


followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
                     )


class User(UserMixin, db.Model):
    """
    Таблица пользователя
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    invitations = db.relationship('Invitation', backref='user', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Europe/Moscow')))
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        """
        метод установки пароля

        :param password: пароль
        :type password: строка
        :return: ничего не возвращает
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        метод проверки пароля

        :param password: пароль
        :type password: строка
        :return: True или False
        """
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        """
        метод утображения объекта аватра пользователя

        :param size: размер картинки
        :type size: число
        :return: аватар пользователя
        """
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        """
        метод добавления пользователя в список друзей

        :param user: пользователь, которого нужно добавить
        :type user: пользователь
        :return: ничено не возврщает
        """
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        """
        метод удаления пользователя в список друзей

        :param user: пользователь, которого нужно удалить
        :type user: пользователь
        :return: ничено не возврщает
        """
        if self.is_following(user):
            self.followed.remove(user)
        elif user.is_following(self):
            user.followed.remove(self)

    def is_following(self, user):
        """
        метод проверки, является пользователь другом

        :param user: пользователь, которого нужно проверить
        :type user: пользователь
        :return: True или False
        """
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0


@login.user_loader
def load_user(id):
    """
    метод загрузки пользователя из бд

    :param id: id пользователя
    :type id: число
    :return: пользователь
    """
    return User.query.get(int(id))


class Post(db.Model):
    """
    таблица сообщений пользователей
    """
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now(pytz.timezone('Europe/Moscow')))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)


class Invitation(db.Model):
    """
    таблица приглашений пользователей в чаты
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'))


user_chats = db.Table('user_chats',
                      db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                      db.Column('chat_id', db.Integer, db.ForeignKey('chat.id'))
                      )


class Chat(db.Model):
    """
    таблица чатов
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    users = db.relationship('User', secondary=user_chats, backref='chats')
    posts = db.relationship('Post', backref='chat', lazy='dynamic')
    invitations = db.relationship('Invitation', backref='chat', lazy='dynamic')
