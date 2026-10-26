
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent / "hall_booking.db"


def get_connection():
    """Create a database connection with foreign-key checks enabled."""
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    """Create the tables required by the hall allocation system."""

    with get_connection() as connection:

        # Hall information.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS halls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK (is_active IN (0, 1))
            )
        """)

        # User accounts. Public registration will create only user accounts.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user'
                    CHECK (role IN ('user', 'admin')),
                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Booking applications submitted by users.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS booking_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,
                hall_id INTEGER NOT NULL,

                applicant_name TEXT NOT NULL,
                department TEXT NOT NULL,
                contact_number TEXT NOT NULL,
                event_name TEXT NOT NULL,
                purpose TEXT NOT NULL,
                attendee_count INTEGER NOT NULL
                    CHECK (attendee_count > 0),
                special_requirements TEXT NOT NULL DEFAULT '',

                booking_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,

                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (
                        status IN (
                            'pending',
                            'approved',
                            'rejected',
                            'cancellation_pending',
                            'cancelled'
                        )
                    ),

                admin_decision_reason TEXT NOT NULL DEFAULT '',
                decided_by INTEGER,
                decided_at TEXT,

                cancellation_reason TEXT NOT NULL DEFAULT '',
                cancellation_decided_by INTEGER,
                cancellation_decided_at TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (hall_id) REFERENCES halls(id),
                FOREIGN KEY (decided_by) REFERENCES users(id),
                FOREIGN KEY (cancellation_decided_by)
                    REFERENCES users(id),

                CHECK (start_time < end_time)
            )
        """)

        # Indexes help retrieve requests by date, hall, and status.
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_requests_schedule
            ON booking_requests (
                hall_id, booking_date, status, start_time, end_time
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_requests_user
            ON booking_requests (user_id, created_at)
        """)

        # Record important administrative decisions for accountability.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS admin_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                request_id INTEGER NOT NULL,
                action TEXT NOT NULL
                    CHECK (
                        action IN (
                            'approved',
                            'rejected',
                            'cancellation_approved',
                            'cancellation_rejected'
                        )
                    ),
                reason TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (admin_id) REFERENCES users(id),
                FOREIGN KEY (request_id)
                    REFERENCES booking_requests(id)
            )
        """)

        # Insert the initial halls without duplicating existing names.
        sample_halls = [
            (
                "Hall A",
                "Suitable for speeches and presentations."
            ),
            (
                "Hall B",
                "Suitable for seminars and workshops."
            ),
            (
                "Hall C",
                "Suitable for meetings and group activities."
            ),
        ]

        connection.executemany("""
            INSERT OR IGNORE INTO halls (name, description)
            VALUES (?, ?)
        """, sample_halls)


def get_all_halls():
    """Return active halls for display on the website."""

    with get_connection() as connection:
        rows = connection.execute("""
            SELECT id, name, description
            FROM halls
            WHERE is_active = 1
            ORDER BY id
        """).fetchall()

        return [dict(row) for row in rows]


def get_table_names():
    """Return the database tables for setup verification."""

    with get_connection() as connection:
        rows = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

        return [row["name"] for row in rows]


if __name__ == "__main__":
    initialize_database()

    print("Database initialized successfully.")
    print(f"Database location: {DATABASE_PATH}")

    print("\nDatabase tables:")
    for table_name in get_table_names():
        print(f"- {table_name}")

    print("\nRegistered halls:")
    for hall in get_all_halls():
        print(f"{hall['id']}. {hall['name']} - {hall['description']}")
