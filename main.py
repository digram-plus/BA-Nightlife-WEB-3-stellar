import traceback
import sys
import os

try:
    # Try to import the real app
    from app.api import app
except Exception as e:
    # If it fails, create a minimal app to report the error
    from fastapi import FastAPI
    app = FastAPI()
    
    error_trace = traceback.format_exc()
    # Log to stdout (Vercel captures this in Runtime Logs)
    print(f"--- CRITICAL IMPORT ERROR ---")
    print(f"Error: {e}")
    print(error_trace)
    print(f"-----------------------------")

    @app.get("/api/health")
    @app.get("/api/error")
    @app.get("/")
    def error_page():
        return {
            "status": "error",
            "message": "Application failed to initialize (ImportError or StartupError)",
            "error_details": str(e),
            "traceback": error_trace.split("\n"),
            "python_version": sys.version,
            "cwd": os.getcwd(),
            "sys_path": sys.path
        }

# Vercel's @vercel/python runtime looks for the 'app' variable
app = app
