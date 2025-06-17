import sqlite3

import db


def get_recipes(page, page_size):
    sql = """SELECT r.id, r.title, r.recipy, r.cuisine, COUNT(c.id) total, MAX(c.sent_at) last
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


def add_comment(content, user_id, recipy_id):
    sql = """INSERT INTO comments (recipy, sent_at, user_id, recipy_id)
             VALUES (?, datetime('now'), ?, ?)"""
    db.execute(sql, [content, user_id, recipy_id])


def get_comments(recipy_id):
    sql = """SELECT c.id, c.content, c.sent_at, c.user_id, u.username
    FROM comments c, users u
    WHERE c.user_id == u.id AND c.recipy_id = ?
    ORDER BY c.id"""

    return db.query(sql, [recipy_id])


def get_comment(comment_id):
    sql = "SELECT id, content, sent_at, user_id, RECIPY_ID FROM COMMENTS WHERE id = ?"
    comment = db.query(sql, [comment_id])[0]
    if comment:
        return comment
    else:
        return None


def update_comments(comment_id, content):
    sql = "UPDATE comments SET content = ? WHERE id = ?"
    db.execute(sql, [content, comment_id])


def remove_comment(comment_id):
    sql = "DELETE FROM comments WHERE id = ?"
    db.execute(sql, [comment_id])
