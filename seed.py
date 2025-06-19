import random
import sqlite3
import string

db = sqlite3.connect("database.db")

def random_username():
    return "user" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

def random_title():
    return random.choice([
        "Pasta Bolognese", "Chicken Curry", "Beef Stew", "Vegan Salad", "Fish Tacos", "Berry Pie",
        "Mushroom Risotto", "Sushi Rolls", "Pizza Margherita", "Lentil Soup", "Pancakes", "Apple Crumble"
    ]) + " " + str(random.randint(1, 100000))

def random_cuisine():
    return random.choice(["Italian", "Indian", "Mexican", "Finnish", "French", "Chinese", "Thai", "American", "Spanish", "Turkish"])

def random_recipy():
    return "This is a test recipe. Step 1: ... Step 2: ... Step 3: ... Enjoy! " + ''.join(random.choices(string.ascii_letters + string.digits, k=20))

def random_comment():
    return random.choice([
        "Great recipe!", "I loved it!", "Will make again.", "Too spicy for me.", "Perfect for dinner.",
        "Easy and tasty.", "My kids enjoyed it.", "Not my favorite.", "Delicious!", "Needs more salt."
    ])

# Clear existing data
print("Deleting old data...")
db.execute("DELETE FROM comments")
db.execute("DELETE FROM recipes")
db.execute("DELETE FROM users")

db.commit()

user_count = 1000
recipe_count = 10000
comment_count = 100000

print(f"Inserting {user_count} users...")
user_ids = []
for i in range(user_count):
    username = random_username()
    db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", [username, "testhash"])
    user_ids.append(db.execute("SELECT last_insert_rowid()").fetchone()[0])

db.commit()

print(f"Inserting {recipe_count} recipes...")
recipe_ids = []
for i in range(recipe_count):
    user_id = random.choice(user_ids)
    db.execute(
        "INSERT INTO recipes (title, recipy, cuisine, user_id) VALUES (?, ?, ?, ?)",
        [random_title(), random_recipy(), random_cuisine(), user_id]
    )
    recipe_ids.append(db.execute("SELECT last_insert_rowid()").fetchone()[0])
    if (i+1) % 1000 == 0:
        print(f"  {i+1} recipes inserted...")

db.commit()

print(f"Inserting {comment_count} comments...")
for i in range(comment_count):
    user_id = random.choice(user_ids)
    recipe_id = random.choice(recipe_ids)
    rating = random.randint(1, 5)
    db.execute(
        """INSERT INTO comments (content, sent_at, user_id, recipy_id, rating)
           VALUES (?, datetime('now'), ?, ?, ?)""",
        [random_comment(), user_id, recipe_id, rating]
    )
    if (i+1) % 5000 == 0:
        print(f"  {i+1} comments inserted...")

db.commit()
db.close()
print("Seeding complete!") 