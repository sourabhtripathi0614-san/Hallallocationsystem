
import os
import sqlite3
from datetime import date
from functools import wraps

from flask import (
    Flask,
    render_template_string,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from database import (
    initialize_database,
    get_connection,
    get_all_halls,
)


app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "local-development-key-change-before-deployment",
)

initialize_database()

OPENING_TIME = "09:00"
CLOSING_TIME = "17:00"

TIME_OPTIONS = [
    f"{hour:02d}:00"
    for hour in range(9, 18)
]


AUTH_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ title }} - Hall Allocation System</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: #f3f5f9;
            padding: 35px 15px;
            color: #1f2937;
        }
        main {
            max-width: 430px;
            margin: auto;
            background: white;
            padding: 28px;
            border-radius: 12px;
            box-shadow: 0 4px 18px #00000010;
        }
        h1 { color: #1d4ed8; }
        label {
            display: block;
            margin-top: 15px;
            font-weight: bold;
        }
        input {
            width: 100%;
            box-sizing: border-box;
            padding: 11px;
            margin-top: 6px;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
        }
        button {
            width: 100%;
            margin-top: 22px;
            padding: 12px;
            border: 0;
            border-radius: 6px;
            background: #1d4ed8;
            color: white;
            cursor: pointer;
        }
        .message {
            padding: 10px;
            background: #eff6ff;
            border-radius: 6px;
        }
        a { color: #1d4ed8; }
    </style>
</head>
<body>
<main>
    <h1>{{ title }}</h1>

    {% for message in get_flashed_messages() %}
        <p class="message">{{ message }}</p>
    {% endfor %}

    {% if mode == "register" %}
        <form method="POST" action="{{ url_for('register') }}">
            <label for="full_name">Full name</label>
            <input id="full_name" name="full_name"
                   required maxlength="100" autocomplete="name">

            <label for="email">Email address</label>
            <input id="email" name="email" type="email"
                   required maxlength="254" autocomplete="email">

            <label for="password">Password (minimum 12 characters)</label>
            <input id="password" name="password" type="password"
                   required minlength="12" maxlength="128"
                   autocomplete="new-password">

            <button type="submit">Create account</button>
        </form>
        <p>Already registered? <a href="{{ url_for('login') }}">Log in</a></p>
    {% else %}
        <form method="POST" action="{{ url_for('login') }}">
            <label for="email">Email address</label>
            <input id="email" name="email" type="email"
                   required autocomplete="email">

            <label for="password">Password</label>
            <input id="password" name="password" type="password"
                   required autocomplete="current-password">

            <button type="submit">Log in</button>
        </form>
        <p>New user? <a href="{{ url_for('register') }}">Create an account</a></p>
    {% endif %}

    <p><a href="{{ url_for('home') }}">Back to home</a></p>
</main>
</body>
</html>
"""


HOME_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Hall Allocation System</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: #f3f5f9;
            padding: 30px 15px;
            color: #1f2937;
        }
        main {
            max-width: 900px;
            margin: auto;
            background: white;
            padding: 28px;
            border-radius: 12px;
        }
        .hall-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 16px;
            margin-top: 20px;
        }
        .hall {
            padding: 18px;
            background: #eff6ff;
            border: 1px solid #dbeafe;
            border-radius: 10px;
        }
        .hall h3 { margin-top: 0; }
        .hall p { line-height: 1.5; min-height: 48px; }
        a { color: #1d4ed8; }
        .button, button {
            display: inline-block;
            padding: 10px 15px;
            border: 0;
            border-radius: 6px;
            background: #1d4ed8;
            color: white;
            text-decoration: none;
            cursor: pointer;
        }
        button.logout { background: #dc2626; }
        .top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
        }
        .top-bar form { margin: 0; }
        .links {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin: 20px 0;
        }
        .message {
            padding: 10px;
            background: #eff6ff;
            border-radius: 6px;
        }
        @media (max-width: 700px) {
            .hall-grid { grid-template-columns: 1fr; }
            .hall p { min-height: auto; }
        }
    </style>
</head>
<body>
<main>
    <div class="top-bar">
        <h1>Hall Allocation System</h1>

        {% if user %}
            <form method="POST" action="{{ url_for('logout') }}">
                <button class="logout" type="submit">Log out</button>
            </form>
        {% endif %}
    </div>

    {% for message in get_flashed_messages() %}
        <p class="message">{{ message }}</p>
    {% endfor %}

    {% if user %}
        <p>Welcome, {{ user.full_name }}!</p>
        <p>Your account role: {{ user.role }}</p>

        <div class="links">
            <a class="button" href="{{ url_for('my_bookings') }}">
                My Bookings
            </a>
            {% if user.role == "admin" %}
                <a class="button" href="{{ url_for('admin_dashboard') }}">
                    Admin Dashboard
                </a>
            {% endif %}
        </div>
    {% else %}
        <p>Please log in or register to request a hall.</p>
        <p>
            <a href="{{ url_for('login') }}">Log in</a> |
            <a href="{{ url_for('register') }}">Register</a>
        </p>
    {% endif %}

    <h2>Choose a hall to check availability</h2>
    <p>Select a hall to view its schedule for a specific date.</p>

    <div class="hall-grid">
        {% for hall in halls %}
            <section class="hall">
                <h3>{{ hall.name }}</h3>
                <p>{{ hall.description }}</p>

                {% if user %}
                    <a class="button"
                       href="{{ url_for('hall_schedule', hall_id=hall.id) }}">
                        View available times
                    </a>
                {% else %}
                    <a class="button" href="{{ url_for('login') }}">
                        Log in to view times
                    </a>
                {% endif %}
            </section>
        {% endfor %}
    </div>
</main>
</body>
</html>
"""


def get_current_user():
    """Return the active logged-in user's details."""

    user_id = session.get("user_id")

    if user_id is None:
        return None

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, full_name, email, role
            FROM users
            WHERE id = ? AND is_active = 1
            """,
            (user_id,),
        ).fetchone()

    return dict(row) if row else None


def login_required(view_function):
    """Protect a route from unauthenticated access."""

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        user = get_current_user()

        if user is None:
            session.clear()
            flash("Please log in to continue.")
            return redirect(url_for("login"))

        return view_function(*args, **kwargs)

    return wrapped_view


def render_booking_form(user, form_data=None, status=200):
    """Render the booking form and preserve entered values."""

    return render_template(
        "book.html",
        user=user,
        halls=get_all_halls(),
        today=date.today().isoformat(),
        time_options=TIME_OPTIONS,
        form_data=form_data or {},
    ), status


@app.route("/")
def home():
    user = get_current_user()

    if session.get("user_id") is not None and user is None:
        session.clear()

    return render_template_string(
        HOME_PAGE,
        user=user,
        halls=get_all_halls(),
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if get_current_user():
        return redirect(url_for("home"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not full_name or len(full_name) > 100:
            flash("Enter a name of at most 100 characters.")
            return redirect(url_for("register"))

        if (
            not email
            or len(email) > 254
            or "@" not in email
            or email.startswith("@")
            or email.endswith("@")
        ):
            flash("Enter a valid email address.")
            return redirect(url_for("register"))

        if len(password) < 12 or len(password) > 128:
            flash("Password must contain 12 to 128 characters.")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        try:
            with get_connection() as connection:
                connection.execute(
                    """
                    INSERT INTO users
                        (full_name, email, password_hash, role)
                    VALUES (?, ?, ?, 'user')
                    """,
                    (full_name, email, password_hash),
                )
        except sqlite3.IntegrityError:
            flash("That email may already be registered.")
            return redirect(url_for("register"))

        flash("Registration successful. Please log in.")
        return redirect(url_for("login"))

    return render_template_string(
        AUTH_PAGE,
        title="Create your account",
        mode="register",
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if get_current_user():
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with get_connection() as connection:
            user = connection.execute(
                """
                SELECT id, password_hash, is_active
                FROM users
                WHERE email = ?
                """,
                (email,),
            ).fetchone()

        if (
            user is None
            or not user["is_active"]
            or not check_password_hash(user["password_hash"], password)
        ):
            flash("Invalid email or password.")
            return redirect(url_for("login"))

        session.clear()
        session["user_id"] = user["id"]

        return redirect(url_for("home"))

    return render_template_string(
        AUTH_PAGE,
        title="Log in",
        mode="login",
    )


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have logged out successfully.")
    return redirect(url_for("login"))


@app.route("/halls/<int:hall_id>/schedule")
@login_required
def hall_schedule(hall_id):
    """Display one hall's hourly status for the selected date."""

    user = get_current_user()

    try:
        selected_date = date.fromisoformat(
            request.args.get("date", date.today().isoformat())
        )
    except ValueError:
        flash("Please select a valid date.")
        return redirect(url_for("home"))

    if selected_date < date.today():
        flash("Past dates cannot be booked.")
        return redirect(url_for("home"))

    with get_connection() as connection:
        hall_row = connection.execute(
            """
            SELECT id, name, description
            FROM halls
            WHERE id = ? AND is_active = 1
            """,
            (hall_id,),
        ).fetchone()

        if hall_row is None:
            flash("The selected hall could not be found.")
            return redirect(url_for("home"))

        # Approved and cancellation-pending bookings still occupy
        # their time until cancellation is approved.
        confirmed_rows = connection.execute(
            """
            SELECT start_time, end_time
            FROM booking_requests
            WHERE hall_id = ?
              AND booking_date = ?
              AND status IN ('approved', 'cancellation_pending')
            """,
            (hall_id, selected_date.isoformat()),
        ).fetchall()

        pending_rows = connection.execute(
            """
            SELECT start_time, end_time
            FROM booking_requests
            WHERE hall_id = ?
              AND booking_date = ?
              AND status = 'pending'
            """,
            (hall_id, selected_date.isoformat()),
        ).fetchall()

    confirmed = [dict(row) for row in confirmed_rows]
    pending = [dict(row) for row in pending_rows]

    slots = []

    if selected_date.weekday() != 6:
        for hour in range(9, 17):
            start = f"{hour:02d}:00"
            end = f"{hour + 1:02d}:00"

            has_confirmed = any(
                booking["start_time"] < end
                and booking["end_time"] > start
                for booking in confirmed
            )

            has_pending = any(
                booking["start_time"] < end
                and booking["end_time"] > start
                for booking in pending
            )

            if has_confirmed:
                status = "booked"
            elif has_pending:
                status = "pending"
            else:
                status = "available"

            slots.append({
                "start": start,
                "end": end,
                "start_label": (
                    f"{hour % 12 or 12}:00 "
                    f"{'AM' if hour < 12 else 'PM'}"
                ),
                "end_label": (
                    f"{(hour + 1) % 12 or 12}:00 "
                    f"{'AM' if hour + 1 < 12 else 'PM'}"
                ),
                "status": status,
            })

    return render_template(
        "hall_schedule.html",
        user=user,
        hall=dict(hall_row),
        selected_date=selected_date.isoformat(),
        today=date.today().isoformat(),
        is_sunday=selected_date.weekday() == 6,
        slots=slots,
    )


@app.route("/book", methods=["GET", "POST"])
@login_required
def book():
    user = get_current_user()

    if request.method == "GET":
        # Prefill the hall and date selected on the schedule page.
        form_data = {
            "hall_id": request.args.get("hall_id", ""),
            "booking_date": request.args.get("booking_date", ""),
            "applicant_name": user["full_name"],
        }
        return render_booking_form(user, form_data)

    form_data = {
        key: request.form.get(key, "").strip()
        for key in [
            "applicant_name",
            "department",
            "contact_number",
            "hall_id",
            "event_name",
            "purpose",
            "attendee_count",
            "booking_date",
            "start_time",
            "end_time",
            "special_requirements",
        ]
    }

    applicant_name = form_data["applicant_name"]
    department = form_data["department"]
    contact_number = form_data["contact_number"]
    event_name = form_data["event_name"]
    purpose = form_data["purpose"]
    special_requirements = form_data["special_requirements"]

    if not applicant_name or len(applicant_name) > 100:
        flash("Enter an applicant name of at most 100 characters.")
        return render_booking_form(user, form_data, 400)

    if not department or len(department) > 100:
        flash("Enter a department of at most 100 characters.")
        return render_booking_form(user, form_data, 400)

    if not contact_number or len(contact_number) > 20:
        flash("Enter a valid contact number.")
        return render_booking_form(user, form_data, 400)

    if not event_name or len(event_name) > 150:
        flash("Enter an event name of at most 150 characters.")
        return render_booking_form(user, form_data, 400)

    if not purpose or len(purpose) > 2000:
        flash("Enter a purpose of at most 2000 characters.")
        return render_booking_form(user, form_data, 400)

    if len(special_requirements) > 2000:
        flash("Special requirements must be at most 2000 characters.")
        return render_booking_form(user, form_data, 400)

    try:
        hall_id = int(form_data["hall_id"])
        attendee_count = int(form_data["attendee_count"])
    except (ValueError, TypeError):
        flash("Choose a valid hall and attendee count.")
        return render_booking_form(user, form_data, 400)

    if attendee_count < 1 or attendee_count > 10000:
        flash("Attendee count must be between 1 and 10000.")
        return render_booking_form(user, form_data, 400)

    try:
        booking_date = date.fromisoformat(form_data["booking_date"])
    except ValueError:
        flash("Choose a valid booking date.")
        return render_booking_form(user, form_data, 400)

    if booking_date < date.today():
        flash("Past dates cannot be booked.")
        return render_booking_form(user, form_data, 400)

    if booking_date.weekday() == 6:
        flash("Sunday bookings are not allowed.")
        return render_booking_form(user, form_data, 400)

    start_time = form_data["start_time"]
    end_time = form_data["end_time"]

    if start_time not in TIME_OPTIONS or end_time not in TIME_OPTIONS:
        flash("Choose times between 9 AM and 5 PM.")
        return render_booking_form(user, form_data, 400)

    if start_time >= end_time:
        flash("End time must be later than start time.")
        return render_booking_form(user, form_data, 400)

    try:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")

            hall = connection.execute(
                """
                SELECT id
                FROM halls
                WHERE id = ? AND is_active = 1
                """,
                (hall_id,),
            ).fetchone()

            if hall is None:
                flash("That hall is not available for booking.")
                return render_booking_form(user, form_data, 400)

            # Prevent overlapping requests as well as overlapping confirmed
            # bookings. Pending requests temporarily reserve their time so
            # two users cannot submit conflicting requests and later have
            # both approved.
            conflict = connection.execute(
                """
                SELECT id, status
                FROM booking_requests
                WHERE hall_id = ?
                  AND booking_date = ?
                  AND status IN (
                      'pending',
                      'approved',
                      'cancellation_pending'
                  )
                  AND start_time < ?
                  AND end_time > ?
                LIMIT 1
                """,
                (
                    hall_id,
                    booking_date.isoformat(),
                    end_time,
                    start_time,
                ),
            ).fetchone()

            if conflict:
                if conflict["status"] == "pending":
                    flash(
                        "A request for this hall and time is already pending. "
                        "Please choose another time or hall."
                    )
                else:
                    flash(
                        "This hall already has a confirmed booking during "
                        "that time. Choose another period or hall."
                    )
                return render_booking_form(user, form_data, 400)

            connection.execute(
                """
                INSERT INTO booking_requests (
                    user_id,
                    hall_id,
                    applicant_name,
                    department,
                    contact_number,
                    event_name,
                    purpose,
                    attendee_count,
                    special_requirements,
                    booking_date,
                    start_time,
                    end_time,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                """,
                (
                    user["id"],
                    hall_id,
                    applicant_name,
                    department,
                    contact_number,
                    event_name,
                    purpose,
                    attendee_count,
                    special_requirements,
                    booking_date.isoformat(),
                    start_time,
                    end_time,
                ),
            )

    except sqlite3.Error:
        app.logger.exception("Unable to save a booking request.")
        flash("The request could not be saved because of a database error.")
        return render_booking_form(user, form_data, 500)

    flash("Booking request submitted. It is pending administrator approval.")
    return redirect(url_for("my_bookings"))


@app.route("/my-bookings")
@login_required
def my_bookings():
    user = get_current_user()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                br.id,
                br.event_name,
                h.name AS hall_name,
                br.booking_date,
                br.start_time,
                br.end_time,
                br.status,
                br.admin_decision_reason,
                br.created_at
            FROM booking_requests AS br
            JOIN halls AS h ON h.id = br.hall_id
            WHERE br.user_id = ?
            ORDER BY br.created_at DESC, br.id DESC
            """,
            (user["id"],),
        ).fetchall()

    return render_template(
        "my_bookings.html",
        bookings=[dict(row) for row in rows],
    )


def require_admin():
    """Return the current user only when the user has administrator access."""
    user = get_current_user()
    if user is None:
        session.clear()
        flash("Please log in to continue.")
        return None, redirect(url_for("login"))
    if user["role"] != "admin":
        flash("You do not have permission to access the administrator dashboard.")
        return None, redirect(url_for("home"))
    return user, None


@app.route("/admin")
@login_required
def admin_dashboard():
    """Show booking request totals and allow administrators to review requests."""
    user, denial_response = require_admin()
    if denial_response is not None:
        return denial_response

    with get_connection() as connection:
        counts_row = connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) AS approved,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) AS rejected,
                SUM(CASE WHEN status = 'cancellation_pending' THEN 1 ELSE 0 END)
                    AS cancellation_pending,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled
            FROM booking_requests
            """
        ).fetchone()

        request_rows = connection.execute(
            """
            SELECT
                br.id,
                br.user_id,
                br.applicant_name,
                br.department,
                br.contact_number,
                br.event_name,
                br.purpose,
                br.attendee_count,
                br.special_requirements,
                br.booking_date,
                br.start_time,
                br.end_time,
                br.status,
                br.admin_decision_reason,
                br.created_at,
                h.name AS hall_name,
                u.email AS account_email
            FROM booking_requests AS br
            JOIN halls AS h ON h.id = br.hall_id
            LEFT JOIN users AS u ON u.id = br.user_id
            ORDER BY
                CASE br.status
                    WHEN 'pending' THEN 0
                    WHEN 'cancellation_pending' THEN 1
                    ELSE 2
                END,
                br.booking_date ASC,
                br.start_time ASC,
                br.created_at DESC,
                br.id DESC
            """
        ).fetchall()

    counts = {
        key: (counts_row[key] or 0)
        for key in (
            "total", "pending", "approved", "rejected",
            "cancellation_pending", "cancelled"
        )
    }
    return render_template(
        "admin_dashboard.html",
        user=user,
        counts=counts,
        booking_requests=[dict(row) for row in request_rows],
    )


@app.route("/admin/requests/<int:request_id>/decision", methods=["POST"])
@login_required
def admin_decide_request(request_id):
    """Approve or reject a pending request, checking conflicts at approval time."""
    user, denial_response = require_admin()
    if denial_response is not None:
        return denial_response

    decision = request.form.get("decision", "").strip().lower()
    reason = request.form.get("reason", "").strip()

    if decision not in {"approved", "rejected"}:
        flash("Choose either approve or reject.")
        return redirect(url_for("admin_dashboard"))

    if len(reason) > 2000:
        flash("The decision reason must be 2000 characters or fewer.")
        return redirect(url_for("admin_dashboard"))

    try:
        with get_connection() as connection:
            # Lock writes while we re-check status and availability, so two
            # administrators cannot approve overlapping requests simultaneously.
            connection.execute("BEGIN IMMEDIATE")

            booking = connection.execute(
                """
                SELECT id, hall_id, booking_date, start_time, end_time, status
                FROM booking_requests
                WHERE id = ?
                """,
                (request_id,),
            ).fetchone()

            if booking is None:
                flash("Booking request not found.")
                return redirect(url_for("admin_dashboard"))

            if booking["status"] != "pending":
                flash("This request is no longer pending and cannot be decided again.")
                return redirect(url_for("admin_dashboard"))

            if decision == "approved":
                conflict = connection.execute(
                    """
                    SELECT id
                    FROM booking_requests
                    WHERE hall_id = ?
                      AND booking_date = ?
                      AND id != ?
                      AND status IN ('approved', 'cancellation_pending')
                      AND start_time < ?
                      AND end_time > ?
                    LIMIT 1
                    """,
                    (
                        booking["hall_id"],
                        booking["booking_date"],
                        request_id,
                        booking["end_time"],
                        booking["start_time"],
                    ),
                ).fetchone()

                if conflict:
                    flash(
                        "Cannot approve this request: its time overlaps an "
                        "already confirmed booking. Reject this request or resolve "
                        "the conflicting booking first."
                    )
                    return redirect(url_for("admin_dashboard"))

            connection.execute(
                """
                UPDATE booking_requests
                SET status = ?,
                    admin_decision_reason = ?,
                    decided_by = ?,
                    decided_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'pending'
                """,
                (decision, reason, user["id"], request_id),
            )

    except sqlite3.Error:
        app.logger.exception("Unable to process administrator decision.")
        flash("The decision could not be saved because of a database error.")
        return redirect(url_for("admin_dashboard"))

    flash(
        "Booking request approved successfully."
        if decision == "approved"
        else "Booking request rejected."
    )
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
