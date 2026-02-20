import json
import logging

from app.core.logging import (
    DevFormatter,
    JSONFormatter,
    clinic_id_var,
    request_id_var,
    setup_logging,
    user_id_var,
)


def test_json_formatter_basic():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    output = formatter.format(record)
    data = json.loads(output)
    assert data["message"] == "hello world"
    assert data["level"] == "INFO"
    assert data["logger"] == "test"


def test_json_formatter_includes_context_vars():
    formatter = JSONFormatter()
    token = request_id_var.set("req-123")
    clinic_token = clinic_id_var.set("clinic-456")
    user_token = user_id_var.set("user-789")
    try:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert data["request_id"] == "req-123"
        assert data["clinic_id"] == "clinic-456"
        assert data["user_id"] == "user-789"
    finally:
        request_id_var.reset(token)
        clinic_id_var.reset(clinic_token)
        user_id_var.reset(user_token)


def test_dev_formatter_includes_request_id():
    formatter = DevFormatter(fmt="%(message)s")
    token = request_id_var.set("abcdef12-3456-7890")
    try:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        assert "[abcdef12]" in output
        assert "hello" in output
    finally:
        request_id_var.reset(token)


def test_setup_logging_development():
    setup_logging("development", False)
    root = logging.getLogger()
    assert root.level == logging.INFO
    assert len(root.handlers) >= 1


def test_setup_logging_production():
    setup_logging("production", False)
    root = logging.getLogger()
    handler = root.handlers[0]
    assert isinstance(handler.formatter, JSONFormatter)
