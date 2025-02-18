
import sqlite3
import psycopg2

def migrate_sqlite_to_postgres(
    sqlite_db_path,
    sqlite_table,
    postgres_host,
    postgres_db,
    postgres_user,
    postgres_password,
    postgres_schema,
    postgres_table
):
    """
    Migrate data from a SQLite table to a PostgreSQL table.
    """

    # 1. Connect to SQLite
    try:
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        cursor_sqlite = sqlite_conn.cursor()
        print(f"Connected to SQLite: {sqlite_db_path}")
    except sqlite3.Error as e:
        print(f"Error connecting to SQLite: {e}")
        return

    # 2. Fetch data from the SQLite table
    try:
        select_query = f"SELECT * FROM {sqlite_table};"
        cursor_sqlite.execute(select_query)
        rows = cursor_sqlite.fetchall()
        # Optionally get column names (if needed for debugging or dynamic insertion)
        col_names = [desc[0] for desc in cursor_sqlite.description]
        print(f"Fetched {len(rows)} rows from {sqlite_table}")
    except sqlite3.Error as e:
        print(f"Error reading from SQLite: {e}")
        cursor_sqlite.close()
        sqlite_conn.close()
        return

    # 3. Connect to PostgreSQL
    try:
        postgres_conn = psycopg2.connect(
            host=postgres_host,
            database=postgres_db,
            user=postgres_user,
            password=postgres_password
        )
        cursor_postgres = postgres_conn.cursor()
        print(f"Connected to PostgreSQL: {postgres_db}")
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        cursor_sqlite.close()
        sqlite_conn.close()
        return

    # 4. Insert data into PostgreSQL table
    #    (Assumes the target table has same column order or you'll map them manually)
    #    Build a parameter placeholder string like (%s, %s, ...)
    num_cols = len(col_names)
    placeholders = ", ".join(["%s"] * num_cols)
    insert_query = f"""
        INSERT INTO {postgres_schema}.{postgres_table}
        ({", ".join(col_names)})
        VALUES ({placeholders})
    """
    try:
        # Insert rows one-by-one (fine for smaller datasets)
        # For very large datasets, consider executemany() or COPY approach
        for row in rows:
            cursor_postgres.execute(insert_query, row)

        postgres_conn.commit()
        print(f"Inserted {len(rows)} rows into {postgres_schema}.{postgres_table} in PostgreSQL.")
    except psycopg2.Error as e:
        postgres_conn.rollback()
        print(f"Error inserting into PostgreSQL: {e}")

    # 5. Close all connections
    cursor_postgres.close()
    postgres_conn.close()
    cursor_sqlite.close()
    sqlite_conn.close()
    print("Migration completed and database connections closed.")


if __name__ == "__main__":
    # Example usage:
    migrate_sqlite_to_postgres(
        sqlite_db_path="lumo_reports_data.db",   # Path to your SQLite DB
        sqlite_table="investor_pipeline",        # Table in SQLite
        postgres_host="localhost",               # Host for PostgreSQL
        postgres_db="lumo_reports_data",                  # PostgreSQL database name
        postgres_user="postgres",                # PostgreSQL user
        postgres_password="MayTheFourth2023!",        # PostgreSQL user password
        postgres_schema="input_data",             # PostgreSQL schema name
        postgres_table="investor_pipeline"       # PostgreSQL table name
    )
