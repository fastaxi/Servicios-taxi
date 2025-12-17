from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import os
import logging
import secrets
from pathlib import Path
from urllib.parse import urlparse
from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId
import csv
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# Simple in-memory cache
class SimpleCache:
    """Cache simple en memoria para datos consultados frecuentemente"""
    def __init__(self):
        self._cache = {}
        self._ttl = {}  # Time-to-live para cada key
    
    def get(self, key: str):
        """Obtener valor del cache si existe y no ha expirado"""
        if key in self._cache:
            # Verificar si no ha expirado (TTL de 5 minutos)
            if key in self._ttl and datetime.utcnow() < self._ttl[key]:
                return self._cache[key]
            else:
                # Expirado, eliminar
                self.delete(key)
        return None
    
    def set(self, key: str, value, ttl_minutes: int = 5):
        """Guardar valor en cache con TTL"""
        self._cache[key] = value
        self._ttl[key] = datetime.utcnow() + timedelta(minutes=ttl_minutes)
    
    def delete(self, key: str):
        """Eliminar valor del cache"""
        if key in self._cache:
            del self._cache[key]
        if key in self._ttl:
            del self._ttl[key]
    
    def clear(self):
        """Limpiar todo el cache"""
        self._cache.clear()
        self._ttl.clear()

# Instancia global del cache
cache = SimpleCache()

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env', override=False)

# MongoDB connection - Compatible con desarrollo y producción
mongo_url = os.getenv('MONGO_URL') or os.getenv('MONGODB_URI')
db_name = os.getenv('DB_NAME') or os.getenv('MONGODB_DB_NAME')

# Validar configuración de MongoDB
if not mongo_url:
    raise ValueError("MONGO_URL or MONGODB_URI must be set in environment variables")

if not db_name:
    # En producción, extraer el nombre de la base de datos de la URL si no está especificado
    if 'mongodb+srv://' in mongo_url or 'mongodb://' in mongo_url:
        # Intentar extraer el nombre de la BD de la URL
        parsed = urlparse(mongo_url)
        if parsed.path and len(parsed.path) > 1:
            db_name = parsed.path[1:].split('?')[0]
            print(f"[STARTUP] Database name extracted from URL: {db_name}")
    
    if not db_name:
        raise ValueError("DB_NAME or MONGODB_DB_NAME must be set in environment variables")

# Log configuration for debugging
print(f"[STARTUP] Connecting to MongoDB...")
print(f"[STARTUP] Database: {db_name}")
print(f"[STARTUP] MongoDB URL type: {'Atlas' if 'mongodb+srv://' in mongo_url else 'Local'}")

try:
    # Configuración optimizada para MongoDB Atlas y local
    client = AsyncIOMotorClient(
        mongo_url,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000,
        maxPoolSize=50,
        minPoolSize=10
    )
    db = client[db_name]
    print("[STARTUP] MongoDB connection initialized successfully")
except Exception as e:
    print(f"[STARTUP ERROR] Failed to connect to MongoDB: {e}")
    raise

# Security
# SECRET_KEY debe estar en .env o variables de entorno
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    # En desarrollo, generar una clave temporal (NO USAR EN PRODUCCIÓN)
    SECRET_KEY = secrets.token_hex(32)
    print("[STARTUP WARNING] SECRET_KEY not set, using temporary key for development")
    print("[STARTUP WARNING] Set SECRET_KEY environment variable for production!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Configure logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main app - TaxiFast Multi-tenant SaaS Platform
app = FastAPI(title="TaxiFast API", version="2.0.0", description="Multi-tenant taxi management SaaS platform")
api_router = APIRouter(prefix="/api")

# Root health check endpoint for deployment systems
@app.get("/")
async def root_health_check():
    """Health check endpoint for deployment verification"""
    return {
        "status": "healthy",
        "service": "taxifast-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

# API health check endpoint
@app.get("/health")
async def health_check():
    """Detailed health check with database connectivity"""
    try:
        # Test database connection
        await db.command("ping")
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# Helper function for ObjectId
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

# ==========================================
# ORGANIZATION MODELS (Multi-tenant SaaS)
# ==========================================
class OrganizationBase(BaseModel):
    nombre: str  # Nombre de la empresa de taxis (ej: "Taxi Tineo", "Radio Taxi Madrid")
    slug: Optional[str] = None  # URL-friendly identifier (auto-generated if not provided)
    cif: Optional[str] = ""  # CIF/NIF de la empresa
    direccion: Optional[str] = ""
    codigo_postal: Optional[str] = ""
    localidad: Optional[str] = ""
    provincia: Optional[str] = ""
    telefono: Optional[str] = ""
    email: Optional[str] = ""
    web: Optional[str] = ""
    logo_base64: Optional[str] = None  # Logo de la empresa en base64
    color_primario: Optional[str] = "#0066CC"  # Color principal de la marca
    color_secundario: Optional[str] = "#FFD700"  # Color secundario
    notas: Optional[str] = ""
    activa: bool = True  # Si la organización está activa

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    nombre: Optional[str] = None
    slug: Optional[str] = None
    cif: Optional[str] = None
    direccion: Optional[str] = None
    codigo_postal: Optional[str] = None
    localidad: Optional[str] = None
    provincia: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    web: Optional[str] = None
    logo_base64: Optional[str] = None
    color_primario: Optional[str] = None
    color_secundario: Optional[str] = None
    notas: Optional[str] = None
    activa: Optional[bool] = None

class OrganizationResponse(OrganizationBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Estadísticas calculadas
    total_taxistas: Optional[int] = 0
    total_vehiculos: Optional[int] = 0
    total_clientes: Optional[int] = 0

    class Config:
        from_attributes = True

# ==========================================
# USER MODELS (Multi-tenant aware)
# ==========================================
class UserBase(BaseModel):
    username: str
    nombre: str
    role: str = "taxista"  # superadmin, admin or taxista
    licencia: Optional[str] = None
    vehiculo_id: Optional[str] = None
    vehiculo_matricula: Optional[str] = None  # Para mostrar sin hacer joins
    organization_id: Optional[str] = None  # ID de la organización (null para superadmin)

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    created_at: datetime
    organization_nombre: Optional[str] = None  # Nombre de la organización para display

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# ==========================================
# COMPANY/CLIENT MODELS (Multi-tenant aware)
# ==========================================
class CompanyBase(BaseModel):
    nombre: str
    cif: Optional[str] = ""
    direccion: Optional[str] = ""
    codigo_postal: Optional[str] = ""
    localidad: Optional[str] = ""
    provincia: Optional[str] = ""
    telefono: Optional[str] = ""
    email: Optional[str] = ""
    numero_cliente: Optional[str] = None
    contacto: Optional[str] = ""
    fecha_alta: Optional[str] = None  # formato dd/mm/yyyy
    notas: Optional[str] = ""
    # organization_id se asigna automáticamente del usuario actual

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: str
    created_at: datetime
    organization_id: Optional[str] = None

    class Config:
        from_attributes = True

class ServiceBase(BaseModel):
    fecha: str
    hora: str
    origen: str
    destino: str
    importe: float  # IVA 10% incluido
    importe_espera: float  # Importe de espera en euros
    importe_total: Optional[float] = None  # Se calcula automáticamente
    kilometros: float
    tipo: str  # "empresa" or "particular"
    empresa_id: Optional[str] = None
    empresa_nombre: Optional[str] = None
    turno_id: Optional[str] = None  # ID del turno asociado
    cobrado: bool = False
    facturar: bool = False

class ServiceCreate(ServiceBase):
    pass

class ServiceResponse(BaseModel):
    id: str
    taxista_id: str
    taxista_nombre: str
    fecha: str
    hora: str
    origen: str
    destino: str
    importe: float
    importe_espera: Optional[float] = 0  # Opcional para compatibilidad con datos antiguos
    importe_total: Optional[float] = 0  # Opcional para compatibilidad con datos antiguos
    kilometros: float
    tipo: str
    empresa_id: Optional[str] = None
    empresa_nombre: Optional[str] = None
    turno_id: Optional[str] = None
    cobrado: Optional[bool] = False
    facturar: Optional[bool] = False
    created_at: datetime
    synced: bool = True
    organization_id: Optional[str] = None  # Multi-tenant support

    class Config:
        from_attributes = True

class ConfigBase(BaseModel):
    nombre_radio_taxi: str
    telefono: str
    web: str
    direccion: Optional[str] = ""
    email: Optional[str] = ""
    logo_base64: Optional[str] = None

class ConfigResponse(ConfigBase):
    id: str
    updated_at: datetime

    class Config:
        from_attributes = True

class ServiceSync(BaseModel):
    services: List[ServiceBase]

# ==========================================
# VEHICULO MODELS (Multi-tenant aware)
# ==========================================
class VehiculoBase(BaseModel):
    matricula: str
    plazas: int
    marca: str
    modelo: str
    km_iniciales: int
    fecha_compra: str  # formato dd/mm/yyyy
    activo: bool = True
    # organization_id se asigna automáticamente del usuario actual

class VehiculoCreate(VehiculoBase):
    pass

class VehiculoResponse(VehiculoBase):
    id: str
    organization_id: Optional[str] = None

    class Config:
        from_attributes = True

# ==========================================
# TURNO MODELS (Multi-tenant aware)
# ==========================================
class TurnoBase(BaseModel):
    taxista_id: str
    taxista_nombre: str
    vehiculo_id: str
    vehiculo_matricula: str
    fecha_inicio: str  # formato dd/mm/yyyy
    hora_inicio: str   # formato HH:mm
    km_inicio: int
    fecha_fin: Optional[str] = None
    hora_fin: Optional[str] = None
    km_fin: Optional[int] = None
    cerrado: bool = False
    liquidado: bool = False
    # organization_id se asigna automáticamente del usuario actual

class TurnoCreate(BaseModel):
    taxista_id: str
    taxista_nombre: str
    vehiculo_id: str
    vehiculo_matricula: str
    fecha_inicio: str
    hora_inicio: str
    km_inicio: int

class TurnoUpdate(BaseModel):
    fecha_inicio: Optional[str] = None
    hora_inicio: Optional[str] = None
    km_inicio: Optional[int] = None
    fecha_fin: Optional[str] = None
    hora_fin: Optional[str] = None
    km_fin: Optional[int] = None
    cerrado: Optional[bool] = None
    liquidado: Optional[bool] = None

class TurnoFinalizarUpdate(BaseModel):
    fecha_fin: str
    hora_fin: str
    km_fin: int
    cerrado: bool = True

class TurnoResponse(TurnoBase):
    id: str
    created_at: datetime
    organization_id: Optional[str] = None
    # Totales calculados
    total_importe_clientes: Optional[float] = 0
    total_importe_particulares: Optional[float] = 0
    total_kilometros: Optional[float] = 0
    cantidad_servicios: Optional[int] = 0

    class Config:
        from_attributes = True

# ==========================================
# AUTH HELPERS (Multi-tenant support)
# ==========================================
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_slug(nombre: str) -> str:
    """Genera un slug URL-friendly a partir del nombre"""
    import re
    # Convertir a minúsculas y reemplazar espacios por guiones
    slug = nombre.lower().strip()
    # Reemplazar caracteres especiales españoles
    replacements = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n', 'ü': 'u'}
    for old, new in replacements.items():
        slug = slug.replace(old, new)
    # Solo permitir alfanuméricos y guiones
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    
    # Verificar que la organización del usuario esté activa (excepto superadmin)
    if user.get("role") != "superadmin" and user.get("organization_id"):
        org = await db.organizations.find_one({"_id": ObjectId(user["organization_id"])})
        if org and not org.get("activa", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu organización está desactivada. Contacta con el administrador."
            )
    
    return user

async def get_current_admin(current_user: dict = Depends(get_current_user)):
    """Permite acceso a admin y superadmin"""
    if current_user.get("role") not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_current_superadmin(current_user: dict = Depends(get_current_user)):
    """Solo permite acceso a superadmin"""
    if current_user.get("role") != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin permissions required"
        )
    return current_user

def get_user_organization_id(user: dict) -> Optional[str]:
    """Obtiene el organization_id del usuario actual"""
    return user.get("organization_id")

def is_superadmin(user: dict) -> bool:
    """Verifica si el usuario es superadmin"""
    return user.get("role") == "superadmin"

async def get_org_filter(user: dict) -> dict:
    """
    Retorna el filtro de organización para queries.
    Superadmin ve todo, otros usuarios solo ven datos de su organización.
    """
    if is_superadmin(user):
        return {}  # Sin filtro, ve todo
    
    org_id = get_user_organization_id(user)
    if org_id:
        return {"organization_id": org_id}
    return {"organization_id": None}  # Datos legacy sin organización

# ==========================================
# AUTH ENDPOINTS
# ==========================================
@api_router.post("/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    user = await db.users.find_one({"username": user_login.username})
    if not user or not verify_password(user_login.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Obtener nombre de la organización si existe
    org_nombre = None
    if user.get("organization_id"):
        org = await db.organizations.find_one({"_id": ObjectId(user["organization_id"])})
        if org:
            org_nombre = org.get("nombre")
    
    access_token = create_access_token(data={"sub": user["username"]})
    user_response = UserResponse(
        id=str(user["_id"]),
        username=user["username"],
        nombre=user["nombre"],
        role=user["role"],
        organization_id=user.get("organization_id"),
        organization_nombre=org_nombre,
        created_at=user["created_at"]
    )
    return Token(access_token=access_token, token_type="bearer", user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    # Obtener nombre de la organización si existe
    org_nombre = None
    if current_user.get("organization_id"):
        org = await db.organizations.find_one({"_id": ObjectId(current_user["organization_id"])})
        if org:
            org_nombre = org.get("nombre")
    
    return UserResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        nombre=current_user["nombre"],
        role=current_user["role"],
        organization_id=current_user.get("organization_id"),
        organization_nombre=org_nombre,
        licencia=current_user.get("licencia"),
        vehiculo_id=current_user.get("vehiculo_id"),
        vehiculo_matricula=current_user.get("vehiculo_matricula"),
        created_at=current_user["created_at"]
    )

# ==========================================
# ORGANIZATION ENDPOINTS (Superadmin only)
# ==========================================
@api_router.post("/organizations", response_model=OrganizationResponse)
async def create_organization(org: OrganizationCreate, current_user: dict = Depends(get_current_superadmin)):
    """Crear nueva organización (solo superadmin)"""
    org_dict = org.dict()
    
    # Generar slug si no se proporciona
    if not org_dict.get("slug"):
        org_dict["slug"] = generate_slug(org_dict["nombre"])
    
    # Verificar slug único
    existing = await db.organizations.find_one({"slug": org_dict["slug"]})
    if existing:
        # Agregar número al slug
        count = await db.organizations.count_documents({"slug": {"$regex": f"^{org_dict['slug']}"}})
        org_dict["slug"] = f"{org_dict['slug']}-{count + 1}"
    
    org_dict["created_at"] = datetime.utcnow()
    org_dict["updated_at"] = datetime.utcnow()
    
    result = await db.organizations.insert_one(org_dict)
    created_org = await db.organizations.find_one({"_id": result.inserted_id})
    
    return OrganizationResponse(
        id=str(created_org["_id"]),
        **{k: v for k, v in created_org.items() if k != "_id"},
        total_taxistas=0,
        total_vehiculos=0,
        total_clientes=0
    )

@api_router.get("/organizations", response_model=List[OrganizationResponse])
async def get_organizations(
    current_user: dict = Depends(get_current_superadmin),
    activa: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo")
):
    """Listar todas las organizaciones (solo superadmin)"""
    query = {}
    if activa is not None:
        query["activa"] = activa
    
    organizations = await db.organizations.find(query).sort("created_at", -1).to_list(1000)
    
    result = []
    for org in organizations:
        org_id = str(org["_id"])
        # Contar estadísticas
        total_taxistas = await db.users.count_documents({"organization_id": org_id, "role": "taxista"})
        total_vehiculos = await db.vehiculos.count_documents({"organization_id": org_id})
        total_clientes = await db.companies.count_documents({"organization_id": org_id})
        
        result.append(OrganizationResponse(
            id=org_id,
            **{k: v for k, v in org.items() if k != "_id"},
            total_taxistas=total_taxistas,
            total_vehiculos=total_vehiculos,
            total_clientes=total_clientes
        ))
    
    return result

@api_router.get("/organizations/{org_id}", response_model=OrganizationResponse)
async def get_organization(org_id: str, current_user: dict = Depends(get_current_superadmin)):
    """Obtener detalle de una organización (solo superadmin)"""
    org = await db.organizations.find_one({"_id": ObjectId(org_id)})
    if not org:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    # Contar estadísticas
    total_taxistas = await db.users.count_documents({"organization_id": org_id, "role": "taxista"})
    total_vehiculos = await db.vehiculos.count_documents({"organization_id": org_id})
    total_clientes = await db.companies.count_documents({"organization_id": org_id})
    
    return OrganizationResponse(
        id=str(org["_id"]),
        **{k: v for k, v in org.items() if k != "_id"},
        total_taxistas=total_taxistas,
        total_vehiculos=total_vehiculos,
        total_clientes=total_clientes
    )

@api_router.put("/organizations/{org_id}", response_model=OrganizationResponse)
async def update_organization(org_id: str, org_update: OrganizationUpdate, current_user: dict = Depends(get_current_superadmin)):
    """Actualizar organización (solo superadmin)"""
    existing = await db.organizations.find_one({"_id": ObjectId(org_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    update_data = {k: v for k, v in org_update.dict().items() if v is not None}
    
    # Si se actualiza el nombre y no el slug, regenerar slug
    if "nombre" in update_data and "slug" not in update_data:
        update_data["slug"] = generate_slug(update_data["nombre"])
    
    update_data["updated_at"] = datetime.utcnow()
    
    await db.organizations.update_one(
        {"_id": ObjectId(org_id)},
        {"$set": update_data}
    )
    
    updated_org = await db.organizations.find_one({"_id": ObjectId(org_id)})
    
    # Contar estadísticas
    total_taxistas = await db.users.count_documents({"organization_id": org_id, "role": "taxista"})
    total_vehiculos = await db.vehiculos.count_documents({"organization_id": org_id})
    total_clientes = await db.companies.count_documents({"organization_id": org_id})
    
    return OrganizationResponse(
        id=str(updated_org["_id"]),
        **{k: v for k, v in updated_org.items() if k != "_id"},
        total_taxistas=total_taxistas,
        total_vehiculos=total_vehiculos,
        total_clientes=total_clientes
    )

@api_router.delete("/organizations/{org_id}")
async def delete_organization(org_id: str, current_user: dict = Depends(get_current_superadmin)):
    """Eliminar organización y todos sus datos (solo superadmin)"""
    org = await db.organizations.find_one({"_id": ObjectId(org_id)})
    if not org:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    # Eliminar todos los datos relacionados
    deleted_users = await db.users.delete_many({"organization_id": org_id})
    deleted_companies = await db.companies.delete_many({"organization_id": org_id})
    deleted_vehiculos = await db.vehiculos.delete_many({"organization_id": org_id})
    deleted_turnos = await db.turnos.delete_many({"organization_id": org_id})
    deleted_services = await db.services.delete_many({"organization_id": org_id})
    
    # Eliminar la organización
    await db.organizations.delete_one({"_id": ObjectId(org_id)})
    
    return {
        "message": f"Organización '{org['nombre']}' eliminada correctamente",
        "deleted": {
            "users": deleted_users.deleted_count,
            "companies": deleted_companies.deleted_count,
            "vehiculos": deleted_vehiculos.deleted_count,
            "turnos": deleted_turnos.deleted_count,
            "services": deleted_services.deleted_count
        }
    }

# Endpoint para crear admin de organización (superadmin)
@api_router.post("/organizations/{org_id}/admin", response_model=UserResponse)
async def create_organization_admin(
    org_id: str,
    user: UserCreate,
    current_user: dict = Depends(get_current_superadmin)
):
    """Crear administrador para una organización (solo superadmin)"""
    # Verificar que la organización existe
    org = await db.organizations.find_one({"_id": ObjectId(org_id)})
    if not org:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    # Verificar username único
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user_dict = user.dict()
    user_dict["password"] = get_password_hash(user_dict["password"])
    user_dict["role"] = "admin"  # Forzar rol admin
    user_dict["organization_id"] = org_id
    user_dict["created_at"] = datetime.utcnow()
    
    result = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    
    return UserResponse(
        id=str(created_user["_id"]),
        username=created_user["username"],
        nombre=created_user["nombre"],
        role=created_user["role"],
        organization_id=created_user.get("organization_id"),
        organization_nombre=org.get("nombre"),
        created_at=created_user["created_at"]
    )

# ==========================================
# USER ENDPOINTS (Multi-tenant - admin only)
# ==========================================
@api_router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, current_user: dict = Depends(get_current_admin)):
    """Crear taxista - se asigna automáticamente a la organización del admin"""
    # Check if user exists
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    user_dict = user.dict()
    user_dict["password"] = get_password_hash(user_dict["password"])
    user_dict["created_at"] = datetime.utcnow()
    
    # Multi-tenant: Asignar organization_id del admin que crea el usuario
    # Superadmin puede crear usuarios sin organización
    if not is_superadmin(current_user):
        user_dict["organization_id"] = get_user_organization_id(current_user)
    elif not user_dict.get("organization_id"):
        user_dict["organization_id"] = None
    
    result = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    
    # Obtener nombre de organización
    org_nombre = None
    if created_user.get("organization_id"):
        org = await db.organizations.find_one({"_id": ObjectId(created_user["organization_id"])})
        if org:
            org_nombre = org.get("nombre")
    
    return UserResponse(
        id=str(created_user["_id"]),
        username=created_user["username"],
        nombre=created_user["nombre"],
        role=created_user["role"],
        licencia=created_user.get("licencia"),
        vehiculo_id=created_user.get("vehiculo_id"),
        vehiculo_matricula=created_user.get("vehiculo_matricula"),
        organization_id=created_user.get("organization_id"),
        organization_nombre=org_nombre,
        created_at=created_user["created_at"]
    )

@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(get_current_admin)):
    """Listar taxistas - filtrado por organización del admin"""
    # Multi-tenant filter
    org_filter = await get_org_filter(current_user)
    query = {"role": "taxista", **org_filter}
    
    users = await db.users.find(
        query,
        {"password": 0}
    ).to_list(1000)
    
    # Obtener nombres de organizaciones
    org_names = {}
    org_ids = set(u.get("organization_id") for u in users if u.get("organization_id"))
    for org_id in org_ids:
        org = await db.organizations.find_one({"_id": ObjectId(org_id)})
        if org:
            org_names[org_id] = org.get("nombre")
    
    return [
        UserResponse(
            id=str(user["_id"]),
            username=user["username"],
            nombre=user["nombre"],
            role=user["role"],
            licencia=user.get("licencia"),
            vehiculo_id=user.get("vehiculo_id"),
            vehiculo_matricula=user.get("vehiculo_matricula"),
            organization_id=user.get("organization_id"),
            organization_nombre=org_names.get(user.get("organization_id")),
            created_at=user["created_at"]
        )
        for user in users
    ]

class UserUpdate(BaseModel):
    username: str
    nombre: str
    role: str = "taxista"
    licencia: Optional[str] = None
    vehiculo_id: Optional[str] = None
    vehiculo_matricula: Optional[str] = None
    password: Optional[str] = None

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user: UserUpdate, current_user: dict = Depends(get_current_admin)):
    user_dict = user.dict(exclude={'password'}, exclude_none=True)
    
    # Si se proporciona una nueva contraseña, hashearla
    if user.password:
        user_dict["password"] = get_password_hash(user.password)
    
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": user_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
    return UserResponse(
        id=str(updated_user["_id"]),
        username=updated_user["username"],
        nombre=updated_user["nombre"],
        role=updated_user["role"],
        licencia=updated_user.get("licencia"),
        vehiculo_id=updated_user.get("vehiculo_id"),
        vehiculo_matricula=updated_user.get("vehiculo_matricula"),
        created_at=updated_user["created_at"]
    )

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_admin)):
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

# ==========================================
# COMPANY/CLIENT ENDPOINTS (Multi-tenant)
# ==========================================
@api_router.post("/companies", response_model=CompanyResponse)
async def create_company(company: CompanyCreate, current_user: dict = Depends(get_current_admin)):
    """Crear cliente/empresa - se asigna automáticamente a la organización del admin"""
    company_dict = company.dict()
    
    # Multi-tenant: Asignar organization_id
    org_id = get_user_organization_id(current_user) if not is_superadmin(current_user) else None
    company_dict["organization_id"] = org_id
    
    # Validar numero_cliente único dentro de la organización
    if company_dict.get("numero_cliente"):
        query = {"numero_cliente": company_dict["numero_cliente"]}
        if org_id:
            query["organization_id"] = org_id
        existing = await db.companies.find_one(query)
        if existing:
            raise HTTPException(status_code=400, detail="Número de cliente ya existe")
    
    company_dict["created_at"] = datetime.utcnow()
    
    result = await db.companies.insert_one(company_dict)
    created_company = await db.companies.find_one({"_id": result.inserted_id})
    
    return CompanyResponse(
        id=str(created_company["_id"]),
        **{k: v for k, v in created_company.items() if k != "_id"}
    )

@api_router.get("/companies", response_model=List[CompanyResponse])
async def get_companies(current_user: dict = Depends(get_current_user)):
    """Listar clientes/empresas - filtrado por organización"""
    # Multi-tenant filter
    org_filter = await get_org_filter(current_user)
    
    companies = await db.companies.find(org_filter).to_list(1000)
    return [
        CompanyResponse(
            id=str(company["_id"]),
            **{k: v for k, v in company.items() if k != "_id"}
        )
        for company in companies
    ]

@api_router.put("/companies/{company_id}", response_model=CompanyResponse)
async def update_company(company_id: str, company: CompanyCreate, current_user: dict = Depends(get_current_admin)):
    """Actualizar cliente/empresa - solo de la propia organización"""
    company_dict = company.dict()
    
    # Multi-tenant: Verificar que la empresa pertenece a la organización del usuario
    org_filter = await get_org_filter(current_user)
    existing_company = await db.companies.find_one({"_id": ObjectId(company_id), **org_filter})
    if not existing_company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Validar numero_cliente único dentro de la organización (excepto el actual)
    if company_dict.get("numero_cliente"):
        query = {
            "numero_cliente": company_dict["numero_cliente"],
            "_id": {"$ne": ObjectId(company_id)},
            **org_filter
        }
        existing = await db.companies.find_one(query)
        if existing:
            raise HTTPException(status_code=400, detail="Número de cliente ya existe")
    
    result = await db.companies.update_one(
        {"_id": ObjectId(company_id)},
        {"$set": company_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    
    updated_company = await db.companies.find_one({"_id": ObjectId(company_id)})
    return CompanyResponse(
        id=str(updated_company["_id"]),
        **{k: v for k, v in updated_company.items() if k != "_id"}
    )

@api_router.delete("/companies/{company_id}")
async def delete_company(company_id: str, current_user: dict = Depends(get_current_admin)):
    """Eliminar cliente/empresa - solo de la propia organización"""
    # Multi-tenant: Verificar que la empresa pertenece a la organización
    org_filter = await get_org_filter(current_user)
    result = await db.companies.delete_one({"_id": ObjectId(company_id), **org_filter})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"message": "Company deleted successfully"}

# ==========================================
# VEHICULO ENDPOINTS (Multi-tenant)
# ==========================================
@api_router.post("/vehiculos", response_model=VehiculoResponse)
async def create_vehiculo(vehiculo: VehiculoCreate, current_user: dict = Depends(get_current_admin)):
    """Crear vehículo - se asigna a la organización del admin"""
    # Multi-tenant: Asignar organization_id
    org_id = get_user_organization_id(current_user) if not is_superadmin(current_user) else None
    
    # Verificar que la matrícula no exista dentro de la organización
    query = {"matricula": vehiculo.matricula}
    if org_id:
        query["organization_id"] = org_id
    existing = await db.vehiculos.find_one(query)
    if existing:
        raise HTTPException(status_code=400, detail="La matrícula ya existe")
    
    vehiculo_dict = vehiculo.dict()
    vehiculo_dict["organization_id"] = org_id
    vehiculo_dict["created_at"] = datetime.utcnow()
    
    result = await db.vehiculos.insert_one(vehiculo_dict)
    created_vehiculo = await db.vehiculos.find_one({"_id": result.inserted_id})
    
    return VehiculoResponse(
        id=str(created_vehiculo["_id"]),
        **{k: v for k, v in created_vehiculo.items() if k != "_id"}
    )

@api_router.get("/vehiculos", response_model=List[VehiculoResponse])
async def get_vehiculos(current_user: dict = Depends(get_current_user)):
    """Listar vehículos - filtrado por organización"""
    org_filter = await get_org_filter(current_user)
    vehiculos = await db.vehiculos.find(org_filter).to_list(1000)
    return [
        VehiculoResponse(
            id=str(vehiculo["_id"]),
            **{k: v for k, v in vehiculo.items() if k != "_id"}
        )
        for vehiculo in vehiculos
    ]

@api_router.put("/vehiculos/{vehiculo_id}", response_model=VehiculoResponse)
async def update_vehiculo(vehiculo_id: str, vehiculo: VehiculoCreate, current_user: dict = Depends(get_current_admin)):
    """Actualizar vehículo - solo de la propia organización"""
    org_filter = await get_org_filter(current_user)
    
    # Verificar que el vehículo pertenece a la organización
    existing_vehiculo = await db.vehiculos.find_one({"_id": ObjectId(vehiculo_id), **org_filter})
    if not existing_vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo not found")
    
    # Verificar que la matrícula no esté en uso por otro vehículo de la organización
    existing = await db.vehiculos.find_one({
        "matricula": vehiculo.matricula,
        "_id": {"$ne": ObjectId(vehiculo_id)},
        **org_filter
    })
    if existing:
        raise HTTPException(status_code=400, detail="La matrícula ya existe")
    
    vehiculo_dict = vehiculo.dict()
    result = await db.vehiculos.update_one(
        {"_id": ObjectId(vehiculo_id)},
        {"$set": vehiculo_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Vehículo not found")
    
    updated_vehiculo = await db.vehiculos.find_one({"_id": ObjectId(vehiculo_id)})
    return VehiculoResponse(
        id=str(updated_vehiculo["_id"]),
        **{k: v for k, v in updated_vehiculo.items() if k != "_id"}
    )

@api_router.delete("/vehiculos/{vehiculo_id}")
async def delete_vehiculo(vehiculo_id: str, current_user: dict = Depends(get_current_admin)):
    """Eliminar vehículo - solo de la propia organización"""
    org_filter = await get_org_filter(current_user)
    result = await db.vehiculos.delete_one({"_id": ObjectId(vehiculo_id), **org_filter})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Vehículo not found")
    return {"message": "Vehículo deleted successfully"}

# ==========================================
# TURNO ENDPOINTS (Multi-tenant)
# ==========================================
@api_router.post("/turnos", response_model=TurnoResponse)
async def create_turno(turno: TurnoCreate, current_user: dict = Depends(get_current_user)):
    """Crear turno - se asigna a la organización del usuario"""
    # Validar que no tenga un turno abierto
    existing_turno = await db.turnos.find_one({
        "taxista_id": str(current_user["_id"]),
        "cerrado": False
    })
    if existing_turno:
        raise HTTPException(status_code=400, detail="Ya tienes un turno abierto. Debes finalizarlo antes de abrir uno nuevo.")
    
    turno_dict = turno.dict()
    # Override taxista info with current user
    turno_dict["taxista_id"] = str(current_user["_id"])
    turno_dict["taxista_nombre"] = current_user["nombre"]
    turno_dict["created_at"] = datetime.utcnow()
    turno_dict["cerrado"] = False
    
    # Multi-tenant: Asignar organization_id del usuario
    turno_dict["organization_id"] = get_user_organization_id(current_user)
    
    result = await db.turnos.insert_one(turno_dict)
    created_turno = await db.turnos.find_one({"_id": result.inserted_id})
    
    return TurnoResponse(
        id=str(created_turno["_id"]),
        **{k: v for k, v in created_turno.items() if k != "_id"}
    )

# HELPER FUNCTION: Batch fetch servicios para turnos (optimiza N+1 queries)
async def get_turnos_with_servicios(turnos: list, include_servicios_detail: bool = False) -> list:
    """
    Optimización: Trae todos los servicios de múltiples turnos en 1 query
    en vez de hacer 1 query por cada turno (N+1 problem)
    
    Args:
        turnos: Lista de turnos
        include_servicios_detail: Si True, incluye la lista completa de servicios en cada turno
    """
    if not turnos:
        return []
    
    # Batch query - traer todos los servicios de una vez
    turno_ids = [str(t["_id"]) for t in turnos]
    all_servicios = await db.services.find(
        {"turno_id": {"$in": turno_ids}}
    ).to_list(100000)
    
    # Agrupar servicios por turno_id en memoria
    servicios_by_turno = {}
    for servicio in all_servicios:
        turno_id = servicio["turno_id"]
        if turno_id not in servicios_by_turno:
            servicios_by_turno[turno_id] = []
        servicios_by_turno[turno_id].append(servicio)
    
    # Calcular totales para cada turno
    result = []
    for turno in turnos:
        turno_id = str(turno["_id"])
        servicios = servicios_by_turno.get(turno_id, [])
        
        total_clientes = sum(s.get("importe_total", s.get("importe", 0)) for s in servicios if s.get("tipo") == "empresa")
        total_particulares = sum(s.get("importe_total", s.get("importe", 0)) for s in servicios if s.get("tipo") == "particular")
        total_km = sum(s.get("kilometros", 0) for s in servicios)
        
        turno_data = {
            **turno,
            "turno_id": turno_id,
            "total_clientes": total_clientes,
            "total_particulares": total_particulares,
            "total_km": total_km,
            "cantidad_servicios": len(servicios)
        }
        
        # Si se solicita, incluir el detalle completo de servicios
        if include_servicios_detail:
            turno_data["servicios"] = servicios
        
        result.append(turno_data)
    
    return result

@api_router.get("/turnos", response_model=List[TurnoResponse])
async def get_turnos(
    current_user: dict = Depends(get_current_user),
    taxista_id: Optional[str] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    cerrado: Optional[bool] = Query(None),
    liquidado: Optional[bool] = Query(None),
    limit: int = Query(500, le=1000, description="Límite de resultados")
):
    """Listar turnos - filtrado por organización"""
    # Multi-tenant filter
    org_filter = await get_org_filter(current_user)
    query = {**org_filter}
    
    # Si no es admin/superadmin, solo sus propios turnos
    if current_user.get("role") not in ["admin", "superadmin"]:
        query["taxista_id"] = str(current_user["_id"])
    elif taxista_id:
        query["taxista_id"] = taxista_id
    
    # Filtro por fechas
    if fecha_inicio:
        query["fecha_inicio"] = {"$gte": fecha_inicio}
    if fecha_fin:
        if "fecha_inicio" in query:
            query["fecha_inicio"]["$lte"] = fecha_fin
        else:
            query["fecha_inicio"] = {"$lte": fecha_fin}
    
    # Filtros por estado
    if cerrado is not None:
        query["cerrado"] = cerrado
    if liquidado is not None:
        query["liquidado"] = liquidado
    
    # Validar y ajustar límite
    if limit <= 0:
        limit = 500  # Default
    elif limit > 1000:
        limit = 1000  # Maximum
    
    turnos = await db.turnos.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    
    # OPTIMIZACIÓN: Batch query - traer todos los servicios de una vez
    if turnos:
        turno_ids = [str(t["_id"]) for t in turnos]
        all_servicios = await db.services.find(
            {"turno_id": {"$in": turno_ids}}
        ).to_list(100000)
        
        # Agrupar servicios por turno_id en memoria
        servicios_by_turno = {}
        for servicio in all_servicios:
            turno_id = servicio["turno_id"]
            if turno_id not in servicios_by_turno:
                servicios_by_turno[turno_id] = []
            servicios_by_turno[turno_id].append(servicio)
    else:
        servicios_by_turno = {}
    
    # Calcular totales para cada turno
    result = []
    for turno in turnos:
        turno_id = str(turno["_id"])
        
        # Obtener servicios del turno desde el diccionario
        servicios = servicios_by_turno.get(turno_id, [])
        
        total_clientes = sum(s.get("importe_total", s.get("importe", 0)) for s in servicios if s.get("tipo") == "empresa")
        total_particulares = sum(s.get("importe_total", s.get("importe", 0)) for s in servicios if s.get("tipo") == "particular")
        
        # Calcular km del turno: usar km_fin si existe, sino usar suma de km de servicios
        if turno.get("km_fin") is not None:
            total_km = turno["km_fin"] - turno["km_inicio"]
        else:
            total_km = sum(s.get("kilometros", 0) for s in servicios)
        
        result.append(TurnoResponse(
            id=turno_id,
            **{k: v for k, v in turno.items() if k != "_id"},
            total_importe_clientes=total_clientes,
            total_importe_particulares=total_particulares,
            total_kilometros=total_km,
            cantidad_servicios=len(servicios)
        ))
    
    return result

@api_router.get("/turnos/activo")
async def get_turno_activo(current_user: dict = Depends(get_current_user)):
    turno = await db.turnos.find_one({
        "taxista_id": str(current_user["_id"]),
        "cerrado": False
    })
    
    if not turno:
        return None
    
    turno_id = str(turno["_id"])
    servicios = await db.services.find({"turno_id": turno_id}).to_list(1000)
    
    total_clientes = sum(s.get("importe_total", s.get("importe", 0)) for s in servicios if s.get("tipo") == "empresa")
    total_particulares = sum(s.get("importe_total", s.get("importe", 0)) for s in servicios if s.get("tipo") == "particular")
    
    # Calcular km del turno: usar km_fin si existe, sino usar suma de km de servicios
    if turno.get("km_fin") is not None:
        total_km = turno["km_fin"] - turno["km_inicio"]
    else:
        total_km = sum(s.get("kilometros", 0) for s in servicios)
    
    return TurnoResponse(
        id=turno_id,
        **{k: v for k, v in turno.items() if k != "_id"},
        total_importe_clientes=total_clientes,
        total_importe_particulares=total_particulares,
        total_kilometros=total_km,
        cantidad_servicios=len(servicios)
    )

@api_router.put("/turnos/{turno_id}/finalizar", response_model=TurnoResponse)
async def finalizar_turno(turno_id: str, turno_update: TurnoFinalizarUpdate, current_user: dict = Depends(get_current_user)):
    existing_turno = await db.turnos.find_one({"_id": ObjectId(turno_id)})
    if not existing_turno:
        raise HTTPException(status_code=404, detail="Turno not found")
    
    # Solo el taxista dueño o admin pueden finalizar
    if current_user.get("role") != "admin" and existing_turno["taxista_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="No autorizado")
    
    update_dict = turno_update.dict()
    await db.turnos.update_one(
        {"_id": ObjectId(turno_id)},
        {"$set": update_dict}
    )
    
    updated_turno = await db.turnos.find_one({"_id": ObjectId(turno_id)})
    
    # Calcular totales
    servicios = await db.services.find({"turno_id": turno_id}).to_list(1000)
    total_clientes = sum(s.get("importe_total", s.get("importe", 0)) for s in servicios if s.get("tipo") == "empresa")
    total_particulares = sum(s.get("importe_total", s.get("importe", 0)) for s in servicios if s.get("tipo") == "particular")
    total_km = sum(s.get("kilometros", 0) for s in servicios)
    
    return TurnoResponse(
        id=turno_id,
        **{k: v for k, v in updated_turno.items() if k != "_id"},
        total_importe_clientes=total_clientes,
        total_importe_particulares=total_particulares,
        total_kilometros=total_km,
        cantidad_servicios=len(servicios)
    )

@api_router.put("/turnos/{turno_id}", response_model=TurnoResponse)
async def update_turno(turno_id: str, turno_update: TurnoUpdate, current_user: dict = Depends(get_current_admin)):
    """Actualizar turno (solo admin). Permite editar cualquier campo del turno."""
    existing_turno = await db.turnos.find_one({"_id": ObjectId(turno_id)})
    if not existing_turno:
        raise HTTPException(status_code=404, detail="Turno not found")
    
    update_dict = turno_update.dict(exclude_none=True)
    await db.turnos.update_one(
        {"_id": ObjectId(turno_id)},
        {"$set": update_dict}
    )
    
    updated_turno = await db.turnos.find_one({"_id": ObjectId(turno_id)})
    
    # Calcular totales
    servicios = await db.services.find({"turno_id": turno_id}).to_list(1000)
    total_clientes = sum(s.get("importe_total", s.get("importe", 0)) for s in servicios if s.get("tipo") == "empresa")
    total_particulares = sum(s.get("importe_total", s.get("importe", 0)) for s in servicios if s.get("tipo") == "particular")
    total_km = sum(s.get("kilometros", 0) for s in servicios)
    
    return TurnoResponse(
        id=turno_id,
        **{k: v for k, v in updated_turno.items() if k != "_id"},
        total_importe_clientes=total_clientes,
        total_importe_particulares=total_particulares,
        total_kilometros=total_km,
        cantidad_servicios=len(servicios)
    )

@api_router.delete("/turnos/{turno_id}")
async def delete_turno(turno_id: str, current_user: dict = Depends(get_current_admin)):
    """
    Eliminar un turno (solo admin).
    También elimina todos los servicios asociados a ese turno.
    """
    # Verificar que el turno existe
    turno = await db.turnos.find_one({"_id": ObjectId(turno_id)})
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    
    # Eliminar todos los servicios asociados al turno
    servicios_result = await db.services.delete_many({"turno_id": turno_id})
    
    # Eliminar el turno
    await db.turnos.delete_one({"_id": ObjectId(turno_id)})
    
    return {
        "message": "Turno eliminado correctamente",
        "turno_id": turno_id,
        "servicios_eliminados": servicios_result.deleted_count
    }

# Exportación de Turnos
@api_router.get("/turnos/export/csv")
async def export_turnos_csv(
    current_user: dict = Depends(get_current_admin),
    taxista_id: Optional[str] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    cerrado: Optional[bool] = Query(None),
    liquidado: Optional[bool] = Query(None)
):
    query = {}
    if taxista_id:
        query["taxista_id"] = taxista_id
    if fecha_inicio:
        query["fecha_inicio"] = {"$gte": fecha_inicio}
    if fecha_fin:
        if "fecha_inicio" in query:
            query["fecha_inicio"]["$lte"] = fecha_fin
        else:
            query["fecha_inicio"] = {"$lte": fecha_fin}
    if cerrado is not None:
        query["cerrado"] = cerrado
    if liquidado is not None:
        query["liquidado"] = liquidado
    
    turnos = await db.turnos.find(query).sort("fecha_inicio", -1).to_list(10000)
    
    # Usar helper function para optimizar queries e incluir servicios detallados
    turnos_con_totales = await get_turnos_with_servicios(turnos, include_servicios_detail=True)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header principal de turnos
    writer.writerow([
        "Tipo", "Taxista", "Vehículo", "Fecha Inicio", "Hora Inicio", "KM Inicio",
        "Fecha Fin", "Hora Fin", "KM Fin", "Total KM",
        "N° Servicios", "Total Clientes (€)", "Total Particulares (€)", "Total (€)",
        "Cerrado", "Liquidado",
        "# SERVICIO: Fecha", "Hora", "Origen", "Destino", "Tipo", "Empresa", 
        "Importe", "Importe Espera", "Total", "KM"
    ])
    
    for turno in turnos_con_totales:
        total_km_turno = turno.get("km_fin", 0) - turno["km_inicio"] if turno.get("km_fin") else 0
        total_importe = turno["total_clientes"] + turno["total_particulares"]
        
        # Fila resumen del turno
        writer.writerow([
            "TURNO",
            turno["taxista_nombre"],
            turno["vehiculo_matricula"],
            turno["fecha_inicio"],
            turno["hora_inicio"],
            turno["km_inicio"],
            turno.get("fecha_fin", ""),
            turno.get("hora_fin", ""),
            turno.get("km_fin", ""),
            total_km_turno,
            turno["cantidad_servicios"],
            f"{turno['total_clientes']:.2f}",
            f"{turno['total_particulares']:.2f}",
            f"{total_importe:.2f}",
            "Sí" if turno.get("cerrado") else "No",
            "Sí" if turno.get("liquidado") else "No",
            "", "", "", "", "", "", "", "", "", ""
        ])
        
        # Filas de servicios del turno
        servicios = turno.get("servicios", [])
        for idx, servicio in enumerate(servicios, 1):
            importe = servicio.get("importe", 0)
            importe_espera = servicio.get("importe_espera", 0)
            importe_total = servicio.get("importe_total", importe + importe_espera)
            empresa_nombre = servicio.get("empresa_nombre", "")
            
            writer.writerow([
                "SERVICIO",
                "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
                f"#{idx}: {servicio.get('fecha', '')}",
                servicio.get("hora", ""),
                servicio.get("origen", ""),
                servicio.get("destino", ""),
                servicio.get("tipo", ""),
                empresa_nombre if servicio.get("tipo") == "empresa" else "",
                f"{importe:.2f}",
                f"{importe_espera:.2f}",
                f"{importe_total:.2f}",
                servicio.get("kilometros", 0)
            ])
        
        # Fila vacía para separar turnos
        writer.writerow([])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=turnos_detallado.csv"}
    )

@api_router.get("/turnos/export/excel")
async def export_turnos_excel(
    current_user: dict = Depends(get_current_admin),
    taxista_id: Optional[str] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    cerrado: Optional[bool] = Query(None),
    liquidado: Optional[bool] = Query(None)
):
    query = {}
    if taxista_id:
        query["taxista_id"] = taxista_id
    if fecha_inicio:
        query["fecha_inicio"] = {"$gte": fecha_inicio}
    if fecha_fin:
        if "fecha_inicio" in query:
            query["fecha_inicio"]["$lte"] = fecha_fin
        else:
            query["fecha_inicio"] = {"$lte": fecha_fin}
    if cerrado is not None:
        query["cerrado"] = cerrado
    if liquidado is not None:
        query["liquidado"] = liquidado
    
    turnos = await db.turnos.find(query).sort("fecha_inicio", -1).to_list(10000)
    
    # Usar helper function para optimizar queries e incluir servicios detallados
    turnos_con_totales = await get_turnos_with_servicios(turnos, include_servicios_detail=True)
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Turnos Detallados"
    
    # Header styling
    header_fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    turno_fill = PatternFill(start_color="FFD966", end_color="FFD966", fill_type="solid")
    servicio_fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
    
    headers = [
        "Tipo", "Taxista", "Vehículo", "Fecha Inicio", "Hora Inicio", "KM Inicio",
        "Fecha Fin", "Hora Fin", "KM Fin", "Total KM",
        "N° Servicios", "Total Clientes (€)", "Total Particulares (€)", "Total (€)",
        "Cerrado", "Liquidado",
        "Servicio #", "Fecha Serv.", "Hora Serv.", "Origen", "Destino", "Tipo Serv.", 
        "Empresa", "Importe", "Imp. Espera", "Total Serv.", "KM Serv."
    ]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
    
    # Data
    current_row = 2
    for turno in turnos_con_totales:
        total_km_turno = turno.get("km_fin", 0) - turno["km_inicio"] if turno.get("km_fin") else 0
        total_importe = turno["total_clientes"] + turno["total_particulares"]
        
        # Fila resumen del turno (con fondo amarillo)
        ws.cell(row=current_row, column=1, value="TURNO")
        ws.cell(row=current_row, column=2, value=turno["taxista_nombre"])
        ws.cell(row=current_row, column=3, value=turno["vehiculo_matricula"])
        ws.cell(row=current_row, column=4, value=turno["fecha_inicio"])
        ws.cell(row=current_row, column=5, value=turno["hora_inicio"])
        ws.cell(row=current_row, column=6, value=turno["km_inicio"])
        ws.cell(row=current_row, column=7, value=turno.get("fecha_fin", ""))
        ws.cell(row=current_row, column=8, value=turno.get("hora_fin", ""))
        ws.cell(row=current_row, column=9, value=turno.get("km_fin", ""))
        ws.cell(row=current_row, column=10, value=total_km_turno)
        ws.cell(row=current_row, column=11, value=turno["cantidad_servicios"])
        ws.cell(row=current_row, column=12, value=round(turno["total_clientes"], 2))
        ws.cell(row=current_row, column=13, value=round(turno["total_particulares"], 2))
        ws.cell(row=current_row, column=14, value=round(total_importe, 2))
        ws.cell(row=current_row, column=15, value="Sí" if turno.get("cerrado") else "No")
        ws.cell(row=current_row, column=16, value="Sí" if turno.get("liquidado") else "No")
        
        # Aplicar fondo amarillo a la fila del turno
        for col in range(1, 27):
            ws.cell(row=current_row, column=col).fill = turno_fill
        
        current_row += 1
        
        # Filas de servicios del turno (con fondo gris claro)
        servicios = turno.get("servicios", [])
        for idx, servicio in enumerate(servicios, 1):
            importe = servicio.get("importe", 0)
            importe_espera = servicio.get("importe_espera", 0)
            importe_total = servicio.get("importe_total", importe + importe_espera)
            empresa_nombre = servicio.get("empresa_nombre", "")
            
            ws.cell(row=current_row, column=1, value="SERVICIO")
            ws.cell(row=current_row, column=17, value=idx)
            ws.cell(row=current_row, column=18, value=servicio.get("fecha", ""))
            ws.cell(row=current_row, column=19, value=servicio.get("hora", ""))
            ws.cell(row=current_row, column=20, value=servicio.get("origen", ""))
            ws.cell(row=current_row, column=21, value=servicio.get("destino", ""))
            ws.cell(row=current_row, column=22, value=servicio.get("tipo", ""))
            ws.cell(row=current_row, column=23, value=empresa_nombre if servicio.get("tipo") == "empresa" else "")
            ws.cell(row=current_row, column=24, value=round(importe, 2))
            ws.cell(row=current_row, column=25, value=round(importe_espera, 2))
            ws.cell(row=current_row, column=26, value=round(importe_total, 2))
            ws.cell(row=current_row, column=27, value=servicio.get("kilometros", 0))
            
            # Aplicar fondo gris claro a la fila del servicio
            for col in range(1, 28):
                ws.cell(row=current_row, column=col).fill = servicio_fill
            
            current_row += 1
        
        # Fila vacía para separar turnos
        current_row += 1
    
    # Auto-adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = min((max_length + 2), 50)  # Máximo 50 caracteres de ancho
        ws.column_dimensions[column].width = adjusted_width
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=turnos_detallado.xlsx"}
    )

@api_router.get("/turnos/export/pdf")
async def export_turnos_pdf(
    current_user: dict = Depends(get_current_admin),
    taxista_id: Optional[str] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    cerrado: Optional[bool] = Query(None),
    liquidado: Optional[bool] = Query(None)
):
    query = {}
    if taxista_id:
        query["taxista_id"] = taxista_id
    if fecha_inicio:
        query["fecha_inicio"] = {"$gte": fecha_inicio}
    if fecha_fin:
        if "fecha_inicio" in query:
            query["fecha_inicio"]["$lte"] = fecha_fin
        else:
            query["fecha_inicio"] = {"$lte": fecha_fin}
    if cerrado is not None:
        query["cerrado"] = cerrado
    if liquidado is not None:
        query["liquidado"] = liquidado
    
    turnos = await db.turnos.find(query).sort("fecha_inicio", -1).to_list(10000)
    
    # Usar helper function para optimizar queries e incluir servicios detallados
    turnos_con_totales = await get_turnos_with_servicios(turnos, include_servicios_detail=True)
    
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    styles = getSampleStyleSheet()
    title = Paragraph("<b>Turnos Detallados - TaxiFast</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.2*inch))
    
    # Procesar cada turno con sus servicios
    for turno_idx, turno in enumerate(turnos_con_totales):
        # Título del turno
        turno_title = Paragraph(
            f"<b>Turno {turno_idx + 1}: {turno['taxista_nombre']} - {turno['vehiculo_matricula']}</b>",
            styles['Heading2']
        )
        elements.append(turno_title)
        elements.append(Spacer(1, 0.1*inch))
        
        # Información del turno
        estado = []
        if turno.get("cerrado"):
            estado.append("Cerrado")
        else:
            estado.append("Activo")
        if turno.get("liquidado"):
            estado.append("Liquidado")
        
        total_km_turno = turno.get("km_fin", 0) - turno["km_inicio"] if turno.get("km_fin") else 0
        total_importe = turno["total_clientes"] + turno["total_particulares"]
        
        info_turno = [
            ["Fecha Inicio:", f"{turno['fecha_inicio']} {turno['hora_inicio']}", 
             "Fecha Fin:", f"{turno.get('fecha_fin', 'N/A')} {turno.get('hora_fin', '')}" if turno.get('fecha_fin') else "En curso"],
            ["KM Inicio:", str(turno["km_inicio"]), 
             "KM Fin:", str(turno.get("km_fin", "N/A"))],
            ["Total KM:", str(total_km_turno), 
             "N° Servicios:", str(turno["cantidad_servicios"])],
            ["Total Clientes:", f"{turno['total_clientes']:.2f}€", 
             "Total Particulares:", f"{turno['total_particulares']:.2f}€"],
            ["Total General:", f"{total_importe:.2f}€", 
             "Estado:", " / ".join(estado)]
        ]
        
        info_table = Table(info_turno, colWidths=[2*inch, 2*inch, 2*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E7E6E6')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#E7E6E6')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 0.15*inch))
        
        # Tabla de servicios del turno
        servicios = turno.get("servicios", [])
        if servicios:
            servicios_title = Paragraph("<b>Servicios:</b>", styles['Heading3'])
            elements.append(servicios_title)
            elements.append(Spacer(1, 0.05*inch))
            
            servicios_data = [["#", "Fecha", "Hora", "Origen", "Destino", "Tipo", "Importe", "KM"]]
            
            for idx, servicio in enumerate(servicios, 1):
                importe_total = servicio.get("importe_total", servicio.get("importe", 0) + servicio.get("importe_espera", 0))
                origen = servicio.get("origen", "")[:15]
                destino = servicio.get("destino", "")[:15]
                
                servicios_data.append([
                    str(idx),
                    servicio.get("fecha", ""),
                    servicio.get("hora", ""),
                    origen,
                    destino,
                    servicio.get("tipo", "")[:4].upper(),
                    f"{importe_total:.2f}€",
                    str(servicio.get("kilometros", 0))
                ])
            
            servicios_table = Table(servicios_data, colWidths=[0.3*inch, 0.9*inch, 0.7*inch, 1.5*inch, 1.5*inch, 0.6*inch, 0.8*inch, 0.5*inch])
            servicios_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 7),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(servicios_table)
        else:
            no_servicios = Paragraph("<i>Este turno no tiene servicios registrados</i>", styles['Normal'])
            elements.append(no_servicios)
        
        # Separador entre turnos
        elements.append(Spacer(1, 0.3*inch))
        if turno_idx < len(turnos_con_totales) - 1:
            elements.append(Paragraph("<hr/>", styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
    
    doc.build(elements)
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=turnos_detallado.pdf"}
    )

# Estadísticas de turnos
@api_router.get("/turnos/estadisticas")
async def get_turnos_estadisticas(
    current_user: dict = Depends(get_current_admin),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    query = {}
    if fecha_inicio:
        query["fecha_inicio"] = {"$gte": fecha_inicio}
    if fecha_fin:
        if "fecha_inicio" in query:
            query["fecha_inicio"]["$lte"] = fecha_fin
        else:
            query["fecha_inicio"] = {"$lte": fecha_fin}
    
    turnos = await db.turnos.find(query).to_list(10000)
    
    total_turnos = len(turnos)
    turnos_cerrados = sum(1 for t in turnos if t.get("cerrado"))
    turnos_liquidados = sum(1 for t in turnos if t.get("liquidado"))
    turnos_activos = total_turnos - turnos_cerrados
    
    # Usar helper function para optimizar queries y calcular totales globales
    turnos_con_totales = await get_turnos_with_servicios(turnos)
    
    total_importe = sum(t["total_clientes"] + t["total_particulares"] for t in turnos_con_totales)
    total_km = sum(t["total_km"] for t in turnos_con_totales)
    total_servicios = sum(t["cantidad_servicios"] for t in turnos_con_totales)
    
    return {
        "total_turnos": total_turnos,
        "turnos_activos": turnos_activos,
        "turnos_cerrados": turnos_cerrados,
        "turnos_liquidados": turnos_liquidados,
        "turnos_pendiente_liquidacion": turnos_cerrados - turnos_liquidados,
        "total_importe": round(total_importe, 2),
        "total_kilometros": round(total_km, 2),
        "total_servicios": total_servicios,
        "promedio_importe_por_turno": round(total_importe / total_turnos, 2) if total_turnos > 0 else 0,
        "promedio_servicios_por_turno": round(total_servicios / total_turnos, 2) if total_turnos > 0 else 0
    }

# Reporte diario por taxista
@api_router.get("/reportes/diario")
async def get_reporte_diario(
    fecha: str = Query(..., description="Fecha en formato dd/mm/yyyy"),
    current_user: dict = Depends(get_current_admin)
):
    """
    Obtiene un reporte diario de todos los taxistas con sus totales del día.
    Entrada: fecha (dd/mm/yyyy)
    Salida: Lista de taxistas con sus totales del día
    """
    
    # Obtener todos los taxistas
    taxistas = await db.users.find({"role": "taxista"}).to_list(1000)
    
    # OPTIMIZACIÓN: Batch query - traer todos los servicios de la fecha de una vez
    all_servicios = await db.services.find({"fecha": fecha}).to_list(10000)
    
    # Agrupar servicios por taxista_id en memoria
    servicios_by_taxista = {}
    for servicio in all_servicios:
        taxista_id = servicio["taxista_id"]
        if taxista_id not in servicios_by_taxista:
            servicios_by_taxista[taxista_id] = []
        servicios_by_taxista[taxista_id].append(servicio)
    
    reporte = []
    
    for taxista in taxistas:
        taxista_id = str(taxista["_id"])
        
        # Obtener servicios del taxista desde el diccionario agrupado
        servicios = servicios_by_taxista.get(taxista_id, [])
        
        if len(servicios) == 0:
            continue  # Omitir taxistas sin servicios ese día
        
        # Calcular totales
        total_servicios = len(servicios)
        total_km = sum(s.get("kilometros", 0) for s in servicios)
        rec_clientes = sum(s.get("importe_total", s.get("importe", 0)) for s in servicios if s.get("tipo") == "empresa")
        rec_particulares = sum(s.get("importe_total", s.get("importe", 0)) for s in servicios if s.get("tipo") == "particular")
        
        reporte.append({
            "taxista_id": taxista_id,
            "taxista_nombre": taxista.get("nombre", "Sin nombre"),
            "fecha": fecha,
            "n_servicios": total_servicios,
            "km_totales": round(total_km, 2),
            "rec_clientes": round(rec_clientes, 2),
            "rec_particulares": round(rec_particulares, 2),
            "total": round(rec_clientes + rec_particulares, 2)
        })
    
    # Ordenar por total descendente
    reporte.sort(key=lambda x: x["total"], reverse=True)
    
    return reporte

# ==========================================
# SERVICE ENDPOINTS (Multi-tenant)
# ==========================================
@api_router.post("/services", response_model=ServiceResponse)
async def create_service(service: ServiceCreate, current_user: dict = Depends(get_current_user)):
    """Crear servicio - se asigna a la organización del usuario"""
    # Si no es admin/superadmin, buscar turno activo y asignar automáticamente
    turno_activo = None
    if current_user.get("role") not in ["admin", "superadmin"]:
        turno_activo = await db.turnos.find_one({
            "taxista_id": str(current_user["_id"]),
            "cerrado": False
        })
        
        if not turno_activo:
            raise HTTPException(
                status_code=400, 
                detail="Debes iniciar un turno antes de registrar servicios"
            )
    
    service_dict = service.dict()
    service_dict["taxista_id"] = str(current_user["_id"])
    service_dict["taxista_nombre"] = current_user["nombre"]
    service_dict["created_at"] = datetime.utcnow()
    service_dict["synced"] = True
    
    # Multi-tenant: Asignar organization_id
    service_dict["organization_id"] = get_user_organization_id(current_user)
    
    # Asignar turno_id automáticamente si hay turno activo
    if turno_activo:
        service_dict["turno_id"] = str(turno_activo["_id"])
    
    # Calcular importe_total automáticamente
    service_dict["importe_total"] = service_dict["importe"] + service_dict.get("importe_espera", 0)
    
    result = await db.services.insert_one(service_dict)
    created_service = await db.services.find_one({"_id": result.inserted_id})
    
    return ServiceResponse(
        id=str(created_service["_id"]),
        **{k: v for k, v in created_service.items() if k != "_id"}
    )

@api_router.post("/services/sync")
async def sync_services(service_sync: ServiceSync, current_user: dict = Depends(get_current_user)):
    """Sincronizar servicios offline - se asignan a la organización del usuario"""
    created_services = []
    org_id = get_user_organization_id(current_user)
    
    for service in service_sync.services:
        service_dict = service.dict()
        service_dict["taxista_id"] = str(current_user["_id"])
        service_dict["taxista_nombre"] = current_user["nombre"]
        service_dict["created_at"] = datetime.utcnow()
        service_dict["synced"] = True
        service_dict["organization_id"] = org_id  # Multi-tenant
        
        result = await db.services.insert_one(service_dict)
        created_services.append(str(result.inserted_id))
    
    return {"message": f"Synced {len(created_services)} services", "ids": created_services}

@api_router.get("/services", response_model=List[ServiceResponse])
async def get_services(
    current_user: dict = Depends(get_current_user),
    tipo: Optional[str] = Query(None),
    empresa_id: Optional[str] = Query(None),
    taxista_id: Optional[str] = Query(None),
    turno_id: Optional[str] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    limit: int = Query(1000, le=10000, description="Límite de resultados")
):
    """Listar servicios - filtrado por organización"""
    # Multi-tenant filter
    org_filter = await get_org_filter(current_user)
    query = {**org_filter}
    
    # If not admin/superadmin, only show own services
    if current_user.get("role") not in ["admin", "superadmin"]:
        query["taxista_id"] = str(current_user["_id"])
    else:
        # If admin and taxista_id filter provided
        if taxista_id:
            query["taxista_id"] = taxista_id
    
    # Apply filters
    if tipo:
        query["tipo"] = tipo
    if empresa_id:
        query["empresa_id"] = empresa_id
    if turno_id:
        query["turno_id"] = turno_id
    if fecha_inicio:
        query["fecha"] = {"$gte": fecha_inicio}
    if fecha_fin:
        if "fecha" in query:
            query["fecha"]["$lte"] = fecha_fin
        else:
            query["fecha"] = {"$lte": fecha_fin}
    
    # Validar y ajustar límite
    if limit <= 0:
        limit = 1000  # Default
    elif limit > 10000:
        limit = 10000  # Maximum
    
    # Proyección: traer solo campos necesarios (todos en este caso, pero preparado para futura optimización)
    services = await db.services.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    return [
        ServiceResponse(
            id=str(service["_id"]),
            **{k: v for k, v in service.items() if k != "_id"}
        )
        for service in services
    ]

@api_router.put("/services/{service_id}", response_model=ServiceResponse)
async def update_service(service_id: str, service: ServiceCreate, current_user: dict = Depends(get_current_user)):
    # Check if service exists and belongs to user (unless admin)
    existing_service = await db.services.find_one({"_id": ObjectId(service_id)})
    if not existing_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if current_user.get("role") != "admin" and existing_service["taxista_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to update this service")
    
    service_dict = service.dict()
    
    # Calcular importe_total automáticamente
    service_dict["importe_total"] = service_dict["importe"] + service_dict.get("importe_espera", 0)
    
    result = await db.services.update_one(
        {"_id": ObjectId(service_id)},
        {"$set": service_dict}
    )
    
    updated_service = await db.services.find_one({"_id": ObjectId(service_id)})
    return ServiceResponse(
        id=str(updated_service["_id"]),
        **{k: v for k, v in updated_service.items() if k != "_id"}
    )

@api_router.delete("/services/{service_id}")
async def delete_service(service_id: str, current_user: dict = Depends(get_current_user)):
    # Check if service exists and belongs to user (unless admin)
    existing_service = await db.services.find_one({"_id": ObjectId(service_id)})
    if not existing_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if current_user.get("role") != "admin" and existing_service["taxista_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to delete this service")
    
    result = await db.services.delete_one({"_id": ObjectId(service_id)})
    return {"message": "Service deleted successfully"}

# Export endpoints
@api_router.get("/services/export/csv")
async def export_csv(
    current_user: dict = Depends(get_current_admin),
    tipo: Optional[str] = Query(None),
    empresa_id: Optional[str] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    query = {}
    if tipo:
        query["tipo"] = tipo
    if empresa_id:
        query["empresa_id"] = empresa_id
    if fecha_inicio:
        query["fecha"] = {"$gte": fecha_inicio}
    if fecha_fin:
        if "fecha" in query:
            query["fecha"]["$lte"] = fecha_fin
        else:
            query["fecha"] = {"$lte": fecha_fin}
    
    services = await db.services.find(query).sort("fecha", 1).to_list(10000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Fecha", "Hora", "Taxista", "Origen", "Destino", "Importe (€)", "Importe Espera (€)", "Importe Total (€)", "Kilómetros", "Tipo", "Empresa", "Cobrado", "Facturar"])
    
    for service in services:
        importe = service.get("importe", 0)
        importe_espera = service.get("importe_espera", 0)
        importe_total = service.get("importe_total", importe + importe_espera)
        
        writer.writerow([
            service["fecha"],
            service["hora"],
            service["taxista_nombre"],
            service["origen"],
            service["destino"],
            f"{importe:.2f}",
            f"{importe_espera:.2f}",
            f"{importe_total:.2f}",
            service["kilometros"],
            service["tipo"],
            service.get("empresa_nombre", ""),
            "Sí" if service.get("cobrado", False) else "No",
            "Sí" if service.get("facturar", False) else "No"
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=servicios.csv"}
    )

@api_router.get("/services/export/excel")
async def export_excel(
    current_user: dict = Depends(get_current_admin),
    tipo: Optional[str] = Query(None),
    empresa_id: Optional[str] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    query = {}
    if tipo:
        query["tipo"] = tipo
    if empresa_id:
        query["empresa_id"] = empresa_id
    if fecha_inicio:
        query["fecha"] = {"$gte": fecha_inicio}
    if fecha_fin:
        if "fecha" in query:
            query["fecha"]["$lte"] = fecha_fin
        else:
            query["fecha"] = {"$lte": fecha_fin}
    
    services = await db.services.find(query).sort("fecha", 1).to_list(10000)
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Servicios"
    
    # Header styling
    header_fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    
    headers = ["Fecha", "Hora", "Taxista", "Origen", "Destino", "Importe (€)", "Importe Espera (€)", "Importe Total (€)", "Kilómetros", "Tipo", "Empresa", "Cobrado", "Facturar"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
    
    # Data
    for row_idx, service in enumerate(services, 2):
        importe = service.get("importe", 0)
        importe_espera = service.get("importe_espera", 0)
        importe_total = service.get("importe_total", importe + importe_espera)
        
        ws.cell(row=row_idx, column=1, value=service["fecha"])
        ws.cell(row=row_idx, column=2, value=service["hora"])
        ws.cell(row=row_idx, column=3, value=service["taxista_nombre"])
        ws.cell(row=row_idx, column=4, value=service["origen"])
        ws.cell(row=row_idx, column=5, value=service["destino"])
        ws.cell(row=row_idx, column=6, value=round(importe, 2))
        ws.cell(row=row_idx, column=7, value=round(importe_espera, 2))
        ws.cell(row=row_idx, column=8, value=round(importe_total, 2))
        ws.cell(row=row_idx, column=9, value=service["kilometros"])
        ws.cell(row=row_idx, column=10, value=service["tipo"])
        ws.cell(row=row_idx, column=11, value=service.get("empresa_nombre", ""))
        ws.cell(row=row_idx, column=12, value="Sí" if service.get("cobrado", False) else "No")
        ws.cell(row=row_idx, column=13, value="Sí" if service.get("facturar", False) else "No")
    
    # Auto-adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=servicios.xlsx"}
    )

@api_router.get("/services/export/pdf")
async def export_pdf(
    current_user: dict = Depends(get_current_admin),
    tipo: Optional[str] = Query(None),
    empresa_id: Optional[str] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    query = {}
    if tipo:
        query["tipo"] = tipo
    if empresa_id:
        query["empresa_id"] = empresa_id
    if fecha_inicio:
        query["fecha"] = {"$gte": fecha_inicio}
    if fecha_fin:
        if "fecha" in query:
            query["fecha"]["$lte"] = fecha_fin
        else:
            query["fecha"] = {"$lte": fecha_fin}
    
    services = await db.services.find(query).sort("fecha", 1).to_list(10000)
    
    output = io.BytesIO()
    # Usar landscape (horizontal) para tener más espacio
    doc = SimpleDocTemplate(output, pagesize=landscape(A4))
    elements = []
    
    styles = getSampleStyleSheet()
    title = Paragraph("<b>Servicios de Taxi - Taxi Tineo</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Table data con más columnas
    data = [["Fecha", "Hora", "Taxista", "Origen", "Destino", "Importe", "Espera", "Total", "KM", "Tipo", "Cobrado"]]
    
    for service in services:
        importe = service.get("importe", 0)
        importe_espera = service.get("importe_espera", 0)
        importe_total = service.get("importe_total", importe + importe_espera)
        
        data.append([
            service["fecha"],
            service["hora"],
            service["taxista_nombre"][:12],
            service["origen"][:12],
            service["destino"][:12],
            f"{importe:.2f}€",
            f"{importe_espera:.2f}€",
            f"{importe_total:.2f}€",
            service["kilometros"],
            service["tipo"][:3].upper(),
            "Sí" if service.get("cobrado", False) else "No"
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=servicios.pdf"}
    )

# Config endpoints
@api_router.get("/config", response_model=ConfigResponse)
async def get_config():
    config = await db.config.find_one()
    if not config:
        # Devolver configuración por defecto
        return ConfigResponse(
            id="default",
            nombre_radio_taxi="Taxi Tineo",
            telefono="985 80 15 15",
            web="www.taxitineo.com",
            direccion="Tineo, Asturias",
            email="",
            logo_base64=None,
            updated_at=datetime.utcnow()
        )
    
    return ConfigResponse(
        id=str(config["_id"]),
        nombre_radio_taxi=config.get("nombre_radio_taxi", "Taxi Tineo"),
        telefono=config.get("telefono", ""),
        web=config.get("web", ""),
        direccion=config.get("direccion", ""),
        email=config.get("email", ""),
        logo_base64=config.get("logo_base64"),
        updated_at=config.get("updated_at", datetime.utcnow())
    )

@api_router.put("/config", response_model=ConfigResponse)
async def update_config(config: ConfigBase, current_user: dict = Depends(get_current_admin)):
    config_dict = config.dict()
    config_dict["updated_at"] = datetime.utcnow()
    
    existing_config = await db.config.find_one()
    
    if existing_config:
        # Actualizar existente
        await db.config.update_one(
            {"_id": existing_config["_id"]},
            {"$set": config_dict}
        )
        config_id = existing_config["_id"]
    else:
        # Crear nuevo
        result = await db.config.insert_one(config_dict)
        config_id = result.inserted_id
    
    updated_config = await db.config.find_one({"_id": config_id})
    
    return ConfigResponse(
        id=str(updated_config["_id"]),
        **{k: v for k, v in updated_config.items() if k != "_id"}
    )

# Initialize default admin user and config
@app.on_event("startup")
async def startup_event():
    # Create database indexes for performance
    print("[STARTUP] Creating database indexes...")
    try:
        # Services indexes - Multi-tenant
        await db.services.create_index("turno_id")
        await db.services.create_index("taxista_id")
        await db.services.create_index("fecha")
        await db.services.create_index("tipo")
        await db.services.create_index("organization_id")  # Multi-tenant index
        await db.services.create_index([("fecha", 1), ("taxista_id", 1)])
        await db.services.create_index([("organization_id", 1), ("fecha", 1)])  # Multi-tenant compound
        
        # Turnos indexes - Multi-tenant
        await db.turnos.create_index("taxista_id")
        await db.turnos.create_index("cerrado")
        await db.turnos.create_index("liquidado")
        await db.turnos.create_index("fecha_inicio")
        await db.turnos.create_index("organization_id")  # Multi-tenant index
        await db.turnos.create_index([("taxista_id", 1), ("cerrado", 1)])
        await db.turnos.create_index([("organization_id", 1), ("cerrado", 1)])  # Multi-tenant compound
        
        # Users indexes - Multi-tenant
        await db.users.create_index("username", unique=True)
        await db.users.create_index("role")
        await db.users.create_index("organization_id")  # Multi-tenant index
        await db.users.create_index([("organization_id", 1), ("role", 1)])  # Multi-tenant compound
        
        # Vehiculos indexes - Multi-tenant
        await db.vehiculos.create_index("matricula", unique=True)
        await db.vehiculos.create_index("organization_id")  # Multi-tenant index
        
        # Companies indexes - Multi-tenant
        await db.companies.create_index("numero_cliente", unique=True, sparse=True)
        await db.companies.create_index("organization_id")  # Multi-tenant index
        
        # Organizations indexes (NEW)
        await db.organizations.create_index("slug", unique=True)
        await db.organizations.create_index("activa")
        
        print("[STARTUP] Database indexes created successfully")
    except Exception as e:
        print(f"[STARTUP WARNING] Error creating indexes: {e}")
        # No fallar si los índices ya existen
    
    # Create default SUPERADMIN if not exists
    superadmin = await db.users.find_one({"role": "superadmin"})
    if not superadmin:
        superadmin_data = {
            "username": "superadmin",
            "password": get_password_hash("superadmin123"),
            "nombre": "Super Administrador TaxiFast",
            "role": "superadmin",
            "organization_id": None,  # Superadmin no pertenece a ninguna organización
            "created_at": datetime.utcnow()
        }
        await db.users.insert_one(superadmin_data)
        logger.info("Default superadmin user created: username=superadmin, password=superadmin123")
        print("[STARTUP] ⚡ SUPERADMIN created: superadmin / superadmin123")
    
    # Migrate existing admin to have organization_id field (backward compatibility)
    admin = await db.users.find_one({"username": "admin"})
    if admin and "organization_id" not in admin:
        await db.users.update_one(
            {"_id": admin["_id"]},
            {"$set": {"organization_id": None}}
        )
        logger.info("Existing admin user updated with organization_id field")
    
    # Create default admin if not exists (legacy support)
    if not admin:
        admin_data = {
            "username": "admin",
            "password": get_password_hash("admin123"),
            "nombre": "Administrador",
            "role": "admin",
            "organization_id": None,  # Legacy admin sin organización
            "created_at": datetime.utcnow()
        }
        await db.users.insert_one(admin_data)
        logger.info("Default admin user created: username=admin, password=admin123")
    
    # Create default config if not exists (global config / legacy)
    config = await db.config.find_one()
    if not config:
        default_config = {
            "nombre_radio_taxi": "TaxiFast",
            "telefono": "900 000 000",
            "web": "www.taxifast.com",
            "direccion": "España",
            "email": "info@taxifast.com",
            "logo_base64": None,
            "updated_at": datetime.utcnow()
        }
        await db.config.insert_one(default_config)
        logger.info("Default config created")
    
    print("[STARTUP] ✅ TaxiFast Multi-tenant SaaS Platform ready!")

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
