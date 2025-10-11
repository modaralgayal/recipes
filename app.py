import math
import secrets
import sqlite3
import time
from os import abort

import markupsafe
from flask import (
    Flask,
    flash,
    g,
    make_response,
    redirect,
    render_template,
    request,
    session,
)
from werkzeug.security import check_password_hash, generate_password_hash

import config
import db
import forum
import users

app = Flask(__name__)
app.secret_key = config.secret_key


# -------------------------------
# Helpers: Validation & Security
# -------------------------------
def validate_text(value, field_name, max_length=500, allow_empty=False):
    """Ensure the text input is safe and within expected limits."""
    if value is None:
        raise ValueError(f"{field_name} is required.")
    value = value.strip()
    if not value and not allow_empty:
        raise ValueError(f"{field_name} cannot be empty.")
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds maximum length ({max_length}).")
    return value


def validate_rating(value):
    """Ensure the rating is between 1 and 5."""
    try:
        rating = int(value)
    except (ValueError, TypeError):
        return 3
    return min(max(rating, 1), 5)


def validate_username(value):
    """Check that username is alphanumeric and reasonable length."""
    value = validate_text(value, "Username", 50)
    if not value.isalnum():
        raise ValueError("Username must contain only letters and numbers.")
    return value


@app.before_request
def before_request():
    g.start_time = time.time()


@app.after_request
def after_request(response):
    elapsed_time = round(time.time() - g.start_time, 2)
    print("elapsed time:", elapsed_time, "s")
    return response


def require_login():
    if "user_id" not in session:
        flash("ERROR: You must be logged in to perform this action")
        return redirect("/")


def check_csrf():
    if request.form.get("csrf_token") != session.get("csrf_token"):
        flash("ERROR: Invalid request")
        return redirect("/")


# -------------------------------
# Routes
# -------------------------------
@app.route("/")
@app.route("/<int:page>")
def index(page=1):
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)

    page_size = 10
    thread_count = forum.recipy_count()
    page_count = max(math.ceil(thread_count / page_size), 1)

    if page < 1:
        return redirect("/1")
    if page > page_count:
        return redirect("/" + str(page_count))

    recipes = forum.get_recipes(page, page_size)
    return render_template("index.html", page=page, page_count=page_count, recipes=recipes)


@app.template_filter()
def show_lines(content):
    content = str(markupsafe.escape(content))
    content = content.replace("\n", "<br />")
    return markupsafe.Markup(content)


@app.route("/edit/<int:comment_id>", methods=["GET", "POST"])
def edit_comment(comment_id):
    login_check = require_login()
    if login_check:
        return login_check

    comment = forum.get_comment(comment_id)
    if not comment:
        flash("ERROR: Comment not found")
        return redirect("/")
    if comment["user_id"] != session["user_id"]:
        flash("ERROR: You can only edit your own comments")
        return redirect("/recipy/" + str(comment["recipy_id"]))

    if request.method == "GET":
        return render_template("edit.html", comment=comment)

    csrf_check = check_csrf()
    if csrf_check:
        return csrf_check

    try:
        content = validate_text(request.form.get("content", ""), "Comment", 2000)
    except ValueError as e:
        flash(f"ERROR: {e}")
        return redirect("/recipy/" + str(comment["recipy_id"]))

    rating = validate_rating(request.form.get("rating", 3))
    forum.update_comment(comment["id"], content, rating)
    return redirect("/recipy/" + str(comment["recipy_id"]))


@app.route("/remove_recipy/<int:recipy_id>", methods=["GET", "POST"])
def remove_recipy(recipy_id):
    login_check = require_login()
    if login_check:
        return login_check

    item = forum.get_recipy(recipy_id)
    type = "recipy"

    if request.method == "GET":
        return render_template("remove.html", item=item, type=type)

    csrf_check = check_csrf()
    if csrf_check:
        return csrf_check

    if "cancel" in request.form:
        return redirect("/")
    if "continue" in request.form:
        success = forum.remove_recipy(recipy_id)
        if not success:
            flash("Cannot delete recipy — likely has comments")
            return redirect("/")
    return redirect("/")


@app.route("/remove/<int:comment_id>", methods=["GET", "POST"])
def remove_comment(comment_id):
    login_check = require_login()
    if login_check:
        return login_check

    item = forum.get_comment(comment_id)
    if not item:
        flash("ERROR: Comment not found")
        return redirect("/")
    type = "comment"

    if request.method == "GET":
        return render_template("remove.html", item=item, type=type)

    csrf_check = check_csrf()
    if csrf_check:
        return csrf_check

    if "continue" in request.form:
        forum.remove_comment(item["id"])
    return redirect("/recipy/" + str(item["recipy_id"]))


@app.route("/login", methods=["POST"])
def login():
    check_csrf()
    try:
        username = validate_username(request.form.get("username", ""))
        password = validate_text(request.form.get("password", ""), "Password")
    except ValueError as e:
        flash(f"ERROR: {e}")
        return redirect("/")

    sql_command = "SELECT id, username, password_hash FROM users WHERE username = ?"
    user = db.query(sql_command, [username])

    if not user:
        flash("ERROR: Invalid username or password")
        return redirect("/")

    user_id = user[0][0]
    username = user[0][1]
    password_hash = user[0][2]

    if check_password_hash(password_hash, password):
        session["user_id"] = user_id
        session["username"] = username
        session["csrf_token"] = secrets.token_hex(16)
        return redirect("/")
    else:
        flash("ERROR: Invalid username or password")
        return redirect("/")


@app.route("/create_user", methods=["POST", "POST"])
def create_user():
    if request.method == "GET":
        return render_template("register.html", filled="")

    csrf_check = check_csrf()
    if csrf_check:
        return csrf_check

    username = request.form.get("username", "")
    password1 = request.form.get("password1", "")
    password2 = request.form.get("password2", "")

    try:
        username = validate_username(username)
        password1 = validate_text(password1, "Password")
        password2 = validate_text(password2, "Password confirmation")
    except ValueError as e:
        flash(f"ERROR: {e}")
        return render_template("register.html", filled={"username": username})

    if password1 != password2:
        flash("ERROR: Passwords don't match")
        return render_template("register.html", filled={"username": username})

    password_hash = generate_password_hash(password1)

    try:
        sql_command = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql_command, [username, password_hash])
    except sqlite3.IntegrityError:
        flash("ERROR: Username already exists")
        return render_template("register.html", filled={"username": username})

    return redirect("/")


@app.route("/new_recipy", methods=["POST"])
def new_recipy():
    login_check = require_login()
    if login_check:
        return login_check
    
    csrf_check = check_csrf()
    if csrf_check:
        return csrf_check

    try:
        title = validate_text(request.form.get("title", ""), "Title", 100)
        recipy = validate_text(request.form.get("recipy", ""), "Recipe", 5000)
        cuisine = validate_text(request.form.get("cuisine", ""), "Cuisine", 50)
    except ValueError as e:
        flash(f"ERROR: {e}")
        return redirect("/")

    user_id = session["user_id"]
    recipy_id = forum.add_recipy(title, recipy, cuisine, user_id)
    return redirect("/recipy/" + str(recipy_id))


@app.route("/recipy/<int:recipy_id>")
def show_recipy(recipy_id):
    recipy = forum.get_recipy(recipy_id)
    if not recipy:
        flash("ERROR: Recipe not found")
        return redirect("/")
    comments = forum.get_comments(recipy_id)
    average_rating = forum.get_average_rating(recipy_id)
    return render_template("recipy.html", recipy=recipy, comments=comments, average_rating=average_rating)


@app.route("/add_image", methods=["GET", "POST"])
def add_image():
    login_check = require_login()
    if login_check:
        return login_check

    if request.method == "GET":
        return render_template("add_image.html")

    csrf_check = check_csrf()
    if csrf_check:
        return csrf_check

    file = request.files["image"]
    if not file or not file.filename.lower().endswith(".jpg"):
        flash("ERROR: The document must be a .jpg file.")
        return redirect("/")

    image = file.read()
    if len(image) > 100 * 1024:
        flash("ERROR: Image is too large (max 100 KB).")
        return redirect("/")

    user_id = session["user_id"]
    users.update_image(user_id, image)
    flash("Image added successfully!")
    return redirect("/user/" + str(user_id))


@app.route("/image/<int:user_id>")
def show_image(user_id):
    login_check = require_login()
    if login_check:
        return login_check
    
    image = users.get_image(user_id)
    if not image:
        flash("ERROR: Image not found")
        return redirect("/")

    response = make_response(bytes(image))
    response.headers.set("Content-Type", "image/jpeg")
    return response


@app.route("/user/<int:user_id>")
def show_user(user_id):
    login_check = require_login()
    if login_check:
        return login_check
    
    user = users.get_user(user_id)
    if not user:
        flash("ERROR: User not found")
        return redirect("/")
    comments = users.get_comments(user_id)
    return render_template("user.html", user=user, comments=comments)


@app.route("/register")
def register():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return render_template("register.html", filled="")


@app.route("/new_comment", methods=["POST"])
def new_comment():
    login_check = require_login()
    if login_check:
        return login_check
    
    csrf_check = check_csrf()
    if csrf_check:
        return csrf_check

    try:
        content = validate_text(request.form.get("content", ""), "Comment", 2000)
    except ValueError as e:
        flash(f"ERROR: {e}")
        return redirect(request.referrer or "/")

    rating = validate_rating(request.form.get("rating", 3))
    user_id = session["user_id"]
    recipy_id = request.form["recipy_id"]

    try:
        forum.add_comment(content, user_id, recipy_id, rating)
    except sqlite3.IntegrityError:
        flash("ERROR: Failed to add comment")
        return redirect("/recipy/" + str(recipy_id))

    return redirect("/recipy/" + str(recipy_id))


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return render_template("search.html", recipes=None, search_term="")
    
    csrf_check = check_csrf()
    if csrf_check:
        return csrf_check
        
    search_term = request.form.get("search_term", "").strip()
    if not search_term:
        flash("Please enter a search term.")
        return render_template("search.html", recipes=None, search_term="")
    
    try:
        search_term = validate_text(search_term, "Search term", 100)
    except ValueError as e:
        flash(f"ERROR: {e}")
        return render_template("search.html", recipes=None, search_term="")
    
    recipes = forum.search_recipes(search_term)
    return render_template("search.html", recipes=recipes, search_term=search_term)


@app.route("/logout")
def logout():
    for key in ("username", "user_id", "csrf_token"):
        session.pop(key, None)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
