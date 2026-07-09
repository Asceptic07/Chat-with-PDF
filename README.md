# 📟 RAG Document AI — Local Terminal v1.0

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C.svg)](https://python.langchain.com/)
[![FAISS](https://img.shields.io/badge/Vector%20Store-FAISS-blue.svg)](https://github.com/facebookresearch/faiss)
[![Ollama](https://img.shields.io/badge/LLM-Ollama%20(Llama%203.2)-black.svg)](https://ollama.ai/)

**RAG Document AI Terminal** is a 100% offline, privacy-first Retrieval-Augmented Generation (RAG) web application that lets you chat with any PDF document. Built with **FastAPI**, **LangChain**, **FAISS**, and **Ollama (Llama 3.2)**, it features a retro CRT cyberpunk terminal UI complete with phosphor scanlines and nostalgic typography.

---

## ✨ Key Features

- **🔒 100% Local & Private:** No API keys required, no external cloud telemetry. Your PDF documents and chat logs never leave your machine.
- **⚡ High-Precision Retrieval-Augmented Generation (RAG):**
  - Uses `RecursiveCharacterTextSplitter` for intelligent document chunking.
  - Embeds document chunks locally using HuggingFace's `all-MiniLM-L6-v2` embedding model.
  - Indexes chunks inside an in-memory **FAISS** vector database for sub-second similarity search.
- **🦙 Local Llama 3.2 Reasoning:** Leverages **Ollama** (`llama3.2`) configured with precise temperature settings to ground responses strictly in the uploaded document.
- **💾 Session & Chat History Management:** Automatically manages and persists multi-turn chat conversations across document uploads (`chat_history.json`).
- **🕹️ Retro CRT Cyberpunk UI:** Custom HTML5/CSS3 terminal shell with authentic scanline effects, retro typography (`VT323` / `Press Start 2P`), and responsive UI interaction.

---

## 🏗️ System Architecture

```text
[ Upload PDF ] ──> [ PyPDFLoader & TextSplitter ]
                         │
                         ▼
             [ HuggingFace Embeddings ] (all-MiniLM-L6-v2)
                         │
                         ▼
             [ FAISS Vector Database ]
                         │
 [ User Question ] ──> [ Semantic Retrieval Chain ] ──> [ Ollama (Llama 3.2) ] ──> [ CRT Terminal UI ]
