from flask import Flask, request, session, redirect, url_for, render_template_string
from bson import ObjectId
import random

# Import existing user management functions
from amos.manage_users import create_user, authenticate_user

# For database access to asteroids
from config.mongodb_config import MongoDBConfig
from models.models import AsteroidModel

app = Flask(__name__)
app.secret_key = "replace_this_with_a_secure_key"  # Replace with a real secret key

# Mongo collections
asteroids_collection = MongoDBConfig.get_collection("asteroids")

# ---------------------
# TEMPLATES (inline for brevity)
# ---------------------
registration_template = """
<!DOCTYPE html>
<html>
<head><title>Register</title></head>
<body>
  <h1>Register</h1>
  <form method="POST">
    <label>Username:</label> <input name="username" type="text" required><br>
    <label>Password:</label> <input name="password" type="password" required><br>
    <button type="submit">Register</button>
  </form>
</body>
</html>
"""

login_template = """
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
  <h1>Login</h1>
  <form method="POST">
    <label>Username:</label> <input name="username" type="text" required><br>
    <label>Password:</label> <input name="password" type="password" required><br>
    <button type="submit">Login</button>
  </form>
</body>
</html>
"""

moid_form_template = """
<!DOCTYPE html>
<html>
<head><title>Select MOID Days</title></head>
<body>
  <h1>Select MOID Days</h1>
  <form method="POST">
    <label>MOID Days:</label> <input name="moid_days" type="number" required>
    <button type="submit">Submit</button>
  </form>
</body>
</html>
"""

asteroids_template = """
<!DOCTYPE html>
<html>
<head><title>Asteroids</title></head>
<body>
  <h1>Random Asteroids for moid_days = {{ moid_days }}</h1>
  <ul>
    {% for asteroid in asteroids %}
      <li>{{ asteroid.full_name }} (Value: {{ asteroid.value }})</li>
    {% endfor %}
  </ul>
  <a href="{{ url_for('moid_form') }}">Search Another Distance</a>
</body>
</html>
"""

# ---------------------
# AUTHENTICATION HELPERS
# ---------------------
def login_required(func):
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# ---------------------
# ROUTES
# ---------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    # Use create_user from manage_users
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if create_user(username, password):
            return redirect(url_for("login"))
        return "User already exists or registration failed."
    return render_template_string(registration_template)

@app.route("/login", methods=["GET", "POST"])
def login():
    # Use authenticate_user from manage_users
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user_record = authenticate_user(username, password)
        if user_record:
            session["user_id"] = str(user_record["_id"])
            return redirect(url_for("moid_form"))
        return "Invalid credentials."
    return render_template_string(login_template)

@app.route("/moid_form", methods=["GET", "POST"])
@login_required
def moid_form():
    if request.method == "POST":
        moid_days = request.form["moid_days"]
        return redirect(url_for("show_asteroids", moid_days=moid_days))
    return render_template_string(moid_form_template)

@app.route("/asteroids/<moid_days>")
@login_required
def show_asteroids(moid_days):
    try:
        moid_days_int = int(moid_days)
    except ValueError:
        return "Invalid MOID days value!"

    matching_asteroids = list(asteroids_collection.find({"moid_days": moid_days_int}))
    valid_asteroids = [AsteroidModel(**a).dict() for a in matching_asteroids]
    # Take up to 3 random asteroids
    random_asteroids = random.sample(valid_asteroids, k=min(len(valid_asteroids), 3))

    return render_template_string(
        asteroids_template,
        moid_days=moid_days_int,
        asteroids=random_asteroids
    )

if __name__ == "__main__":
    app.run(debug=True)