import db


def get_user(user_id):
    sql = """SELECT id, username, image IS NOT NULL has_image
             FROM users
             WHERE id = ?"""
    result = db.query(sql, [user_id])
    return result[0] if result else None


def get_comments(user_id):
    sql = """SELECT m.id,
                m.recipy_id,
                t.title recipy_title,
                m.sent_at
            FROM recipes t, comments m
            WHERE t.id = m.recipy_id AND
                m.user_id = ?
            ORDER BY m.sent_at DESC"""
    return db.query(sql, [user_id])


def update_image(user_id, image):
    sql = "UPDATE users SET image = ? WHERE id = ?"
    db.execute(sql, [image, user_id])


def get_image(user_id):
    sql = "SELECT image FROM users WHERE id = ?"
    result = db.query(sql, [user_id])
    return result[0][0] if result else None
