from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import jwt
import requests
import os

app = FastAPI()

# --- CONFIGURACIÓN CORS ---
# Permite peticiones desde el navegador (Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# URL interna de K8s para buscar la clave pública
OAUTH_SERVER_URL = os.getenv("OAUTH_URL", "http://oauth-service")
PUBLIC_KEY = None

@app.on_event("startup")
def startup_event():
    """Al iniciar, descargamos la clave pública del servidor Go"""
    global PUBLIC_KEY
    try:
        print(f"🔌 [Boot] Conectando a {OAUTH_SERVER_URL}/public-key...")
        response = requests.get(f"{OAUTH_SERVER_URL}/public-key", timeout=10)
        
        if response.status_code == 200:
            PUBLIC_KEY = response.content
            print("✅ [Boot] Clave Pública cargada exitosamente.")
        else:
            print(f"⚠️ [Boot] Error: OAuth server respondió {response.status_code}")
            
    except Exception as e:
        print(f"❌ [Boot] No se pudo conectar con OAuth Server: {e}")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Middleware: Valida matemáticamente la firma del token"""
    token = credentials.credentials
    
    if not PUBLIC_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sistema de Auth no disponible (Sin clave pública)"
        )

    try:
        # Decodificamos y validamos firma RS256
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="El token ha expirado")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")

# --- ENDPOINTS ---

@app.get("/dashboard")
def get_dashboard(user_data: dict = Depends(verify_token)):
    print(f"🔓 Acceso concedido a: {user_data.get('sub')}")
    return {
        "status": "online",
        "secret_data": "CONFIDENCIAL: Los servidores están al 10% de carga.",
        "user_id": user_data.get("sub"),
        "issuer": user_data.get("iss")
    }

@app.get("/health")
def health():
    return {"status": "ok"}