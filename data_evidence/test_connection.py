"""
test_connection.py
Run this first. Confirms DB + storage are reachable before you build
anything else on top of them.

    python test_connection.py

Expect two ✅ lines. If either fails, double-check the matching
values in .env.
"""

import sys
import uuid


def check_database() -> bool:
    try:
        from sqlmodel import Session, text
        from database import engine

        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        print("✅ Database connection OK")
        return True
    except Exception as e:
        print(f"❌ Database connection FAILED: {e}")
        return False


def check_storage() -> bool:
    try:
        from storage import upload_bytes, download_bytes, delete_object

        test_key = f"connection-test/{uuid.uuid4().hex}.txt"
        payload = b"metroscan connection test"

        upload_bytes(payload, test_key, content_type="text/plain")
        fetched = download_bytes(test_key)
        delete_object(test_key)

        if fetched == payload:
            print("✅ Storage connection OK")
            return True
        else:
            print("❌ Storage connection FAILED: uploaded/downloaded bytes did not match")
            return False
    except Exception as e:
        print(f"❌ Storage connection FAILED: {e}")
        return False


if __name__ == "__main__":
    db_ok = check_database()
    storage_ok = check_storage()

    if db_ok and storage_ok:
        print("\nAll good — you're ready to design/create the schema (init_db()).")
        sys.exit(0)
    else:
        print("\nFix the failing check(s) above before continuing.")
        sys.exit(1)
