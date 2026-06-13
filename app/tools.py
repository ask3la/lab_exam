import hashlib
import html
import os
import re

from flask import current_app
from markupsafe import Markup
from werkzeug.utils import secure_filename

try:
    import bleach
except ImportError:
    bleach = None

try:
    import markdown
except ImportError:
    markdown = None


ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'blockquote', 'code',
    'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a',
]
ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}


def sanitize_markdown(value):
    value = value or ''
    if bleach:
        return bleach.clean(value, tags=[], attributes={}, strip=True).strip()
    return re.sub(r'<[^>]*>', '', value).strip()


def render_markdown(value):
    value = value or ''
    if markdown:
        rendered = markdown.markdown(value, extensions=['extra', 'sane_lists'])
    else:
        rendered = html.escape(value)
        rendered = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', rendered)
        rendered = re.sub(r'\*(.+?)\*', r'<em>\1</em>', rendered)
        rendered = re.sub(r'^### (.+)$', r'<h3>\1</h3>', rendered, flags=re.MULTILINE)
        rendered = re.sub(r'^## (.+)$', r'<h2>\1</h2>', rendered, flags=re.MULTILINE)
        rendered = re.sub(r'^# (.+)$', r'<h1>\1</h1>', rendered, flags=re.MULTILINE)
        rendered = '<p>' + rendered.replace('\n\n', '</p><p>').replace('\n', '<br>') + '</p>'
    if bleach:
        rendered = bleach.clean(rendered, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    return Markup(rendered)


def validate_cover(file):
    if not file or not file.filename:
        return 'Необходимо выбрать файл обложки.'
    extension = os.path.splitext(secure_filename(file.filename))[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return 'Допустимые форматы обложки: JPG, PNG, WEBP, GIF.'
    return None


def prepare_cover(file):
    data = file.read()
    file.seek(0)
    return {
        'file_name': secure_filename(file.filename),
        'mime_type': file.mimetype or 'application/octet-stream',
        'md5_hash': hashlib.md5(data).hexdigest(),
        'data': data,
    }


def save_cover_file(cover_data):
    extension = os.path.splitext(cover_data['file_name'])[1].lower()
    storage_filename = f"{cover_data['md5_hash']}{extension}"
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], storage_filename)
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    if not os.path.exists(path):
        with open(path, 'wb') as file:
            file.write(cover_data['data'])


def delete_cover_file(cover):
    if not cover:
        return
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], cover.storage_filename)
    if not os.path.exists(path):
        return
    from models import Cover
    same_file_count = Cover.query.filter(
        Cover.md5_hash == cover.md5_hash,
        Cover.id != cover.id,
    ).count()
    if same_file_count == 0:
        os.remove(path)
