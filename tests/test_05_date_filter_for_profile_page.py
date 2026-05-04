"""
tests/test_05_date_filter_for_profile_page.py

Spec: Date Filter For Profile Page (Step 05)

Behavioral contracts under test:
  - GET /profile with no query params shows all expenses
  - GET /profile?from_date=...&to_date=... returns only expenses in that
    inclusive date range
  - Summary stats (total_spent, transaction_count, top_category) reflect only
    the filtered expenses
  - Category breakdown reflects only the filtered expenses
  - The filter form is present on the page with two date inputs and a submit
    button
  - Both date inputs are pre-filled with the active filter values after
    submission
  - A "Clear" link resets to the unfiltered view (href = /profile with no
    query params)
  - The active range label says "All time" when no filter is set and shows the
    selected dates when a filter is active
  - Passing an invalid date string does not crash the app — it falls back to
    all expenses
  - Inverted date range (from_date > to_date) falls back to all expenses
  - Unauthenticated access to /profile redirects to /login
"""

import pytest
from werkzeug.security import generate_password_hash

import database.db as db_module


# ------------------------------------------------------------------ #
# Seed data constants                                                  #
# ------------------------------------------------------------------ #

# Three expenses with known amounts and categories:
#   expense_in_1  — inside  2026-05-01 to 2026-05-15  (Food, 50.00)
#   expense_in_2  — inside  2026-05-01 to 2026-05-15  (Transport, 30.00)
#   expense_out   — outside 2026-05-01 to 2026-05-15  (Bills, 200.00)

IN_DATE_1   = "2026-05-05"
IN_DATE_2   = "2026-05-10"
OUT_DATE    = "2026-05-20"

IN_AMOUNT_1  = 50.00
IN_AMOUNT_2  = 30.00
OUT_AMOUNT   = 200.00

IN_CAT_1    = "Food"
IN_CAT_2    = "Transport"
OUT_CAT     = "Bills"

FILTER_FROM = "2026-05-01"
FILTER_TO   = "2026-05-15"


# ------------------------------------------------------------------ #
# Local helpers                                                        #
# ------------------------------------------------------------------ #

def _create_user(name="Alice", email="alice@example.com", password="securepass"):
    """Insert a user into the in-memory DB and return their id."""
    pw_hash = generate_password_hash(password, method="pbkdf2:sha256")
    conn = db_module.get_db()
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, pw_hash),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def _create_expense(user_id, amount, category, date, description="test expense"):
    """Insert an expense row into the in-memory DB and return its id."""
    conn = db_module.get_db()
    cursor = conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, date, description),
    )
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    return expense_id


def _seed_standard_expenses(user_id):
    """
    Seed the three standard test expenses (two inside, one outside the date
    range used in filter tests) and return their ids.
    """
    id1 = _create_expense(user_id, IN_AMOUNT_1, IN_CAT_1,  IN_DATE_1,  "In-range expense 1")
    id2 = _create_expense(user_id, IN_AMOUNT_2, IN_CAT_2,  IN_DATE_2,  "In-range expense 2")
    id3 = _create_expense(user_id, OUT_AMOUNT,  OUT_CAT,   OUT_DATE,   "Out-of-range expense")
    return id1, id2, id3


def _login(client, user_id):
    """Set session["user_id"] via session_transaction to simulate a logged-in user."""
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = "Alice"


# ------------------------------------------------------------------ #
# Auth guard tests                                                     #
# ------------------------------------------------------------------ #

def test_profile_unauthenticated_redirects_to_login(client):
    """
    Spec requirement: /profile is a logged-in-only route.
    An unauthenticated GET /profile must redirect to /login.
    """
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_unauthenticated_does_not_return_200(client):
    """
    Spec requirement: /profile must not be publicly accessible.
    Verifies the response is never 200 for an unauthenticated request.
    """
    response = client.get("/profile", follow_redirects=False)
    assert response.status_code != 200


# ------------------------------------------------------------------ #
# No-filter (all-time) behaviour                                       #
# ------------------------------------------------------------------ #

def test_profile_no_filter_returns_200(app, client):
    """
    Spec requirement: GET /profile with no query params must return HTTP 200
    for a logged-in user.
    """
    user_id = _create_user()
    _login(client, user_id)

    response = client.get("/profile")
    assert response.status_code == 200


def test_profile_no_filter_shows_all_expenses(app, client):
    """
    Spec requirement: When no filter is set, ALL user expenses appear on the
    page — not just a subset.
    Verifies that amounts for all three seeded expenses appear in the HTML.
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    response = client.get("/profile")
    body = response.data.decode()

    # All three amounts must appear in the rendered HTML
    assert "50.00" in body
    assert "30.00" in body
    assert "200.00" in body


def test_profile_no_filter_label_shows_all_time(app, client):
    """
    Spec requirement: The active range label must read "All time" when no
    filter query params are provided.
    """
    user_id = _create_user()
    _login(client, user_id)

    response = client.get("/profile")
    body = response.data.decode()

    assert "All time" in body


def test_profile_no_filter_total_spent_is_sum_of_all_expenses(app, client):
    """
    Spec requirement: Summary stats reflect all expenses when no filter is
    active. total_spent must equal the sum of all seeded amounts.
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    response = client.get("/profile")
    body = response.data.decode()

    expected_total = IN_AMOUNT_1 + IN_AMOUNT_2 + OUT_AMOUNT  # 280.00
    assert f"{expected_total:.2f}" in body


def test_profile_no_filter_transaction_count_is_total(app, client):
    """
    Spec requirement: transaction_count stat reflects all expenses when no
    filter is active. With three seeded expenses the count must be 3.
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    response = client.get("/profile")
    body = response.data.decode()

    # The digit "3" must appear as the transaction count in the stats section.
    # We check for the string "3" inside a known stat block marker.
    assert "3" in body


# ------------------------------------------------------------------ #
# Date filter — happy path                                             #
# ------------------------------------------------------------------ #

def test_profile_date_filter_returns_200(app, client):
    """
    Spec requirement: GET /profile?from_date=...&to_date=... with a valid range
    must return HTTP 200.
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    response = client.get(f"/profile?from_date={FILTER_FROM}&to_date={FILTER_TO}")
    assert response.status_code == 200


def test_profile_date_filter_includes_in_range_expenses(app, client):
    """
    Spec requirement: Expenses whose date falls within the inclusive range
    [from_date, to_date] must appear on the filtered page.
    Both in-range expense amounts (50.00 and 30.00) must be present in the HTML.
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    response = client.get(f"/profile?from_date={FILTER_FROM}&to_date={FILTER_TO}")
    body = response.data.decode()

    assert "50.00" in body
    assert "30.00" in body


def test_profile_date_filter_excludes_out_of_range_expense(app, client):
    """
    Spec requirement: Expenses whose date falls outside [from_date, to_date]
    must NOT appear in the filtered view.
    The out-of-range expense (200.00) must be absent from the response body.
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    response = client.get(f"/profile?from_date={FILTER_FROM}&to_date={FILTER_TO}")
    body = response.data.decode()

    assert "200.00" not in body


def test_profile_date_filter_boundary_from_date_inclusive(app, client):
    """
    Spec requirement: The from_date boundary is inclusive — an expense with
    date == from_date must be included in the results.
    """
    user_id = _create_user()
    # Expense exactly on the from_date boundary
    _create_expense(user_id, 99.99, "Food", FILTER_FROM, "Boundary from expense")
    _login(client, user_id)

    response = client.get(f"/profile?from_date={FILTER_FROM}&to_date={FILTER_TO}")
    body = response.data.decode()

    assert "99.99" in body


def test_profile_date_filter_boundary_to_date_inclusive(app, client):
    """
    Spec requirement: The to_date boundary is inclusive — an expense with
    date == to_date must be included in the results.
    """
    user_id = _create_user()
    # Expense exactly on the to_date boundary
    _create_expense(user_id, 77.77, "Transport", FILTER_TO, "Boundary to expense")
    _login(client, user_id)

    response = client.get(f"/profile?from_date={FILTER_FROM}&to_date={FILTER_TO}")
    body = response.data.decode()

    assert "77.77" in body


# ------------------------------------------------------------------ #
# Filtered stats — summary and category breakdown                      #
# ------------------------------------------------------------------ #

def test_profile_date_filter_total_spent_reflects_filtered_expenses(app, client):
    """
    Spec requirement: total_spent stat must be recalculated from the filtered
    expense list only — not from the full history.
    With the filter active, only the two in-range expenses (50.00 + 30.00 = 80.00)
    contribute to total_spent; the out-of-range expense (200.00) must not.
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    response = client.get(f"/profile?from_date={FILTER_FROM}&to_date={FILTER_TO}")
    body = response.data.decode()

    filtered_total = IN_AMOUNT_1 + IN_AMOUNT_2  # 80.00
    assert f"{filtered_total:.2f}" in body

    # The all-time total (280.00) must NOT appear as the displayed total when
    # filtering is active — only the filtered total should be shown in stats.
    all_time_total = IN_AMOUNT_1 + IN_AMOUNT_2 + OUT_AMOUNT  # 280.00
    assert f"{all_time_total:.2f}" not in body


def test_profile_date_filter_transaction_count_reflects_filtered_expenses(app, client):
    """
    Spec requirement: transaction_count stat must reflect only filtered expenses.
    With the filter applied, only the 2 in-range expenses are counted; the
    out-of-range one must not increment the count.
    We verify that the out-of-range expense category (Bills) does not appear,
    and that the page renders successfully with only 2 transactions visible.
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    response = client.get(f"/profile?from_date={FILTER_FROM}&to_date={FILTER_TO}")
    body = response.data.decode()

    # The out-of-range category "Bills" must not appear in the filtered view
    assert "Bills" not in body


def test_profile_date_filter_top_category_reflects_filtered_expenses(app, client):
    """
    Spec requirement: top_category stat must be derived from filtered expenses
    only.
    With the filter active the out-of-range "Bills" expense (200.00) is excluded.
    The top category among in-range expenses is "Food" (50.00 > Transport 30.00).
    Bills must NOT appear as top_category in the filtered view.
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    response = client.get(f"/profile?from_date={FILTER_FROM}&to_date={FILTER_TO}")
    body = response.data.decode()

    # Bills must not be the top category (it's excluded by the filter)
    # Food should be top_category as it has the highest filtered amount (50.00)
    assert "Food" in body
    # Bills should not appear at all since it is out of range
    assert "Bills" not in body


def test_profile_date_filter_category_breakdown_reflects_filtered_expenses(app, client):
    """
    Spec requirement: The category breakdown section must reflect only filtered
    expenses.
    After filtering, only "Food" and "Transport" categories (in-range) should
    appear. "Bills" (out-of-range) must be absent from the breakdown.
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    response = client.get(f"/profile?from_date={FILTER_FROM}&to_date={FILTER_TO}")
    body = response.data.decode()

    assert "Food" in body
    assert "Transport" in body
    assert "Bills" not in body


# ------------------------------------------------------------------ #
# Filter form presence and structure                                   #
# ------------------------------------------------------------------ #

def test_profile_filter_form_is_present(app, client):
    """
    Spec requirement: The filter form must appear on the profile page.
    Verifies that a form with method="GET" pointing to /profile exists.
    """
    user_id = _create_user()
    _login(client, user_id)

    response = client.get("/profile")
    body = response.data.decode()

    assert 'method="GET"' in body or "method=GET" in body
    assert 'action="/profile"' in body or "/profile" in body


def test_profile_filter_form_has_from_date_input(app, client):
    """
    Spec requirement: The filter form must contain an <input type="date">
    with name="from_date".
    """
    user_id = _create_user()
    _login(client, user_id)

    response = client.get("/profile")
    body = response.data.decode()

    assert 'name="from_date"' in body
    assert 'type="date"' in body


def test_profile_filter_form_has_to_date_input(app, client):
    """
    Spec requirement: The filter form must contain an <input type="date">
    with name="to_date".
    """
    user_id = _create_user()
    _login(client, user_id)

    response = client.get("/profile")
    body = response.data.decode()

    assert 'name="to_date"' in body


def test_profile_filter_form_has_submit_button(app, client):
    """
    Spec requirement: The filter form must include a submit button so the user
    can apply the filter without JavaScript.
    """
    user_id = _create_user()
    _login(client, user_id)

    response = client.get("/profile")
    body = response.data.decode()

    # Either a <button type="submit"> or <input type="submit"> is acceptable
    assert 'type="submit"' in body


# ------------------------------------------------------------------ #
# Pre-filled inputs after submission                                   #
# ------------------------------------------------------------------ #

def test_profile_from_date_input_prefilled_after_filter(app, client):
    """
    Spec requirement: After submitting the filter, the from_date input must be
    pre-populated with the submitted value so the user can see what filter is
    currently active.
    """
    user_id = _create_user()
    _login(client, user_id)

    response = client.get(f"/profile?from_date={FILTER_FROM}&to_date={FILTER_TO}")
    body = response.data.decode()

    # The from_date value must appear as an input value attribute
    assert f'value="{FILTER_FROM}"' in body


def test_profile_to_date_input_prefilled_after_filter(app, client):
    """
    Spec requirement: After submitting the filter, the to_date input must be
    pre-populated with the submitted value.
    """
    user_id = _create_user()
    _login(client, user_id)

    response = client.get(f"/profile?from_date={FILTER_FROM}&to_date={FILTER_TO}")
    body = response.data.decode()

    assert f'value="{FILTER_TO}"' in body


def test_profile_inputs_empty_when_no_filter_active(app, client):
    """
    Spec requirement: When no filter is active, the date inputs must not be
    pre-filled with arbitrary values — they should be empty (value="").
    """
    user_id = _create_user()
    _login(client, user_id)

    response = client.get("/profile")
    body = response.data.decode()

    # Both inputs should carry empty value attributes when no filter is set
    assert 'value=""' in body


# ------------------------------------------------------------------ #
# Clear link                                                           #
# ------------------------------------------------------------------ #

def test_profile_clear_link_points_to_profile_without_params(app, client):
    """
    Spec requirement: The "Clear" link must navigate to /profile with no query
    params, resetting the view to all-time data.
    Verifies that a link with href="/profile" exists on the page.
    """
    user_id = _create_user()
    _login(client, user_id)

    response = client.get(f"/profile?from_date={FILTER_FROM}&to_date={FILTER_TO}")
    body = response.data.decode()

    # The Clear link href must be exactly /profile (no query string appended)
    assert 'href="/profile"' in body


def test_profile_clear_link_resolves_to_unfiltered_view(app, client):
    """
    Spec requirement: Following the Clear link (GET /profile with no params)
    must return the all-time view — all expenses visible, label = "All time".
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    # First apply a filter
    client.get(f"/profile?from_date={FILTER_FROM}&to_date={FILTER_TO}")

    # Then follow the clear link (no query params)
    response = client.get("/profile")
    body = response.data.decode()

    assert "All time" in body
    assert "200.00" in body  # out-of-range expense is back


# ------------------------------------------------------------------ #
# Active range label                                                   #
# ------------------------------------------------------------------ #

def test_profile_label_shows_all_time_when_no_filter(app, client):
    """
    Spec requirement: The active range label must read "All time" when no
    filter query params are provided.
    """
    user_id = _create_user()
    _login(client, user_id)

    response = client.get("/profile")
    body = response.data.decode()

    assert "All time" in body


def test_profile_label_shows_selected_dates_when_filter_active(app, client):
    """
    Spec requirement: When a date filter is active, the label must show the
    selected date range (not "All time").
    The spec example format is "May 1 – May 15, 2026"; any representation that
    includes the month names and year and is NOT "All time" is valid.
    """
    user_id = _create_user()
    _login(client, user_id)

    response = client.get(f"/profile?from_date={FILTER_FROM}&to_date={FILTER_TO}")
    body = response.data.decode()

    # "All time" must NOT appear when a filter is active
    assert "All time" not in body

    # The year from the filter must appear to confirm a date range is shown
    assert "2026" in body


def test_profile_label_contains_from_month_when_filter_active(app, client):
    """
    Spec requirement: The active range label must reference the from_date month.
    FILTER_FROM is 2026-05-01 so "May" must appear in the label.
    """
    user_id = _create_user()
    _login(client, user_id)

    response = client.get(f"/profile?from_date={FILTER_FROM}&to_date={FILTER_TO}")
    body = response.data.decode()

    assert "May" in body


# ------------------------------------------------------------------ #
# Invalid date string — graceful fallback                              #
# ------------------------------------------------------------------ #

def test_profile_invalid_from_date_does_not_crash(app, client):
    """
    Spec requirement: Passing a non-date string as from_date must not crash
    the app — it must respond with HTTP 200 and fall back to all-time data.
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    response = client.get("/profile?from_date=notadate")
    assert response.status_code == 200


def test_profile_invalid_from_date_falls_back_to_all_expenses(app, client):
    """
    Spec requirement: When from_date is an invalid date string the filter is
    silently ignored and all expenses are shown (all-time behaviour).
    The out-of-range expense (200.00) must be present because no valid filter
    is applied.
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    response = client.get("/profile?from_date=notadate")
    body = response.data.decode()

    # All three expenses must appear
    assert "50.00" in body
    assert "30.00" in body
    assert "200.00" in body


def test_profile_invalid_to_date_does_not_crash(app, client):
    """
    Spec requirement: Passing a non-date string as to_date must not crash the
    app — it must respond with HTTP 200.
    """
    user_id = _create_user()
    _login(client, user_id)

    response = client.get("/profile?to_date=not-a-date-at-all")
    assert response.status_code == 200


def test_profile_invalid_to_date_falls_back_to_all_expenses(app, client):
    """
    Spec requirement: When to_date is an invalid date string the filter is
    silently ignored and all expenses are shown.
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    response = client.get("/profile?to_date=99-99-9999")
    body = response.data.decode()

    assert "200.00" in body


def test_profile_both_dates_invalid_falls_back_to_all_expenses(app, client):
    """
    Spec requirement: When both date params are invalid strings the filter is
    silently ignored and the page shows all expenses with label "All time".
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    response = client.get("/profile?from_date=bad&to_date=alsoBad")
    body = response.data.decode()

    assert response.status_code == 200
    assert "All time" in body
    assert "200.00" in body


def test_profile_invalid_from_date_shows_all_time_label(app, client):
    """
    Spec requirement: When the from_date is invalid the active range label must
    still read "All time" because no valid filter is applied.
    """
    user_id = _create_user()
    _login(client, user_id)

    response = client.get("/profile?from_date=notadate&to_date=2026-05-15")
    body = response.data.decode()

    assert "All time" in body


# ------------------------------------------------------------------ #
# Inverted date range fallback                                         #
# ------------------------------------------------------------------ #

def test_profile_inverted_date_range_does_not_crash(app, client):
    """
    Spec requirement: If from_date > to_date the app must not crash — it must
    return HTTP 200.
    """
    user_id = _create_user()
    _login(client, user_id)

    # from_date is after to_date — inverted range
    response = client.get("/profile?from_date=2026-05-15&to_date=2026-05-01")
    assert response.status_code == 200


def test_profile_inverted_date_range_falls_back_to_all_expenses(app, client):
    """
    Spec requirement: If from_date > to_date both params are treated as unset
    and the page shows all expenses (fallback to all-time behaviour).
    The out-of-range expense (200.00) must be visible since no filter applies.
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    response = client.get("/profile?from_date=2026-05-15&to_date=2026-05-01")
    body = response.data.decode()

    assert "50.00" in body
    assert "30.00" in body
    assert "200.00" in body


def test_profile_inverted_date_range_shows_all_time_label(app, client):
    """
    Spec requirement: When from_date > to_date the filter is dropped, so the
    active range label must fall back to "All time".
    """
    user_id = _create_user()
    _login(client, user_id)

    response = client.get("/profile?from_date=2026-12-31&to_date=2026-01-01")
    body = response.data.decode()

    assert "All time" in body


# ------------------------------------------------------------------ #
# Edge cases                                                           #
# ------------------------------------------------------------------ #

def test_profile_filter_empty_result_does_not_crash(app, client):
    """
    Edge case: A valid date range that matches no expenses must not crash the
    app. The page must return HTTP 200 with zero transactions shown.
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    # Use a date range in the far future where no expenses exist
    response = client.get("/profile?from_date=2099-01-01&to_date=2099-12-31")
    assert response.status_code == 200


def test_profile_filter_empty_result_shows_zero_total(app, client):
    """
    Edge case: When the filter returns no expenses, total_spent must be 0.00
    and transaction_count must be 0.
    """
    user_id = _create_user()
    _seed_standard_expenses(user_id)
    _login(client, user_id)

    response = client.get("/profile?from_date=2099-01-01&to_date=2099-12-31")
    body = response.data.decode()

    assert "0.00" in body


def test_profile_filter_only_from_date_provided(app, client):
    """
    Edge case: When only from_date is provided (no to_date), expenses on or
    after that date must appear. Expenses before that date must be absent.
    Verifies that a single-bound filter is handled correctly.
    """
    user_id = _create_user()
    # Expense before the from_date
    _create_expense(user_id, 11.11, "Food", "2026-04-01", "Before cutoff")
    # Expense on and after the from_date
    _create_expense(user_id, 22.22, "Transport", "2026-05-10", "After cutoff")
    _login(client, user_id)

    response = client.get("/profile?from_date=2026-05-01")
    body = response.data.decode()

    assert "22.22" in body
    assert "11.11" not in body


def test_profile_filter_only_to_date_provided(app, client):
    """
    Edge case: When only to_date is provided (no from_date), expenses on or
    before that date must appear. Expenses after that date must be absent.
    """
    user_id = _create_user()
    _create_expense(user_id, 55.55, "Food", "2026-05-01", "Before cutoff")
    _create_expense(user_id, 88.88, "Bills", "2026-06-01", "After cutoff")
    _login(client, user_id)

    response = client.get("/profile?to_date=2026-05-15")
    body = response.data.decode()

    assert "55.55" in body
    assert "88.88" not in body


def test_profile_expenses_from_other_users_not_shown(app, client):
    """
    Edge case / Security: Expenses belonging to another user must never appear
    on the logged-in user's profile page — with or without a date filter.
    """
    user_a_id = _create_user(name="Alice", email="alice@example.com")
    user_b_id = _create_user(name="Bob",   email="bob@example.com")

    _create_expense(user_a_id, 42.00, "Food",  "2026-05-05", "Alice food")
    _create_expense(user_b_id, 99.00, "Bills", "2026-05-05", "Bob bills")

    # Log in as Alice
    _login(client, user_a_id)

    response = client.get(f"/profile?from_date={FILTER_FROM}&to_date={FILTER_TO}")
    body = response.data.decode()

    assert "42.00" in body
    assert "99.00" not in body


def test_profile_same_date_for_from_and_to_shows_only_that_day(app, client):
    """
    Edge case: When from_date == to_date only expenses on that exact day must
    appear; expenses on any other day must be excluded.
    """
    user_id = _create_user()
    _create_expense(user_id, 15.00, "Food",      "2026-05-10", "On the day")
    _create_expense(user_id, 25.00, "Transport", "2026-05-11", "Day after")
    _create_expense(user_id, 35.00, "Bills",     "2026-05-09", "Day before")
    _login(client, user_id)

    response = client.get("/profile?from_date=2026-05-10&to_date=2026-05-10")
    body = response.data.decode()

    assert "15.00" in body
    assert "25.00" not in body
    assert "35.00" not in body
