import os
from dotenv import load_dotenv

# Cargar variables desde .env si existe
load_dotenv()

class Settings:
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
    
    # Llaves por defecto son las llaves de Prueba públicas de Google (Siempre retornan éxito)
    RECAPTCHA_SITE_KEY: str = os.getenv("RECAPTCHA_SITE_KEY", "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI")
    RECAPTCHA_SECRET_KEY: str = os.getenv("RECAPTCHA_SECRET_KEY", "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe")
    RECAPTCHA_SCORE_THRESHOLD: float = float(os.getenv("RECAPTCHA_SCORE_THRESHOLD", "0.5"))

settings = Settings()
