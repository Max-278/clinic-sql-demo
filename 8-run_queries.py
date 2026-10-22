"""run_queries.py - runs every query in queries.sql and prints the results.

Queries are separated by blank-line-free statement blocks; each block starts
with a `-- name: <query_name>` marker so tests can refer to results by name.
"""
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).parent
DB = HERE / "clinic_demo.db"
SQL = HERE / "queries.sql"


def load_queries(path=SQL):
    text = path.read_text()
    blocks = re.split(r";\s*\n", text)
    queries = {}
    for block in blocks:
        m = re.search(r"--\s*name:\s*(\w+)", block)
        if m and "SELECT" in block.upper():
            # strip comment lines for execution, keep them for docs
            sql = "\n".join(l for l in block.split("\n") if not l.strip().startswith("--")).strip()
            queries[m.group(1)] = sql
    return queries


def run(db_path=DB):
    queries = load_queries()
    results = {}
    with sqlite3.connect(db_path) as con:
        for name, sql in queries.items():
            cur = con.execute(sql)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            results[name] = (cols, rows)
    return results


def main():
    if not DB.exists():
        sys.exit("clinic_demo.db not found - run: python3 generate_data.py")
    for name, (cols, rows) in run().items():
        print(f"\n== {name} ==")
        print(" | ".join(cols))
        for r in rows:
            print(" | ".join(str(v) for v in r))


if __name__ == "__main__":
    main()
