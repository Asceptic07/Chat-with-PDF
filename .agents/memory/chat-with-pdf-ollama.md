---
name: Chat-with-PDF Ollama local-only
description: Why RAG answering fails in Replit and what that means for testing this project.
---

The RAG chat backend (`backend_rag.py`) calls a local `ChatOllama` model (`llama3.2`) via `langchain_ollama`.
Replit's container has no Ollama server running and none should be installed here — per the project
owner, this app is generated on Replit but run locally on their own machine (Windows) specifically to
keep documents private. Ollama connects to `localhost:11434` wherever the app actually runs.

**Why:** The user explicitly asked to keep the Ollama integration untouched and only use Replit to
generate/edit the code; they run the exported app locally themselves.

**How to apply:** When testing this app in the Replit preview, PDF upload/summary and Q&A calls will
fail or hang unless Ollama is reachable — that's expected here, not a bug. Only verify the FastAPI
server, routes, and frontend UI work; don't try to make Ollama itself work inside Replit (e.g. don't
install/run Ollama as a workflow) unless the user changes this requirement.
