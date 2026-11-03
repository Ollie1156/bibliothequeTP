from fastapi import FastAPI

app = FastAPI(title="Service Auth")


@app.get("/health")
def health():
    return {"status": "ok"}