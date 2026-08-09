from __future__ import annotations

from pathlib import Path

import pytest

from flowproof.auth import AuthError, AuthStore, verify_password, hash_password


def store(tmp_path: Path) -> AuthStore:
    return AuthStore(tmp_path / "auth.db")


def test_password_hash_roundtrip():
    h = hash_password("correct horse battery")
    assert verify_password("correct horse battery", h)
    assert not verify_password("wrong", h)


def test_signup_and_authenticate(tmp_path: Path):
    s = store(tmp_path)
    uid = s.create_user("Sci@lab.org", "supersecret")
    assert s.authenticate("sci@lab.org", "supersecret") == uid


def test_duplicate_email_rejected(tmp_path: Path):
    s = store(tmp_path)
    s.create_user("a@b.com", "supersecret")
    with pytest.raises(AuthError):
        s.create_user("a@b.com", "anotherpass")


def test_short_password_rejected(tmp_path: Path):
    with pytest.raises(AuthError):
        store(tmp_path).create_user("a@b.com", "short")


def test_bad_credentials_rejected(tmp_path: Path):
    s = store(tmp_path)
    s.create_user("a@b.com", "supersecret")
    with pytest.raises(AuthError):
        s.authenticate("a@b.com", "nope")


def test_api_key_lifecycle(tmp_path: Path):
    s = store(tmp_path)
    uid = s.create_user("a@b.com", "supersecret")
    key = s.create_api_key(uid, "laptop")
    assert key.startswith("fpk_")
    assert s.user_for_api_key(key) == uid
    listed = s.list_api_keys(uid)
    assert len(listed) == 1 and listed[0].label == "laptop"
    assert s.revoke_api_key(uid, listed[0].id)
    assert s.user_for_api_key(key) is None
    assert s.list_api_keys(uid) == []


def test_key_only_belongs_to_owner(tmp_path: Path):
    s = store(tmp_path)
    owner = s.create_user("owner@b.com", "supersecret")
    other = s.create_user("other@b.com", "supersecret")
    key = s.create_api_key(owner, "k")
    key_id = s.list_api_keys(owner)[0].id
    assert not s.revoke_api_key(other, key_id)
    assert s.user_for_api_key(key) == owner


def test_session_roundtrip(tmp_path: Path):
    s = store(tmp_path)
    uid = s.create_user("a@b.com", "supersecret")
    session = s.create_session(uid)
    assert s.user_for_session(session) == uid
    assert s.user_for_session("bogus") is None
