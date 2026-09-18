import sys
import os

# Add the parent directory to sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.models.user_model import User
from app.models.project_model import Cliente, Proyecto, TipoProyecto, NivelDiseno, EstadoProyecto
from app.models import investigation_model, file_model

def seed_data():
    db = SessionLocal()
    try:
        # 1. Crear un usuario si no existe
        user = db.query(User).filter(User.email == "admin@style.com").first()
        if not user:
            print("Creando usuario por defecto...")
            user = User(
                username="admin_style",
                email="admin@style.com",
                hashed_password="dummy_hash",
                full_name="Administrador STYLE"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # 2. Crear un cliente si no existe
        cliente = db.query(Cliente).filter(Cliente.nombre == "Colegio San Martín").first()
        if not cliente:
            print("Creando cliente por defecto...")
            cliente = Cliente(
                nombre="Colegio San Martín",
                contacto_nombre="Director",
                contacto_correo="director@colegiosanmartin.edu"
            )
            db.add(cliente)
            db.commit()
            db.refresh(cliente)

        # 3. Crear un proyecto si no existe
        proyecto = db.query(Proyecto).filter(Proyecto.id == 1).first()
        if not proyecto:
            print("Creando proyecto 1...")
            proyecto = Proyecto(
                nombre="Plataforma Educativa",
                tipo=TipoProyecto.nuevo,
                cliente_id=cliente.id,
                plataforma="Web",
                nivel_diseno_objetivo=NivelDiseno.medio,
                estado=EstadoProyecto.en_proceso,
                fase_actual_id=1,
                user_id=user.id
            )
            db.add(proyecto)
            db.commit()
            db.refresh(proyecto)
            print(f"Proyecto creado con ID: {proyecto.id}")
        else:
            print(f"El proyecto con ID {proyecto.id} ya existe.")
            
        print("¡Datos semilla insertados correctamente!")

    except Exception as e:
        print(f"Error al insertar datos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
