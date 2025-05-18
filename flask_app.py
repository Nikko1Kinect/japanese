from flask import Flask, render_template, send_from_directory, request, jsonify, redirect, url_for, session
import os
import json
from ai import ShiritoriAI
from urllib.request import urlretrieve
import logging
from ebooklib import epub
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

path = r"C:\Users\natal\Documents\python_project\learn.japanes\site\\"

app = Flask(__name__)
app.secret_key = "shiritori-secret"
BOOKS_DIR = os.path.join(path, 'books')
BOOKS_METADATA = os.path.join(path, 'books.json')
Manga_METADATA = os.path.join(path, 'manga.json')
PROGRESS_FILE = os.path.join(path, 'progress.json')

# Load books metadata
def load_books():
    if os.path.exists(BOOKS_METADATA):
        with open(BOOKS_METADATA, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Load books metadata
def load_manga():
    if os.path.exists(Manga_METADATA):
        with open(Manga_METADATA, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Load reading progress
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Save reading progress
def save_progress(progress):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=4)

@app.route('/')
def index():
    query = request.args.get('q', '').lower()
    books = load_books()
    progress = load_progress()

    if query:
        books = [book for book in books if query in book['title'].lower() or query in book['author'].lower()]

    return render_template('index.html', books=books, progress=progress)

@app.route("/apps")
def apps():
    updates = [
        {
            "version": "1.2.0",
            "description": "Додано автосинхронізацію таймінгів і покращену точність розпізнавання.",
            "details": [
                "Покращено точність розпізнавання",
                "Зменшено час обробки великих файлів",
                "Новий стиль оформлення субтитрів"
            ]
        },
        {
            "version": "1.0",
            "description": "Реліз",
            "details": [
            ]
        }
    ]
    
    return render_template("apps.html", updates=updates)


@app.route('/manga')
def manga():
    query = request.args.get('q', '').lower()
    books = load_manga()

    if query:
        books = [book for book in books if query in book['title'].lower() or query in book['author'].lower()]

    return render_template('manga.html', books=books)

@app.route('/upload_manga', methods=['POST'])
def upload_manga():
    data = request.form
    file = request.form.get("file_url")
    cover_file = request.files.get('cover_file')


    # Ensure the static/covers directory exists
    covers_dir = os.path.join(path, 'static', 'covers')
    os.makedirs(covers_dir, exist_ok=True)

    # Only allow cover file upload
    if cover_file and cover_file.filename != '':
        cover_path = os.path.join(covers_dir, cover_file.filename)
        cover_file.save(cover_path)
        cover = f'covers/{cover_file.filename}'
    else:
        cover = ''

    # Add metadata to books.json
    books = load_manga()
    books.append({
        "title": data.get('title', 'Untitled'),
        "author": data.get('author', 'Unknown'),
        "cover": cover,
        "filename": file
    })
    with open(Manga_METADATA, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=4)

    return jsonify({"message": "Book uploaded successfully!"})

@app.route('/search_manga')
def search_manga():
    query = request.args.get('q', '').lower()
    books = load_manga()
    filtered_books = [book for book in books if query in book['title'].lower() or query in book['author'].lower()]
    return render_template('index.html', books=filtered_books)

@app.route('/delete_manga', methods=['POST'])
def delete_manga():
    data = request.json
    books = load_manga()
    books = [book for book in books]
    with open(Manga_METADATA, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=4)


@app.route('/books/<filename>')
def book(filename):
    try:
        return send_from_directory(BOOKS_DIR, filename)
    except FileNotFoundError:
        return jsonify({"message": "File not found"}), 404

@app.route('/save_progress', methods=['POST'])
def save_reading_progress():
    data = request.json
    progress = load_progress()
    progress[data['book']] = data['page']
    save_progress(progress)
    return jsonify({"message": "Progress saved successfully!"})

@app.route('/mark_finished', methods=['POST'])
def mark_finished():
    data = request.json
    progress = load_progress()
    progress[data['book']] = "Finished"
    save_progress(progress)
    return jsonify({"message": "Book marked as finished!"})

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    books = load_books()
    filtered_books = [book for book in books if query in book['title'].lower() or query in book['author'].lower()]
    progress = load_progress()
    return render_template('index.html', books=filtered_books, progress=progress)

@app.route('/whats_new')
def whats_new():
    return render_template('whats_new.html', updates=[
         {
            "version": "1.5",
            "description": "Додано новий розділ",
            "details": [
                "Доданий розділ \"Манга\".",
                "Розділ \"Головний\" змінено на \"Книги\""
            ]
        },
        {
            "version": "1.4.5",
            "description": "Виправленння багів та малі дороблення.",
            "details": [
                "Додані для більшості вкладок міні значок вкладки.",
                "Виправленно перегляд епабів.",
            ]
        },
        {
            "version": "1.4",
            "description": "Додано вкладку субтитри де можна отримати субтитри для різних відео та пісень та про проект.",
            "details": [
                "Додана вкладка \"Субтитри\".",
                "Можливість додавати субтитри та відео і аудіо",
                "До ширіторі додано більше слів на る"
            ]
        },
        {
            "version": "1.3",
            "description": "Додана гра в слова しりとり",
            "details": [
                "Додана вкладка \"Ширіторі\".",
                "База із більше ніж 11000 слів.",
                "Працює сканування через Йомічан"
            ]
        },
        {
            "version": "1.2",
            "description": "Додано нові функції для покращення роботи з книгами.",
            "details": [
                "Можливість завантаження книг у формати PDF.",
                "Додано функцію видалення книг.",
                "Додано вкладку 'Що нового' для перегляду оновлень.",
                "Покращено дизайн інтерфейсу для зручності користувачів."
            ]
        },
        {
            "version": "1.0",
            "description": "Додано базовий функціонал для перегляду книг."
        }
    ])

@app.route('/upload', methods=['POST'])
def upload_book():
    data = request.form
    file = request.files.get('file')
    cover_file = request.files.get('cover_file')

    if not file or file.filename == '':
        return jsonify({"message": "No file selected"}), 400

    # Save the book file
    file.save(os.path.join(BOOKS_DIR, file.filename))

    # Ensure the static/covers directory exists
    covers_dir = os.path.join(path, 'static', 'covers')
    os.makedirs(covers_dir, exist_ok=True)

    # Only allow cover file upload
    if cover_file and cover_file.filename != '':
        cover_path = os.path.join(covers_dir, cover_file.filename)
        cover_file.save(cover_path)
        cover = f'covers/{cover_file.filename}'
    else:
        cover = ''

    # Add metadata to books.json
    books = load_books()
    books.append({
        "title": data.get('title', 'Untitled'),
        "author": data.get('author', 'Unknown'),
        "cover": cover,
        "filename": file.filename
    })
    with open(BOOKS_METADATA, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=4)

    return jsonify({"message": "Book uploaded successfully!"})

@app.context_processor
def inject_version():
    return {"version": "1.5"}

@app.route('/delete_book', methods=['POST'])
def delete_book():
    data = request.json
    books = load_books()
    books = [book for book in books if book['filename'] != data['filename']]
    with open(BOOKS_METADATA, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=4)
    # Remove the file from the directory
    file_path = os.path.join(BOOKS_DIR, data['filename'])
    if os.path.exists(file_path):
        os.remove(file_path)
    return jsonify({"message": "Book deleted successfully!"})

@app.route('/viewer/<filename>')
def viewer(filename):
    try:
        file_path = os.path.join(BOOKS_DIR, filename)
        if not os.path.exists(file_path):
            return jsonify({"message": "File not found"}), 404
        if filename.lower().endswith('.epub'):
            book = epub.read_epub(file_path)
            chapters = []
            for item in book.get_items():
                if isinstance(item, epub.EpubHtml):
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    title = soup.title.string if soup.title else item.get_name()
                    text = soup.get_text().strip()
                    # Remove technical/empty chapters
                    if not text or text.lower() in ["titlepage", "0000", "", None] or text.isdigit():
                        continue
                    # Remove technical titles
                    clean_title = title.replace('text/part', '').replace('.html', '').replace('.xhtml', '').replace('.htm', '').replace('/', '').strip()
                    if clean_title.lower() in ["titlepage", "0000", "", None] or clean_title.isdigit():
                        continue
                    chapters.append({'title': clean_title, 'content': text})
            # Load progress from session
            progress_key = f'epub_progress_{filename}'
            page = int(request.args.get('page', session.get(progress_key, 0)))
            page = max(0, min(page, len(chapters) - 1))
            # Save progress to session
            session[progress_key] = page
            return render_template('epub_viewer.html', filename=filename, chapters=chapters, page=page)
        elif filename.lower().endswith('.pdf'):
            return render_template('pdf_viewer.html', filename=filename)
        elif filename.lower().endswith('.html'):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return render_template('viewer.html', filename=filename, content=content)
        else:
            return send_from_directory(BOOKS_DIR, filename, as_attachment=True)
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

@app.route('/read/<filename>')
def read_book(filename):
    try:
        file_path = os.path.join(BOOKS_DIR, filename)
        if not os.path.exists(file_path):
            return jsonify({"message": "File not found"}), 404

        if filename.lower().endswith('.epub'):
            book = epub.read_epub(file_path)
            chapters = []
            technical_titles = {"titlepage", "0000", "cover", "toc", "copyright", "colophon", "nav"}
            for item in book.get_items():
                if isinstance(item, epub.EpubHtml):
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    # Get title, fallback to item name
                    title = soup.title.string.strip() if soup.title and soup.title.string else item.get_name().strip()
                    text = soup.get_text().strip()
                    # Remove technical/empty chapters
                    if not text:
                        continue
                    # Remove chapters with only numbers or technical markers
                    if title.lower() in technical_titles or title.strip().isdigit():
                        continue
                    if text.lower() in technical_titles or text.strip().isdigit():
                        continue
                    # Remove chapters that are too short (e.g. less than 10 chars)
                    if len(text) < 10:
                        continue
                    chapters.append({'title': title, 'content': text})

            # Load progress from session
            progress_key = f'epub_progress_{filename}'
            page = int(request.args.get('page', session.get(progress_key, 0)))
            page = max(0, min(page, len(chapters) - 1))

            # Save progress to session
            session[progress_key] = page

            return render_template('epub_viewer.html',
                                   filename=filename,
                                   chapters=chapters,
                                   page=page)
        elif filename.lower().endswith('.html'):
            print(filename)
            return send_from_directory(BOOKS_DIR, filename)

        else:
            return send_from_directory(BOOKS_DIR, filename, as_attachment=True)
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

@app.route('/books/<filename>')
def books(filename):
    return render_template(filename)


@app.route('/subtitles')
def subtitles():
    query = request.args.get('q', '').lower()
    subtitles = []
    subtitles_file = os.path.join(path, 'data', 'subtitles.json')
    if os.path.exists(subtitles_file):
        with open(subtitles_file, 'r', encoding='utf-8') as f:
            subtitles = json.load(f)

    if query:
        subtitles = [subtitle for subtitle in subtitles if query in subtitle['title'].lower()]

    return render_template('subtitles.html', subtitles=subtitles)

@app.route('/subtitles/<filename>')
def subtitle_viewer(filename):
    subtitles_file = os.path.join(path, 'data', 'subtitles.json')
    if os.path.exists(subtitles_file):
        with open(subtitles_file, 'r', encoding='utf-8') as f:
            subtitles = json.load(f)
            subtitle = next((s for s in subtitles if s['filename'] == filename), None)
            if subtitle:
                return render_template('subtitle_viewer.html', subtitle=subtitle)
    return "Subtitle not found", 404

@app.route('/upload_subtitle', methods=['POST'])
def upload_subtitle():
    try:
        data = request.form
        video_url = data.get('video_url')
        subtitle_file = request.files.get('subtitle_file')
        cover_file = request.files.get('cover_file')  # теперь это файл

        if not subtitle_file or subtitle_file.filename == '':
            logging.error("No subtitle file selected")
            return jsonify({"message": "No subtitle file selected"}), 400

        subtitle_path = os.path.join(path, 'static', 'subtitles', subtitle_file.filename)
        subtitle_file.save(subtitle_path)

        if not video_url:
            logging.error("No video URL provided")
            return jsonify({"message": "No video URL provided"}), 400

        covers_dir = os.path.join(path, 'static', 'covers')
        os.makedirs(covers_dir, exist_ok=True)

        # Загрузка файла обложки
        if cover_file and cover_file.filename != '':
            cover_filename = cover_file.filename
            cover_path = os.path.join(covers_dir, cover_filename)
            cover_file.save(cover_path)
            cover = f'covers/{cover_filename}'
        else:
            cover = ''

        subtitles_file = os.path.join(path, 'data', 'subtitles.json')
        subtitles = []
        if os.path.exists(subtitles_file):
            with open(subtitles_file, 'r', encoding='utf-8') as f:
                subtitles = json.load(f)

        subtitles.append({
            "title": data.get('title', 'Untitled'),
            "description": data.get('description', 'No description'),
            "cover": cover,
            "video": video_url,
            "subtitle_file": f'subtitles/{subtitle_file.filename}'
        })

        with open(subtitles_file, 'w', encoding='utf-8') as f:
            json.dump(subtitles, f, ensure_ascii=False, indent=4)

        logging.info("Subtitle uploaded successfully")
        return jsonify({"message": "Subtitle uploaded successfully!"})

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500


@app.route('/delete_subtitle', methods=['POST'])
def delete_subtitle():
    try:
        data = request.json
        subtitle_file = data.get('subtitle_file')

        # Load existing subtitles
        subtitles_file = os.path.join(path, 'data', 'subtitles.json')
        subtitles = []
        if os.path.exists(subtitles_file):
            with open(subtitles_file, 'r', encoding='utf-8') as f:
                subtitles = json.load(f)

        # Filter out the subtitle to delete
        subtitles = [s for s in subtitles if s['subtitle_file'] != subtitle_file]

        # Save updated subtitles
        with open(subtitles_file, 'w', encoding='utf-8') as f:
            json.dump(subtitles, f, ensure_ascii=False, indent=4)

        # Delete the subtitle file from the static directory
        subtitle_path = os.path.join(path, 'static', subtitle_file)
        if os.path.exists(subtitle_path):
            os.remove(subtitle_path)

        return jsonify({"message": "Subtitle deleted successfully!"})
    except Exception as e:
        logging.error(f"An error occurred while deleting subtitle: {str(e)}")
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

ai = ShiritoriAI()

@app.route("/shiritori", methods=["GET", "POST"])
def shiritori():
    if "history" not in session:
        session["history"] = []
        ai.reset()
        session["last_kana"] = None

    history = session["history"]
    last_kana = session.get("last_kana")

    if request.method == "POST":
        user_input = request.form["message"].strip()

        user_reading = ai.get_reading(user_input)
        history.append(("Ти", user_input))

        if not user_reading:
            ai.add_unknown(user_input)
            history.append(("🤖", "❌ Я не знаю це слово. Додай у навчання."))
        elif last_kana and not user_reading.startswith(last_kana):
            history.append(("🤖", f"❌ Слово не починається на '{last_kana}'"))
        elif user_reading[-1] == "ん":
            history.append(("🤖", "❌ Слово закінчується на 'ん'. Гра завершена!"))
            session["last_kana"] = None
        else:
            ai.used_words.add(user_input)
            history.append(("🤖", f"✅ Добре!"))

            # AI отвечает
            last_kana = ai.get_last_kana(user_input)
            ai_word = ai.get_next_word(last_kana)

            if not ai_word:
                history.append(("🤖", "🤖 Я не знаю слова. Ти виграв!"))
                session["last_kana"] = None
            else:
                ai_reading = ai.get_reading(ai_word)
                history.append(("🤖", f"{ai_word}【{ai_reading}】"))

                if ai_reading[-1] == "ん":
                    history.append(("🤖", "❌ Моє слово закінчується на 'ん'. Ти виграв!"))
                    session["last_kana"] = None
                else:
                    session["last_kana"] = ai.get_last_kana(ai_word)

        session["history"] = history
        return redirect(url_for("shiritori"))

    return render_template("chat.html", history=history)

@app.route("/reset")
def reset():
    session.clear()
    ai.reset()
    return redirect(url_for("shiritori"))

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == "__main__":
    app.run()

