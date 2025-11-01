-- users Page --

CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEX NOT NULL COLLATE NOCASE UNIQUE,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    hash TEXT NOT NULL
);

-- Schedule Page --

CREATE TABLE IF NOT EXISTS schedules(
    user_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Applications Page --

CREATE TABLE IF NOT EXISTS applications(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    company TEXT NOT NULL,
    programme TEXT NOT NULL,
    open_date TEXT,
    close_date TEXT,
    cv TEXT NOT NULL DEFAULT 'Yes' CHECK (cv IN ('Yes','No')),
    cover TEXT NOT NULL DEFAULT 'Optional' CHECK (cover IN ('Yes','No','Optional')),
    written TEXT NOT NULL DEFAULT 'Optional' CHECK (written IN ('Yes','No','Optional')),
    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TRIGGER IF NOT EXISTS trg_applications_touch_updated_at
AFTER UPDATE ON applications
FOR EACH ROW
BEGIN
    UPDATE applications
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE INDEX IF NOT EXISTS idx_applications_user ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_close_date ON applications(close_date);


-- Grade Tracker Page --

CREATE TABLE IF NOT EXISTS modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    term INTEGER NOT NULL,
    credits REAL NOT NULL CHECK (credits > 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    weight_pct REAL NOT NULL CHECK (weight_pct >= 0 AND weight_pct <= 100),
    score_pct REAL CHECK (score_pct >= 0 AND score_pct <= 100),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
);

CREATE TRIGGER IF NOT EXISTS trg_modules_touch_updated
AFTER UPDATE ON modules
FOR EACH ROW
BEGIN
    UPDATE modules
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_assessments_touch_updated
AFTER UPDATE ON assessments
FOR EACH ROW
BEGIN
    UPDATE assessments
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE INDEX IF NOT EXISTS idx_modules_user
    ON modules(user_id);

CREATE INDEX IF NOT EXISTS idx_grade_assess_module
    ON assessments(module_id);
