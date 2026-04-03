<div align="center">
  <h1>🤖 PDF to LLM Optimizer & OCR Processor</h1>
  
  **Autor:** Carlos Guzmán  <br/>
  *Un procesador técnico e inteligente de PDFs diseñado para optimizar el consumo de tokens en Modelos de Lenguaje Grande (LLMs).*

  ---
</div>

## 📌 ¿De qué trata el proyecto?

Este proyecto nació con un solo objetivo en mente: **hacer que tus LLMs consuman menos tokens de "basura" visual y sean mucho más exactos.**

Es una aplicación *full-stack* que toma tus documentos técnicos en PDF (los que a menudo están llenos de molestos diagramas rotos, pies de página o imágenes Base64 ilegibles para inteligencias artificiales de texto) y extrae su estructura hacia un **Markdown cristalino** mediante el motor PyMuPDF. Luego, entra nuestra capa interna destructiva que arrasa con anomalías de formato logrando ahorrar un porcentaje masivo del peso total sin perder semántica útil.

Todo esto, envuelto en una moderna y fresca interfaz web *"Glassmorphism"* impulsada asíncronamente por **FastAPI**.

---

## 🛠️ Herramientas Utilizadas y Requerimientos

La aplicación es extremadamente ligera y prescinde de complicados frameworks en el lado cliente. 

- **Backend / API:** Python 3.10+, [FastAPI](https://fastapi.tiangolo.com/), Uvicorn & Gunicorn.
- **Motor OCR / Parser:** `PyMuPDF` (específicamente la optimización `pymupdf4llm`).
- **Seguridad Web:** `python-dotenv`, CORS Middleware nativo, Google reCAPTCHA v3.
- **Frontend Interfaz:** Vanilla JavaScript, HTML5 semántico, Custom CSS.

---

## 📦 Instrucciones de Instalación multiplataforma

Tener el entorno andando en tu máquina es cuestión de segundos. Abre tu terminal (Terminal en Mac/Linux, o PowerShell en Windows) y sigue estos pasos:

1. Clona el repositorio:**
```bash
git clone https://github.com/cags84/python-ocr-api.git
cd python-ocr-api
```

2. Crea tu Entorno Virtual (Aislado): Crea un entorno virtual para no interferir con las variables globales de tu sistema operativo.

En macOS / Linux:
```bash
python3 -m venv venv
```

En Windows (PowerShell):
```bash
python -m venv venv
```

3. Activa el Entorno Virtual:

En macOS / Linux:
```bash
source venv/bin/activate
```

En Windows (PowerShell o CMD):
```bash
venv\Scripts\activate
```

4. IInstala los requerimientos de la aplicación: Una vez activado (verás un (venv) en el prefijo de tu terminal), ejecuta la descarga de paquetes:

```bash
pip install -r requirements.txt
```

5. Configura el entorno: Copia el archivo de prueba local .env.example para crear tu propio .env.

```bash
cp .env.example .env
```

Asegúrate de conseguir tus llaves públicas gratis desde Google reCAPTCHA Console y colócalas dentro.

🚀 Uso en Desarrollo

Abre una terminal interactiva e instruye a FastAPI que empiece en modo recarga:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Ingresa desde cualquier navegador a http://localhost:8000. Listo. Sube un PDF técnico y extrae el tesoro de su interior al instante.

⚙️ Recomendaciones de Implementación y Optimización (Despliegue)
Este proyecto está construido pensando en servidores y la nube, no solo en tu PC local.

⛔ Cuidado con Funciones Serverless (Como Vercel / AWS Lambda)
El backend utiliza operaciones nativas BackgroundTasks asíncronas para reportar progreso porcentual 0% -> 100% al frontend. Modelos serverless (como Vercel) terminan la ejecución localizadamente en cuanto envían una respuesta, lo cual "matará" tu proceso de extracción a la mitad e impedirá el poll de estados. ¡Evítalos si deseas la barra animada funcional!

✅ Sugerencia Recomendada: Despliegue Permanente (Render, Railway)
Para la mejor experiencia, mantén el backend como un servicio web encendido persistente.

He incluido en la raíz de este proyecto el código de arquitectura en formato archivo render.yaml. Si vinculas este repo con Render.com, el contenedor reconocerá la directiva de despliegue en un clic, instalará gunicorn y abrirá la matriz CORS que tú especifiques para servir en producción. Solo recuerda introducir tu Llave Secreta en el Dashboard, ¡Nunca la dejes en texto plano el GitHub!