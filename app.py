import os
import json
import shutil
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend_rag import RAGHelper

HISTORY_FILE = "chat_history.json"
UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Local RAG Chat")

rag = RAGHelper()

state = {
    "current_history": [],
    "current_session_name": None,
    "document_ready": False,
}


class AskRequest(BaseModel):
    message: str


def load_all_sessions():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_current_session():
    if not state["current_session_name"]:
        return

    new_entry = {
        "session_name": state["current_session_name"],
        "messages": state["current_history"],
    }

    data = load_all_sessions()

    session_exists = False
    for i, session in enumerate(data):
        if session.get("session_name") == state["current_session_name"] or session.get("session") == state["current_session_name"]:
            data[i] = new_entry
            session_exists = True
            break

    if not session_exists:
        data.append(new_entry)

    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)


@app.get("/api/history")
def get_history():
    data = load_all_sessions()
    sessions = []
    for session in reversed(data):
        name = session.get("session_name") or session.get("session") or "Unknown Session"
        sessions.append({"session_name": name, "messages": session.get("messages", [])})
    return {"sessions": sessions}


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    try:
        rag.load_document(file_path)
        overview_text = rag.get_document_overview()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    state["current_session_name"] = f"{file.filename} ({timestamp})"
    state["current_history"] = []
    state["document_ready"] = True

    welcome_msg = f"Document '{file.filename}' uploaded successfully.\n\nHere is a summary:\n{overview_text}"
    state["current_history"].append({"sender": "System", "message": welcome_msg})
    save_current_session()

    return {
        "session_name": state["current_session_name"],
        "overview": overview_text,
        "message": welcome_msg,
    }


@app.post("/api/ask")
def ask_question(payload: AskRequest):
    if not state["document_ready"]:
        raise HTTPException(status_code=400, detail="Please upload a PDF document first.")

    user_input = payload.message.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    state["current_history"].append({"sender": "You", "message": user_input})
    save_current_session()

    try:
        response = rag.ask_question(user_input)
    except Exception as e:
        response = f"Error: {str(e)}"

    state["current_history"].append({"sender": "Bot", "message": response})
    save_current_session()

    return {"answer": response}


@app.get("/api/status")
def get_status():
    return {
        "document_ready": state["document_ready"],
        "session_name": state["current_session_name"],
    }


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return FileResponse("templates/index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=False)
