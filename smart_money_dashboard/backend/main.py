from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import shutil
import os

from . import sm_analysis

app = FastAPI(title="Smart Money Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
os.makedirs(DATA_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    return FileResponse(index_path)

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/analyze/file")
async def analyze_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")
    save_path = os.path.join(DATA_DIR, "uploaded.csv")
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        result = sm_analysis.analyze(save_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return result

@app.get("/api/analyze/sample")
async def analyze_sample():
    csv_path = os.path.join(DATA_DIR, "XAUUSD_15m_sample.csv")
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Sample CSV not found")
    try:
        result = sm_analysis.analyze(csv_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return result
