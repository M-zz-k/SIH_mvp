"""
METROSCAN AI — test suite.

Uses the existing TestClient pattern; no extra frameworks introduced.
`with` block ensures the lifespan (which creates DB tables) runs.
"""
import io

import pytest
from fastapi.testclient import TestClient

from app.main import app

# Shared client — lifespan (DB table creation) runs once for the module.
client = TestClient(app)
client.__enter__()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register_and_login(email: str, password: str = "pass1234") -> str:
    """Register (ignore 400 if already exists) and return a JWT token."""
    client.post("/auth/register", json={"email": email, "password": password})
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"Login failed for {email}: {r.text}"
    return r.json()["access_token"]


def _fake_image(name: str = "label.jpg", content: bytes = b"fake image bytes"):
    return (name, io.BytesIO(content), "image/jpeg")


# ---------------------------------------------------------------------------
# Task 1 baseline: original happy-path tests still pass
# ---------------------------------------------------------------------------

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_and_login_and_scan_flow():
    r = client.post(
        "/auth/register",
        json={"email": "test@doca.gov.in", "password": "pass1234"},
    )
    # 200 first time, 400 if already registered (re-runs)
    assert r.status_code in (200, 400)

    r = client.post(
        "/auth/login",
        json={"email": "test@doca.gov.in", "password": "pass1234"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = client.post(
        "/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": _fake_image()},
    )
    assert r.status_code == 200
    body = r.json()
    assert "overall_tier" in body
    assert body["overall_tier"] in (
        "likely_compliant", "needs_officer_review", "likely_violation"
    )


# ---------------------------------------------------------------------------
# Task 1: Security — register always creates inspector; no role elevation
# ---------------------------------------------------------------------------

def test_register_always_creates_inspector():
    """Public registration must produce an inspector regardless of any tricks."""
    r = client.post(
        "/auth/register",
        json={"email": "sneaky_admin@hack.io", "password": "hax0r"},
    )
    # 200 first time, 400 if email already exists on re-run
    assert r.status_code in (200, 400)
    if r.status_code == 200:
        assert r.json()["role"] == "inspector"


def test_promote_requires_admin_token():
    """Inspector token must get 403 when hitting the promote endpoint."""
    token = _register_and_login("inspector_promo_test@example.com")
    r = client.post(
        "/auth/promote",
        json={"email": "inspector_promo_test@example.com", "new_role": "supervisor"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Task 3: Bulk upload — success path, partial failure path
# ---------------------------------------------------------------------------

def test_bulk_upload_success():
    """POST /bulk with 3 fake images should complete all items."""
    token = _register_and_login("bulk_user@doca.gov.in")
    r = client.post(
        "/bulk",
        headers={"Authorization": f"Bearer {token}"},
        files=[
            ("files", _fake_image("img1.jpg")),
            ("files", _fake_image("img2.jpg")),
            ("files", _fake_image("img3.jpg")),
        ],
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total_items"] == 3
    assert body["completed_items"] == 3
    assert body["failed_items"] == 0
    assert body["failed_filenames"] == []
    assert body["status"] == "done"


def test_bulk_upload_partial_failure(monkeypatch):
    """
    If one file's pipeline raises, only that item is counted as failed,
    the rest succeed, and the failed filename is listed in the response.
    """
    import app.api.routes.bulk as bulk_module

    call_count = 0
    original_pipeline = bulk_module.run_full_pipeline

    def flaky_pipeline(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:  # make the 2nd file blow up
            raise RuntimeError("Simulated OCR failure")
        return original_pipeline(*args, **kwargs)

    monkeypatch.setattr(bulk_module, "run_full_pipeline", flaky_pipeline)

    token = _register_and_login("bulk_fail_user@doca.gov.in")
    r = client.post(
        "/bulk",
        headers={"Authorization": f"Bearer {token}"},
        files=[
            ("files", _fake_image("good1.jpg")),
            ("files", _fake_image("bad_file.jpg")),
            ("files", _fake_image("good2.jpg")),
        ],
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total_items"] == 3
    assert body["completed_items"] == 2
    assert body["failed_items"] == 1
    assert "bad_file.jpg" in body["failed_filenames"]


# ---------------------------------------------------------------------------
# Task 4: GET /results filters
# ---------------------------------------------------------------------------

def test_results_q_filter():
    """q= filter must return 200 (even if empty list when DB is fresh)."""
    token = _register_and_login("results_user@doca.gov.in")
    r = client.get(
        "/results",
        params={"q": "nonexistent_product_xyz"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_results_tier_filter():
    """tier= filter must return 200 and only matching-tier items."""
    token = _register_and_login("results_user2@doca.gov.in")
    r = client.get(
        "/results",
        params={"tier": "likely_compliant"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    for item in r.json():
        assert item["overall_tier"] == "likely_compliant"


def test_results_invalid_tier_rejected():
    """An invalid tier value should produce a 422 validation error."""
    token = _register_and_login("results_user3@doca.gov.in")
    r = client.get(
        "/results",
        params={"tier": "not_a_real_tier"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Task 4: GET /dashboard/stats RBAC
# ---------------------------------------------------------------------------

def test_dashboard_stats_forbidden_for_inspector():
    """Plain inspector token must receive 403 from /dashboard/stats."""
    token = _register_and_login("inspector_dash@doca.gov.in")
    r = client.get(
        "/dashboard/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


def test_dashboard_stats_accessible_for_admin(monkeypatch):
    """
    Admin-role token must receive 200 from /dashboard/stats.
    We inject an admin token directly via create_access_token rather than
    going through the promote endpoint (which itself requires an existing admin).
    """
    from app.core.security import create_access_token, hash_password
    from app.db.session import get_db
    from app.models.db_models import User, UserRoleDB
    from app.models.schemas import UserRole

    admin_token = create_access_token(subject="synthetic_admin@doca.gov.in", role="admin")

    # Ensure the synthetic admin user exists in DB so foreign keys / lookups pass if needed
    db = next(get_db())
    existing = db.query(User).filter(User.email == "synthetic_admin@doca.gov.in").first()
    if not existing:
        db.add(User(
            email="synthetic_admin@doca.gov.in",
            hashed_password=hash_password("adminpass"),
            role=UserRole.ADMIN.value,
        ))
        db.commit()
    db.close()

    r = client.get(
        "/dashboard/stats",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "total_scans" in body
    assert "top_violation_types" in body


# ---------------------------------------------------------------------------
# Task: GET /auth/me
# ---------------------------------------------------------------------------

def test_me_returns_own_profile():
    """GET /auth/me should return the caller's email and role."""
    token = _register_and_login("me_test@example.com")
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "me_test@example.com"
    assert body["role"] == "inspector"
    assert "id" in body


def test_me_requires_auth():
    """GET /auth/me with no token must return 401."""
    r = client.get("/auth/me")
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Task: POST /auth/demote
# ---------------------------------------------------------------------------

def test_demote_supervisor_back_to_inspector():
    """Admin can demote a supervisor back to inspector."""
    # Use the seeded admin account.
    r = client.post("/auth/login", json={
        "email": "admin@metroscan.local",
        "password": "CHANGE_ME_ADMIN_PASSWORD",
    })
    assert r.status_code == 200
    admin_token = r.json()["access_token"]

    # Register a fresh user and promote them to supervisor.
    target_email = "demote_target@example.com"
    client.post("/auth/register", json={"email": target_email, "password": "pass1234"})
    client.post(
        "/auth/promote",
        json={"email": target_email, "new_role": "supervisor"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Demote back to inspector.
    r = client.post(
        "/auth/demote",
        json={"email": target_email, "new_role": "inspector"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "inspector"
    assert r.json()["email"] == target_email


def test_demote_rejected_for_non_admin():
    """Inspector token must get 403 from /auth/demote."""
    inspector_token = _register_and_login("demote_nonadmin@example.com")
    r = client.post(
        "/auth/demote",
        json={"email": "demote_nonadmin@example.com", "new_role": "inspector"},
        headers={"Authorization": f"Bearer {inspector_token}"},
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Last-admin guard tests
# ---------------------------------------------------------------------------

def test_demote_blocks_last_admin():
    """
    Demoting the sole remaining admin must return 400 with a message that
    mentions 'admin' — the system cannot be left admin-less.

    Earlier tests (e.g. test_dashboard_stats_accessible_for_admin) may have
    inserted extra admin accounts.  We *temporarily* demote them so exactly
    one admin remains while the guard is exercised, then restore them in a
    finally block — keeping DB changes purely transient so later tests are
    not polluted regardless of pass/fail.
    """
    from app.core.config import settings
    from app.db.session import get_db
    from app.models.db_models import User, UserRoleDB
    from app.models.schemas import UserRole

    # Log in as the seeded bootstrap admin (always exists thanks to seed_admin()).
    r = client.post("/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD,
    })
    assert r.status_code == 200, r.text
    admin_token = r.json()["access_token"]

    # Snapshot the emails of extra admins BEFORE touching anything.
    db = next(get_db())
    extra_admin_emails = [
        u.email
        for u in db.query(User)
        .filter(User.role == UserRoleDB.admin, User.email != settings.ADMIN_EMAIL)
        .all()
    ]
    db.close()

    # Temporarily demote extras → run the guard check → always restore.
    db = next(get_db())
    try:
        for email in extra_admin_emails:
            u = db.query(User).filter(User.email == email).first()
            if u:
                u.role = UserRole.INSPECTOR.value
        db.commit()

        # Attempt to demote the last remaining admin — must be rejected.
        r = client.post(
            "/auth/demote",
            json={"email": settings.ADMIN_EMAIL, "new_role": "inspector"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 400, r.text
        assert "admin" in r.json()["detail"].lower()

    finally:
        # Restore every temporarily-demoted account back to admin so that
        # later tests (and subsequent pytest runs on the same DB) still find
        # them with the role they expect.
        for email in extra_admin_emails:
            u = db.query(User).filter(User.email == email).first()
            if u:
                u.role = UserRoleDB.admin
        db.commit()
        db.close()


def test_demote_succeeds_when_second_admin_exists():
    """
    Demoting one admin is allowed when at least one other admin remains.
    Steps: promote a second user to admin, then demote the original seeded
    admin — this must succeed with 200.

    seed_admin() is called first so this test is safe on repeated pytest runs
    where the seed admin may have been demoted by a previous run of this test.
    """
    from app.core.config import settings
    from app.db.session import seed_admin

    # Re-ensure the seed admin is an admin (idempotent, safe every run).
    seed_admin()

    # Log in as the seeded bootstrap admin.
    r = client.post("/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD,
    })
    assert r.status_code == 200, r.text
    admin_token = r.json()["access_token"]

    # Register a second user and promote them to admin.
    second_email = "second_admin_guard@example.com"
    client.post("/auth/register", json={"email": second_email, "password": "pass1234"})
    r = client.post(
        "/auth/promote",
        json={"email": second_email, "new_role": "admin"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200, r.text

    try:
        # Now demote the original seeded admin — should succeed because a second admin exists.
        r = client.post(
            "/auth/demote",
            json={"email": settings.ADMIN_EMAIL, "new_role": "inspector"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["role"] == "inspector"
        assert r.json()["email"] == settings.ADMIN_EMAIL
    finally:
        seed_admin()
