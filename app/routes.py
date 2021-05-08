# -*- coding: utf-8 -*-
import sqlite3

from flask import render_template, flash, redirect, url_for, request, make_response
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, SearchAndCreateChatForm, SearchUserForm, PostForm,\
    CreateNewsForm
from flask_login import current_user, login_user
from app.models import User, Chat, Post, Invitation, News
from flask_login import logout_user, login_required
from datetime import datetime
import pytz


"""
модуль routes
"""


@app.before_request
def before_request():
    """
    метод определения времени последнего действия пользователя

    :return: ничего не возвращает
    """
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(pytz.timezone('Europe/Moscow'))
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    """
    метод отбражения главной страницы сайта

    :return: главная страница
    """
    form = SearchAndCreateChatForm()
    if form.validate_on_submit():
        if form.create_name.data == '':
            chat = Chat.query.filter_by(name=form.search_name.data).first()
            if chat in current_user.chats:
                return redirect(url_for('chat', chat_id=chat.id))
        if form.search_name.data == '':
            chat = Chat.query.filter_by(name=form.create_name.data).first()
            if chat is None:
                chat = Chat(name=form.create_name.data)
                chat.users.append(current_user)
                db.session.add(chat)
                post = Post(body=f'{current_user.username} создал чат', author=current_user, chat=chat,
                            timestamp=datetime.now(pytz.timezone('Europe/Moscow')))
                db.session.add(post)
                db.session.commit()
                flash('Поздравляю, вы создали новую беседу!')
                return redirect(url_for('chat', chat_id=chat.id))
    chats = current_user.chats
    chats.sort(key=lambda x: x.posts[-1].timestamp)
    invite = Invitation.query.filter_by(user=current_user).first()
    if invite is None:
        return render_template('index.html', title='Главная страница', chats=reversed(chats), count=0,
                               form=form)
    return render_template('index.html', title='Главная страница', chats=reversed(chats),
                           invitations=current_user.invitations, count=1, form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    метод отбражения страницы авторизации

    :return: страница авторизации или переход на метод index()
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неправильные имя пользователя или пароль')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Войти', form=form)


@app.route('/logout')
def logout():
    """
    метод выхода из акаунта

    :return: переход на главную страницу
    """
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    метод отбражения страницы регистрации

    :return: страница авторизации или переход на метод index()
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Поздравляю, теперь вы зарегистрированный пользователь!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    """
    метод отбражеия профиля пользователя

    :param username: имя пользователя
    :type username: строка
    :return: страница профиля пользователя
    """
    user = User.query.filter_by(username=username).first_or_404()
    chats = user.chats
    news = user.news[::-1][:app.config['NEWS_PER_USER_PAGE']]
    return render_template('user.html', user=user, chats=chats, news=news, title=user.username)


@app.route('/write_message/<username>')
@login_required
def write_message(username):
    """
    метод перехода на страницу личной переписки с пльзователем

    :param username: имя пользователя
    :type username: строка
    :return: переход на метод chat(name)
    """
    user = User.query.filter_by(username=username).first_or_404()
    chat = Chat.query.filter_by(name='none'+user.username+current_user.username).first()
    if chat is None:
        chat = Chat.query.filter_by(name='none' + current_user.username + user.username).first()
    if chat is None:
        chat = Chat(name='none' + user.username + current_user.username)
        chat.users.append(current_user)
        chat.users.append(user)
        post = Post(body=f'{current_user.username} создал чат', author=current_user, chat=chat,
                    timestamp=datetime.now(pytz.timezone('Europe/Moscow')))
        db.session.add(post)
        db.session.commit()
    return redirect(url_for('chat', chat_id=chat.id))


@app.route('/chat/<chat_id>', methods=['GET'])
@login_required
def chat(chat_id):
    """
    метод отбражения страницы чата

    :param chat_id: id чата
    :type chat_id: число
    :return: страница чата
    """
    chat = Chat.query.filter_by(id=chat_id).first()
    page = request.args.get('page', len(list(chat.posts)) // app.config['MESSAGES_PER_PAGE'] + 1, type=int)
    posts = chat.posts.paginate(page, app.config['MESSAGES_PER_PAGE'], False)
    next_url = url_for('chat', chat_id=chat_id, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('chat', chat_id=chat_id, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("chat.html", title='Home Page', chat=chat,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/message/<chat_id>', methods=['POST'])
@login_required
def message(chat_id):
    text = request.form.get('text')
    chat = Chat.query.filter_by(id=chat_id).first()
    post = Post(body=text, author=current_user, chat=chat,
                timestamp=datetime.now(pytz.timezone('Europe/Moscow')))
    db.session.add(post)
    db.session.commit()
    return redirect(url_for('chat', chat_id=chat_id))


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    метод отбражения страницы изменения данных пользователя

    :return: страница изменения данных пользователя или переход на метод user(username)
    """
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Ваши изменения были сохранены.')
        return redirect(url_for('user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Изменение профиля',
                           form=form)


@app.route('/invite_user/<chat_id>', methods=['GET', 'POST'])
@login_required
def invite_user(chat_id):
    """
    метод приглашения аользователя в чат

    :param chat_id: id чата
    :type chat_id: число
    :return: страница поиска пользователя или переход на метод chat(name)
    """
    form = SearchUserForm()
    chat = Chat.query.filter_by(id=chat_id).first()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            flash('извините, пользователя с таким именем не существует')
            return redirect(url_for('invite_user', chat_id=chat_id))
        invitation = Invitation()
        invitation.user = user
        invitation.chat = chat
        db.session.add(invitation)
        db.session.commit()
        flash('Поздравляю, вы приглосили нового пользователя!')
        return redirect(url_for('chat', chat_id=chat_id))
    return render_template('search_user.html', title='Поиск беседы', form=form)


@app.route('/accept_the_invitation/<invitation_id>')
@login_required
def accept_the_invitation(invitation_id):
    """
    метод принятия приглашения

    :param invitation_id: id приглашения
    :type invitation_id: строка
    :return: переход на метод index()
    """
    invitation = Invitation.query.filter_by(id=int(invitation_id)).first()
    current_user.chats.append(invitation.chat)
    db.session.delete(invitation)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/decline_the_invitation/<invitation_id>')
@login_required
def decline_the_invitation(invitation_id):
    """
    метод отклонения приглашения

    :param invitation_id: id приглашения
    :type invitation_id: строка
    :return: переход на метод index()
    """
    invitation = Invitation.query.filter_by(id=int(invitation_id)).first()
    db.session.delete(invitation)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/follow/<username>')
@login_required
def follow(username):
    """
    метод добавления пользователя в список друзей

    :param username: имя пользователя
    :type username: строка
    :return: переход на метод index()
    """
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Пользователь {} не найден.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('Вы не можете подружиться с самим собой')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    """
    метод удаления пользователя из списока друзей

    :param username: имя пользователя
    :type username: строка
    :return: переход на метод index()
    """
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Пользователь {} не найден.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('Вы не можете подружиться с самим собой.')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    return redirect(url_for('user', username=username))


@app.route('/list_of_friends', methods=['GET', 'POST'])
@login_required
def list_of_friends():
    """
    метод отбражения страницы списка друзей

    :return: страница списка друзей
    """
    users = User.query.all()
    followers = []
    followed = []
    for user in users:
        if user.is_following(current_user):
            followers.append(user)
        elif current_user.is_following(user):
            followed.append(user)
    form = SearchUserForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            flash('извините, пользователя с таким именем не существует')
            return redirect(url_for('list_of_friends'))
        return redirect(url_for('user', username=user.username))
    return render_template('list_of_friends.html', title='Список друзей', followers=followers, followed=followed,
                           form=form)


@app.route('/upload', methods=['POST'])
@login_required
def upload():
    file = request.files['file']
    img = file.read()
    current_user.image = sqlite3.Binary(img)
    db.session.commit()
    return redirect(url_for('user', username=current_user.username))


@app.route('/upload_chat_image/<chat_id>', methods=['POST'])
@login_required
def upload_chat_image(chat_id):
    file = request.files['file']
    img = file.read()
    chat = Chat.query.filter_by(id=chat_id).first()
    chat.image = sqlite3.Binary(img)
    db.session.commit()
    return redirect(url_for('chat', chat_id=chat_id))


@app.route('/create_news', methods=['GET', 'POST'])
@login_required
def create_news():
    form = CreateNewsForm()
    if form.validate_on_submit():
        news = News(text=form.text.data, timestamp=datetime.now(pytz.timezone('Europe/Moscow')),
                    user_id=current_user.id)
        db.session.add(news)
        db.session.commit()
        return render_template('set_news_image.html', title='Выбор изображения', news_id=news.id)
    return render_template('create_news.html', title='Создание новости', form=form)


@app.route('/comment/<username>/<news_id>', methods=['POST'])
@login_required
def comment(username, news_id):
    text = request.form.get('comment')
    news = News.query.filter_by(id=news_id).first()
    post = Post(body=text, author=current_user, news=news,
                timestamp=datetime.now(pytz.timezone('Europe/Moscow')))
    db.session.add(post)
    db.session.commit()
    return redirect(url_for('user', username=username))


@app.route('/comment_from_news/<username>/<news_id>', methods=['POST'])
@login_required
def comment_from_news(username, news_id):
    text = request.form.get('comment')
    news = News.query.filter_by(id=news_id).first()
    post = Post(body=text, author=current_user, news=news,
                timestamp=datetime.now(pytz.timezone('Europe/Moscow')))
    db.session.add(post)
    db.session.commit()
    return redirect(url_for('news'))


@app.route('/upload_news_image/<news_id>', methods=['POST'])
@login_required
def upload_news_image(news_id):
    file = request.files['file']
    img = file.read()
    news = News.query.filter_by(id=news_id).first()
    news.image = sqlite3.Binary(img)
    db.session.commit()
    return redirect(url_for('user', username=current_user.username))


@app.route('/news')
@login_required
def news():
    """
    метод отбражения страницы новостей

    :return: страница новостей
    """
    news = []
    users = User.query.all()
    followers = []
    followed = []
    for user in users:
        if user.is_following(current_user):
            followers.append(user)
        elif current_user.is_following(user):
            followed.append(user)
    for follower in followers:
        news += follower.news
    for follower in followed:
        news += follower.news
    news.sort(key=lambda x: x.timestamp)
    return render_template('news.html', title='Новости', news=news[::-1][:app.config['NEWS_PER_PAGE']])
