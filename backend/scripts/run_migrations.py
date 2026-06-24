import subprocess
import sys


def main() -> int:
    print("Running Alembic migrations...")
    result = subprocess.run(["alembic", "upgrade", "head"], cwd="/app/qdra")
    if result.returncode != 0:
        print("Alembic migrations failed")
        return result.returncode
    print("Alembic migrations completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
