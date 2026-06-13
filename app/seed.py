import hashlib
import os

from flask import current_app

from models import Book, Cover, Genre, ReviewStatus, Role, User, db


DEFAULT_COVER = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="900" viewBox="0 0 600 900">'
    '<rect width="600" height="900" fill="#27231f"/>'
    '<rect x="55" y="55" width="490" height="790" fill="none" stroke="#d19b36" stroke-width="5"/>'
    '<text x="300" y="420" text-anchor="middle" fill="#f4f0e8" font-family="serif" font-size="48">Электронная</text>'
    '<text x="300" y="485" text-anchor="middle" fill="#f4f0e8" font-family="serif" font-size="48">библиотека</text>'
    '<circle cx="300" cy="590" r="34" fill="#a6492d"/>'
    '</svg>'
).encode('utf-8')


def ensure_role(name, description):
    role = db.session.execute(db.select(Role).filter_by(name=name)).scalar_one_or_none()
    if not role:
        role = Role(name=name, description=description)
        db.session.add(role)
        db.session.flush()
    return role


def ensure_user(login, password, last_name, first_name, middle_name, role):
    user = db.session.execute(db.select(User).filter_by(login=login)).scalar_one_or_none()
    if not user:
        user = User(
            login=login,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            role_id=role.id,
        )
        user.set_password(password)
        db.session.add(user)


def ensure_reference_data():
    roles = {
        'Администратор': ensure_role('Администратор', 'Полный доступ к системе'),
        'Модератор': ensure_role('Модератор', 'Редактирование книг и модерация рецензий'),
        'Пользователь': ensure_role('Пользователь', 'Создание рецензий'),
    }
    for name in ('Роман', 'Фантастика', 'Научная литература', 'Программирование', 'История'):
        if not db.session.execute(db.select(Genre).filter_by(name=name)).scalar_one_or_none():
            db.session.add(Genre(name=name))
    for name in ('На рассмотрении', 'Одобрена', 'Отклонена'):
        if not db.session.execute(db.select(ReviewStatus).filter_by(name=name)).scalar_one_or_none():
            db.session.add(ReviewStatus(name=name))
    db.session.flush()
    ensure_user('admin', 'Admin123!', 'Арзамазов', 'Виктор', 'Владимирович', roles['Администратор'])
    ensure_user('moderator', 'Moderator123!', 'Петров', 'Петр', 'Петрович', roles['Модератор'])
    ensure_user('user', 'User123!', 'Иванов', 'Иван', 'Иванович', roles['Пользователь'])
    db.session.commit()


def ensure_books():
    if db.session.execute(db.select(Book)).first():
        return
    genres = {
        genre.name: genre
        for genre in db.session.execute(db.select(Genre)).scalars().all()
    }
    books = [
        ('Мастер и Маргарита', 1967, 'Азбука', 'Михаил Булгаков', 480, ['Роман', 'Фантастика']),
        ('Чистый код', 2008, 'Питер', 'Роберт Мартин', 464, ['Программирование']),
        ('Краткая история времени', 1988, 'АСТ', 'Стивен Хокинг', 232, ['Научная литература']),
    ]
    md5_hash = hashlib.md5(DEFAULT_COVER).hexdigest()
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], f'{md5_hash}.svg')
    if not os.path.exists(path):
        with open(path, 'wb') as file:
            file.write(DEFAULT_COVER)
    for title, year, publisher, author, pages, genre_names in books:
        book = Book(
            title=title,
            description=f'## {title}\n\nКраткое описание книги **{title}**. Данные можно изменить через интерфейс.',
            year=year,
            publisher=publisher,
            author=author,
            pages=pages,
        )
        book.genres = [genres[name] for name in genre_names]
        db.session.add(book)
        db.session.flush()
        db.session.add(Cover(
            file_name='default.svg',
            mime_type='image/svg+xml',
            md5_hash=md5_hash,
            book_id=book.id,
        ))
    db.session.commit()


def seed_data():
    ensure_reference_data()
    ensure_books()
