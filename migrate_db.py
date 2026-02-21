"""
Migration Script - Adds wallet_balance column to users table
and creates the transactions table if they don't exist.

Run this ONCE on your production database to apply schema changes.
Safe to run multiple times - uses IF NOT EXISTS checks.
"""

import os
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()


def run_migrations(app):
    """Run all pending schema migrations safely."""
    with app.app_context():
        from models import db

        print("Running database migrations...")

        with db.engine.connect() as conn:

            # ── 1. Add wallet_balance to users ──────────────────────────────
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'wallet_balance'
            """))
            if result.fetchone() is None:
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN wallet_balance FLOAT NOT NULL DEFAULT 0.0
                """))
                conn.commit()
                print("✅ Added wallet_balance column to users table")
            else:
                print("✔ wallet_balance column already exists")

            # ── 1.5 Add pending_approval to services ────────────────────────
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'services'
                AND column_name = 'pending_approval'
            """))
            if result.fetchone() is None:
                conn.execute(text("""
                    ALTER TABLE services
                    ADD COLUMN pending_approval BOOLEAN DEFAULT FALSE
                """))
                conn.commit()
                print("✅ Added pending_approval column to services table")
            else:
                print("✔ pending_approval column already exists")

            # ── 2. Create transactions table ─────────────────────────────────
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id          SERIAL PRIMARY KEY,
                    txn_id      VARCHAR(50) NOT NULL,
                    user_id     INTEGER NOT NULL REFERENCES users(id),
                    username    VARCHAR(80),
                    amount      FLOAT NOT NULL,
                    method      VARCHAR(20),
                    status      VARCHAR(20),
                    txn_type    VARCHAR(10),
                    description TEXT,
                    new_balance FLOAT,
                    timestamp   TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_transactions_txn_id  
                ON transactions (txn_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_transactions_user_id 
                ON transactions (user_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_transactions_timestamp 
                ON transactions (timestamp)
            """))
            conn.commit()
            print("✅ transactions table ready")

            # ── 3. Create certificates table (dialect-safe via SQLAlchemy) ─────
            # Using db.create_all() is safer than raw SQL because it handles
            # both SQLite (local dev) and PostgreSQL (Render production)
            # automatically without dialect-specific keywords like SERIAL.
            try:
                db.create_all()
                conn.commit()
                print("OK: certificates table ready (via db.create_all)")
            except Exception as ce:
                print("WARNING: db.create_all for certificates had an issue:", ce)

        print("All migrations complete ✅")

    # ── 4. Create required directories ─────────────────────────────────
    base = os.path.abspath(os.path.dirname(__file__))
    os.makedirs(os.path.join(base, 'static', 'certificates'), exist_ok=True)
    os.makedirs(os.path.join(base, 'static', 'fonts'), exist_ok=True)
    print("✅ Static folders verified")