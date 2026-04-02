from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "success", "message": "Minimal server is ACTIVE on port 8000"}

if __name__ == "__main__":
    print("--- STARTING MINIMAL DIAGNOSTIC SERVER (PORT 8001) ---")
    uvicorn.run(app, host="0.0.0.0", port=8001)
