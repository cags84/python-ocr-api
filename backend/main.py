import os
import shutil
import uuid
from typing import Dict
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from backend.services.ocr_service import process_pdf_with_progress
from backend.core.config import settings

app = FastAPI(
    title="Procesador PDF a LLM con Progreso",
    docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
    redoc_url=None if settings.ENVIRONMENT == "production" else "/redoc",
    openapi_url=None if settings.ENVIRONMENT == "production" else "/openapi.json"
)

# Configurar CORS Security (Cross-Origin Resource Sharing)
origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "backend/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Diccionario simple para almacenar el progreso en memoria
# En producción sería mejor Redis / Celery
TASK_STATUS: Dict[str, dict] = {}

def process_file_background(task_id: str, pdf_path: str, filename: str):
    """
    Función que corre en segundo plano para procesar el PDF.
    """
    def progress_callback(percentage: int, status_text: str = ""):
        TASK_STATUS[task_id]["progress"] = percentage
        if status_text:
            TASK_STATUS[task_id]["status_text"] = status_text

    try:
        TASK_STATUS[task_id]["status"] = "processing"
        
        # Procesar con callback
        result_metrics = process_pdf_with_progress(pdf_path, update_progress_cb=progress_callback)
        
        # Guardar resultado
        TASK_STATUS[task_id]["status"] = "completed"
        TASK_STATUS[task_id]["progress"] = 100
        TASK_STATUS[task_id]["result"] = result_metrics["optimized_text"]
        TASK_STATUS[task_id]["stats"] = {
            "raw_len": result_metrics["raw_len"],
            "opt_len": result_metrics["opt_len"]
        }
        
    except Exception as e:
        TASK_STATUS[task_id]["status"] = "error"
        TASK_STATUS[task_id]["error"] = str(e)
    finally:
        # Limpiar archivo temporal
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


@app.get("/api/config")
async def get_config():
    """Devuelve la configuración pública necesaria para el cliente web."""
    return JSONResponse(content={"recaptcha_site_key": settings.RECAPTCHA_SITE_KEY})

@app.post("/api/process")
async def process_document(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    recaptcha_token: str = Form(...)
):
    """
    Recibe un PDF, verifica que no sea un bot con reCAPTCHA, 
    lo guarda temporalmente e inicia el procesamiento en segundo plano.
    """
    # 1. Validación de reCAPTCHA
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": settings.RECAPTCHA_SECRET_KEY,
                "response": recaptcha_token
            }
        )
        recaptcha_data = res.json()
        
        if not recaptcha_data.get("success") or recaptcha_data.get("score", 1.0) < settings.RECAPTCHA_SCORE_THRESHOLD:
            raise HTTPException(status_code=403, detail="Actividad inusual detectada (Bloqueo Bot)")

    # 2. Validación de archivo

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF.")
        
    task_id = str(uuid.uuid4())
    pdf_path = os.path.join(UPLOAD_DIR, f"{task_id}.pdf")
    
    # Guardar archivo localmente
    try:
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando el archivo: {str(e)}")
            
    # Inicializar estado
    TASK_STATUS[task_id] = {
        "status": "pending",
        "progress": 0,
        "status_text": "Iniciando...",
        "filename": file.filename,
        "result": None,
        "stats": None,
        "error": None
    }
    
    # Iniciar tarea en background
    background_tasks.add_task(process_file_background, task_id, pdf_path, file.filename)
    
    return JSONResponse(content={
        "task_id": task_id,
        "message": "Procesamiento iniciado."
    })

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    """
    Devuelve el estado, progreso y resultado (si finalizó) de una tarea.
    """
    if task_id not in TASK_STATUS:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
        
    status_data = TASK_STATUS[task_id]
    
    return JSONResponse(content={
        "task_id": task_id,
        "status": status_data["status"],
        "progress": status_data["progress"],
        "status_text": status_data.get("status_text", ""),
        "filename": status_data["filename"],
        "result": status_data["result"],
        "stats": status_data.get("stats"),
        "error": status_data["error"]
    })

# Servir el Frontend estáticamente en la raíz
app.mount("/", StaticFiles(directory="backend/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
