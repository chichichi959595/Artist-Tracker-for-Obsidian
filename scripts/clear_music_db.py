from __future__ import annotations

import sqlite3
from pathlib import Path


def main() -> int:
    db_path = Path("data/tracker.db")
    if not db_path.exists():
        print("data/tracker.db does not exist.")
        return 0

    connection = sqlite3.connect(db_path)
    before = connection.execute(
        "SELECT COUNT(1) FROM updates WHERE platform = ?",
        ("music",),
    ).fetchone()[0]
    connection.execute("DELETE FROM updates WHERE platform = ?", ("music",))
    connection.commit()
    after = connection.execute(
        "SELECT COUNT(1) FROM updates WHERE platform = ?",
        ("music",),
    ).fetchone()[0]
    connection.close()

    print(f"music updates before={before} after={after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
