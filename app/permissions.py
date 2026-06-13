from functools import wraps

from flask import flash, redirect, request, url_for
from flask_login import current_user


ROLE_ADMIN = 'Администратор'
ROLE_MODERATOR = 'Модератор'
ROLE_USER = 'Пользователь'
AUTH_MESSAGE = 'Для выполнения данного действия необходимо пройти процедуру аутентификации'
RIGHTS_MESSAGE = 'У вас недостаточно прав для выполнения данного действия'


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash(AUTH_MESSAGE, 'warning')
                return redirect(url_for('auth.login', next=request.url))
            if not current_user.role or current_user.role.name not in roles:
                flash(RIGHTS_MESSAGE, 'danger')
                return redirect(url_for('books.index'))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def has_role(*roles):
    return current_user.is_authenticated and current_user.role and current_user.role.name in roles
