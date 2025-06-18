import sqlite3

import db


def get_recipes(page, page_size):
    sql = """SELECT r.id, r.title, r.recipy, r.cuisine, COUNT(c.id) total, MAX(c.sent_at) last, AVG(c.rating) avg_rating
             FROM recipes r
             LEFT JOIN comments c ON r.id = c.recipy_id
             GROUP BY r.id
             ORDER BY r.id DESC
             LIMIT ? OFFSET ?"""
    limit = page_size
    offset = page_size * (page - 1)
    result = db.query(sql, [limit, offset])
    print(result)
    return result


def recipy_count():
    sql_command = "SELECT COUNT(*) FROM recipes"
    count = db.query(sql_command)
    print(count[0][0])
    return count[0][0]  # assuming count is a list of one tuple


def add_recipy(title, recipy, cuisine, user_id):
    sql = "INSERT INTO recipes (title, recipy, cuisine, user_id) VALUES (?, ?, ?, ?)"
    db.execute(sql, [title, recipy, cuisine, user_id])
    recipy_id = db.last_insert_id()
    return recipy_id


def get_recipy(recipy_id):
    sql = "SELECT id, title, recipy, cuisine FROM recipes WHERE id = ?"
    result = db.query(sql, [recipy_id])
    return result[0] if result else None


def add_comment(content, user_id, recipy_id, rating=3):
    sql = """INSERT INTO comments (content, sent_at, user_id, recipy_id, rating)
             VALUES (?, datetime('now'), ?, ?, ?)"""
    db.execute(sql, [content, user_id, recipy_id, rating])


def get_comments(recipy_id):
    sql = """SELECT c.id, c.content, c.sent_at, c.user_id, u.username, c.rating
    FROM comments c, users u
    WHERE c.user_id == u.id AND c.recipy_id = ?
    ORDER BY c.id"""

    return db.query(sql, [recipy_id])


def get_comment(comment_id):
    sql = "SELECT id, content, sent_at, user_id, recipy_id, rating FROM comments WHERE id = ?"
    comment = db.query(sql, [comment_id])
    return comment[0] if comment else None


def update_comment(comment_id, content, rating=None):
    if rating is not None:
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
        print("Deleting recipy:", recipy_id)
        sql = "DELETE FROM recipes WHERE id = ?"
        db.execute(sql, [int(recipy_id)])
        return True
    except sqlite3.IntegrityError as e:
        print("Delete failed due to FK constraint:", e)
        return False


def update_comments(comment_id, content):
    sql = "UPDATE comments SET content = ? WHERE id = ?"
    db.execute(sql, [content, comment_id])


def search_recipes(search_term):
    """Search recipes by title, content, or cuisine"""
    sql = """SELECT r.id, r.title, r.recipy, r.cuisine, COUNT(c.id) total, MAX(c.sent_at) last, AVG(c.rating) avg_rating
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
