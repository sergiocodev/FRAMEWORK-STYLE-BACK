# API STYLE - Backend

Esta es la API RESTful para el marco de trabajo **STYLE**, construida con **FastAPI**. Gestión de datos con conexión a una base de datos **MySQL**.

## 🚀 Tecnologías Principales

- **Framework Web:** [FastAPI]
- **Servidor ASGI:** Uvicorn
- **ORM:** SQLAlchemy
- **Base de Datos:** MySQL
- **Validación:** Pydantic
- **Autenticación:** JSON Web Tokens (JWT)

## 📁 Estructura del Proyecto

La arquitectura del proyecto sigue una estructura modular para mantener la separación de responsabilidades:

```text
FRAMEWORK_BACKEND/
├── app/
│   ├── core/           # Configuración central y conexión a BD
│   ├── models/         # Modelos de base de datos SQLAlchemy (Entidades)
│   ├── schemas/        # Esquemas de validación de Pydantic (DTOs)
│   ├── services/       # Lógica de negocio y consultas a BD
│   ├── routers/        # Controladores y endpoints de la API
│   ├── main.py         # Punto de entrada de la aplicación FastAPI
│   └── __init__.py
├── venv/               # Entorno virtual
├── .env                # Variables de entorno
└── requirements.txt    # Lista de dependencias del proyecto
```
