CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    image TEXT,
    password_hash TEXT
);

CREATE TABLE recipes (
    id INTEGER PRIMARY KEY,
    title TEXT,
    recipy TEXT, 
    cuisine TEXT,
    user_id INTEGER REFERENCES users
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY,
    content TEXT,
    sent_at TEXT,
    user_id INTEGER REFERENCES users,
    recipy_id INTEGER REFERENCES recipes
);