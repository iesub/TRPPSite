from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import User, Chat

"""
модуль forms
"""
class LoginForm(FlaskForm):
    """
    форма авторизации пользователя
    """
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    """
    форма регистрации пользователя
    """
    username = StringField('Имя пользователя', validators=[DataRequired()])
    email = StringField('Адрес электронной почты', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField(
        'Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        """
        метод проверки имени пользователя

        :param username: имя пользователя
        :type username: строка
        :return: ничего не возвращает
        """
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Пожалуста, используйте другое имя пользователя.')

    def validate_email(self, email):
        """
        метод проверки email

        :param email: email
        :type email: строка
        :return: ничего не возвращает
        """
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Пожалуйста, используйте другой адрес электронной почты.')


class EditProfileForm(FlaskForm):
    """
    форма изменения профиля пользователя
    """
    username = StringField('Новое имя пользователя', validators=[DataRequired()])
    about_me = TextAreaField('О себе', validators=[Length(min=0, max=140)])
    submit = SubmitField('Подтвердить')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        """
        метод проверки имени пользователя

        :param username: имя пользователя
        :type username: строка
        :return: ничего не возвращает
        """
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Пожалуйста, используйте другое имя пользоателя.')


class SearchAndCreateChatForm(FlaskForm):
    """
    форма создания чата
    """
    search_name = StringField('Название', validators=[])
    search_submit = SubmitField('найти чат')
    create_name = StringField('Название', validators=[])
    create_submit = SubmitField('создать чат')

    def validate_name(self, name):
        """
        метод проверки названия чата

        :param name: название чата
        :type name: строка
        :return: ничего не возвращает
        """
        chat = Chat.query.filter_by(name=name.data).first()
        if chat is not None:
            raise ValidationError('Пожалуста, используйте другое название для беседы.')


class SearchUserForm(FlaskForm):
    """
    форма поиска пользователя
    """
    username = StringField('Имя пользователя', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')


class PostForm(FlaskForm):
    """
    форма написания сообщения
    """
    post = TextAreaField('Написать сообщение', validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('отправить')


class CreateNewsForm(FlaskForm):
    text = TextAreaField('Сообщение')
    submit = SubmitField('перейти к выбору изображения')
