import queue
import random
import threading
import time

from fastapi import HTTPException

Session = str


def create_session() -> Session:
    time.sleep(1.5)
    return f"session-{random.randint(1000, 9999)}"


def close_session(session: Session) -> None:
    time.sleep(1.5)
    print(f"Session {session} closed")


def keep_alive(session: Session) -> None:
    print(f"Session {session} kept alive")


def ping(session: Session) -> bool:
    return random.choice([True, True, False])


def should_keep_sessions_alive() -> bool:
    return True


class SessionManager:
    def __init__(self, max_sessions: int) -> None:
        self.max_sessions = max_sessions
        self.session_pool = queue.Queue(max_sessions)
        self.lock = threading.Lock()
        self.alive_sessions = set()

    def get_session(self) -> Session:
        with self.lock:
            if not self.session_pool.empty():
                session = self.session_pool.get()
                if ping(session):
                    return session
                else:
                    self.alive_sessions.remove(session)
                    new_session = create_session()
                    self.alive_sessions.add(new_session)
                    return new_session
            elif len(self.alive_sessions) < self.max_sessions:
                new_session = create_session()
                self.alive_sessions.add(new_session)
                return new_session
            else:
                raise HTTPException(status_code=503, detail="No available sessions")

    def release_session(self, session: Session) -> bool:
        with self.lock:
            if session in self.alive_sessions:
                self.session_pool.put(session)
                return True
            return False

    def close_all_sessions(self) -> None:
        with self.lock:
            while not self.session_pool.empty():
                session = self.session_pool.get_nowait()
                close_session(session)
                self.alive_sessions.remove(session)


    def keep_sessions_alive(self) -> None:
        while should_keep_sessions_alive():
            with self.lock:
                for session in list(self.alive_sessions):
                    if not ping(session):
                        self.alive_sessions.remove(session)
                        close_session(session)
                    else:
                        keep_alive(session)
            time.sleep(60)
