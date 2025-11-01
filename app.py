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


# ================ GRADES ================

def _calc_module_stats(module_id: int):


    # It will return the total_weight, current_grade or None for a given module

    rows = db.execute(
        "SELECT weight_pct, score_pct FROM assessments WHERE module_id = ?",
        module_id
    )

    if not rows:
        return (0.0, None)

    # total_weight: sum of all weight_pct for the module
    total_weight = sum((r["weight_pct"] or 0) for r in rows)

    w_sum = 0.0     # sum of weights that have a valid score
    ws_sum = 0.0    # sum of weight * score

    for r in rows:
        w = float(r["weight_pct"] or 0)
        s = r["score_pct"]

        if s is not None:
            w_sum += w
            ws_sum += w * s
    
    # current: weighted average using only the assessments that have a non null score_pct (if no scores exists ==> return None)
    current = round(ws_sum / w_sum, 2) if w_sum > 0 else None
    return (round(total_weight, 2), current)


@app.route("/grades", methods=["GET"])
def grades_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    modules = db.execute(
        "SELECT id, name, term, credits FROM modules WHERE user_id = ? ORDER BY term, name",
        session["user_id"]
    )

    # organizing the assessments per module and then modules per term
    assessments_by_module = {}
    modules_by_term = {}

    for m in modules:
        #load assessments for each module
        arows = db.execute(
            "SELECT id, title, weight_pct, source_pct FROM assessments WHERE module_id = ? ORDER BY id",
            m["id"]
        )
        assessments_by_module[m["id"]] = arows
        
        # computing stats for module
        total_w, cur_grade = _calc_module_stats(m["id"])

        m["total_weight"] = total_w
        m["current_grade"] = cur_grade

        term = int(m["term"])
        modules_by_term.setdefault(term, []).append(m)
    
    # summarising per team (credits-weighted avergae) and the overall average
    term_summaries = {}
    overall_credits = 0.0
    overall_weighted = 0.0

    for term, mods in modules_by_term.items():
        t_credits = 0.0
        t_weighted = 0.0

        for m in mods:
            c = float(m["credits"])
            t_credits += c

            # only includes the modules that currently have a grade
            if m["current_grade"] is not None:
                t_weighted += c * float(m["current_grade"])
        
        t_avg = round(t_weighted / t_credits, 2) if t_credits > 0 else None

        term_summaries[term] = {
            "credit s": round(t_credits, 2),
            "avg": t_avg
        }

        overall_credits += t_credits
        overall_weighted += t_weighted
    
    overall_avg = round(overall_weighted / overall_credits, 2) if overall_credits > 0 else None

    return render_template("grades.html", show_nav=True,
                           modules_by_term = modules_by_term,
                           assessments_by_module = assessments_by_module,
                           term_summaries = term_summaries,
                           overall_avg = overall_avg)

# -------- Modules: create / update / delete ----------

@app.route("/grades/module/add", methods=["POST"])
def grades_module_add():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    term = request.args.get("term", type=int) or 1

    db.execute(
        "INSERT INTO modules (user_id, name, term, credits) VALUES (?, ?, ?, ?)",
        session["user_id"], "New Module", term, 5.0
    )

    flash("Module created.", "success")
    return redirect(url_for("grades_page"))

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


# -------- Assessments: create / update / delete ----------

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
    weight_raw = request.form.ger("weight_pct")
    score_raw =  request.form.ger("score_pct")

    # parsing numbers safely
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
    weight_raw = request.form.ger("weight_pct")
    score_raw =  request.form.ger("score_pct")

    # parsing numbers safely
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


# ===============================

if __name__ == "__main__":
    app.run(debug=True)


