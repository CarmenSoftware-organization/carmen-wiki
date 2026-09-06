"""Tests for push_pages.apply_page() — the create/update decision.

push_pages.py reads scripts/.env and defines URL/TOKEN at import time, so
importing it here requires that file to exist (same requirement the script
already has to run at all; not introduced by these tests). No network call
is made: every test injects a fake `gql_fn` in place of the real GraphQL
client.
"""
from scripts import push_pages as pp

PAGE_VARS = {
    "content": "body text",
    "description": "a page",
    "editor": "markdown",
    "isPrivate": False,
    "isPublished": True,
    "locale": "en",
    "path": "platform/licenses",
    "tags": ["platform"],
    "title": "Licenses",
}


def test_create_path_used_when_pid_is_none():
    """No existing page id -> apply_page calls CREATE, not UPDATE."""
    calls = []

    def fake_gql(query, variables):
        calls.append((query, variables))
        return {"data": {"pages": {"create": {
            "responseResult": {"succeeded": True, "errorCode": 0, "message": "Ok"},
            "page": {"id": 999},
        }}}}

    ok, rr, result_id = pp.apply_page(fake_gql, None, PAGE_VARS)

    assert ok is True
    assert rr["succeeded"] is True
    assert result_id == 999
    assert len(calls) == 1
    query, variables = calls[0]
    assert query is pp.CREATE
    assert "id" not in variables  # create takes no id
    assert variables == PAGE_VARS


def test_update_path_used_when_pid_is_known():
    """Existing page id -> apply_page calls UPDATE with that id."""
    calls = []

    def fake_gql(query, variables):
        calls.append((query, variables))
        return {"data": {"pages": {"update": {
            "responseResult": {"succeeded": True, "errorCode": 0, "message": "Ok"},
        }}}}

    ok, rr, result_id = pp.apply_page(fake_gql, 42, PAGE_VARS)

    assert ok is True
    assert rr["succeeded"] is True
    assert result_id == 42  # update returns the given pid unchanged
    assert len(calls) == 1
    query, variables = calls[0]
    assert query is pp.UPDATE
    assert variables["id"] == 42
    for k, v in PAGE_VARS.items():
        assert variables[k] == v


def test_create_failure_reports_response_result_and_no_id():
    def fake_gql(query, variables):
        return {"data": {"pages": {"create": {
            "responseResult": {"succeeded": False, "errorCode": 1, "message": "value too long"},
            "page": None,
        }}}}

    ok, rr, result_id = pp.apply_page(fake_gql, None, PAGE_VARS)

    assert ok is False
    assert rr["succeeded"] is False
    assert rr["message"] == "value too long"
    assert result_id is None


def test_update_failure_reports_response_result():
    def fake_gql(query, variables):
        return {"data": {"pages": {"update": {
            "responseResult": {"succeeded": False, "errorCode": 1, "message": "value too long"},
        }}}}

    ok, rr, result_id = pp.apply_page(fake_gql, 42, PAGE_VARS)

    assert ok is False
    assert rr["message"] == "value too long"
    assert result_id == 42
