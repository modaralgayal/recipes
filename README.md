# Recipe App

A simple web application for sharing and discovering recipes, built with Flask and SQLite.

## Features
- User registration and login
- Add, edit, and delete recipes
- Comment on and rate recipes (1-5 stars)
- View average ratings and all comments for each recipe
- Search recipes by keyword or cuisine
- Pagination for browsing large numbers of recipes
- User profile pages with comment history
- CSRF protection and flash message error handling

## Setup
1. **Install dependencies:**
   ```bash
   pip install flask werkzeug markupsafe
   ```
2. **Initialize the database:**
   ```bash
   sqlite3 database.db < schema.sql
   ```
3. **(Optional) Seed with test data:**
   ```bash
   python seed.py
   ```
4. **Run the app:**
   ```bash
   python app.py
   ```

## Test Data
- Speed of execution is printed in the terminal provided by the @app.before_request and @app.after_request functionality.


## File Structure
- `app.py` — Main Flask application
- `forum.py`, `users.py`, `db.py` — App logic and database helpers
- `templates/` — HTML templates
- `static/style.css` — App styling
- `schema.sql` — Database schema
- `seed.py` — Script to generate test data

## License
MIT
