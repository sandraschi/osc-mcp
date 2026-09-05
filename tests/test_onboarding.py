"""Tests for the onboarding/app-detection surface (oscmcp.app_detect + the REST endpoint)."""

from fastapi.testclient import TestClient

from oscmcp.api.main import app
from oscmcp.app_detect import APP_SPECS, detect_all, detect_app


def test_detect_all_returns_one_status_per_spec():
    statuses = detect_all()
    assert len(statuses) == len(APP_SPECS)
    assert {s.key for s in statuses} == {spec.key for spec in APP_SPECS}


def test_qlab_is_never_testable_on_a_non_macos_host():
    status = detect_app("qlab")
    assert status.platform == "macos"
    assert status.testable_here is False


def test_detect_app_never_reports_installed_for_a_path_that_does_not_exist(monkeypatch):
    monkeypatch.setattr(
        "oscmcp.app_detect.glob.glob",
        lambda pattern: [],
    )
    status = detect_app("obs")
    assert status.installed is False
    assert status.installed_path is None


def test_onboarding_apps_endpoint_returns_all_specs():
    client = TestClient(app)
    r = client.get("/api/v1/onboarding/apps")
    assert r.status_code == 200
    data = r.json()
    assert data["total_count"] == len(APP_SPECS)
    assert data["installed_count"] <= data["total_count"]
    keys = {a["key"] for a in data["apps"]}
    assert keys == {spec.key for spec in APP_SPECS}
    # Every app must report a license classification the onboarding UI can render
    for a in data["apps"]:
        assert a["license"] in {"free", "commercial", "commercial-trial", "hardware"}
