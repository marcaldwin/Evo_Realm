from unittest.mock import MagicMock

from pytest import MonkeyPatch
from sqlalchemy.exc import SQLAlchemyError

from backend.app.db import health as database_health


def test_database_is_ready_when_query_succeeds(
    monkeypatch: MonkeyPatch,
) -> None:
    mock_engine = MagicMock()
    mock_connection = mock_engine.connect.return_value.__enter__.return_value
    monkeypatch.setattr(database_health, "engine", mock_engine)

    result = database_health.is_database_ready()

    assert result is True
    mock_engine.connect.assert_called_once()
    mock_connection.execute.assert_called_once()


def test_database_is_not_ready_when_connection_fails(
    monkeypatch: MonkeyPatch,
) -> None:
    mock_engine = MagicMock()
    mock_engine.connect.side_effect = SQLAlchemyError("Database unavailable")
    monkeypatch.setattr(database_health, "engine", mock_engine)

    result = database_health.is_database_ready()

    assert result is False
    mock_engine.connect.assert_called_once()
