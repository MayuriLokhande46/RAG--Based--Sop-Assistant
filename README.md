# DocuMind Enterprise - RAG SOP Assistant

DocuMind is a Retrieval-Augmented Generation (RAG) assistant designed for corporate Standard Operating Procedures (SOPs). Upload a PDF, index it into a high-performance vector store, and ask grounded questions through an intuitive web dashboard.

## Key Features

- **Accurate PDF Ingestion**: High-quality document parsing with `PyPDF`.
- **Intelligent Chunking**: optimized text splitting with LangChain for context retention.
- **AI-Powered Retrieval**: Fast, semantic search powered by Pinecone and HuggingFace embeddings.
- **Reliable Answer Generation**: Responses grounded in corporate context using Google Gemini models.
- **Strict Guardrails**: Refuses to hallucinate; if the answer isn't in your docs, it'll tell you.
- **Integrated History**: Keeps track of your previous queries and answers per user session.

## Tech Stack

- **Backend**: FastAPI
- **LLM**: Google Gemini via `langchain-google-genai`
- **Vector DB**: Pinecone
- **Embeddings**: Sentence Transformers (`all-MiniLM-L6-v2`)
- **Frontend**: Glassmorphic UI with Vanilla CSS & Modern JS
- **Database**: SQLite (SQLAlchemy) for user management and chat history

## Getting Started

1. **Clone the repository**:
   ```bash
   git clone <your-repo-link>
   cd Rag-Sop-Assistant
   ```

2. **Set up the environment**:
   Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Configure API Keys**:
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_google_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_INDEX_NAME=documind-enterprise-v2
   GOOGLE_MODEL_NAME=models/gemini-1.5-flash
   ```
   *Tip: Ensure standard Pinecone serverless specs are available in your region.*

4. **Run the Application**:
   ```bash
   uvicorn main:app --reload
   ```
   Access the dashboard at `http://127.0.0.1:8000`.

## Testing the API

- **Ingest**: Use the UI or POST to `/ingest` with a PDF file.
- **Query**: Use the dashboard or POST to `/query` with your question.
- **Auth**: Secured via OAuth2 JWT tokens.

