import asyncio
import aiohttp
import urllib.parse
from flask import abort, flash, redirect, render_template, request, url_for

from .models import URLMap
from .app import app, db
from .forms import HomeForm, DownloadForm
from .utils import get_unique_short_id
from .constants import REQUEST_UPLOAD_URL, DOWNLOAD_LINK_URL


@app.route('/', methods=['GET', 'POST'])
def index_view():
    form = HomeForm()
    if form.validate_on_submit():
        original_link = form.original_link.data
        custom_id = form.custom_id.data.strip() if form.custom_id.data else None

        if custom_id:
            existing = URLMap.query.filter_by(short=custom_id).first()
            if existing or custom_id == 'files':
                flash('Предложенный вариант короткой ссылки уже существует.')
                return render_template('index.html', form=form)
            short_id = custom_id
        else:
            short_id = get_unique_short_id()

        url_map = URLMap(original=original_link, short=short_id)
        try:
            db.session.add(url_map)
            db.session.commit()
            short_link = url_for('redirect_view', short_id=short_id, _external=True)
            return render_template('index.html', form=form, short_link=short_link)
        except Exception:
            db.session.rollback()
            if custom_id:
                flash('Предложенный вариант короткой ссылки уже существует.')
            else:
                short_id = get_unique_short_id()
                url_map = URLMap(original=original_link, short=short_id)
                db.session.add(url_map)
                db.session.commit()
                short_link = url_for('redirect_view', short_id=short_id, _external=True)
                return render_template('index.html', form=form, short_link=short_link)

    return render_template('index.html', form=form)


@app.route('/files', methods=['GET', 'POST'])
def files_view():
    form = DownloadForm()
    uploaded_files = []

    if request.method == 'POST':
        files = request.files.getlist('files')
        if not files or not any(f.filename for f in files):
            flash('Необходимо выбрать хотя бы один файл.')
        else:

            try:
                uploaded_files = asyncio.run(upload_files_to_disk(files))
                if not uploaded_files:
                    flash('Не удалось загрузить файлы.')
            except Exception as e:
                flash(f'Ошибка при загрузке файлов: {str(e)}')

    return render_template('files.html', form=form, uploaded_files=uploaded_files)


async def upload_files_to_disk(files):
    """Асинхронная загрузка файлов на Яндекс Диск."""
    disk_token = app.config.get('DISK_TOKEN')
    if not disk_token:
        return []

    auth_headers = {'Authorization': f'OAuth {disk_token}'}
    file_results = []

    async with aiohttp.ClientSession() as session:
        tasks = []
        for file in files:
            if file.filename:
                tasks.append(upload_single_file(session, file, auth_headers))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, dict) and 'error' not in result:
                file_results.append(result)

    uploaded_files = []
    for file_result in file_results:
        if 'download_link' in file_result:
            short_id = get_unique_short_id()
            url_map = URLMap(original=file_result['download_link'], short=short_id)
            db.session.add(url_map)
            db.session.commit()
            short_link = url_for('redirect_view', short_id=short_id, _external=True)
            uploaded_files.append({
                'name': file_result['name'],
                'short_link': short_link
            })

    return uploaded_files


async def upload_single_file(session, file, auth_headers):
    """Загружает один файл на Яндекс Диск и возвращает download_link и filename."""
    try:
        filename = file.filename
        file_content = file.read()
        file.seek(0)

        path = f'app:/{filename}'
        params = {'path': path, 'overwrite': 'True'}

        async with session.get(REQUEST_UPLOAD_URL, headers=auth_headers, params=params) as resp:
            if resp.status != 200:
                return {'error': f'Ошибка получения URL для загрузки: {resp.status}'}
            upload_data = await resp.json()
            upload_url = upload_data['href']

        async with session.put(upload_url, data=file_content) as resp:
            if resp.status not in (201, 202):
                return {'error': f'Ошибка загрузки файла: {resp.status}'}

            location = resp.headers.get('Location', '')
            if location:

                location = urllib.parse.unquote(location)
                if location.startswith('/disk'):
                    location = location.replace('/disk', '', 1)

                download_params = {'path': location}
                async with session.get(DOWNLOAD_LINK_URL, headers=auth_headers, params=download_params) as download_resp:
                    if download_resp.status == 200:
                        download_data = await download_resp.json()
                        download_link = download_data['href']
                        
                        return {
                            'name': filename,
                            'download_link': download_link
                        }

        return {'error': 'Не удалось получить ссылку на скачивание'}
    except Exception as e:
        return {'error': str(e)}


@app.route('/<short_id>')
def redirect_view(short_id):
    url_map = URLMap.query.filter_by(short=short_id).first()
    if url_map:
        return redirect(url_map.original)
    else:
        abort(404)
