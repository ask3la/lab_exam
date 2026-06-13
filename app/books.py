import os
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError

from models import Book, Cover, Genre, Review, ReviewStatus, db
from permissions import ROLE_ADMIN, ROLE_MODERATOR, has_role, role_required
from tools import delete_cover_file, prepare_cover, sanitize_markdown, save_cover_file, validate_cover


bp = Blueprint('books', __name__)


def form_data(book=None):
    if request.method == 'POST':
        return {
            'title': request.form.get('title', '').strip(),
            'description': request.form.get('description', '').strip(),
            'year': request.form.get('year', '').strip(),
            'publisher': request.form.get('publisher', '').strip(),
            'author': request.form.get('author', '').strip(),
            'pages': request.form.get('pages', '').strip(),
            'genre_ids': request.form.getlist('genre_ids'),
        }
    return {
        'title': book.title if book else '',
        'description': book.description if book else '',
        'year': str(book.year) if book else '',
        'publisher': book.publisher if book else '',
        'author': book.author if book else '',
        'pages': str(book.pages) if book else '',
        'genre_ids': [str(genre.id) for genre in book.genres] if book else [],
    }


def validate_book(data, require_cover):
    errors = {}
    for field in ('title', 'description', 'year', 'publisher', 'author', 'pages'):
        if not data[field]:
            errors[field] = 'Поле не может быть пустым.'
    if not data['genre_ids']:
        errors['genre_ids'] = 'Выберите хотя бы один жанр.'
    try:
        year = int(data['year'])
        if year < 1 or year > datetime.now().year:
            errors['year'] = 'Укажите корректный год издания.'
    except ValueError:
        errors['year'] = 'Год должен быть целым числом.'
    try:
        pages = int(data['pages'])
        if pages < 1:
            errors['pages'] = 'Количество страниц должно быть больше нуля.'
    except ValueError:
        errors['pages'] = 'Количество страниц должно быть целым числом.'
    if require_cover:
        cover_error = validate_cover(request.files.get('cover'))
        if cover_error:
            errors['cover'] = cover_error
    return errors


@bp.route('/')
def index():
    query = db.select(Book).order_by(Book.year.desc(), Book.id.desc())
    pagination = db.paginate(query, per_page=10, error_out=False)
    return render_template('books/index.html', title='Электронная библиотека', pagination=pagination)


@bp.route('/books/<int:book_id>')
def show(book_id):
    book = db.get_or_404(Book, book_id)
    approved_status = db.session.execute(
        db.select(ReviewStatus).filter_by(name='Одобрена')
    ).scalar_one()
    approved_reviews = db.session.execute(
        db.select(Review)
        .filter_by(book_id=book.id, status_id=approved_status.id)
        .order_by(Review.created_at.desc())
    ).scalars().all()
    own_review = None
    if current_user.is_authenticated:
        own_review = db.session.execute(
            db.select(Review).filter_by(book_id=book.id, user_id=current_user.id)
        ).scalar_one_or_none()
    return render_template(
        'books/show.html',
        title=book.title,
        book=book,
        approved_reviews=approved_reviews,
        own_review=own_review,
    )


@bp.route('/books/new', methods=['GET', 'POST'])
@role_required(ROLE_ADMIN)
def create():
    data = form_data()
    errors = {}
    genres = db.session.execute(db.select(Genre).order_by(Genre.name)).scalars().all()
    if request.method == 'POST':
        errors = validate_book(data, True)
        if not errors:
            cover_data = prepare_cover(request.files['cover'])
            book = Book(
                title=data['title'],
                description=sanitize_markdown(data['description']),
                year=int(data['year']),
                publisher=data['publisher'],
                author=data['author'],
                pages=int(data['pages']),
            )
            book.genres = db.session.execute(
                db.select(Genre).filter(Genre.id.in_([int(value) for value in data['genre_ids']]))
            ).scalars().all()
            try:
                db.session.add(book)
                db.session.flush()
                cover = Cover(
                    file_name=cover_data['file_name'],
                    mime_type=cover_data['mime_type'],
                    md5_hash=cover_data['md5_hash'],
                    book_id=book.id,
                )
                db.session.add(cover)
                db.session.flush()
                save_cover_file(cover_data)
                db.session.commit()
                flash('Книга успешно добавлена.', 'success')
                return redirect(url_for('books.show', book_id=book.id))
            except (SQLAlchemyError, OSError):
                db.session.rollback()
                flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'danger')
    return render_template(
        'books/form_page.html',
        title='Добавление книги',
        heading='Добавление книги',
        data=data,
        errors=errors,
        genres=genres,
        is_create=True,
    )


@bp.route('/books/<int:book_id>/edit', methods=['GET', 'POST'])
@role_required(ROLE_ADMIN, ROLE_MODERATOR)
def edit(book_id):
    book = db.get_or_404(Book, book_id)
    data = form_data(book)
    errors = {}
    genres = db.session.execute(db.select(Genre).order_by(Genre.name)).scalars().all()
    if request.method == 'POST':
        errors = validate_book(data, False)
        if not errors:
            book.title = data['title']
            book.description = sanitize_markdown(data['description'])
            book.year = int(data['year'])
            book.publisher = data['publisher']
            book.author = data['author']
            book.pages = int(data['pages'])
            book.genres = db.session.execute(
                db.select(Genre).filter(Genre.id.in_([int(value) for value in data['genre_ids']]))
            ).scalars().all()
            try:
                db.session.commit()
                flash('Данные книги успешно обновлены.', 'success')
                return redirect(url_for('books.show', book_id=book.id))
            except SQLAlchemyError:
                db.session.rollback()
                flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'danger')
    return render_template(
        'books/form_page.html',
        title='Редактирование книги',
        heading=f'Редактирование книги «{book.title}»',
        data=data,
        errors=errors,
        genres=genres,
        is_create=False,
        book=book,
    )


@bp.route('/books/<int:book_id>/delete', methods=['POST'])
@role_required(ROLE_ADMIN)
def delete(book_id):
    book = db.get_or_404(Book, book_id)
    cover = book.cover
    try:
        delete_cover_file(cover)
        db.session.delete(book)
        db.session.commit()
        flash('Книга успешно удалена.', 'success')
    except (SQLAlchemyError, OSError):
        db.session.rollback()
        flash('При удалении книги возникла ошибка.', 'danger')
    return redirect(url_for('books.index'))


@bp.route('/covers/<int:cover_id>')
def cover(cover_id):
    image = db.get_or_404(Cover, cover_id)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], image.storage_filename)
