# 🧠 DocuMind Enterprise - RAG SOP Assistant

Hey! This is a high-performance RAG (Retrieval-Augmented Generation) assistant built specifically for digging through massive corporate SOPs (Standard Operating Procedures). 

Instead of manual scrolling, just ask a question and let the AI do the heavy lifting. It fetches the exact page numbers so you can verify everything instantly.

## 🚀 What's inside?
- **Fast Parsing:** Uses `unstructured` to handle messy PDFs without breaking a sweat.
- **Smart Retrieval:** Uses Pinecone to find exactly what you need in seconds.
- **No BS Guardrails:** If the info isn't in your docs, the AI won't make stuff up. It'll just tell you it doesn't know.
- **Citations included:** Every answer comes with the page number it found it on.

## 🛠 Tech Stack
- **FastAPI** (for the heavy lifting API)
- **LangChain** (the glue holding it together)
- **OpenAI GPT-4o** (the brain)
- **Pinecone** (the memory)

## 🔧 Getting Started

1. **Clone it:**
   ```bash
   git clone <your-repo-link>
   cd Rag-Sop-Assistant
   ```

2. **Setup your environment:**
   Make sure you've got Python installed, then:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Keys & Config:**
   Crack open the `.env` file and drop in your API keys (don't share these!):
   ```env
   OPENAI_API_KEY=your_secret_key
   PINECONE_API_KEY=your_secret_key
   PINECONE_INDEX_NAME=documind-enterprise
   ```

4. **Fire it up:**
   ```bash
   python main.py
   ```
   Head over to `http://127.0.0.1:8000/docs` to start testing the endpoints.

## 🧪 Testing the API
- **Ingest:** Upload your PDF to `/ingest`.
- **Ask:** Hit `/query` with your question and see the magic happen.

*Happy Coding! 🚀*
