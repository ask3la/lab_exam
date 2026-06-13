from urllib.parse import urljoin, urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_user, logout_user

from models import User, db
from permissions import AUTH_MESSAGE


bp = Blueprint('auth', __name__, url_prefix='/auth')


def init_login_manager(app):
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = AUTH_MESSAGE
    login_manager.login_message_category = 'warning'
    login_manager.user_loader(load_user)
    login_manager.init_app(app)


def load_user(user_id):
    return db.session.get(User, int(user_id))


def is_safe_url(target):
    if not target:
        return False
    reference = urlparse(request.host_url)
    tested = urlparse(urljoin(request.host_url, target))
    return tested.scheme in ('http', 'https') and reference.netloc == tested.netloc


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('books.index'))
    if request.method == 'POST':
        login_value = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        user = db.session.execute(db.select(User).filter_by(login=login_value)).scalar_one_or_none()
        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember_me') == 'on')
            next_page = request.args.get('next')
            return redirect(next_page if is_safe_url(next_page) else url_for('books.index'))
        flash('Невозможно аутентифицироваться с указанными логином и паролем', 'danger')
    return render_template('auth/login.html', title='Вход')


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(request.referrer or url_for('books.index'))
