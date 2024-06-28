import threading

from fastapi import FastAPI
from pydantic import BaseModel

from session_manager import SessionManager


class SessionRequest(BaseModel):
    session: str


app = FastAPI()
max_sessions = 5
session_manager = SessionManager(max_sessions)


@app.on_event("startup")
async def startup_event():
    threading.Thread(target=session_manager.keep_sessions_alive, daemon=True).start()


@app.get("/get_session")
async def get_session():
    session = session_manager.get_session()
    return {"session": session}


@app.post("/release_session")
async def release_session(request: SessionRequest):
    if session_manager.release_session(request.session):
        return {"detail": "Session released"}
    return {"detail": "Session not found"}


@app.on_event("shutdown")
def shutdown_event():
    session_manager.close_all_sessions()
