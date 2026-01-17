from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import jwt
import requests
import os
import time # <--- IMPORTANTE: Necesario para esperar entre reintentos

app = FastAPI()

# --- CONFIGURACIÓN CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

OAUTH_SERVER_URL = os.getenv("OAUTH_URL", "http://oauth-service")
PUBLIC_KEY = None

@app.on_event("startup")
def startup_event():
    """Descarga la clave pública con REINTENTOS automáticos (Resiliencia)"""
    global PUBLIC_KEY
    
    print(f"🔌 [Boot] Iniciando conexión con Auth Server en: {OAUTH_SERVER_URL}")
    
    while PUBLIC_KEY is None:
        try:
            print(f"   🔄 Intentando obtener clave pública...")
            response = requests.get(f"{OAUTH_SERVER_URL}/public-key", timeout=5)
            
            if response.status_code == 200:
                PUBLIC_KEY = response.content
                print("✅ [Boot] Clave Pública cargada exitosamente. ¡Sistema listo!")
            else:
                print(f"⚠️ [Boot] El servidor respondió {response.status_code}. Reintentando en 3s...")
                time.sleep(3)
                
        except requests.exceptions.ConnectionError:
            print(f"❌ [Boot] Auth Server no responde (Connection Refused). ¿Está arrancando? Reintentando en 3s...")
            time.sleep(3)
        except Exception as e:
            print(f"❌ [Boot] Error inesperado: {e}. Reintentando en 3s...")
            time.sleep(3)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    
    # Si por algún milagro llegamos aquí sin clave, intentamos una vez más (Lazy Loading)
    if not PUBLIC_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El sistema de Auth aún no está listo (Esperando clave pública)"
        )

    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="El token ha expirado")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")

# --- ENDPOINTS ---

@app.get("/dashboard")
def get_dashboard(user_data: dict = Depends(verify_token)):
    return {
        "status": "online",
        "secret_data": "CONFIDENCIAL: Los servidores están al 10% de carga.",
        "user_id": user_data.get("sub"),
        "issuer": user_data.get("iss")
    }

@app.get("/health")
def health():
    # Health check simple para Kubernetes
    return {"status": "ok"}