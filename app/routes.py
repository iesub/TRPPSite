# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, url_for, request
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, CreateChatForm, SearchChatForm, SearchUserForm, \
    PostForm
from flask_login import current_user, login_user
from app.models import User, Chat, Post, Invitation
from flask_login import logout_user, login_required
from datetime import datetime
import pytz


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(pytz.timezone('Europe/Moscow'))
        db.session.commit()


@app.route('/')
@app.route('/index')
@login_required
def index():
    invite = Invitation.query.filter_by(user=current_user).first()
    if invite is None:
        return render_template('index.html', title='Главная страница', chats=current_user.chats, count=0)
    return render_template('index.html', title='Главная страница', chats=current_user.chats,
                           invitations=current_user.invitations, count=1)


@app.route('/login', methods=['GET', 'POST'])
def login():
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
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
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
    user = User.query.filter_by(username=username).first_or_404()
    chats = user.chats
    return render_template('user.html', user=user, chats=chats, title=user.username)


@app.route('/write_message/<username>')
@login_required
def write_message(username):
    user = User.query.filter_by(username=username).first_or_404()
    chat = Chat.query.filter_by(name='none'+user.username+current_user.username).first()
    if chat is None:
        chat = Chat.query.filter_by(name='none' + current_user.username + user.username).first()
    if chat is None:
        chat = Chat(name='none' + user.username + current_user.username)
        chat.users.append(current_user)
        chat.users.append(user)
        db.session.commit()
    return redirect(url_for('chat', name=chat.name))


@app.route('/chat/<name>', methods= ['GET', 'Post'])
@login_required
def chat(name):
    form = PostForm()
    chat = Chat.query.filter_by(name=name).first()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user, chat=chat)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('chat', name=chat.name))
    posts = chat.posts
    return render_template("chat.html", title='Home Page', form=form, chat=chat,
                           posts=posts)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Ваши изменения были сохранены.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Изменение профиля',
                           form=form)


@app.route('/create_chat', methods=['GET', 'POST'])
@login_required
def create_chat():
    form = CreateChatForm()
    if form.validate_on_submit():
        chat = Chat(name=form.name.data)
        chat.users.append(current_user)
        db.session.add(chat)
        db.session.commit()
        flash('Поздравляю, вы создали новую беседу!')
        return redirect(url_for('index'))
    return render_template('create_chat.html', title='Создание беседы', form=form)


@app.route('/search_chat', methods=['GET', 'POST'])
@login_required
def search_chat():
    form = SearchChatForm()
    if form.validate_on_submit():
        chat = Chat.query.filter_by(name = form.name.data).first()
        if chat is None:
            flash('извините, такой беседы не существует')
            return redirect(url_for('search_chat'))
        chat.users.append(current_user)
        db.session.commit()
        flash('Поздравляю, вы присоединились к беседе!')
        return redirect(url_for('index'))
    return render_template('search_chat.html', title='Поиск беседы', form=form)


@app.route('/search_user', methods=['GET', 'POST'])
@login_required
def search_user():
    form = SearchUserForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user is None:
            flash('извините, пользователя с таким именем не существует')
            return redirect(url_for('search_user'))
        chat = Chat(name='none' + user.username + current_user.username)
        chat.users.append(current_user)
        chat.users.append(user)
        db.session.commit()
        flash('Поздравляю, вы присоединились к беседе!')
        return redirect(url_for('index'))
    return render_template('search_user.html', title='Поиск беседы', form=form)


@app.route('/invite_user/<name>', methods=['GET', 'POST'])
@login_required
def invite_user(name):
    form = SearchUserForm()
    chat = Chat.query.filter_by(name=name).first()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            flash('извините, пользователя с таким именем не существует')
            return redirect(url_for('search_user'))
        invitation = Invitation()
        invitation.user = user
        invitation.chat = chat
        db.session.add(invitation)
        db.session.commit()
        flash('Поздравляю, вы приглосили нового пользователя!')
        return redirect(url_for('index'))
    return render_template('search_user.html', title='Поиск беседы', form=form)


@app.route('/accept_the_invitation/<invitation_id>')
@login_required
def accept_the_invitation(invitation_id):
    invitation = Invitation.query.filter_by(id=int(invitation_id)).first()
    current_user.chats.append(invitation.chat)
    db.session.delete(invitation)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/decline_the_invitation/<invitation_id>')
@login_required
def decline_the_invitation(invitation_id):
    invitation = Invitation.query.filter_by(id=int(invitation_id)).first()
    db.session.delete(invitation)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/follow/<username>')
@login_required
def follow(username):
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


@app.route('/list_of_friends')
@login_required
def list_of_friends():
    users = User.query.all()
    followers = []
    followed = []
    for user in users:
        if user.is_following(current_user):
            followers.append(user)
        elif current_user.is_following(user):
            followed.append(user)
    return render_template('list_of_friends.html', title='Список друзей', followers=followers, followed=followed)


@app.route('/news')
@login_required
def news():
    return render_template('news.html', title='Новости')
