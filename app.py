from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import SQL
import sqlite3

app = Flask(__name__)
app.secret_key = "change-this-in-prod"

db = SQL()

CREATE_USERS_SQL = """
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hash TEXT NOT NULL
);
"""

try:
    db.execute(CREATE_USERS_SQL)
except Exception as e:
    print("DB init error:", e)

# ================ ROUTES ================

@app.route("/")
def welcome():
    # Navbar is not shown in the welcome page
    return render_template("welcome.html", show_nav=False)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        # Validation:

        if not username or not email or not password or not confirm:
            flash("Please fill in all fields.", "warning")
            return redirect(url_for("signup"))
        
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("signup"))
        
        if "@" not in email or "." not in email:
            flash("Please enter a valid email address.", "warning")
            return redirect(url_for("signup"))

        pw_hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)

        try:
            db.execute(
                "INSERT INTO users (username, email, hash) VALUES (?, ?, ?)",
                username, email, pw_hash
            )
        
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                flash("Username already exists. Try another one.", "danger")
            
            elif "email" in str(e):
                flash("Email already registered. Try logging in.", "info")
            
            else:
                flash("Database error. Try again.", "danger")
            
            return redirect(url_for("signup"))

        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html", show_nav=False)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        rows = db.execute(
            "SELECT id, username, email, hash FROM users WHERE email = ?",
            email
        )

        if not rows:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

        user = rows[0]
        if not check_password_hash(user["hash"], password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["email"] = user["email"]

        return redirect(url_for("home"))
    
    return render_template("login.html", show_nav=False)

@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    return render_template("home.html", show_nav=True, username=session.get("username"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out succesfully.", "info")
    return redirect(url_for("welcome"))

@app.route("/schedule")
def schedule():
    return render_template("schedule.html", show_nav=True)

@app.route("/applies")
def applies():
    return render_template("applies.html", show_nav=True)

if __name__ == "__main__":
    app.run(debug=True)


