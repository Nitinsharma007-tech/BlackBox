from sqlalchemy import text

from backend.database.postgresql import engine


def migrate():
    if engine is None:
        raise RuntimeError(
            "DATABASE_URL is not configured."
        )

    with engine.begin() as connection:

        # Check whether the column already exists
        result = connection.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'safety_events'
                  AND column_name = 'status'
                """
            )
        )

        exists = result.scalar()

        if exists:
            print(
                "✓ status column already exists."
            )
            return

        # Add status column
        connection.execute(
            text(
                """
                ALTER TABLE safety_events
                ADD COLUMN status VARCHAR(30)
                NOT NULL
                DEFAULT 'detected'
                """
            )
        )

        print(
            "✓ status column added successfully."
        )

        # Existing incidents automatically receive:
        # status = detected


if __name__ == "__main__":
    migrate()