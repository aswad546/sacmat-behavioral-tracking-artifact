#!/usr/bin/env python3
"""Query multicore_static_info and print a paper-claim table."""
import os

import psycopg2

DSN = dict(
    host=os.environ.get("PGHOST", "localhost"),
    port=int(os.environ.get("PGPORT", "5434")),
    dbname=os.environ.get("PGDATABASE", "vv8_backend"),
    user=os.environ.get("PGUSER", "vv8"),
    password=os.environ.get("PGPASSWORD", "vv8"),
)


def main():
    conn = psycopg2.connect(**DSN)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM script_flow;")
    n_scripts = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM multicore_static_info;")
    n_analyzed = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM multicore_static_info WHERE dataflow_to_sink = TRUE;")
    n_sink = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM multicore_static_info "
        "WHERE behavioral_source_api_count > 0 AND dataflow_to_sink = TRUE;"
    )
    n_behavioral = cur.fetchone()[0]

    print("SACMAT 2026 artifact — results summary")
    print(f"  scripts collected:                {n_scripts}")
    print(f"  scripts analyzed:                 {n_analyzed}")
    print(f"  scripts with dataflow to sink:    {n_sink}")
    print(f"  behavioral-tracking candidates:   {n_behavioral}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
