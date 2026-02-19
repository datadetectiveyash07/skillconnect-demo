import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# ================= USERS (for login system) =================
c.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT,   -- worker/company/admin
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ================= WORKER PROFILE =================
c.execute("""
CREATE TABLE IF NOT EXISTS worker_profiles(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    skills TEXT,
    experience INTEGER,
    location TEXT,
    expected_salary INTEGER,
    availability TEXT,
    rating REAL DEFAULT 0,
    total_reviews INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# ================= COMPANY PROFILE =================
c.execute("""
CREATE TABLE IF NOT EXISTS company_profiles(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    company_name TEXT,
    location TEXT,
    description TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# ================= JOBS =================
c.execute("""
CREATE TABLE IF NOT EXISTS jobs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER,
    title TEXT,
    skill_required TEXT,
    experience_required INTEGER,
    location TEXT,
    salary INTEGER,
    job_type TEXT,
    description TEXT,
    status TEXT DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(company_id) REFERENCES users(id)
)
""")

# ================= JOB APPLICATIONS =================
c.execute("""
CREATE TABLE IF NOT EXISTS applications(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    worker_id INTEGER,
    status TEXT DEFAULT 'pending',  -- pending/accepted/rejected/completed
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(id),
    FOREIGN KEY(worker_id) REFERENCES users(id)
)
""")

# ================= WORK HISTORY =================
c.execute("""
CREATE TABLE IF NOT EXISTS work_history(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER,
    company_id INTEGER,
    job_id INTEGER,
    duration TEXT,
    feedback TEXT,
    FOREIGN KEY(worker_id) REFERENCES users(id),
    FOREIGN KEY(company_id) REFERENCES users(id)
)
""")

# ================= RATINGS =================
c.execute("""
CREATE TABLE IF NOT EXISTS ratings(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER,
    company_id INTEGER,
    job_id INTEGER,
    rating INTEGER,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(worker_id) REFERENCES users(id),
    FOREIGN KEY(company_id) REFERENCES users(id),
    FOREIGN KEY(job_id) REFERENCES jobs(id)
)
""")

# ================= ADMIN TABLE =================
c.execute("""
CREATE TABLE IF NOT EXISTS admin(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
""")

# default admin
c.execute("INSERT OR IGNORE INTO admin(id,username,password) VALUES(1,'admin','admin')")

conn.commit()
conn.close()

print("🔥 Professional Database Created Successfully")
