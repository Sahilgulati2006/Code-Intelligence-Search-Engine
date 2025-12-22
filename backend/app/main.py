from fastapi import FastAPI

app = FastAPI(title="Code Intelligence Backend")

@app.get("/health")
def health_check():
    return {"status": "ok"}
