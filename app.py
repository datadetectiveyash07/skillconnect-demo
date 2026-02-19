from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import os
app = Flask(__name__)
app.secret_key = "supersecretkey"

########################################
# DB CONNECTION
########################################
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

########################################
# HOME
########################################
@app.route("/")
def home():
    return render_template("home.html")

########################################
# WORKER REGISTER
########################################
@app.route("/worker_register", methods=["GET","POST"])
def worker_register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        skills = request.form["skills"]
        exp = request.form["experience"]
        location = request.form.get("location","Pune")

        db = get_db()

        # insert into users
        cur = db.execute(
            "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
            (name,email,password,"worker"))
        user_id = cur.lastrowid

        # worker profile
        db.execute("""
        INSERT INTO worker_profiles(user_id,skills,experience,location)
        VALUES(?,?,?,?)
        """,(user_id,skills,exp,location))

        db.commit()
        flash("Worker Registered Successfully")
        return redirect("/worker_login")

    return render_template("worker_register.html")

########################################
# WORKER LOGIN
########################################
@app.route("/worker_login", methods=["GET","POST"])
def worker_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        user = db.execute("""
        SELECT * FROM users WHERE email=? AND password=? AND role='worker'
        """,(email,password)).fetchone()

        if user:
            session["worker_id"] = user["id"]
            return redirect("/worker_dashboard")
        else:
            flash("Invalid login")

    return render_template("worker_login.html")

########################################
# WORKER DASHBOARD + JOB MATCHING
########################################
@app.route("/worker_dashboard")
def worker_dashboard():
    if "worker_id" not in session:
        return redirect("/worker_login")

    db = get_db()

    worker = db.execute("""
    SELECT users.name, worker_profiles.*
    FROM worker_profiles
    JOIN users ON worker_profiles.user_id = users.id
    WHERE user_id=?
    """,(session["worker_id"],)).fetchone()

    # 🔥 smart job matching
    jobs = db.execute("""
    SELECT * FROM jobs
    WHERE skill_required LIKE ?
    AND status='open'
    """,('%'+worker["skills"]+'%',)).fetchall()

    return render_template("worker_dashboard.html",worker=worker,jobs=jobs)

########################################
# APPLY JOB
########################################
@app.route("/apply_job/<int:job_id>")
def apply_job(job_id):
    if "worker_id" not in session:
        return redirect("/worker_login")

    db = get_db()

    exist = db.execute("""
    SELECT * FROM applications WHERE job_id=? AND worker_id=?
    """,(job_id,session["worker_id"])).fetchone()

    if not exist:
        db.execute("""
        INSERT INTO applications(job_id,worker_id,status)
        VALUES(?,?,?)
        """,(job_id,session["worker_id"],"pending"))
        db.commit()

    flash("Applied Successfully")
    return redirect("/worker_dashboard")

########################################
# COMPANY REGISTER
########################################
@app.route("/company_register", methods=["GET","POST"])
def company_register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        location = request.form["location"]

        db = get_db()

        cur = db.execute("""
        INSERT INTO users(name,email,password,role)
        VALUES(?,?,?,?)
        """,(name,email,password,"company"))
        user_id = cur.lastrowid

        db.execute("""
        INSERT INTO company_profiles(user_id,company_name,location)
        VALUES(?,?,?)
        """,(user_id,name,location))

        db.commit()
        flash("Company Registered")
        return redirect("/company_login")

    return render_template("company_register.html")

########################################
# COMPANY LOGIN
########################################
@app.route("/company_login", methods=["GET","POST"])
def company_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        comp = db.execute("""
        SELECT * FROM users WHERE email=? AND password=? AND role='company'
        """,(email,password)).fetchone()

        if comp:
            session["company_id"] = comp["id"]
            return redirect("/company_dashboard")
        else:
            flash("Invalid login")

    return render_template("company_login.html")

########################################
# COMPANY DASHBOARD
########################################
@app.route("/company_dashboard")
def company_dashboard():
    if "company_id" not in session:
        return redirect("/company_login")

    db = get_db()

    jobs = db.execute("SELECT * FROM jobs WHERE company_id=?",
                      (session["company_id"],)).fetchall()

    applications = db.execute("""
    SELECT applications.*, users.name, worker_profiles.skills
    FROM applications
    JOIN users ON applications.worker_id = users.id
    JOIN worker_profiles ON worker_profiles.user_id = users.id
    JOIN jobs ON applications.job_id = jobs.id
    WHERE jobs.company_id=?
    """,(session["company_id"],)).fetchall()

    return render_template("company_dashboard.html",
                           jobs=jobs,
                           applications=applications)

########################################
# POST JOB
########################################
@app.route("/post_job", methods=["POST"])
def post_job():
    if "company_id" not in session:
        return redirect("/company_login")

    title = request.form["title"]
    skill = request.form["skill"]
    location = request.form["location"]
    salary = request.form["salary"]
    desc = request.form["desc"]

    db = get_db()
    db.execute("""
    INSERT INTO jobs(company_id,title,skill_required,location,salary,description)
    VALUES(?,?,?,?,?,?)
    """,(session["company_id"],title,skill,location,salary,desc))
    db.commit()

    flash("Job Posted")
    return redirect("/company_dashboard")

########################################
# ACCEPT WORKER
########################################
@app.route("/accept/<int:app_id>")
def accept_worker(app_id):
    db = get_db()
    db.execute("UPDATE applications SET status='accepted' WHERE id=?",(app_id,))
    db.commit()
    flash("Worker Accepted")
    return redirect("/company_dashboard")

########################################
# ⭐ RATE WORKER
########################################
@app.route("/rate/<int:worker_id>", methods=["POST"])
def rate_worker(worker_id):
    rating = float(request.form["rating"])
    feedback = request.form.get("feedback","")

    db = get_db()

    # store rating history
    db.execute("""
    INSERT INTO ratings(worker_id,company_id,rating,feedback)
    VALUES(?,?,?,?)
    """,(worker_id,session["company_id"],rating,feedback))

    # update avg rating
    avg = db.execute("SELECT AVG(rating) as avg FROM ratings WHERE worker_id=?",
                     (worker_id,)).fetchone()["avg"]

    db.execute("""
    UPDATE worker_profiles SET rating=? WHERE user_id=?
    """,(avg,worker_id))

    db.commit()
    flash("Rating Submitted")
    return redirect("/company_dashboard")

########################################
# ADMIN LOGIN
########################################
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form["username"]=="admin" and request.form["password"]=="admin":
            session["admin"]=True
            return redirect("/admin_dashboard")

    return render_template("admin_login.html")

########################################
# ADMIN DASHBOARD
########################################
@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin")

    db = get_db()

    workers = db.execute("""
    SELECT users.name, worker_profiles.skills, worker_profiles.rating
    FROM users JOIN worker_profiles
    ON users.id = worker_profiles.user_id
    """).fetchall()

    companies = db.execute("""
    SELECT users.name, company_profiles.location
    FROM users JOIN company_profiles
    ON users.id = company_profiles.user_id
    """).fetchall()

    jobs = db.execute("SELECT * FROM jobs").fetchall()

    return render_template("admin_dashboard.html",
                           workers=workers,
                           companies=companies,
                           jobs=jobs)

########################################
# LOGOUT
########################################
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

########################################
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
