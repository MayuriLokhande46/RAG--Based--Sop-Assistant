# DocuMind Enterprise - RAG SOP Assistant

DocuMind is a Retrieval-Augmented Generation assistant for corporate SOPs. Upload a PDF, index it into Pinecone, and ask grounded questions against the document set through a FastAPI backend and a simple web UI.

## Features

- PDF ingestion with `pypdf`
- Chunking with LangChain text splitters
- Embeddings via `sentence-transformers/all-MiniLM-L6-v2`
- Vector search with Pinecone
- Answer generation with Google Gemini
- Guardrails that refuse to invent answers outside the indexed context

## Tech Stack

- FastAPI
- LangChain integrations
- Google Gemini via `langchain-google-genai`
- Pinecone
- Sentence Transformers

## Getting Started

1. Clone it:
   ```bash
   git clone <your-repo-link>
   cd Rag-Sop-Assistant
   ```

2. Setup your environment:
   Make sure you've got Python installed, then:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. Keys & Config:
   Create a `.env` file with real service credentials:
   ```env
   GOOGLE_API_KEY=your_google_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_INDEX_NAME=documind-enterprise-v2
   GOOGLE_MODEL_NAME=gemini-2.0-flash
   ```
   `GOOGLE_API_KEY` and `PINECONE_API_KEY` must be different values.

4. Fire it up:
   ```bash
   uvicorn main:app --reload
   ```
   Open `http://127.0.0.1:8000` for the UI or `http://127.0.0.1:8000/docs` for the API docs.

## Testing the API

- Ingest a PDF with `POST /ingest`
- Ask questions with `POST /query`
