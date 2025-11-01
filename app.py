from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
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

# ================ APPLICATIONS ================

STATUS_CHOICES = [
    "Not Applied",
    "Interested",
    "Application Submitted",
    "Online Assessment",
    "Case Study",
    "HireVue",
    "Telephone Interview",
    "Video Interview",
    "Face-to-face Interview",
    "Assessment Centre",
    "Offer Received",
    "Rejected",
    "Not Interested"
]

CV_CHOICES = ["Yes", "No"]
OPT_CHOICES = ["Yes", "No", "Optional"]

@app.route("/applications", methods=["GET"])
def applications_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    rows = db.execute(
        "SELECT id, status, company, programme, open_date, close_date, cv, cover, written, notes "
        "FROM applications WHERE user_id = ? ORDER BY id DESC",
        session["user_id"]
    )

    return render_template("applications.html", show_nav=True, 
        applications = rows, 
        STATUS_CHOICES = STATUS_CHOICES, 
        CV_CHOICES = CV_CHOICES, 
        OPT_CHOICES = OPT_CHOICES
    )

@app.route("/applications/add", methods=["POST"])
def applications_add():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    status = request.form.get("status", "Not Applied").strip()
    company = request.form.get("company", "").strip()
    programme = request.form.get("programme", "").strip()
    open_date = request.form.get("open_date") or None
    close_date = request.form.get("close_date") or None
    cv = request.form.get("cv", "Yes").strip()
    cover = request.form.get("cover", "Optional").strip()
    written = request.form.get("written", "Optional").strip()
    notes = request.form.get("notes", "").strip()

    if status not in STATUS_CHOICES or cv not in CV_CHOICES or cover not in OPT_CHOICES or written not in OPT_CHOICES:
        flash("Invalid selection.", "warning")
        return redirect(url_for("applications_page"))
    
    if not company or not programme:
        flash("Please fill Company and Programme.", "warning")
        return redirect(url_for("applications_page"))
    
    db.execute(
        "INSERT INTO applications (user_id, status, company, programme, open_date, close_date, cv, cover, written, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        session["user_id"], status, company, programme, open_date, close_date, cv, cover, written, notes
    )

    flash("Application added.", "success")
    return redirect(url_for("applications_page"))

@app.route("/applications/<int:app_id>/update", methods=["POST"])
def applications_update(app_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    owner = db.execute("SELECT user_id FROM applications WHERE id = ?", app_id)

    if not owner or owner[0]["user_id"] != session["user_id"]:
        abort(403)

    status = request.form.get("status", "Not Applied").strip()
    company = request.form.get("company", "").strip()
    programme = request.form.get("programme", "").strip()
    open_date = request.form.get("open_date") or None
    close_date = request.form.get("close_date") or None
    cv = request.form.get("cv", "Yes").strip()
    cover = request.form.get("cover", "Optional").strip()
    written = request.form.get("written", "Optional").strip()
    notes = request.form.get("notes", "").strip()

    if status not in STATUS_CHOICES or cv not in CV_CHOICES or cover not in OPT_CHOICES or written not in OPT_CHOICES:
        flash("Invalid selection.", "warning")
        return redirect(url_for("applications_page"))
    
    if not company or not programme:
        flash("Please fill Company and Programme.", "warning")
        return redirect(url_for("applications_page"))
    
    db.execute(
        "UPDATE applications SET status = ?, company = ?, programme = ?, open_date = ?, close_date = ?, cv = ?, cover = ?, written = ?, notes = ? "
        "WHERE id = ?",
        status, company, programme, open_date, close_date, cv, cover, written, notes, app_id
    )
    flash("Saved.", "success")
    return redirect(url_for("applications_page"))

@app.route("/applications/<int:app_id>/delete", methods=["POST"])
def applications_delete(app_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    owner = db.execute("SELECT user_id FROM applications WHERE id = ?", app_id)

    if not owner or owner[0]["user_id"] != session["user_id"]:
        abort(403)
    
    db.execute("DELETE FROM applications WHERE id = ?", app_id)
    flash("Deleted.", "info")
    return redirect(url_for("applications_page"))


# ===============================

if __name__ == "__main__":
    app.run(debug=True)


