CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEX NOT NULL COLLATE NOCASE UNIQUE,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schedules(
    user_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

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
