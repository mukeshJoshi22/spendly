# Spec: Login and Logout

## Overview
Implement login and logout so registered users can authenticate and end their
session. `GET /login` and `login.html` already exist as shells; this step wires
up `POST /login` (validates credentials, sets session, redirects) and converts
the `GET /logout` stub into a working route that clears the session. The navbar
in `base.html` is also updated to reflect whether the user is signed in,
showing a greeting and logout link when a session is active.

## Depends on
- Step 1 — Database setup (`get_db`, `users` table, `get_user_by_email`)
- Step 2 — Registration (`session["user_id"]`, `session["user_name"]` contract established)

## Routes
- `POST /login` — validate credentials, set session, redirect to landing — public
- `GET /logout` — clear session, redirect to landing — logged-in (no hard guard needed; safe to call unauthenticated)

## Database changes
No new tables or columns. No new DB helper functions needed — `get_user_by_email` from Step 2 covers the lookup.

## Templates
- **Modify** `templates/login.html`:
  - Replace hardcoded `action="/login"` with `action="{{ url_for('login') }}"`
  - Add `value="{{ email or '' }}"` to the email input so it is retained on validation failure
- **Modify** `templates/base.html`:
  - Replace the static nav links with a conditional block:
    - If `session.user_id` is set: show the user's name and a "Sign out" link to `url_for('logout')`
    - Otherwise: show the existing "Sign in" and "Get started" links

## Files to change
- `app.py` — import `check_password_hash`, add `POST` to the login route, implement logout
- `database/db.py` — no changes
- `templates/login.html` — fix hardcoded action URL, retain email on error
- `templates/base.html` — dynamic nav based on session state

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security.check_password_hash` is already installed.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only
- Parameterised queries only — no f-strings in SQL
- Verify passwords with `werkzeug.security.check_password_hash` — never compare plain text
- Use CSS variables — never hardcode hex values in any new styles
- All templates extend `base.html`
- On successful login: set `session["user_id"]` and `session["user_name"]`, then `redirect(url_for("landing"))`
- On failed login: re-render `login.html` with `error=<message>` and `email=email` — do not redirect
- Logout must call `session.clear()` then `redirect(url_for("landing"))` — do not use `session.pop` for individual keys

## Validation rules (POST /login)
1. `email` and `password` fields must both be non-empty → error: `"All fields are required."`
2. No user found for that email → error: `"Invalid email or password."`
3. Password does not match stored hash → error: `"Invalid email or password."`

Note: errors 2 and 3 use the same message intentionally — never reveal whether the email exists.

## Definition of done
- [ ] Submitting valid credentials sets `session["user_id"]` and `session["user_name"]` and redirects to `/`
- [ ] Navbar shows the user's name and a "Sign out" link when logged in
- [ ] Navbar shows "Sign in" and "Get started" links when not logged in
- [ ] Visiting `/logout` clears the session and redirects to `/`
- [ ] Submitting empty fields re-renders `login.html` with "All fields are required."
- [ ] Submitting a non-existent email re-renders with "Invalid email or password."
- [ ] Submitting a wrong password re-renders with "Invalid email or password."
- [ ] Email field retains its value on validation failure
- [ ] `action` attribute in `login.html` uses `url_for('login')` — no hardcoded URLs
- [ ] App starts without errors after these changes