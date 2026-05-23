# DevTrack — Engineering Issue Tracker API

A minimal Django REST backend for tracking engineering bugs and tasks.  
Data is persisted in flat JSON files (`reporters.json`, `issues.json`).

---

## How to Run

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd devtrack

# 2. Install dependencies
pip install django

# 3. Reset data files (first time)
echo "[]" > reporters.json
echo "[]" > issues.json

# 4. Start the server
python manage.py runserver
```

Server runs at `http://127.0.0.1:8000`

---

## Endpoints

### Reporter Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `POST` | `/api/reporters/` | Create a new reporter |
| `GET` | `/api/reporters/` | Get all reporters |
| `GET` | `/api/reporters/?id=1` | Get a single reporter by ID |

**POST /api/reporters/ — example body**
```json
{
  "id": 1,
  "name": "Thahaseen",
  "email": "tasee@example.com",
  "team": "backend"
}
```

---

### Issue Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `POST` | `/api/issues/` | Create a new issue |
| `GET` | `/api/issues/` | Get all issues |
| `GET` | `/api/issues/?id=1` | Get a single issue by ID |
| `GET` | `/api/issues/?status=open` | Filter issues by status |

**POST /api/issues/ — example body**
```json
{
  "id": 1,
  "title": "Login button not working on mobile",
  "description": "Users on iOS 17 cannot tap the login button",
  "status": "open",
  "priority": "critical",
  "reporter_id": 1
}
```

**201 Created response (critical priority)**
```json
{
  "id": 1,
  "title": "Login button not working on mobile",
  "description": "Users on iOS 17 cannot tap the login button",
  "status": "open",
  "priority": "critical",
  "reporter_id": 1,
  "created_at": "2026-05-23 10:00:00.000000",
  "message": "[URGENT] Login button not working on mobile — needs immediate attention"
}
```

**400 Bad Request (validation failure)**
```json
{ "error": "Title cannot be empty" }
```

**404 Not Found**
```json
{ "error": "Issue not found" }
```

Valid values:
- `status`: `open`, `in_progress`, `resolved`, `closed`
- `priority`: `low`, `medium`, `high`, `critical`

---

## Design Decision

**Why flat JSON files instead of SQLite/a real DB?**

The brief required storing data without running Django migrations or setting up models as database tables. Using `reporters.json` and `issues.json` keeps the project dependency-free (no `db.sqlite3` setup needed), makes the stored data human-readable and easy to inspect during development, and lets the OOP classes in `models.py` stay pure Python — they are not Django ORM models. The trade-off is no concurrent-write safety, but that's acceptable for a learning project of this scope.

---

## OOP Design

- `BaseEntity` (abstract) — defines `validate()` and `to_dict()`
- `Reporter(BaseEntity)` — validates name, email, team
- `Issue(BaseEntity)` — validates title, status, priority; has `describe()`
- `CriticalIssue(Issue)` — overrides `describe()` with `[URGENT]` prefix
- `LowPriorityIssue(Issue)` — overrides `describe()` with low-priority note
