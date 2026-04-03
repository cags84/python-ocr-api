import os
import re
import fitz  # PyMuPDF
import pymupdf4llm

def optimize_llm_markdown(text: str) -> str:
    """
    Realiza una pasada de optimización profunda ideal para el contexto
    y el conteo de tokens de LLMs, eliminando ruido y compactando el formato.
    """
    if not text:
        return ""
    
    # 1. Eliminar caracteres nulos o de control extraños (mantiene \n, \t)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # 2. Eliminar Bloques Base64 MASIVOS (imágenes o datos embebidos)
    text = re.sub(r'!\[.*?\]\((data:image\/[^;]+;base64,[A-Za-z0-9+/=]+)\)', '[IMAGEN OMITIDA]', text)
    text = re.sub(r'(?<!\S)[A-Za-z0-9+/=_-]{40,}(?!\S)', '[BINARIO_OMITIDO]', text)
    
    # 3. Unir palabras brutalmente separadas por guiones a fin de línea (común en PDFs)
    text = re.sub(r'([a-záéíóúñA-ZÁÉÍÓÚÑ])-\n+([a-záéíóúñA-ZÁÉÍÓÚÑ])', r'\1\2', text)
    
    # 4. Tablas hiper-fragmentadas vacías o separadores inservibles
    text = re.sub(r'(-{4,}\n)+', '---\n', text)
    text = re.sub(r'(?:\|\s*){3,}\|\n', '\n', text) # Filas de tabla | | | vacias
    
    # 5. Cabeceras y pies de páginas huérfanos (Ej: Un \n seguido de "12" \n)
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
    
    # 6. Eliminar ruidos de índices (Ej: .... .... ... )
    text = re.sub(r'(?:\.\s*){5,}', '... ', text)
    
    # 7. Reducir múltiples espacios horizontales a un solo espacio
    text = re.sub(r'[ \t]{2,}', ' ', text)
    
    # 8. Eliminar espacios en blanco antes de un salto de línea
    text = re.sub(r'[ \t]+\n', '\n', text)
    
    # 9. Reducir múltiples saltos de línea consecutivos (más de 3) a máximo 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def process_pdf_with_progress(filepath: str, update_progress_cb=None) -> dict:
    """
    Extrae el contenido de un PDF, aplica optimizaciones finales
    y devuelve resultados y métricas.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"El archivo {filepath} no existe.")
        
    try:
        doc = fitz.open(filepath)
        total_pages = len(doc)
        raw_markdown_parts = []
        
        for i in range(total_pages):
            # Procesar la página actual de forma bruta
            try:
                page_md = pymupdf4llm.to_markdown(doc, pages=[i])
                raw_markdown_parts.append(page_md)
            except Exception as e:
                print(f"Advertencia: fallo al extraer la página {i}: {e}")
                
            # Reportar progreso de extracción (hasta 85%)
            if update_progress_cb:
                percentage = int(((i + 1) / total_pages) * 85)
                update_progress_cb(percentage, "Extrayendo geometría y texto...")
                
        doc.close()
        
        # Texto original para comparativas de LLM
        raw_text = "\n\n".join(raw_markdown_parts)
        
        # Progreso: Optimización Final
        if update_progress_cb:
            update_progress_cb(90, "Aplicando optimizaciones de modelo y compresión de tokens...")
            
        # Limpiar la información innecesaria para el LLM en toda la estructura
        optimized_text = optimize_llm_markdown(raw_text)
        
        if update_progress_cb:
            update_progress_cb(100, "¡Completado!")
            
        return {
            "raw_text": raw_text,
            "optimized_text": optimized_text,
            "raw_len": len(raw_text),
            "opt_len": len(optimized_text)
        }
        
    except Exception as e:
        raise RuntimeError(f"Error procesando el PDF: {str(e)}")
