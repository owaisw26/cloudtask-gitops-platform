from fastapi import FastAPI

app = FastAPI(title="Cloudops Event Platform")

@app.get("/health")
def getHealth():
    return {
        "status": "ok"
    }

