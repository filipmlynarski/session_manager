from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app import SessionManager


@pytest.fixture
def session_manager():
    return SessionManager(max_sessions=2)


def test_get_session_available(session_manager):
    with patch('session_manager.create_session', return_value='session-1234'), \
            patch('session_manager.ping', return_value=True):
        session = session_manager.get_session()
        assert session == 'session-1234'
        assert session in session_manager.alive_sessions


def test_release_session(session_manager):
    with patch('session_manager.create_session', return_value='session-1234'), \
            patch('session_manager.ping', return_value=True):
        session = session_manager.get_session()
        session_manager.release_session(session)
        assert not session_manager.session_pool.empty()
        assert session_manager.session_pool.get() == 'session-1234'


def test_no_available_sessions(session_manager):
    with patch('session_manager.create_session', return_value='session-1001'):
        session_manager.get_session()
    with patch('session_manager.create_session', return_value='session-1002'):
        session_manager.get_session()
    with patch('session_manager.create_session', return_value='session-1003'), \
            patch('session_manager.ping', return_value=True):
        with pytest.raises(HTTPException) as excinfo:
            session_manager.get_session()
        assert excinfo.value.status_code == 503
        assert excinfo.value.detail == "No available sessions"


def test_keep_sessions_alive(session_manager):
    with patch('session_manager.create_session', return_value='session-1234'), \
            patch('session_manager.ping', return_value=True), \
            patch('session_manager.should_keep_sessions_alive', side_effect=[True, False]), \
            patch('time.sleep'), \
            patch('session_manager.keep_alive') as mock_keep_alive:
        session = session_manager.get_session()
        session_manager.keep_sessions_alive()
        mock_keep_alive.assert_called_with(session)
