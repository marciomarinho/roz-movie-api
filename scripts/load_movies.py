#!/usr/bin/env python
"""Load MovieLens movies.csv into PostgreSQL database."""
# docker run --name my-postgres -e POSTGRES_PASSWORD=mysecretpassword -p 5432:5432 -d postgres

# python scripts/load_movies.py \
#   --dbname=postgres \
#   --user=postgres \
#   --password=mysecretpassword \
#   --drop-table --create-table
#   --csv-path=data/movies_large.csv

# python scripts/load_movies.py --dbname=postgres --user=postgres --password=mysecretpassword --drop-table --create-table --csv-path=../data/movies.csv

# python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

#!/usr/bin/env python
import argparse
import csv
import re

import psycopg2
from psycopg2 import extras


YEAR_REGEX = re.compile(r"\((\d{4})\)\s*$")


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS public.movies (
    movie_id  INTEGER PRIMARY KEY,
    title     TEXT NOT NULL,
    year      INTEGER,
    genres    TEXT[] NOT NULL
);
"""

DROP_TABLE_SQL = """
DROP TABLE IF EXISTS public.movies;
"""


def parse_year(title: str):
    """
    Extracts the year from a movie title like 'Toy Story (1995)'.
    Returns an int year or None if not found.
    """
    match = YEAR_REGEX.search(title)
    if match:
        return int(match.group(1))
    return None


def drop_table(conn):
    """Drops the movies table."""
    with conn.cursor() as cur:
        cur.execute(DROP_TABLE_SQL)
    conn.commit()
    print("Dropped table public.movies (if it existed).")


def ensure_table_exists(conn):
    """
    Creates the movies table if it does not exist.
    """
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    print("Ensured public.movies table exists.")


def load_movies(csv_path: str, conn_params: dict, create_table: bool = False):
    """
    Loads movies CSV into public.movies table.
    """
    conn = psycopg2.connect(**conn_params)
    try:
        if create_table:
            ensure_table_exists(conn)

        with conn.cursor() as cur, open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            rows = []
            for row in reader:
                movie_id = int(row["movieId"])
                title = row["title"]
                year = parse_year(title)

                genres_raw = row["genres"] or ""
                genres = [g for g in genres_raw.split("|") if g and g != "(no genres listed)"]
                if not genres:
                    genres = ["Unknown"]

                rows.append((movie_id, title, year, genres))

            if not rows:
                print("No rows found in CSV. Nothing to insert.")
                return

            insert_sql = """
                INSERT INTO public.movies (movie_id, title, year, genres)
                VALUES %s
                ON CONFLICT (movie_id) DO UPDATE
                SET title = EXCLUDED.title,
                    year = EXCLUDED.year,
                    genres = EXCLUDED.genres;
            """

            extras.execute_values(cur, insert_sql, rows, page_size=1000)
            conn.commit()

            print(f"Inserted/updated {len(rows)} movies.")

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Load MovieLens movies.csv into PostgreSQL 'movies' table."
    )

    parser.add_argument(
        "--csv-path",
        default="../data/movies_small.csv",
        help="Path to movies.csv (default: ../data/movies_small.csv)",
    )
    parser.add_argument("--host", default="localhost", help="PostgreSQL host (default: localhost)")
    parser.add_argument("--port", default=5432, type=int, help="PostgreSQL port (default: 5432)")
    parser.add_argument("--dbname", required=True, help="PostgreSQL database name")
    parser.add_argument("--user", required=True, help="PostgreSQL user")
    parser.add_argument("--password", required=True, help="PostgreSQL password")

    parser.add_argument(
        "--create-table",
        action="store_true",
        help="Create the 'movies' table if it does not exist before loading data.",
    )
    parser.add_argument(
        "--drop-table",
        action="store_true",
        help="Drop the 'movies' table before doing anything else.",
    )

    args = parser.parse_args()

    conn_params = {
        "host": args.host,
        "port": args.port,
        "dbname": args.dbname,
        "user": args.user,
        "password": args.password,
    }

    conn = psycopg2.connect(**conn_params)

    try:
        # Handle --drop-table
        if args.drop_table:
            drop_table(conn)
            # If user ONLY wants to drop, don't proceed
            if not args.create_table:
                print("Drop complete. Exiting (no create/load requested).")
                conn.close()
                return

        # Handle loading
        load_movies(args.csv_path, conn_params, create_table=args.create_table)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
