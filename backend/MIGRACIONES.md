# Guía de Migraciones con Alembic

## ¿Qué son las migraciones?

Las migraciones son cambios versionados en la estructura de la base de datos. Permiten:
- ✅ Controlar versiones del esquema de base de datos
- ✅ Aplicar cambios de forma segura en producción
- ✅ Hacer rollback si algo sale mal
- ✅ Colaborar en equipo sin conflictos de base de datos

## Comandos Básicos

### Ver el estado actual
```bash
cd backend
python -m alembic current
```

### Aplicar migraciones pendientes
```bash
cd backend
python -m alembic upgrade head
```

### Crear nueva migración (autogenerada)
```bash
cd backend
python -m alembic revision --autogenerate -m "Descripción del cambio"
```

### Crear nueva migración (manual)
```bash
cd backend
python -m alembic revision -m "Descripción del cambio"
```

### Rollback a la migración anterior
```bash
cd backend
python -m alembic downgrade -1
```

### Rollback a una migración específica
```bash
cd backend
python -m alembic downgrade <revision_id>
```

### Ver historial de migraciones
```bash
cd backend
python -m alembic history
```

## Flujo de Trabajo Recomendado

### 1. Modificar modelos
Edita los modelos en `app/models/mood.py`:

```python
class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    # Nuevo campo:
    email = Column(String, unique=True)
```

### 2. Generar migración
```bash
cd backend
python -m alembic revision --autogenerate -m "Add email to users"
```

### 3. Revisar la migración generada
Abre el archivo generado en `backend/alembic/versions/` y verifica que:
- Los cambios son correctos
- No hay datos que se puedan perder
- Las operaciones son reversibles

### 4. Aplicar la migración
```bash
python -m alembic upgrade head
```

### 5. Si algo sale mal, hacer rollback
```bash
python -m alembic downgrade -1
```

## Buenas Prácticas

### ✅ DO (Hacer)
- Siempre revisar las migraciones autogeneradas antes de aplicarlas
- Usar nombres descriptivos para las migraciones
- Probar las migraciones en desarrollo antes de producción
- Hacer backup de la base de datos antes de migraciones en producción
- Incluir tanto `upgrade()` como `downgrade()` en las migraciones

### ❌ DON'T (No hacer)
- No usar `Base.metadata.create_all()` en producción
- No editar migraciones que ya se aplicaron
- No borrar archivos de migración
- No hacer cambios directamente en la base de datos sin migración

## Migraciones en Producción

### Antes de aplicar:
1. **Backup completo** de la base de datos
2. **Probar** en ambiente de staging
3. **Planificar downtime** si es necesario
4. **Tener plan de rollback** listo

### Aplicar en producción:
```bash
cd backend

# 1. Ver qué migraciones se aplicarán
python -m alembic history

# 2. Aplicar migraciones
python -m alembic upgrade head

# 3. Verificar estado
python -m alembic current

# 4. Si algo sale mal, rollback inmediato
python -m alembic downgrade <revision_id_anterior>
```

## Ejemplos Comunes

### Agregar columna nullable
```python
# En la migración autogenerada:
def upgrade():
    op.add_column('usuarios', sa.Column('bio', sa.String(), nullable=True))

def downgrade():
    op.drop_column('usuarios', 'bio')
```

### Agregar columna NOT NULL (requiere valor default)
```python
def upgrade():
    # Opción 1: Agregar con default
    op.add_column('usuarios', sa.Column('active', sa.Boolean(), server_default='1', nullable=False))

    # Opción 2: Agregar nullable primero, llenar datos, luego hacer NOT NULL
    op.add_column('usuarios', sa.Column('active', sa.Boolean(), nullable=True))
    op.execute("UPDATE usuarios SET active = 1")
    op.alter_column('usuarios', 'active', nullable=False)
```

### Renombrar columna
```python
def upgrade():
    op.alter_column('usuarios', 'nombre', new_column_name='full_name')

def downgrade():
    op.alter_column('usuarios', 'full_name', new_column_name='nombre')
```

### Agregar índice
```python
def upgrade():
    op.create_index('ix_usuarios_email', 'usuarios', ['email'])

def downgrade():
    op.drop_index('ix_usuarios_email', 'usuarios')
```

## Troubleshooting

### "Target database is not up to date"
```bash
# Ver estado actual
python -m alembic current

# Aplicar migraciones faltantes
python -m alembic upgrade head
```

### "Can't locate revision identified by 'xxxxx'"
Esto significa que falta un archivo de migración. Asegúrate de:
1. Tener todos los archivos de migración en `alembic/versions/`
2. Hacer pull de las migraciones del repositorio

### "FAILED: Multiple head revisions are present"
Esto pasa cuando hay ramas de migración. Para resolver:
```bash
python -m alembic merge heads -m "Merge migration branches"
python -m alembic upgrade head
```

## Referencias

- [Documentación oficial de Alembic](https://alembic.sqlalchemy.org/)
- [Tutorial de Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
