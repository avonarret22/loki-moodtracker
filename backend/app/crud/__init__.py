# Import all CRUD functions here
from app.crud.mood import get_usuario, get_usuario_by_telefono, get_usuarios, create_usuario, get_or_create_usuario
from app.crud.mood import get_estado_animo, get_estados_animo_by_usuario, create_estado_animo
from app.crud.mood import (
    get_habito, get_habitos_by_usuario, create_habito, update_habito, delete_habito,
    get_registro_habito, get_registros_by_usuario, get_registros_by_habito, create_registro_habito,
    get_conversacion, get_conversaciones_by_usuario, create_conversacion,
    get_correlacion, get_correlaciones_by_usuario, create_correlacion, delete_correlacion
)