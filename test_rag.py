import os
from dotenv import load_dotenv
from core_rag import get_retrieval_chain

load_dotenv()

INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "documind-enterprise-v2")

try:
    print(f"Index: {INDEX_NAME}")
    print("Getting chain...")
    chain = get_retrieval_chain(INDEX_NAME, namespace="user_1")
    print("Invoking chain with input 'Hello'...")
    response = chain.invoke({"input": "Hello, what is in the document?"})
    print("Chain invoked successfully!")
    print("Response keys:", response.keys())
    print("Answer:", response.get("answer"))
    print("Result:", response.get("result"))
except Exception as e:
    import traceback
    print(traceback.format_exc())
