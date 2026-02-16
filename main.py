from fastapi import FastAPI
import sys
import os

app = FastAPI()

@app.get("/api/health")
@app.get("/")
def diagnostic():
    return {
        "status": "diagnostic",
        "message": "Pure FastAPI app is running on Vercel!",
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "env_keys": list(os.environ.keys())
    }

# Export app instance
app = app
