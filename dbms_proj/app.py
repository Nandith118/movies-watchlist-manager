from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'replace-with-a-random-secret' 


db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'nandu_018',
    'database': 'media_app',
    'auth_plugin': 'mysql_native_password'
}
def get_db():
    return mysql.connector.connect(**db_config)

# API endpoints for feature pack (add to app.py)

from flask import jsonify
import random

@app.route('/api/media')
def api_media():
    """
    Return compact media list for front-end features.
    Optional query params:
      - type (Movie/Series)
      - genre_id
      - year
      - min_rating (IMDb)
    """
    media_type = request.args.get('type')
    genre_id = request.args.get('genre')
    year = request.args.get('year')
    min_rating = request.args.get('min_rating')

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    sql = "SELECT media_id, title, media_type, release_year, imdb_rating, image_url, description FROM Media WHERE 1=1"
    params = []
    if media_type and media_type != 'all':
        sql += " AND media_type=%s"; params.append(media_type)
    if year and year != 'all':
        sql += " AND release_year=%s"; params.append(year)
    if min_rating and min_rating != '0':
        sql += " AND imdb_rating >= %s"; params.append(min_rating)
    # simple genre filter via join if provided
    if genre_id and genre_id != 'all':
        sql = ("SELECT m.media_id, m.title, m.media_type, m.release_year, m.imdb_rating, m.image_url, m.description "
               "FROM Media m JOIN MediaGenre mg ON m.media_id = mg.media_id "
               "WHERE mg.genre_id=%s")
        params = [genre_id]
        if media_type and media_type != 'all':
            sql += " AND m.media_type=%s"; params.append(media_type)
    sql += " ORDER BY release_year DESC, imdb_rating DESC LIMIT 100"
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows)

@app.route('/api/random')
def api_random():
    """Return a small random sample for the poster collage / wheel"""
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT media_id, title, image_url FROM Media ORDER BY RAND() LIMIT 40")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows)

@app.route('/api/avg/<int:mid>')
def api_avg(mid):
    """Return avg rating and count from UserReviews & WatchlistItem.user_rating (if you have both)"""
    conn = get_db(); cur = conn.cursor()
    # prefer official UserReviews table
    cur.execute("SELECT AVG(rating), COUNT(*) FROM UserReviews WHERE media_id=%s", (mid,))
    avg, cnt = cur.fetchone()
    cur.close(); conn.close()
    return jsonify({'avg': float(avg) if avg else None, 'count': cnt})



ADMIN_USERNAME = "xyz"
ADMIN_PASSWORD = "000"


def current_user_id():
    return session.get('user_id')


@app.route('/')
def index():
    # filters from querystring (keep existing defaults)
    media_type = request.args.get("type", "all")
    genre_id = request.args.get("genre", "all")
    year = request.args.get("year", "all")
    platform_id = request.args.get("platform", "all")
    min_rating = request.args.get("min_rating", "0")

    conn = get_db()

    # --- fetch genres & platforms as dicts for filters ---
    cur_dict = conn.cursor(dictionary=True)
    cur_dict.execute("SELECT genre_id, genre_name FROM Genre ORDER BY genre_name")
    genres = cur_dict.fetchall()

    cur_dict.execute("SELECT platform_id, platform_name FROM StreamingPlatform ORDER BY platform_name")
    platforms = cur_dict.fetchall()
    cur_dict.close()

    # --- year list from current year down to 1980 ---
    import datetime
    current_year = datetime.datetime.now().year
    years = list(range(current_year, 1979, -1))

    # --- Build main media query (returns tuples for compatibility with templates) ---
    cur = conn.cursor()
    
    sql = """
    SELECT 
        m.media_id,
        m.title,
        m.media_type,
        m.release_year,
        m.imdb_rating,
        m.image_url,
        GROUP_CONCAT(DISTINCT g.genre_name SEPARATOR ', ') AS genre_names
    FROM Media m
    LEFT JOIN MediaGenre mg ON m.media_id = mg.media_id
    LEFT JOIN Genre g ON mg.genre_id = g.genre_id
    LEFT JOIN MediaPlatform mp ON m.media_id = mp.media_id
    WHERE 1=1
"""

    params = []

    if media_type != "all":
        sql += " AND m.media_type = %s"
        params.append(media_type)

    if genre_id != "all":
        sql += " AND mg.genre_id = %s"
        params.append(genre_id)

    if year != "all":
        sql += " AND m.release_year = %s"
        params.append(year)

    if platform_id != "all":
        sql += " AND mp.platform_id = %s"
        params.append(platform_id)

    if min_rating != "0":
        sql += " AND m.imdb_rating >= %s"
        params.append(min_rating)

    sql += " GROUP BY m.media_id ORDER BY m.release_year DESC, m.imdb_rating DESC"

    cur.execute(sql, params)
    media = cur.fetchall()

    # --- TRENDING: media most added to watchlists (option 2) ---
    # returns tuples (media_id, title, media_type, release_year, imdb_rating, image_url, adds)
    trending_sql = """
        SELECT m.media_id, m.title, m.media_type, m.release_year, m.imdb_rating, m.image_url,
               COUNT(w.user_id) AS adds
        FROM Media m
        LEFT JOIN WatchlistItem w ON m.media_id = w.media_id
        GROUP BY m.media_id
        ORDER BY adds DESC
        LIMIT 8
    """
    cur.execute(trending_sql)
    trending = cur.fetchall()

    # fallback: if trending empty (no watchlist records), pick random ones
    if not trending:
        cur.execute("SELECT media_id, title, media_type, release_year, imdb_rating, image_url FROM Media ORDER BY RAND() LIMIT 8")
        trending = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "index.html",
        media=media,
        genres=genres,
        years=years,
        platforms=platforms,
        media_type=media_type,
        genre_id=genre_id,
        year=year,
        platform_id=platform_id,
        min_rating=min_rating,
        trending=trending
    )




@app.route('/search')
def search():
    query = request.args.get('query', '').strip()
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    sql = """
        SELECT media_id, title, media_type, release_year, imdb_rating, image_url
        FROM Media
        WHERE title LIKE %s OR media_type LIKE %s
        ORDER BY release_year DESC
    """
    val = ("%" + query + "%", "%" + query + "%")
    cur.execute(sql, val)
    results = cur.fetchall()
    cur.close(); conn.close()
    return render_template('search_results.html', query=query, results=results)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))

        pw_hash = generate_password_hash(password)
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO User (username, email, password_hash, join_date)
                VALUES (%s,%s,%s,%s)
            """, (username, email, pw_hash, datetime.now().date()))
            conn.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Username or email already exists.', 'danger')
        finally:
            cur.close(); conn.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        password = request.form.get('password')

       
        if user == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['user_role'] = 'admin'
            session['user_id'] = 0
            flash('Welcome Admin 👑', 'success')
            return redirect(url_for('admin_dashboard'))

       
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT user_id, password_hash FROM User WHERE username=%s OR email=%s", (user, user))
        row = cur.fetchone()
        cur.close(); conn.close()

        if row and check_password_hash(row[1], password):
            session['user_id'] = row[0]
            session['user_role'] = 'user'
            flash('Logged in successfully ✅', 'success')
            return redirect(url_for('index'))
        else:
            flash('Wrong credentials.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/users')
def admin_users():
    if session.get('user_role') != 'admin':
        return "Unauthorized Access", 403

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT user_id, username, email, join_date AS created_at
        FROM User
        ORDER BY user_id ASC
    """)
    users = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("admin_users.html", users=users)

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('user_role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT media_id, title, media_type, release_year, imdb_rating, image_url FROM Media ORDER BY release_year DESC")
    media = cur.fetchall()
    cur.close(); conn.close()
    return render_template('admin_dashboard.html', media=media)

@app.route('/add_media', methods=['GET', 'POST'])
def add_media():
    if session.get('user_role') != 'admin':
        flash('Only admin can add media.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        media_type = request.form['media_type']
        release_year = request.form.get('release_year') or None
        imdb_rating = request.form.get('imdb_rating') or None
        image_url = request.form.get('image_url') or None
        description = request.form.get('description') or None

        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            INSERT INTO Media (title, media_type, release_year, imdb_rating, image_url, description)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (title, media_type, release_year, imdb_rating, image_url, description))
        conn.commit()
        cur.close(); conn.close()
        flash('✅ Media added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_media.html')

@app.route('/delete_media/<int:mid>')
def delete_media(mid):
    if session.get('user_role') != 'admin':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('index'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM Media WHERE media_id=%s", (mid,))
    conn.commit()
    cur.close(); conn.close()
    flash('Media deleted successfully.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_logout')
def admin_logout():
    session.pop('user_role', None)
    session.pop('user_id', None)
    flash('Admin logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/media/<int:mid>')
def media_detail(mid):
    conn = get_db()
    cur = conn.cursor()

    
    cur.execute("SELECT * FROM Media WHERE media_id=%s", (mid,))
    media = cur.fetchone()
    if not media:
        cur.close(); conn.close()
        return "Media not found", 404

    
    cur.execute("""
        SELECT g.genre_name FROM Genre g
        JOIN MediaGenre mg ON g.genre_id = mg.genre_id
        WHERE mg.media_id=%s
    """, (mid,))
    genres = [r[0] for r in cur.fetchall()]

    
    cur.execute("""
        SELECT sp.platform_name, mp.availability_status 
        FROM StreamingPlatform sp
        JOIN MediaPlatform mp ON sp.platform_id = mp.platform_id
        WHERE mp.media_id=%s
    """, (mid,))
    platforms = cur.fetchall()

    
    cur.execute("""
        SELECT u.username, r.rating, r.review_text, r.review_date
        FROM UserReviews r 
        JOIN User u ON r.user_id = u.user_id
        WHERE r.media_id=%s 
        ORDER BY r.review_date DESC
    """, (mid,))
    reviews = cur.fetchall()

    
    cur.execute("""
        SELECT ROUND(AVG(user_rating),1), COUNT(user_rating)
        FROM WatchlistItem
        WHERE media_id = %s AND user_rating IS NOT NULL
    """, (mid,))
    avg_row = cur.fetchone()
    avg_rating = avg_row[0] if avg_row[0] else None
    total_reviews = avg_row[1] if avg_row[1] else 0

    
    user_id = current_user_id()
    w_status = None
    if user_id:
        cur.execute("SELECT status FROM WatchlistItem WHERE user_id=%s AND media_id=%s", (user_id, mid))
        row = cur.fetchone()
        if row:
            w_status = row[0]

    cur.close()
    conn.close()

    return render_template(
        'media_detail.html',
        media=media,
        genres=genres,
        platforms=platforms,
        reviews=reviews,
        avg_rating=avg_rating,
        total_reviews=total_reviews,
        w_status=w_status
    )



@app.route('/add_to_watchlist/<int:mid>', methods=['POST'])
def add_to_watchlist(mid):
    user_id = current_user_id()
    if not user_id:
        flash('Please login to add to watchlist', 'warning')
        return redirect(url_for('login'))

    status = request.form.get('status', 'Planned')
    
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO WatchlistItem (user_id, media_id, status, date_added)
            VALUES (%s, %s, %s, %s)
        """, (user_id, mid, status, datetime.now()))
        conn.commit()
        flash('Added to watchlist', 'success')
    except mysql.connector.IntegrityError:
        
        try:
            cur.execute("UPDATE WatchlistItem SET status=%s WHERE user_id=%s AND media_id=%s", (status, user_id, mid))
            conn.commit()
            flash('Watchlist status updated', 'success')
        except Exception:
            flash('Already in watchlist', 'info')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('media_detail', mid=mid))


@app.route('/watchlist')
def watchlist():
    user_id = current_user_id()
    if not user_id:
        flash('Please login to view watchlist', 'warning')
        return redirect(url_for('login'))

    filter_status = request.args.get('status', 'all')
    sort_order = request.args.get('sort', 'none')

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    sql = """
    SELECT w.media_id, m.title, m.image_url AS image_url, w.status, w.user_rating, w.user_review,
           (SELECT ROUND(AVG(user_rating),1) FROM WatchlistItem WHERE media_id = w.media_id AND user_rating IS NOT NULL) AS avg_rating,
           (SELECT COUNT(user_rating) FROM WatchlistItem WHERE media_id = w.media_id AND user_rating IS NOT NULL) AS rating_count
    FROM WatchlistItem w
    JOIN Media m ON w.media_id = m.media_id
    WHERE w.user_id = %s
"""
    params = [user_id]

    if filter_status != 'all':
        sql += " AND w.status = %s"
        params.append(filter_status)

    if sort_order == 'rating_desc':
      sql += " ORDER BY (w.user_rating IS NULL), w.user_rating DESC"
    elif sort_order == 'rating_asc':
      sql += " ORDER BY (w.user_rating IS NULL), w.user_rating ASC"
    else:
      sql += " ORDER BY w.date_added DESC"


    cur.execute(sql, params)
    items = cur.fetchall()
    cur.close(); conn.close()
    return render_template('watchlist.html', items=items, filter_status=filter_status, sort_order=sort_order)


@app.route('/watchlist/rate/<int:mid>', methods=['POST'])
def rate_watchlist_item(mid):
    user_id = current_user_id()
    if not user_id:
        flash('Please login first.', 'warning')
        return redirect(url_for('login'))

    try:
        rating = float(request.form.get('rating', 0))
    except ValueError:
        rating = 0.0
    
    rating = max(0.0, min(5.0, rating))
    review = request.form.get('review', '').strip()

    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        UPDATE WatchlistItem
        SET user_rating=%s, user_review=%s
        WHERE user_id=%s AND media_id=%s
    """, (rating, review if review != '' else None, user_id, mid))
    conn.commit()
    cur.close(); conn.close()

    flash('Your rating and review have been saved.', 'success')
    return redirect(url_for('watchlist'))


@app.route('/watchlist/update/<int:mid>', methods=['POST'])
def update_watch_status(mid):
    user_id = current_user_id()
    if not user_id:
        flash('Login needed', 'warning')
        return redirect(url_for('login'))
    new_status = request.form.get('status')
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE WatchlistItem SET status=%s WHERE user_id=%s AND media_id=%s",
                (new_status, user_id, mid))
    conn.commit()
    cur.close(); conn.close()
    flash('Status updated', 'success')
    return redirect(url_for('watchlist'))


@app.route('/watchlist/remove/<int:mid>', methods=['POST'])
def remove_watchlist(mid):
    user_id = current_user_id()
    if not user_id:
        flash('Login needed', 'warning')
        return redirect(url_for('login'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM WatchlistItem WHERE user_id=%s AND media_id=%s",
                (user_id, mid))
    conn.commit()
    cur.close(); conn.close()
    flash('Removed from watchlist', 'info')
    return redirect(url_for('watchlist'))


@app.context_processor
def inject_user():
    return dict(current_user_id=session.get('user_id'),
                user_role=session.get('user_role'))


if __name__ == "__main__":
    app.run(debug=True)
