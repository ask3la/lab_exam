import os

from flask import Flask
from flask_migrate import Migrate

from auth import bp as auth_bp, init_login_manager
from books import bp as books_bp
from models import db
from permissions import ROLE_ADMIN, ROLE_MODERATOR, ROLE_USER, has_role
from reviews import bp as reviews_bp
from seed import seed_data
from tools import render_markdown


app = Flask(__name__)
application = app
app.config.from_pyfile('config.py')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db.init_app(app)
Migrate(app, db)
init_login_manager(app)

app.register_blueprint(auth_bp)
app.register_blueprint(books_bp)
app.register_blueprint(reviews_bp)


@app.context_processor
def inject_helpers():
    return {
        'ROLE_ADMIN': ROLE_ADMIN,
        'ROLE_MODERATOR': ROLE_MODERATOR,
        'ROLE_USER': ROLE_USER,
        'has_role': has_role,
    }


app.jinja_env.filters['markdown'] = render_markdown


@app.cli.command('seed')
def seed_command():
    seed_data()
    print('Начальные данные добавлены.')


if __name__ == '__main__':
    app.run()
