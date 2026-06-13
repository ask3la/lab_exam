from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError

from models import Book, Review, ReviewStatus, db
from permissions import ROLE_ADMIN, ROLE_MODERATOR, ROLE_USER, role_required
from tools import sanitize_markdown


bp = Blueprint('reviews', __name__, url_prefix='/reviews')

RATING_OPTIONS = [
    (5, 'Отлично'),
    (4, 'Хорошо'),
    (3, 'Удовлетворительно'),
    (2, 'Неудовлетворительно'),
    (1, 'Плохо'),
    (0, 'Ужасно'),
]


@bp.route('/book/<int:book_id>/new', methods=['GET', 'POST'])
@role_required(ROLE_ADMIN, ROLE_MODERATOR, ROLE_USER)
def create(book_id):
    book = db.get_or_404(Book, book_id)
    existing = db.session.execute(
        db.select(Review).filter_by(book_id=book.id, user_id=current_user.id)
    ).scalar_one_or_none()
    if existing:
        flash('Вы уже оставили рецензию на эту книгу.', 'warning')
        return redirect(url_for('books.show', book_id=book.id))
    data = {
        'rating': request.form.get('rating', '5'),
        'text': request.form.get('text', ''),
    }
    errors = {}
    if request.method == 'POST':
        try:
            rating = int(data['rating'])
            if rating < 0 or rating > 5:
                errors['rating'] = 'Выберите оценку от 0 до 5.'
        except ValueError:
            errors['rating'] = 'Выберите корректную оценку.'
        if not data['text'].strip():
            errors['text'] = 'Поле не может быть пустым.'
        if not errors:
            pending_status = db.session.execute(
                db.select(ReviewStatus).filter_by(name='На рассмотрении')
            ).scalar_one()
            review = Review(
                book_id=book.id,
                user_id=current_user.id,
                status_id=pending_status.id,
                rating=rating,
                text=sanitize_markdown(data['text']),
            )
            try:
                db.session.add(review)
                db.session.commit()
                flash('Рецензия отправлена на рассмотрение.', 'success')
                return redirect(url_for('books.show', book_id=book.id))
            except SQLAlchemyError:
                db.session.rollback()
                flash('При сохранении рецензии возникла ошибка.', 'danger')
    return render_template(
        'reviews/form.html',
        title='Новая рецензия',
        book=book,
        data=data,
        errors=errors,
        rating_options=RATING_OPTIONS,
    )


@bp.route('/mine')
@role_required(ROLE_USER)
def mine():
    reviews = db.session.execute(
        db.select(Review)
        .filter_by(user_id=current_user.id)
        .order_by(Review.created_at.desc())
    ).scalars().all()
    return render_template('reviews/mine.html', title='Мои рецензии', reviews=reviews)


@bp.route('/moderation')
@role_required(ROLE_ADMIN, ROLE_MODERATOR)
def moderation():
    pending_status = db.session.execute(
        db.select(ReviewStatus).filter_by(name='На рассмотрении')
    ).scalar_one()
    query = (
        db.select(Review)
        .filter_by(status_id=pending_status.id)
        .order_by(Review.created_at.asc())
    )
    pagination = db.paginate(query, per_page=10, error_out=False)
    return render_template(
        'reviews/moderation.html',
        title='Модерация рецензий',
        pagination=pagination,
    )


@bp.route('/moderation/<int:review_id>')
@role_required(ROLE_ADMIN, ROLE_MODERATOR)
def moderation_show(review_id):
    review = db.get_or_404(Review, review_id)
    return render_template(
        'reviews/moderation_show.html',
        title='Рассмотрение рецензии',
        review=review,
    )


@bp.route('/moderation/<int:review_id>/<action>', methods=['POST'])
@role_required(ROLE_ADMIN, ROLE_MODERATOR)
def moderation_update(review_id, action):
    review = db.get_or_404(Review, review_id)
    status_name = {'approve': 'Одобрена', 'reject': 'Отклонена'}.get(action)
    if not status_name:
        flash('Неизвестное действие.', 'danger')
        return redirect(url_for('reviews.moderation'))
    status = db.session.execute(
        db.select(ReviewStatus).filter_by(name=status_name)
    ).scalar_one()
    review.status_id = status.id
    try:
        db.session.commit()
        flash(f'Рецензия получила статус «{status.name}».', 'success')
    except SQLAlchemyError:
        db.session.rollback()
        flash('При изменении статуса возникла ошибка.', 'danger')
    return redirect(url_for('reviews.moderation'))
