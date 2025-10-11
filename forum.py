import sqlite3
import db


# -------------------------------
# Simple input validation helpers
# -------------------------------
def _validate_text(value, field_name, max_length, allow_empty=False):
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    value = value.strip()
    if not value and not allow_empty:
        raise ValueError(f"{field_name} cannot be empty")
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds {max_length} characters")
    return value


def _validate_rating(rating):
    try:
        rating = int(rating)
    except (ValueError, TypeError):
        rating = 3
    return min(max(rating, 1), 5)


# -------------------------------
# Forum functions
# -------------------------------
def get_recipes(page, page_size):
    sql = """SELECT r.id, r.title, r.recipy, r.cuisine, r.user_id, COUNT(c.id) total, 
                    MAX(c.sent_at) last, AVG(c.rating) avg_rating
             FROM recipes r
             LEFT JOIN comments c ON r.id = c.recipy_id
             GROUP BY r.id
             ORDER BY r.id DESC
             LIMIT ? OFFSET ?"""
    limit = page_size
    offset = page_size * (page - 1)
    result = db.query(sql, [limit, offset])
    return result


def recipy_count():
    sql_command = "SELECT COUNT(*) FROM recipes"
    count = db.query(sql_command)
    return count[0][0] if count else 0


def add_recipy(title, recipy, cuisine, user_id):
    """Add a new recipe with basic validation"""
    title = _validate_text(title, "Title", 100)
    recipy = _validate_text(recipy, "Recipe", 500)
    cuisine = _validate_text(cuisine, "Cuisine", 50)

    sql = "INSERT INTO recipes (title, recipy, cuisine, user_id) VALUES (?, ?, ?, ?)"
    db.execute(sql, [title, recipy, cuisine, user_id])
    return db.last_insert_id()


def get_recipy(recipy_id):
    sql = "SELECT id, title, recipy, cuisine FROM recipes WHERE id = ?"
    result = db.query(sql, [recipy_id])
    return result[0] if result else None


def add_comment(content, user_id, recipy_id, rating=3):
    """Add a new comment with content and rating validation"""
    content = _validate_text(content, "Comment", 2000)
    rating = _validate_rating(rating)

    sql = """INSERT INTO comments (content, sent_at, user_id, recipy_id, rating)
             VALUES (?, datetime('now'), ?, ?, ?)"""
    db.execute(sql, [content, user_id, recipy_id, rating])


def get_comments(recipy_id):
    sql = """SELECT c.id, c.content, c.sent_at, c.user_id, u.username, c.rating
             FROM comments c
             JOIN users u ON c.user_id = u.id
             WHERE c.recipy_id = ?
             ORDER BY c.id"""
    return db.query(sql, [recipy_id])


def get_comment(comment_id):
    sql = "SELECT id, content, sent_at, user_id, recipy_id, rating FROM comments WHERE id = ?"
    comment = db.query(sql, [comment_id])
    return comment[0] if comment else None


def update_comment(comment_id, content, rating=None):
    """Update a comment's content and rating safely"""
    content = _validate_text(content, "Comment", 2000)
    if rating is not None:
        rating = _validate_rating(rating)
        sql = "UPDATE comments SET content = ?, rating = ? WHERE id = ?"
        db.execute(sql, [content, rating, comment_id])
    else:
        sql = "UPDATE comments SET content = ? WHERE id = ?"
        db.execute(sql, [content, comment_id])


def remove_comment(comment_id):
    sql = "DELETE FROM comments WHERE id = ?"
    db.execute(sql, [comment_id])


def remove_recipy(recipy_id):
    try:
        sql = "DELETE FROM recipes WHERE id = ?"
        db.execute(sql, [int(recipy_id)])
        return True
    except sqlite3.IntegrityError as e:
        print("Delete failed due to FK constraint:", e)
        return False


def update_comments(comment_id, content):
    content = _validate_text(content, "Comment", 2000)
    sql = "UPDATE comments SET content = ? WHERE id = ?"
    db.execute(sql, [content, comment_id])


def search_recipes(search_term):
    """Search recipes by title, content, or cuisine (safe pattern)"""
    search_term = _validate_text(search_term, "Search term", 100)
    sql = """SELECT r.id, r.title, r.recipy, r.cuisine, COUNT(c.id) total, 
                    MAX(c.sent_at) last, AVG(c.rating) avg_rating
             FROM recipes r
             LEFT JOIN comments c ON r.id = c.recipy_id
             WHERE r.title LIKE ? OR r.recipy LIKE ? OR r.cuisine LIKE ?
             GROUP BY r.id
             ORDER BY r.id DESC"""
    search_pattern = f"%{search_term}%"
    result = db.query(sql, [search_pattern, search_pattern, search_pattern])
    return result


def get_average_rating(recipy_id):
    """Get the average rating for a recipe"""
    sql = "SELECT AVG(rating) FROM comments WHERE recipy_id = ?"
    result = db.query(sql, [recipy_id])
    avg_rating = result[0][0] if result and result[0][0] else 0
    return round(avg_rating, 1) if avg_rating else 0
