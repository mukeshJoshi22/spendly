# Spec: Registration

## Overview
Implement user registration so new visitors can create a Spendly account.
The `GET /register` route and `register.html` template already exist; this step
wires up the `POST /register` handler, adds two DB helpers, and establishes
Flask session support so a newly registered user is immediately signed in.
After registration the user is redirected to the landing page (dashboard is a
future step).

## Depends on
- Step 1 — Database setup (`get_db`, `init_db`, `seed_db`, `users` table).

## Routes
- `POST /register` — validate form data, create user, set session, redirect — public

## Database changes
No new tables or columns.

Two new helper functions in `database/db.py`:

| Function | Signature | Purpose |
|---|---|---|
| `get_user_by_email` | `(email: str) → Row \| None` | Look up a user by email; returns `None` if not found |
| `create_user` | `(name: str, email: str, password_hash: str) → int` | Insert a new user row; returns the new `id` |

## Templates
- **Modify** `templates/register.html` — replace hardcoded `action="/register"` with `action="{{ url_for('register') }}"`.  The `{{ error }}` block and all input fields are already correct.

## Files to change
- `app.py` — add `secret_key`, import `request / session / redirect` from Flask, add `POST /register` route
- `database/db.py` — add `get_user_by_email()` and `create_user()`
- `templates/register.html` — fix hardcoded action URL

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security` is already installed.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only
- Parameterised queries only — no f-strings in SQL
- Hash passwords with `werkzeug.security.generate_password_hash` (method `pbkdf2:sha256`)
- `app.secret_key` must be read from `os.environ.get("SECRET_KEY", "dev-secret-key")` — never hardcode a production secret
- Use `abort()` for unexpected HTTP errors — not bare string returns
- Use CSS variables in any new styles — never hardcode hex values
- All templates extend `base.html`
- After successful registration set `session["user_id"]` and `session["user_name"]`, then `redirect(url_for("landing"))`
- On validation failure, **re-render** `register.html` passing `error=<message>` — do not redirect

## Validation rules (POST /register)
1. `name`, `email`, `password` fields must all be non-empty → error: `"All fields are required."`
2. `password` must be at least 8 characters → error: `"Password must be at least 8 characters."`
3. Email must not already exist in `users` table → error: `"An account with that email already exists."`

## Definition of done
- [ ] Submitting the form with all valid data creates a new row in `users` with a hashed password
- [ ] Browser is redirected to the landing page (`/`) after successful registration
- [ ] `session["user_id"]` and `session["user_name"]` are set after registration
- [ ] Submitting with an empty field re-renders `register.html` with the error message "All fields are required."
- [ ] Submitting a password shorter than 8 characters re-renders with "Password must be at least 8 characters."
- [ ] Submitting a duplicate email re-renders with "An account with that email already exists."
- [ ] Raw password is never stored — `password_hash` column contains a werkzeug hash string
- [ ] `action` attribute in `register.html` uses `url_for('register')` — no hardcoded URLs
- [ ] App starts without errors after these changes