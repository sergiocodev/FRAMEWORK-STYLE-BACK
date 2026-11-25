# API STYLE - Backend
# TEST CI/CD

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

## 🛠️ Instalación y Uso Local

Sigue estos pasos para configurar el entorno de desarrollo en tu máquina local:

1. **Clonar el repositorio:**
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd FRAMEWORK_BACKEND
   ```

2. **Crear y activar el entorno virtual:**
   - En Windows (PowerShell):
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - En Linux/Mac:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**
   Copia el archivo de ejemplo para configurar tus credenciales locales:
   - Crea un archivo llamado `.env` en la raíz del proyecto.
   - Copia el contenido del archivo `.env.example` dentro de tu nuevo `.env`.
   - Ajusta los valores con tus credenciales de base de datos MySQL.

5. **Iniciar el servidor local:**
   ```bash
   uvicorn app.main:app --reload
   ```
   El servidor estará corriendo en `http://127.0.0.1:8000`. Puedes consultar la documentación interactiva en `http://127.0.0.1:8000/docs`.
