from fastapi import FastAPI
import sys
import traceback

app = FastAPI()
results = {}

def try_import(name):
    try:
        # Import the module dynamically
        __import__(name)
        results[name] = "OK"
        return True
    except Exception as e:
        results[name] = f"FAILED: {str(e)}\n{traceback.format_exc()}"
        return False

# Sequential check
try_import("app")
try_import("app.config")
try_import("app.db")
try_import("app.models")
try_import("app.services.payments")
try_import("app.api")

@app.get("/api/health")
@app.get("/")
def diagnostic():
    return {
        "status": "incremental_diagnostic",
        "import_results": results,
        "python_version": sys.version,
    }

# Export either the real app (if OK) or the diagnostic one
if results.get("app.api") == "OK":
    from app.api import app as real_app
    app = real_app
else:
    app = app
