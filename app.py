from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from db import SQL
from datetime import datetime, date
import sqlite3

app = Flask(__name__)
app.secret_key = "change-this-in-prod"

db = SQL()

# For some parts of this file (mainly the aggregation logic for grades / overviews) i used ChatGPT to learn and refine techniques and ideas to improve my code structure (all code is written by me) 

# Simple fallaback DDL for users table (if not exists)
CREATE_USERS_SQL = """
CREATE TABLE IF NOT EXISTS users(
    id INTEget PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hash TEXT NOT NULL
);
"""

try:

    # Try to ensure users table exists (at app start)
    db.execute(CREATE_USERS_SQL)
except Exception as e:
    print("DB init error:", e)

# ================ ROUTES ================

# Authentication, home, dashboard, schedule, applications, grades, assignments
@app.route("/")
def welcome():
    # Navbar is not shown in the welcome page
    return render_template("welcome.html", show_nav=False)

# Signup route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":

        # Read and normilize inputs
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        # Validation on required fields
 
        if not username or not email or not password or not confirm:
            flash("Please fill in all fields.", "warning")
            return redirect(url_for("signup"))
        
        if password != confirm:
            flash("Passwords do not match.", "danget")
            return redirect(url_for("signup"))
        
        if "@" not in email or "." not in email:
            flash("Please enter a valid email address.", "warning")
            return redirect(url_for("signup"))

        # Hash the password before storing it in the database
        pw_hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)

        try:
            # Insert the new user into the database
            db.execute(
                "INSERT INTO users (username, email, hash) VALUES (?, ?, ?)",
                username, email, pw_hash
            )
        
        except sqlite3.IntegrityError as e:

            # Handle unique constraint violations for username/email
            if "username" in str(e):
                flash("Username already exists. Try another one.", "danget")
            
            elif "email" in str(e):
                flash("Email already registered. Try logging in.", "info")
            
            else:
                flash("Database error. Try again.", "danget")
            
            return redirect(url_for("signup"))

        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html", show_nav=False)

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        # Read and normalize inputs
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Lookup user by email
        rows = db.execute(
            "SELECT id, username, email, hash FROM users WHERE email = ?",
            email
        )

        if not rows:
            flash("Invalid email or password.", "danget")
            return redirect(url_for("login"))

        user = rows[0]

        # Verify password
        if not check_password_hash(user["hash"], password):
            flash("Invalid email or password.", "danget")
            return redirect(url_for("login"))

        # Store user info in session
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["email"] = user["email"]

        return redirect(url_for("home"))
    
    return render_template("login.html", show_nav=False)

# Home / Dashboard route
@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    uid = session["user_id"]

    # Assignments: count only those due in the next 7 days and not done (used chatGPT to refine this type of date-filtering SQL queries but wrote all code myself)
    assignments_due = db.execute (
        "SELECT COUNT(*) AS c FROM assignments "
        "WHERE user_id = ? "
        "AND due_date IS NOT NULL "
        "AND DATE(due_date) >= DATE('now') "
        "AND DATE(due_date) <= DATE('now', '+7 day') "
        "AND status <> 'done'",
        uid
    )[0]["c"]

    # Applications: the count of only the active ones (not rejected/not interested ones)
    apps_active = db.execute (
        "SELECT COUNT(*) AS c FROM applications "
        "WHERE user_id = ? "
        "AND status NOT IN ('Rejected', 'Not Interested')",
        uid
    )[0]["c"]

    # Next application closing date (soonest close_date in the future)
    next_closing = db.execute (
        "SELECT MIN(close_date) AS d FROM applications "
        "WHERE user_id = ?  AND close_date IS NOT NULL "
        "AND DATE(close_date) >= DATE('now')",
        uid
    )[0]["d"]

    # Overall grade: weighted average across all modules 
    mods = db.execute(
        "SELECT id, credits FROM modules WHERE user_id = ?",
        uid
    )

    total_c = 0.0 # total credits
    acc = 0.0     # sum of grade * credits

    for m in mods:
        rows = db.execute(
            "SELECT weight_pct, score_pct FROM assessments WHERE module_id = ?", m["id"]
        )

        if not rows:
            continue

        w_sum = 0.0     # sum of weights with scores
        ws = 0.0        # sum of weight * score

        for r in rows:
            w = float(r["weight_pct"] or 0)
            s = r["score_pct"]

            if s is not None:
                w_sum += w
                ws += w * s
            
        if w_sum > 0:
            grade = ws / w_sum
            c = float(m["credits"] or 0.0)
            acc += grade * c
            total_c += c
    
    overall_grade = round(acc / total_c, 2) if total_c > 0 else None

    # Collect overview data for template
    overview = {
        "assignments_due_7d": assignments_due,
        "apps_active": apps_active,
        "next_closing": next_closing,
        "overall_grade": overall_grade
    }
    
    return render_template("home.html", show_nav=True, username=session.get("username"), overview=overview)

# Logout route
@app.route("/logout")
def logout():

    # Clear all session data and redirect to welcome page
    session.clear()
    flash("Logged out succesfully.", "info")
    return redirect(url_for("welcome"))


# ================ WEEKLY SCHEDULE ================

# Days helper
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Schedule main page:
@app.route("/schedule", methods=["GET"])
def schedule_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    # Load schedule items for the logged-in user
    rows = db.execute(
        "SELECT id, weekday, start_time, end_time, title, notes "
        "FROM schedule_items WHERE user_id = ? "
        "ORDER BY weekday ASC, start_time ASC, id ASC",
        session["user_id"]
    )
    print("SCHEDULE rows for user", session["user_id"], "=>", rows)  # <— ΔΕΣ ΤΟ LOG

    # Group rows by weekday for easier rendering
    items_by_day = {i: [] for i in range(7)}

    for r in rows:
        day = int(r["weekday"])
        items_by_day[day].append(r)

    return render_template("schedule.html", show_nav=True, items_by_day=items_by_day, days=DAYS)

# Save (add/update) a slot on schedule table
@app.route("/schedule/save", methods=["POST"])
def schedule_save():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    item_id_raw = request.form.get("id", "").strip()
    weekday_raw = request.form.get("weekday", "").strip()
    start = (request.form.get("start_time") or "").strip()
    end = (request.form.get("end_time") or "").strip()
    title = (request.form.get("title") or "").strip()
    notes = (request.form.get("notes") or "").strip()

    # Helper to check valid time format HH:MM
    def valid_time(t):
        if not t or len(t) != 5 or t[2] != ":":
            return False
        
        hh, mm = t.split(":")
        return hh.isdigit() and mm.isdigit() and 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59

    # validations:
    try:
        weekday = int(weekday_raw)
    except:
        weekday = -1
    
    if weekday < 0 or weekday > 6:
        flash("Please select a valid day", "warning")
        return redirect(url_for("schedule_page"))
    
    if not valid_time(start) or not valid_time(end):
        flash("Please enter valid times", "warning")
        return redirect(url_for("schedule_page"))
    
    if end <= start:
        flash("End time must be after start time", "warning")
        return redirect(url_for("schedule_page"))
    
    if not title:
        flash("Please enter a title", "warning")
        return redirect(url_for("schedule_page"))
    
    # Update or Insert 
    item_id = None
    if item_id_raw:

        # Update existing item
        try:
            item_id = int(item_id_raw)
        except:
            flash("Invalid item id", "warning")
            return redirect(url_for("schedule_page"))
    
    # Check for overlapping slots
    params = [session["user_id"], weekday]
    query = (
        "SELECT id, start_time, end_time, title "
        "FROM schedule_items WHERE user_id = ? AND weekday = ?"
    )

    # Exclude current item if updating
    if item_id is not None:
        query += " AND id != ?"
        params.append(item_id)
    
    existing = db.execute(query, *params)
    
    for r in existing:
        other_start = r["start_time"]
        other_end = r["end_time"]

        if not (end <= other_start or start >= other_end):
            flash(f"This slot overlaps with '{r['title']}' ({other_start} - {other_end}). Please choose a different time.", "warning")
            return redirect(url_for("schedule_page"))

    # If item_id is provided, update existing item
    if item_id is not None:
        row = db.execute(
            "SELECT user_id FROM schedule_items WHERE id = ?", item_id
        )

        if not row or row[0]["user_id"] != session["user_id"]:
            abort(403)
    
        db.execute(
            "UPDATE schedule_items "
            "SET weekday = ?, start_time = ?, end_time = ?, title = ?, notes = ? "
            "WHERE id = ?",
            weekday, start, end, title, notes, item_id
        )
        flash("Slot updated", "success")

    else:
        # Insert new item
        db.execute(
            "INSERT INTO schedule_items(user_id, weekday, start_time, end_time, title, notes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            session["user_id"], weekday, start, end, title, notes
        )
        flash("Slot added", "success")
    
    return redirect(url_for("schedule_page"))

# Delete a slot on schedule table
@app.route("/schedule/delete/<int:item_id>", methods=["POST"])
def schedule_delete(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    row = db.execute(
        "SELECT user_id FROM schedule_items WHERE id = ?", item_id
    )

    if not row or row[0]["user_id"] != session["user_id"]:
        abort(403)
    
    db.execute (
        "DELETE FROM schedule_items WHERE id = ?", item_id
    )

    flash("Slot deleted", "success")
    return redirect(url_for("schedule_page"))

# Clear the whole table
@app.route("/schedule/clear", methods=["POST"])
def schedule_clear():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    db.execute(
        "DELETE FROM schedule_items WHERE user_id = ?", session["user_id"]
    )

    flash("Schedule cleared", "success")
    return redirect(url_for("schedule_page"))



# ================ APPLICATIONS ================

# Application status / CV / other choices
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

# Applications main page
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

# Create a new application
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

    # Validations
    if status not in STATUS_CHOICES or cv not in CV_CHOICES or cover not in OPT_CHOICES or written not in OPT_CHOICES:
        flash("Invalid selection.", "warning")
        return redirect(url_for("applications_page"))
    
    # Required fields
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

# Update an existing application
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

# Delete an application
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


# ================ GRADES ================

# Helper to calculate per-module stats
# Used ChatGPT to learn techniques for weighted averages and data aggregation but wrote all code myself
def _calc_module_stats(module_id: int):

    # It calculates the weight of the assessments and the grade
    rows = db.execute(
        "SELECT weight_pct, score_pct FROM assessments WHERE module_id = ?",
        module_id
    )

    if not rows:
        return (0.0, None, 0.0, 0.0)
    
    total_weight = sum((r["weight_pct"] or 0) for r in rows)
    
    w_sum = 0.0     # sum of weights with scores
    ws_sum = 0.0    # sum of weight * score

    for r in rows:
        w = float(r["weight_pct"] or 0)
        s = r["score_pct"]

        if s is not None:
            w_sum += w
            ws_sum += w * s
        
    current_grade = round(ws_sum / w_sum, 2) if w_sum > 0 else None
    current_points = round(ws_sum / 100.0, 2)
        
    return (round(total_weight, 2), current_grade, round(w_sum, 2), current_points)

# Grades main page
@app.route("/grades", methods=["GET"])
def grades_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    # Load modules for the user
    modules = db.execute(
        "SELECT id, name, term, credits FROM modules WHERE user_id = ? ORDER BY term, name",
        session["user_id"]
    )

    # Building assessments_by_module and modules_by_term
    assessments_by_module = {}
    modules_by_term = {}

    for m in modules:
        # Load assessments for each module
        arows = db.execute(
            "SELECT id, title, weight_pct, score_pct FROM assessments WHERE module_id = ? ORDER BY id",
            m["id"]
        )
        assessments_by_module[m["id"]] = arows
        
        # Computing per-module stats
        total_w, cur_grade, w_with_score, cur_points = _calc_module_stats(m["id"])

        m["total_weight"] = total_w
        m["current_grade"] = cur_grade
        m["w_with_score"] = w_with_score
        m["current_points"] = cur_points

        term = int(m["term"])
        modules_by_term.setdefault(term, []).append(m)
    
    # ---- Term summaries (credits-weighted) ----
    term_summaries = {}
    for term, mods in modules_by_term.items():
        t_credits = 0.0
        t_weighted = 0.0

        for m in mods:
            c = float(m["credits"])
            t_credits += c
            if m["current_grade"] is not None:
                t_weighted += c * float(m["current_grade"])

        t_avg = round(t_weighted / t_credits, 2) if t_credits > 0 else None
        term_summaries[term] = {
            "credits": round(t_credits, 2),
            "avg": t_avg,
        }
    
    # Build courses map to combine repeated modules with the same name across terms
    courses_map = {}

    for term, mods in modules_by_term.items():
        for m in mods:
            cname = (m.get("name") or "").strip()
            if not cname:
                continue

            credits = float(m.get("credits") or 0.0)
            points = float(m.get("current_points") or 0.0)

            agg = courses_map.setdefault(cname, {
                
                "name": cname, 
                "ects_total" : 0.0,
                "terms": {},            # term -> { "points": float }
            })

            agg["ects_total"] += credits

            tentry = agg["terms"].setdefault(term, {"points": 0.0})
            tentry["points"] += points

    # Collapse for templates and calculate overall averages
    courses_overall = []
    for cname, agg in courses_map.items():
        per_terms = []
        overall_points = 0.0

        for t in sorted(agg["terms"].keys()):
            pts = round(agg["terms"][t]["points"], 2)
            per_terms.append({"term": t, "grade": pts})
            overall_points += pts

        courses_overall.append({
            "name": agg["name"],
            "overall": round(overall_points, 2),
            "ects_total": int(agg["ects_total"]) if agg["ects_total"].is_integer() else round(agg["ects_total"], 1),
            "terms_count": len(agg["terms"]),
            "per_terms": per_terms,
        })

    # Sort courses alphabetically
    courses_overall.sort(key=lambda x: x["name"].lower())

    # Calculate overall average based on overall points for each course
    vals = [c["overall"] for c in courses_overall if isinstance(c.get("overall"), (int, float))]
    overall_avg = round(sum(vals) / len(vals), 2) if vals else None


    return render_template("grades.html", show_nav=True,
                           modules_by_term = modules_by_term,
                           assessments_by_module = assessments_by_module,
                           term_summaries = term_summaries,
                           overall_avg = overall_avg, 
                           courses_overall=courses_overall)

# Add a new module
@app.route("/grades/module/add", methods=["POST"])
def grades_module_add():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    # Simple helper to quickly add a new module with default values
    term = request.args.get("term", type=int) or 1

    new_id = db.execute(
        "INSERT INTO modules (user_id, name, term, credits) VALUES (?, ?, ?, ?)",
        session["user_id"], "New Module", term, 5.0
    )

    flash("Module created.", "success")
    return redirect(url_for("grades_page", open=new_id))

# Create a module
@app.route("/grades/module/create", methods=["POST"])
def grades_module_create():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    name = (request.form.get("name") or "").strip()
    term = int(request.form.get("term") or 1)
    credits = float(request.form.get("credits") or 0)

    if not name or credits <= 0 or term < 1:
        flash("Please fill module name, valid term and credits.", "warning")
        return redirect(url_for("grades_page"))
    
    db.execute(
        "INSERT INTO modules (user_id, name, term, credits) VALUES (?, ?, ?, ?)",
        session["user_id"], name, term, credits
    )

    flash("Module saved.", "success")
    return redirect(url_for("grades_page"))

# Update an existing module
@app.route("/grades/module/<int:module_id>/update", methods=["POST"])
def grades_module_update(module_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    owner = db.execute(
        "SELECT user_id FROM modules WHERE id = ?", module_id
    )

    if not owner or owner[0]["user_id"] != session["user_id"]:
        abort(403)
    
    name = (request.form.get("name") or "").strip()
    term = int(request.form.get("term") or 1)
    credits = float(request.form.get("credits") or 0)

    if not name or credits <= 0 or term < 1:
        flash("Please fill module name, valid term and credits.", "warning")
        return redirect(url_for("grades_page"))
    
    db.execute(
        "UPDATE modules SET name = ?, term = ?, credits = ? WHERE id = ?",
        name, term, credits, module_id
    )

    flash("Module updated.", "success")
    return redirect(url_for("grades_page"))

# Delete a module
@app.route("/grades/modules/<int:module_id>/delete", methods=["POST"])
def grades_module_delete(module_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    owner = db.execute(
        "SELECT user_id FROM modules WHERE id = ?", module_id
    )

    if not owner or owner[0]["user_id"] != session["user_id"]:
        abort(403)
    
    db.execute(
        "DELETE FROM modules WHERE id = ?", module_id
    )

    flash("Module deleted.", "info")
    return redirect(url_for("grades_page"))


# Create a new assessment for a module
@app.route("/grades/modules/<int:module_id>/assessment/create", methods=["POST"])
def grades_assessment_create(module_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    owner = db.execute(
        "SELECT user_id FROM modules WHERE id = ?", module_id
    )

    if not owner or owner[0]["user_id"] != session["user_id"]:
        abort(403)
    

    title = (request.form.get("title") or "").strip()
    weight_raw = request.form.get("weight_pct")
    score_raw =  request.form.get("score_pct")

    # Parsing numbers safely (empty strings -> None)
    try:
        weight = float(weight_raw)
    except:
        weight = None
    
    try:
        score = float(score_raw) if score_raw not in (None, "",) else None
    except:
        score = None
    
    if not title or weight is None or weight < 0 or weight > 100:
        flash("Fill a valid assessment title and weight (0-100).", "warning")
        return redirect(url_for("grades_page"))
    
    db.execute(
        "INSERT INTO assessments (module_id, title, weight_pct, score_pct) VALUES (?, ?, ?, ? )",
        module_id, title, weight, score
    )

    flash("Assessment added.", "success")
    return redirect(url_for("grades_page"))

# Update an existing assessment
@app.route("/grades/assessment/<int:assessment_id>/update", methods=["POST"])
def grades_assessment_update(assessment_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    row = db.execute(
        "SELECT a.module_id, m.user_id FROM assessments a JOIN modules m ON m.id = a.module_id WHERE a.id = ?",
        assessment_id
    )

    if not row or row[0]["user_id"] != session["user_id"]:
        abort(403)
    
    title = (request.form.get("title") or "").strip()
    weight_raw = request.form.get("weight_pct")
    score_raw =  request.form.get("score_pct")

    # Parsing numbers safely (empty strings -> None)
    try:
        weight = float(weight_raw)
    except:
        weight = None
    
    try:
        score = float(score_raw) if score_raw not in (None, "",) else None
    except:
        score = None
    
    if not title or weight is None or weight < 0 or weight > 100:
        flash("Fill a valid assessment title and weight (0-100).", "warning")
        return redirect(url_for("grades_page"))
    
    db.execute(
        "UPDATE assessments SET title = ?, weight_pct = ?, score_pct = ? WHERE id = ?",
        title, weight, score, assessment_id
    )

    flash("Assessment updated.", "success")
    return redirect(url_for("grades_page"))

# Delete an assessment
@app.route("/grades/assessment/<int:assessment_id>/delete", methods=["POST"])
def grades_assessment_delete(assessment_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    row = db.execute(
        "SELECT a.module_id, m.user_id FROM assessments a JOIN modules m ON m.id = a.module_id WHERE a.id = ?",
        assessment_id
    )
    if not row or row[0]["user_id"] != session["user_id"]:
        abort(403)

    db.execute("DELETE FROM assessments WHERE id = ?", assessment_id)
    flash("Assessment deleted.", "info")
    return redirect(url_for("grades_page"))


# ================ ASSIGNMENTS ================

# Helper to auto-assign priority based on due date
def auto_priority(due_date_str):
    if not due_date_str:
        return 3
    
    try:
        due = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    except ValueError:
        return 3
    
    diff = (due - date.today()).days

    if diff < 0:
        return 0    # overdue
    if diff <= 3:
        return 1    # urgent
    if diff <= 14:
        return 2    # soon
    return 3        # low

# Helper to compute assignment status based on stages (done/in_progress/pending)
def compute_assignment_status(assignment_id):

    stages = db.execute(
        "SELECT done FROM assignments_stages WHERE assignment_id = ?", assignment_id
    )
    total = len(stages)
    done = sum(s["done"] for s in stages)
    progress = (done / total * 100) if total > 0 else 0

    status = (
        "done" if progress == 100
        else "in_progress" if done > 0
        else "pending"
    )

    db.execute (
        "UPDATE assignments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        status, assignment_id
    )

    return progress, status


# Assignments main page
@app.route("/assignments", methods=["GET"])
def assignments_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_id = session["user_id"]

    # Assignments sorted by priority and due date
    assignments = db.execute (
        "SELECT id, title, due_date, notes, priority, status, created_at, updated_at "
        "FROM assignments WHERE user_id = ? "
        "ORDER BY priority ASC, "
        "CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, "
        "due_date ASC, id DESC",
        user_id
    )

    # Recompute priority dynamically so it always respects today's date
    for a in assignments:
        a["priority"] = auto_priority(a["due_date"])

    # Sort by priority, due_date, id descending
    # Used chatGPT to learn about custom sorting with multiple criteria but wrote all code myself
    def sort_key(a):
        due_key = a["due_date"] or "9999-12-31"
        return (a["priority"], due_key, -a["id"])
    
    assignments.sort(key=sort_key)

    # Load stages for all assignments of the user
    stage_rows = db.execute (
        "SELECT id, assignment_id, title, done, position " 
        "FROM assignments_stages "
        "WHERE assignment_id  IN (SELECT id FROM assignments WHERE user_id = ?) " 
        "ORDER BY assignment_id, position ASC, id ASC",
        user_id
    )

    # Group stages by assignment_id
    stages_by_assignment = {}

    for s in stage_rows:
        stages_by_assignment.setdefault(s["assignment_id"], []).append(s)
    
    
    return render_template("assignments.html", show_nav=True, assignments=assignments, stages_by_assignment=stages_by_assignment, today=date.today().isoformat())

# Add a new assignment
@app.route("/assignments/add", methods=["POST"])
def assignments_add():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    title = (request.form.get("title") or "").strip()
    due_date = request.form.get("due_date") or None
    notes = (request.form.get("notes") or "").strip()
    status = (request.form.get("status") or "pending").strip()

    priority = auto_priority(due_date)

    new_id = db.execute(
        "INSERT INTO assignments (user_id, title, due_date, priority, notes, status) VALUES (?, ?, ?, ?, ?, ?)",
        session["user_id"], title, due_date, priority, notes, status
    )

    flash("Assignment created", "success")
    return redirect(url_for("assignments_page", open=new_id))

# Update an existing assignment
@app.route("/assignments/<int:assignment_id>/update", methods=["POST"])
def assignments_update(assignment_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    row = db.execute (
        "SELECT user_id FROM assignments WHERE id = ?", assignment_id
    )

    if not row or row[0]["user_id"] != session["user_id"]:
        abort(403)
    
    title = (request.form.get("title") or "").strip()
    due_date = request.form.get("due_date") or None
    notes = (request.form.get("notes") or "").strip()
    status = (request.form.get("status") or "pending").strip()

    # When saving notes only, keep existing title and due_date
    if not title:
        row2 = db.execute("SELECT title, due_date FROM assignments WHERE id = ?", assignment_id)
        title = row2[0]["title"]
        due_date = row2[0]["due_date"]
    
    priority = auto_priority(due_date)
    
    db.execute (
        "UPDATE assignments SET title = ?, due_date = ?, priority = ?, notes = ?, status = ? WHERE id = ?",
        title, due_date, priority, notes, status, assignment_id
    )

    flash("Assignment updated", "success")
    return redirect(url_for("assignments_page"))

# Delete an assignment
@app.route("/assignments/<int:assignment_id>/delete", methods=["POST"])
def assignments_delete(assignment_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    row = db.execute (
        "SELECT user_id FROM assignments WHERE id = ?", assignment_id
    )

    if not row or row[0]["user_id"] != session["user_id"]:
        abort(403)
    
    db.execute (
        "DELETE FROM assignments WHERE id = ?", assignment_id
    )

    flash("Assignment deleted", "success")
    return redirect(url_for("assignments_page"))


# Add a new stage to an assignment
@app.route("/assignments/<int:assignment_id>/stage/add", methods=["POST"])
def stage_add(assignment_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    row = db.execute (
        "SELECT user_id FROM assignments WHERE id = ?", assignment_id
    )

    if not row or row[0]["user_id"] != session["user_id"]:
        abort(403)
    
    title = (request.form.get("title") or "").strip()
    if not title:
        flash("Stage title cannot be empty", "warning")
        return redirect(url_for("assignments_page"))
    
    # Compute next position
    next_pos = db.execute (
        "SELECT COALESCE(MAX(position), 0) AS maxp FROM assignments_stages WHERE assignment_id = ?", assignment_id
    )[0]["maxp"] + 1

    db.execute (
        "INSERT INTO assignments_stages (assignment_id, title, done, position) VALUES (?, ?, ?, ?)",
        assignment_id, title, 0, next_pos
    )

    flash("Stage added", "success")
    return redirect(url_for("assignments_page"))


# Toggle stage done/not done
@app.route("/assignments/stage/<int:stage_id>/toggle", methods=["POST"])
def stage_toggle(stage_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    row = db.execute (
        "SELECT a.user_id, s.assignment_id AS assignment_id "
        "FROM assignments_stages s "
        "JOIN assignments a ON a.id = s.assignment_id "
        "WHERE s.id = ?",
        stage_id 
    )

    if not row or row[0]["user_id"] != session["user_id"]:
        abort(403)
    
    assignment_id = row[0]["assignment_id"]
    
    # Flip the done flag (1 -> 0 , 0 -> 1)
    db.execute (
        "UPDATE assignments_stages SET done = CASE done WHEN 1 THEN 0 ELSE 1 END WHERE id = ?", stage_id
    )    

    compute_assignment_status(assignment_id)

    flash("Stage updated", "success")
    return redirect(url_for("assignments_page"))

# Delete stage
@app.route("/assignments/stage/<int:stage_id>/delete", methods=["POST"])
def stage_delete(stage_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    row = db.execute (
        "SELECT a.user_id, s.assignment_id AS assignment_id "
        "FROM assignments_stages s "
        "JOIN assignments a ON a.id = s.assignment_id "
        "WHERE s.id = ?",
        stage_id 
    )

    if not row or row[0]["user_id"] != session["user_id"]:
        abort(403)

    assignment_id = row[0]["assignment_id"]
    
    db.execute (
        "DELETE FROM assignments_stages WHERE id = ?", stage_id
    )

    # Recompute assignment status after stage deletion
    compute_assignment_status(assignment_id)

    flash("Stage deleted", "success")
    return redirect(url_for("assignments_page"))


# Toggle whole assignment done/not done
@app.route("/assignments/<int:assignment_id>/toggle_done", methods=["POST"])
def assignment_toggle_done(assignment_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    row = db.execute (
        "SELECT user_id, status FROM assignments WHERE id = ?", assignment_id
    )

    if not row or row[0]["user_id"] != session["user_id"]:
        abort(403)
    
    current_status = row[0]["status"]

    if current_status == "done":
        compute_assignment_status(assignment_id)  # recompute based on stages
    else:
        # Mark as done directly
        db.execute (
            "UPDATE assignments SET status = 'done', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            assignment_id
        )
    
    flash("Assignment status updated", "success")
    return redirect(url_for("assignments_page"))
    

# ===============================

if __name__ == "__main__":
    
    # Run the app in debug mode for development
    app.run(debug=True)