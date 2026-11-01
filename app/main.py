from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import user_router, auth_router, investigation_router, project_router, diseno_conceptual_router, diseno_detallado_router, diseno_detallado_pantallas_router, diseno_visual_router, client_router, assessment_router
from app.core.database import engine, Base
from app.models import user_model, client_model, project_model, file_model, investigation_model, diseno_conceptual_model, diseno_visual_model, diseno_detallado_model, assessment_model
# Crear las tablas en la base de datos automáticamente al iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI(title="API STYLE")

# CORS config
origins = [
    "http://localhost:4200",
    "http://localhost:8080",
    "http://localhost:3000",
]

from fastapi.staticfiles import StaticFiles

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(investigation_router.router)
app.include_router(project_router.router)
app.include_router(diseno_conceptual_router.router)
app.include_router(diseno_visual_router.router)
app.include_router(diseno_detallado_router.router)
app.include_router(diseno_detallado_pantallas_router.router)
app.include_router(client_router.router)
app.include_router(assessment_router.router)
app.include_router(assessment_router.public_router)


@app.get("/")
def read_root():
    return {"status": "ok", "message": "ConexiÃƒÂ³n exitosa desde el backend FastAPI"}


