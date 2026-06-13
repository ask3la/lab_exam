from alembic import op
import sqlalchemy as sa


revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'genres',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_genres')),
        sa.UniqueConstraint('name', name=op.f('uq_genres_name')),
    )
    op.create_table(
        'review_statuses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_review_statuses')),
        sa.UniqueConstraint('name', name=op.f('uq_review_statuses_name')),
    )
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_roles')),
        sa.UniqueConstraint('name', name=op.f('uq_roles_name')),
    )
    op.create_table(
        'books',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('publisher', sa.String(length=255), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=False),
        sa.Column('pages', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_books')),
    )
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('login', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('middle_name', sa.String(length=100), nullable=True),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('fk_users_role_id_roles')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('login', name=op.f('uq_users_login')),
    )
    op.create_table(
        'book_genres',
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('genre_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], name=op.f('fk_book_genres_book_id_books'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['genre_id'], ['genres.id'], name=op.f('fk_book_genres_genre_id_genres'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('book_id', 'genre_id', name=op.f('pk_book_genres')),
    )
    op.create_table(
        'covers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('md5_hash', sa.String(length=32), nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], name=op.f('fk_covers_book_id_books'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_covers')),
        sa.UniqueConstraint('book_id', name=op.f('uq_covers_book_id')),
    )
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('rating >= 0 AND rating <= 5', name=op.f('ck_reviews_rating_range')),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], name=op.f('fk_reviews_book_id_books'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['status_id'], ['review_statuses.id'], name=op.f('fk_reviews_status_id_review_statuses')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_reviews_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_reviews')),
        sa.UniqueConstraint('book_id', 'user_id', name='uq_reviews_book_user'),
    )


def downgrade():
    op.drop_table('reviews')
    op.drop_table('covers')
    op.drop_table('book_genres')
    op.drop_table('users')
    op.drop_table('books')
    op.drop_table('roles')
    op.drop_table('review_statuses')
    op.drop_table('genres')
