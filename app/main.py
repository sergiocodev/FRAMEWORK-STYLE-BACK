from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import user_router, auth_router, investigation_router, project_router, diseno_conceptual_router
from app.core.database import engine, Base
from app.models import user_model, project_model, file_model, investigation_model, diseno_conceptual_model

# Crear las tablas en la base de datos automáticamente al iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI(title="API STYLE")

# CORS config
origins = [
    "http://localhost:4200",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(investigation_router.router)
app.include_router(project_router.router)
app.include_router(diseno_conceptual_router.router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Conexión exitosa desde el backend FastAPI"}
