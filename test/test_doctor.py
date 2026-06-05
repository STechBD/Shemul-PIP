from __future__ import annotations

from shemul.doctor import Doctor


def test_doctor_returns_checks(monkeypatch):
    monkeypatch.setattr("shemul.doctor.updater._fetch_manifest", lambda *a, **k: None)
    monkeypatch.setattr(
        "shemul.doctor.shutil.which",
        lambda n: f"/usr/bin/{n}" if n in {"python", "python3", "node"} else None,
    )

    checks = Doctor().run()
    names = [c.name for c in checks]

    assert "os" in names
    assert "python" in names and "python3" in names and "node" in names
    assert "alias s" in names

    python = next(c for c in checks if c.name == "python")
    assert python.ok is True

    manifest = next(c for c in checks if c.name == "update manifest")
    assert manifest.ok is False  # forced offline


def test_doctor_reports_manifest_reachable(monkeypatch):
    from shemul.updater import UpdateInfo

    monkeypatch.setattr(
        "shemul.doctor.updater._fetch_manifest",
        lambda *a, **k: UpdateInfo("9.9.9", 99, 1, "u", ""),
    )
    monkeypatch.setattr("shemul.doctor.shutil.which", lambda n: None)

    checks = Doctor().run()
    manifest = next(c for c in checks if c.name == "update manifest")
    assert manifest.ok is True
    assert "9.9.9" in manifest.detail
