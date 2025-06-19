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
    if request.form["csrf_token"] != session["csrf_token"]:
        flash("ERROR: Invalid request")
        return redirect("/")


@app.route("/")
@app.route("/<int:page>")
def index(page=1):
    # Generate CSRF token for guest users if not present
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
        
    page_size = 10
    thread_count = forum.recipy_count()
    page_count = math.ceil(thread_count / page_size)
    page_count = max(page_count, 1)

    if page < 1:
        return redirect("/1")
    if page > page_count:
        return redirect("/" + str(page_count))

    recipes = forum.get_recipes(page, page_size)
    print("These are the recipes", recipes)
    return render_template(
        "index.html", page=page, page_count=page_count, recipes=recipes
    )


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
    print(comment["id"])
    print(comment["user_id"])
    print(session["user_id"])
    if comment["user_id"] != session["user_id"]:
        flash("ERROR: You can only edit your own comments")
        return redirect("/recipy/" + str(comment["recipy_id"]))
    if request.method == "GET":
        return render_template("edit.html", comment=comment)

    if request.method == "POST":
        csrf_check = check_csrf()
        if csrf_check:
            return csrf_check
        content = request.form["content"]
        rating = int(request.form.get("rating", 3))
        
        # Validate rating
        if rating < 1 or rating > 5:
            rating = 3
            
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

    if request.method == "POST":
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

    if request.method == "POST":
        csrf_check = check_csrf()
        if csrf_check:
            return csrf_check
        if "continue" in request.form:
            forum.remove_comment(item["id"])
        return redirect("/recipy/" + str(item["recipy_id"]))


@app.route("/login", methods=["POST"])
def login():
    check_csrf()
    username = request.form["username"]
    password = request.form["password"]

    sql_command = "SELECT id, username, password_hash FROM users WHERE username = ?"
    user = db.query(sql_command, [username])

    # Check if user was found
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

    if request.method == "POST":
        csrf_check = check_csrf()
        if csrf_check:
            return csrf_check

        username = request.form["username"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]
        if password1 != password2:
            flash("VIRHE: Passwords don't match")
            filled = {"username": username}
            return render_template("register.html", filled=filled)
        password_hash = generate_password_hash(password1)

        try:
            sql_command = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
            db.execute(sql_command, [username, password_hash])
        except sqlite3.IntegrityError:
            flash("VIRHE: Username already exists")
            filled = {"username": username}
            return render_template("register.html", filled=filled)

        return redirect("/")


@app.route("/new_recipy", methods=["POST"])
def new_recipy():
    login_check = require_login()
    if login_check:
        return login_check
    
    csrf_check = check_csrf()
    if csrf_check:
        return csrf_check

    title = request.form["title"]
    recipy = request.form["recipy"]
    cuisine = request.form["cuisine"]
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

    if request.method == "POST":
        csrf_check = check_csrf()
        if csrf_check:
            return csrf_check

        file = request.files["image"]
        if not file.filename.endswith(".jpg"):
            flash("ERROR: The document is not a jpg-file.")
            return redirect("/")

        image = file.read()
        if len(image) > 100 * 1024:
            flash("ERROR: Image is too large.")
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
    # Generate CSRF token for guest users if not present
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

    content = request.form["content"]
    rating = int(request.form.get("rating", 3))
    user_id = session["user_id"]
    recipy_id = request.form["recipy_id"]

    # Validate rating
    if rating < 1 or rating > 5:
        rating = 3

    try:
        forum.add_comment(content, user_id, recipy_id, rating)
    except sqlite3.IntegrityError:
        flash("ERROR: Failed to add comment")
        return redirect("/recipy/" + str(recipy_id))

    return redirect("/recipy/" + str(recipy_id))


@app.route("/logout")
def logout():
    del session["username"]
    del session["user_id"]
    del session["csrf_token"]
    return redirect("/")


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return render_template("search.html", recipes=None, search_term="")
    
    if request.method == "POST":
        csrf_check = check_csrf()
        if csrf_check:
            return csrf_check
        
        search_term = request.form.get("search_term", "").strip()
        if not search_term:
            return render_template("search.html", recipes=None, search_term="")
        
        recipes = forum.search_recipes(search_term)
        return render_template("search.html", recipes=recipes, search_term=search_term)


if __name__ == "__main__":
    app.run(debug=True)
