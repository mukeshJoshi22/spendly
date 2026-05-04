# Spec: Date Filter For Profile Page

## Overview
Add a date range filter to the profile page so users can narrow their expense
view by selecting a `from_date` and `to_date`. Currently the profile fetches
every expense ever recorded; this step introduces a lightweight query-string
filter (`?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD`) that scopes the transaction
list, summary stats, and category breakdown to only the matching rows. When no
filter is set the page behaves exactly as before — showing all time data.

## Depends on
- Step 1 — Database setup (`get_db`, `expenses` table)
- Step 3 — Login / Logout (session guard on `/profile`)
- Step 4 — Profile Page (the full profile UI already exists and must stay intact)

## Routes
No new routes. The existing route is modified:

- `GET /profile` — now also reads optional `from_date` and `to_date` query
  params; passes them to the DB helper and back to the template — logged-in only

## Database changes
No new tables or columns.

One DB helper is modified in `database/db.py`:

| Function | Change |
|---|---|
| `get_user_expenses(user_id, from_date=None, to_date=None)` | Add two optional keyword args; when provided, append `AND date >= ?` and/or `AND date <= ?` to the existing query using parameterised placeholders |

The default (`from_date=None, to_date=None`) must reproduce the current
behaviour exactly so all existing callers continue to work.

## Templates
- **Modify** `templates/profile.html`:
  - Add a filter form **above** the `stats-row` section
  - The form uses `method="GET"` and `action="{{ url_for('profile') }}"`
  - Two `<input type="date">` fields: `name="from_date"` and `name="to_date"`
  - Both inputs are pre-populated with the current filter values from context
  - A "Filter" submit button
  - A "Clear" link that navigates to `{{ url_for('profile') }}` (no query params)
  - A one-line label showing the active range, e.g. "Showing: May 1 – May 31, 2026"
    or "Showing: All time" when no filter is active

## Files to change
- `database/db.py` — extend `get_user_expenses` with optional date params
- `app.py` — read `from_date` and `to_date` from `request.args`, validate them,
  pass to `get_user_expenses`, and forward the values to the template
- `templates/profile.html` — add the filter form above the stats row
- `static/css/profile.css` — add styles for the filter form (`.filter-bar` block)

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only
- Parameterised queries only — no f-strings in SQL
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Date validation in the route: if either value is non-empty and does not match
  `YYYY-MM-DD` format, silently ignore it (treat as if not provided) — do not
  abort or show an error
- If `from_date > to_date` both are treated as unset (ignore the filter) so the
  user always sees data rather than a confusing empty state
- Stats (`total_spent`, `transaction_count`, `top_category`) must be recalculated
  from the filtered expense list — not from a separate unfiltered query
- The filter form must not break the page when JavaScript is disabled

## Definition of done
- [ ] Visiting `/profile` with no query params shows all expenses (unchanged behaviour)
- [ ] Visiting `/profile?from_date=2026-05-01&to_date=2026-05-15` returns only
      expenses with `date` between 2026-05-01 and 2026-05-15 inclusive
- [ ] Summary stats (total spent, transaction count, top category) reflect only
      the filtered expenses, not the full history
- [ ] Category breakdown reflects only the filtered expenses
- [ ] The filter form appears on the page with two date inputs and a submit button
- [ ] Both date inputs are pre-filled with the active filter values after submission
- [ ] A "Clear" link resets the page to the unfiltered all-time view
- [ ] The active range label says "All time" when no filter is set and shows the
      selected dates when a filter is active
- [ ] Passing an invalid date string (e.g. `?from_date=notadate`) does not crash
      the app — it silently falls back to showing all expenses
- [ ] No hex colour values appear in any new HTML — only CSS variables or classes
- [ ] App starts without errors after these changes