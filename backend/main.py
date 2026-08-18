from fastapi import FastAPI

app = FastAPI(title="CareerSync API")


@app.get("/")
def root():
    return {
        "message": "CareerSync backend is running"
    }