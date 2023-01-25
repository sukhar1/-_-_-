from flask import Flask, render_template, redirect
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import redirect
from flask_login import LoginManager

from forms.notes import NotesForm
from forms.user import RegisterForm, LoginForm
from models import db_session
from sqlalchemy import orm
from models.notes import Notes
from models.users import User


app = Flask(name)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'very_secret_key'

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

def main():
    db_session.global_init("db/notes.db")
    app.run()



@app.route('/')
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        notes = db_sess.query(Notes).filter((Notes.user == current_user) | (Notes.is_private != True))
    else:
        notes = db_sess.query(Notes).filter(Notes.is_private != True)
    return render_template("index.html", notes=notes)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form, message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,message="Такой пользователь уже есть")
        user = User(name=form.name.data, email=form.email.data, about=form.about.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        return render_template('login.html', message='Неправильный логин или пароль', form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/notes', methods=['GET', 'POST'])
@login_required
def add_notes():
    form = NotesForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        notes = Notes()
        notes.title = form.title.data
        notes.content = form.content.data
        notes.is_private = form.is_private.data
        current_user.note.append(notes)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('notes.html', title='Добавление записи', form=form)


@app.errorhandler(404)
def error404(error):
    return 'Страница не найдена ('


if name == 'main':
    main()