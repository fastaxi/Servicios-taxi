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
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId
import csv
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
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
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection - Compatible con desarrollo y producción
mongo_url = os.getenv('MONGO_URL', os.getenv('MONGODB_URI', 'mongodb://localhost:27017'))
db_name = os.getenv('DB_NAME') or os.getenv('MONGODB_DB_NAME')

# Validar que db_name está configurado
if not db_name:
    raise ValueError("DB_NAME or MONGODB_DB_NAME must be set in environment variables")

# Log configuration for debugging
print(f"[STARTUP] Connecting to MongoDB...")
print(f"[STARTUP] Database: {db_name}")

try:
    client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
    db = client[db_name]
    print("[STARTUP] MongoDB connection initialized successfully")
except Exception as e:
    print(f"[STARTUP ERROR] Failed to connect to MongoDB: {e}")
    raise

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'taxi-tineo-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

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

# Models
class UserBase(BaseModel):
    username: str
    nombre: str
    role: str = "taxista"  # admin or taxista
    licencia: Optional[str] = None
    vehiculo_id: Optional[str] = None
    vehiculo_matricula: Optional[str] = None  # Para mostrar sin hacer joins

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class CompanyBase(BaseModel):
    nombre: str
    cif: str
    direccion: str
    codigo_postal: Optional[str] = ""
    localidad: str
    provincia: str
    telefono: Optional[str] = ""
    email: Optional[str] = ""
    numero_cliente: Optional[str] = None
    fecha_alta: Optional[str] = None  # formato dd/mm/yyyy
    notas: Optional[str] = ""

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: str
    created_at: datetime

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

# Vehículo models
class VehiculoBase(BaseModel):
    matricula: str
    plazas: int
    marca: str
    modelo: str
    km_iniciales: int
    fecha_compra: str  # formato dd/mm/yyyy
    activo: bool = True

class VehiculoCreate(VehiculoBase):
    pass

class VehiculoResponse(VehiculoBase):
    id: str

    class Config:
        from_attributes = True

# Turno models
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
    # Totales calculados
    total_importe_clientes: Optional[float] = 0
    total_importe_particulares: Optional[float] = 0
    total_kilometros: Optional[float] = 0
    cantidad_servicios: Optional[int] = 0

    class Config:
        from_attributes = True

# Auth helpers
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
    return user

async def get_current_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Auth endpoints
@api_router.post("/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    user = await db.users.find_one({"username": user_login.username})
    if not user or not verify_password(user_login.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": user["username"]})
    user_response = UserResponse(
        id=str(user["_id"]),
        username=user["username"],
        nombre=user["nombre"],
        role=user["role"],
        created_at=user["created_at"]
    )
    return Token(access_token=access_token, token_type="bearer", user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        nombre=current_user["nombre"],
        role=current_user["role"],
        created_at=current_user["created_at"]
    )

# User endpoints (admin only)
@api_router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, current_user: dict = Depends(get_current_admin)):
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
    
    result = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    
    return UserResponse(
        id=str(created_user["_id"]),
        username=created_user["username"],
        nombre=created_user["nombre"],
        role=created_user["role"],
        licencia=created_user.get("licencia"),
        vehiculo_id=created_user.get("vehiculo_id"),
        vehiculo_matricula=created_user.get("vehiculo_matricula"),
        created_at=created_user["created_at"]
    )

@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(get_current_admin)):
    # Proyección: excluir password únicamente (no se puede mezclar inclusión y exclusión)
    users = await db.users.find(
        {"role": "taxista"},
        {"password": 0}  # Solo excluir password, traer todos los demás campos
    ).to_list(1000)
    return [
        UserResponse(
            id=str(user["_id"]),
            username=user["username"],
            nombre=user["nombre"],
            role=user["role"],
            licencia=user.get("licencia"),
            vehiculo_id=user.get("vehiculo_id"),
            vehiculo_matricula=user.get("vehiculo_matricula"),
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

# Company endpoints
@api_router.post("/companies", response_model=CompanyResponse)
async def create_company(company: CompanyCreate, current_user: dict = Depends(get_current_admin)):
    company_dict = company.dict()
    
    # Validar numero_cliente único si se proporciona
    if company_dict.get("numero_cliente"):
        existing = await db.companies.find_one({"numero_cliente": company_dict["numero_cliente"]})
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
    companies = await db.companies.find().to_list(1000)
    return [
        CompanyResponse(
            id=str(company["_id"]),
            **{k: v for k, v in company.items() if k != "_id"}
        )
        for company in companies
    ]

@api_router.put("/companies/{company_id}", response_model=CompanyResponse)
async def update_company(company_id: str, company: CompanyCreate, current_user: dict = Depends(get_current_admin)):
    company_dict = company.dict()
    
    # Validar numero_cliente único si se proporciona (excepto el actual)
    if company_dict.get("numero_cliente"):
        existing = await db.companies.find_one({
            "numero_cliente": company_dict["numero_cliente"],
            "_id": {"$ne": ObjectId(company_id)}
        })
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
    result = await db.companies.delete_one({"_id": ObjectId(company_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"message": "Company deleted successfully"}

# Vehículo endpoints
@api_router.post("/vehiculos", response_model=VehiculoResponse)
async def create_vehiculo(vehiculo: VehiculoCreate, current_user: dict = Depends(get_current_admin)):
    # Verificar que la matrícula no exista
    existing = await db.vehiculos.find_one({"matricula": vehiculo.matricula})
    if existing:
        raise HTTPException(status_code=400, detail="La matrícula ya existe")
    
    vehiculo_dict = vehiculo.dict()
    vehiculo_dict["created_at"] = datetime.utcnow()
    
    result = await db.vehiculos.insert_one(vehiculo_dict)
    created_vehiculo = await db.vehiculos.find_one({"_id": result.inserted_id})
    
    return VehiculoResponse(
        id=str(created_vehiculo["_id"]),
        **{k: v for k, v in created_vehiculo.items() if k != "_id"}
    )

@api_router.get("/vehiculos", response_model=List[VehiculoResponse])
async def get_vehiculos(current_user: dict = Depends(get_current_user)):
    vehiculos = await db.vehiculos.find().to_list(1000)
    return [
        VehiculoResponse(
            id=str(vehiculo["_id"]),
            **{k: v for k, v in vehiculo.items() if k != "_id"}
        )
        for vehiculo in vehiculos
    ]

@api_router.put("/vehiculos/{vehiculo_id}", response_model=VehiculoResponse)
async def update_vehiculo(vehiculo_id: str, vehiculo: VehiculoCreate, current_user: dict = Depends(get_current_admin)):
    # Verificar que la matrícula no esté en uso por otro vehículo
    existing = await db.vehiculos.find_one({
        "matricula": vehiculo.matricula,
        "_id": {"$ne": ObjectId(vehiculo_id)}
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
    result = await db.vehiculos.delete_one({"_id": ObjectId(vehiculo_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Vehículo not found")
    return {"message": "Vehículo deleted successfully"}

# Turno endpoints
@api_router.post("/turnos", response_model=TurnoResponse)
async def create_turno(turno: TurnoCreate, current_user: dict = Depends(get_current_user)):
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
    
    result = await db.turnos.insert_one(turno_dict)
    created_turno = await db.turnos.find_one({"_id": result.inserted_id})
    
    return TurnoResponse(
        id=str(created_turno["_id"]),
        **{k: v for k, v in created_turno.items() if k != "_id"}
    )

# HELPER FUNCTION: Batch fetch servicios para turnos (optimiza N+1 queries)
async def get_turnos_with_servicios(turnos: list) -> list:
    """
    Optimización: Trae todos los servicios de múltiples turnos en 1 query
    en vez de hacer 1 query por cada turno (N+1 problem)
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
        
        result.append({
            **turno,
            "turno_id": turno_id,
            "total_clientes": total_clientes,
            "total_particulares": total_particulares,
            "total_km": total_km,
            "cantidad_servicios": len(servicios)
        })
    
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
    query = {}
    
    # Si no es admin, solo sus propios turnos
    if current_user.get("role") != "admin":
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
    
    # Usar helper function para optimizar queries
    turnos_con_totales = await get_turnos_with_servicios(turnos)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Taxista", "Vehículo", "Fecha Inicio", "Hora Inicio", "KM Inicio",
        "Fecha Fin", "Hora Fin", "KM Fin", "Total KM",
        "Servicios", "Total Clientes (€)", "Total Particulares (€)", "Total (€)",
        "Cerrado", "Liquidado"
    ])
    
    for turno in turnos_con_totales:
        writer.writerow([
            turno["taxista_nombre"],
            turno["vehiculo_matricula"],
            turno["fecha_inicio"],
            turno["hora_inicio"],
            turno["km_inicio"],
            turno.get("fecha_fin", ""),
            turno.get("hora_fin", ""),
            turno.get("km_fin", ""),
            turno.get("km_fin", 0) - turno["km_inicio"] if turno.get("km_fin") else 0,
            turno["cantidad_servicios"],
            turno["total_clientes"],
            turno["total_particulares"],
            turno["total_clientes"] + turno["total_particulares"],
            "Sí" if turno.get("cerrado") else "No",
            "Sí" if turno.get("liquidado") else "No"
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=turnos.csv"}
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
    
    # Usar helper function para optimizar queries
    turnos_con_totales = await get_turnos_with_servicios(turnos)
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Turnos"
    
    # Header styling
    header_fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    
    headers = [
        "Taxista", "Vehículo", "Fecha Inicio", "Hora Inicio", "KM Inicio",
        "Fecha Fin", "Hora Fin", "KM Fin", "Total KM",
        "Servicios", "Total Clientes (€)", "Total Particulares (€)", "Total (€)",
        "Cerrado", "Liquidado"
    ]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
    
    # Data
    for row_idx, turno in enumerate(turnos_con_totales, 2):
        ws.cell(row=row_idx, column=1, value=turno["taxista_nombre"])
        ws.cell(row=row_idx, column=2, value=turno["vehiculo_matricula"])
        ws.cell(row=row_idx, column=3, value=turno["fecha_inicio"])
        ws.cell(row=row_idx, column=4, value=turno["hora_inicio"])
        ws.cell(row=row_idx, column=5, value=turno["km_inicio"])
        ws.cell(row=row_idx, column=6, value=turno.get("fecha_fin", ""))
        ws.cell(row=row_idx, column=7, value=turno.get("hora_fin", ""))
        ws.cell(row=row_idx, column=8, value=turno.get("km_fin", ""))
        ws.cell(row=row_idx, column=9, value=turno.get("km_fin", 0) - turno["km_inicio"] if turno.get("km_fin") else 0)
        ws.cell(row=row_idx, column=10, value=turno["cantidad_servicios"])
        ws.cell(row=row_idx, column=11, value=turno["total_clientes"])
        ws.cell(row=row_idx, column=12, value=turno["total_particulares"])
        ws.cell(row=row_idx, column=13, value=turno["total_clientes"] + turno["total_particulares"])
        ws.cell(row=row_idx, column=14, value="Sí" if turno.get("cerrado") else "No")
        ws.cell(row=row_idx, column=15, value="Sí" if turno.get("liquidado") else "No")
    
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
        headers={"Content-Disposition": "attachment; filename=turnos.xlsx"}
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
    
    # Usar helper function para optimizar queries
    turnos_con_totales = await get_turnos_with_servicios(turnos)
    
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title = Paragraph("<b>Turnos - Taxi Tineo</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Table data
    data = [["Taxista", "Vehículo", "Fecha", "KM", "Servicios", "Total €", "Estado"]]
    
    for turno in turnos_con_totales:
        estado = []
        if turno.get("cerrado"):
            estado.append("C")
        if turno.get("liquidado"):
            estado.append("L")
        
        data.append([
            turno["taxista_nombre"][:15],
            turno["vehiculo_matricula"],
            turno["fecha_inicio"],
            str(turno.get("km_fin", 0) - turno["km_inicio"] if turno.get("km_fin") else 0),
            turno["cantidad_servicios"],
            f"{turno['total_clientes'] + turno['total_particulares']:.2f}€",
            "/".join(estado) if estado else "A"
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("<i>Estados: A=Activo, C=Cerrado, L=Liquidado</i>", styles['Normal']))
    doc.build(elements)
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=turnos.pdf"}
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
    
    reporte = []
    
    for taxista in taxistas:
        taxista_id = str(taxista["_id"])
        
        # Obtener servicios del taxista en la fecha específica
        servicios = await db.services.find({
            "taxista_id": taxista_id,
            "fecha": fecha
        }).to_list(1000)
        
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

# Service endpoints
@api_router.post("/services", response_model=ServiceResponse)
async def create_service(service: ServiceCreate, current_user: dict = Depends(get_current_user)):
    # Si no es admin, buscar turno activo y asignar automáticamente
    turno_activo = None
    if current_user.get("role") != "admin":
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
    
    # Asignar turno_id automáticamente si no es admin y hay turno activo
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
    created_services = []
    for service in service_sync.services:
        service_dict = service.dict()
        service_dict["taxista_id"] = str(current_user["_id"])
        service_dict["taxista_nombre"] = current_user["nombre"]
        service_dict["created_at"] = datetime.utcnow()
        service_dict["synced"] = True
        
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
    query = {}
    
    # If not admin, only show own services
    if current_user.get("role") != "admin":
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
    writer.writerow(["Fecha", "Hora", "Taxista", "Origen", "Destino", "Importe (€)", "Importe Espera (€)", "Kilómetros", "Tipo", "Empresa"])
    
    for service in services:
        writer.writerow([
            service["fecha"],
            service["hora"],
            service["taxista_nombre"],
            service["origen"],
            service["destino"],
            service["importe"],
            service.get("importe_espera", 0),
            service["kilometros"],
            service["tipo"],
            service.get("empresa_nombre", "")
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
    
    headers = ["Fecha", "Hora", "Taxista", "Origen", "Destino", "Importe (€)", "Importe Espera (€)", "Kilómetros", "Tipo", "Empresa"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
    
    # Data
    for row_idx, service in enumerate(services, 2):
        ws.cell(row=row_idx, column=1, value=service["fecha"])
        ws.cell(row=row_idx, column=2, value=service["hora"])
        ws.cell(row=row_idx, column=3, value=service["taxista_nombre"])
        ws.cell(row=row_idx, column=4, value=service["origen"])
        ws.cell(row=row_idx, column=5, value=service["destino"])
        ws.cell(row=row_idx, column=6, value=service["importe"])
        ws.cell(row=row_idx, column=7, value=service.get("importe_espera", 0))
        ws.cell(row=row_idx, column=8, value=service["kilometros"])
        ws.cell(row=row_idx, column=9, value=service["tipo"])
        ws.cell(row=row_idx, column=10, value=service.get("empresa_nombre", ""))
    
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
    doc = SimpleDocTemplate(output, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title = Paragraph("<b>Servicios de Taxi - Taxi Tineo</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Table data
    data = [["Fecha", "Hora", "Taxista", "Origen", "Destino", "Importe", "KM"]]
    
    for service in services:
        data.append([
            service["fecha"],
            service["hora"],
            service["taxista_nombre"][:15],
            service["origen"][:15],
            service["destino"][:15],
            f"{service['importe']}€",
            service["kilometros"]
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
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
        # Services indexes
        await db.services.create_index("turno_id")
        await db.services.create_index("taxista_id")
        await db.services.create_index("fecha")
        await db.services.create_index("tipo")
        await db.services.create_index([("fecha", 1), ("taxista_id", 1)])  # Compound index
        
        # Turnos indexes
        await db.turnos.create_index("taxista_id")
        await db.turnos.create_index("cerrado")
        await db.turnos.create_index("liquidado")
        await db.turnos.create_index("fecha_inicio")
        await db.turnos.create_index([("taxista_id", 1), ("cerrado", 1)])  # Compound index
        
        # Users indexes
        await db.users.create_index("username", unique=True)
        await db.users.create_index("role")
        
        # Vehiculos indexes
        await db.vehiculos.create_index("matricula", unique=True)
        
        # Companies indexes
        await db.companies.create_index("numero_cliente", unique=True, sparse=True)
        
        print("[STARTUP] Database indexes created successfully")
    except Exception as e:
        print(f"[STARTUP WARNING] Error creating indexes: {e}")
        # No fallar si los índices ya existen
    
    # Create default admin if not exists
    admin = await db.users.find_one({"username": "admin"})
    if not admin:
        admin_data = {
            "username": "admin",
            "password": get_password_hash("admin123"),
            "nombre": "Administrador",
            "role": "admin",
            "created_at": datetime.utcnow()
        }
        await db.users.insert_one(admin_data)
        logger.info("Default admin user created: username=admin, password=admin123")
    
    # Create default config if not exists
    config = await db.config.find_one()
    if not config:
        default_config = {
            "nombre_radio_taxi": "Taxi Tineo",
            "telefono": "985 80 15 15",
            "web": "www.taxitineo.com",
            "direccion": "Tineo, Asturias",
            "email": "",
            "logo_base64": None,
            "updated_at": datetime.utcnow()
        }
        await db.config.insert_one(default_config)
        logger.info("Default config created")

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
