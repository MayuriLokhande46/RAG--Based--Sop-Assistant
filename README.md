# DocuMind Enterprise: RAG-based SOP Assistant

A high-performance RAG (Retrieval-Augmented Generation) assistant designed for corporate Standard Operating Procedures (SOPs). Built with FastAPI, LangChain, OpenAI, and Pinecone.

## Features
- **PDF Ingestion:** Robust PDF parsing using `unstructured`.
- **Advanced RAG:** Retrieval-focused chunking and semantic search.
- **Accuracy & Safety:** Hallucination guardrails and source citations (page numbers).
- **FastAPI Interface:** Easy-to-use API endpoints for ingestion and querying.

## Tech Stack
- **Backend:** FastAPI, Python
- **Orchestration:** LangChain
- **LLM:** OpenAI (GPT-4o)
- **Vector DB:** Pinecone
- **Parser:** Unstructured.io

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd Rag-Sop-Assistant
   ```

2. **Create Virtual Environment:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file and add your keys:
   ```env
   OPENAI_API_KEY=your_key
   PINECONE_API_KEY=your_key
   PINECONE_INDEX_NAME=your_index
   ```

5. **Run the App:**
   ```bash
   python main.py
   ```
   Access Swagger UI at `http://127.0.0.1:8000/docs`
