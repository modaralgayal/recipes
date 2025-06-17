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

app = Flask(__name__)
app.secret_key = config.secret_key


def require_login():
    if "user_id" not in session:
        abort(403)


def check_csrf():
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)


@app.route("/")
@app.route("/<int:page>")
def index(page=1):
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


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    sql_command = "SELECT id, username, password_hash FROM users WHERE username = ?"
    user = db.query(sql_command, [username])

    # Check if user was found
    if not user:
        return "ERROR: Invalid username or password", 401

    user_id = user[0][0]
    username = user[0][1]
    password_hash = user[0][2]

    if check_password_hash(password_hash, password):
        session["user_id"] = user_id
        session["username"] = username
        session["csrf_token"] = secrets.token_hex(16)
        return redirect("/")
    else:
        return "ERROR: Invalid username or password", 401


@app.route("/create_user", methods=["POST", "POST"])
def create_user():

    if request.method == "GET":
        return render_template("register.html", filled="")

    if request.method == "POST":

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
            flash("VIRHE: Passwords don't match")
            filled = {"username": username}
            return render_template("register.html", filled=filled)

        return redirect("/")


@app.route("/new_recipy", methods=["POST"])
def new_thread():
    require_login()
    check_csrf()

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
        abort(403)
    comments = forum.get_comments(recipy_id)
    return render_template("recipy.html", recipy=recipy, comments=comments)


@app.route("/register")
def register():
    return render_template("register.html", filled="")


@app.route("/logout")
def logout():
    del session["username"]
    del session["user_id"]
    del session["csrf_token"]
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
