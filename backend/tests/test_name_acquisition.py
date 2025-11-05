"""
Test del flujo de obtención del nombre del usuario.
Verifica que Loki pregunte el nombre en la primera interacción y lo guarde correctamente.
"""

import pytest
from app.services.ai_service import loki_service


class TestNameAcquisitionFlow:
    """Tests para el flujo de obtención del nombre del usuario."""
    
    def test_is_asking_for_name_with_none(self):
        """Debe retornar True si el nombre es None."""
        assert loki_service._is_asking_for_name(None) is True
    
    def test_is_asking_for_name_with_empty_string(self):
        """Debe retornar True si el nombre es una cadena vacía."""
        assert loki_service._is_asking_for_name("") is True
        assert loki_service._is_asking_for_name("   ") is True
    
    def test_is_asking_for_name_with_valid_name(self):
        """Debe retornar False si hay un nombre válido."""
        assert loki_service._is_asking_for_name("Diego") is False
        assert loki_service._is_asking_for_name("María José") is False
    
    def test_extract_name_from_message_simple_name(self):
        """Debe extraer nombres simples de una palabra."""
        assert loki_service._extract_name_from_message("Diego") == "Diego"
        assert loki_service._extract_name_from_message("maría") == "María"
        assert loki_service._extract_name_from_message("CARLOS") == "Carlos"
    
    def test_extract_name_from_message_with_me_llamo(self):
        """Debe extraer el nombre cuando dice 'me llamo'."""
        assert loki_service._extract_name_from_message("Me llamo Diego") == "Diego"
        assert loki_service._extract_name_from_message("me llamo maría josé") == "María José"
    
    def test_extract_name_from_message_with_soy(self):
        """Debe extraer el nombre cuando dice 'soy'."""
        assert loki_service._extract_name_from_message("Soy Diego") == "Diego"
        assert loki_service._extract_name_from_message("soy ana maría") == "Ana María"
    
    def test_extract_name_from_message_with_mi_nombre_es(self):
        """Debe extraer el nombre cuando dice 'mi nombre es'."""
        assert loki_service._extract_name_from_message("Mi nombre es Diego") == "Diego"
        assert loki_service._extract_name_from_message("mi nombre es carlos alberto") == "Carlos Alberto"
    
    def test_extract_name_from_message_with_llamame(self):
        """Debe extraer el nombre cuando dice 'llámame' o 'dime'."""
        assert loki_service._extract_name_from_message("Llámame Diego") == "Diego"
        assert loki_service._extract_name_from_message("dime Juan") == "Juan"
        assert loki_service._extract_name_from_message("puedes decirme Ana") == "Ana"
    
    def test_extract_name_from_message_invalid_names(self):
        """No debe extraer nombres inválidos."""
        # Demasiado corto
        assert loki_service._extract_name_from_message("X") is None
        
        # Demasiado largo (más de 30 caracteres)
        assert loki_service._extract_name_from_message("Juan Carlos Alberto Fernando Miguel") is None
        
        # Con números o caracteres especiales
        assert loki_service._extract_name_from_message("Diego123") is None
        assert loki_service._extract_name_from_message("Carlos@") is None
    
    def test_extract_name_from_message_non_name_responses(self):
        """No debe extraer nombres de respuestas que no son nombres."""
        # Respuestas comunes que NO son nombres
        assert loki_service._extract_name_from_message("hola") is None
        assert loki_service._extract_name_from_message("¿cómo estás?") is None
        assert loki_service._extract_name_from_message("bien gracias") is None
        assert loki_service._extract_name_from_message("no sé") is None
    
    def test_generate_ask_name_response(self):
        """Debe generar una respuesta pidiendo el nombre."""
        response = loki_service._generate_ask_name_response()
        assert isinstance(response, str)
        assert len(response) > 0
        # Debe mencionar "Loki"
        assert "Loki" in response
        # Debe tener un signo de interrogación (es una pregunta)
        assert "?" in response
    
    def test_generate_greeting_with_name(self):
        """Debe generar un saludo personalizado con el nombre."""
        nombre = "Diego"
        response = loki_service._generate_greeting_with_name(nombre)
        assert isinstance(response, str)
        assert nombre in response
        assert len(response) > 0
        # Debe incluir alguna pregunta de seguimiento
        assert "?" in response
    
    @pytest.mark.asyncio
    async def test_generate_response_asks_for_name_first_time(self):
        """Primera interacción sin nombre debe pedir el nombre."""
        response = await loki_service.generate_response(
            mensaje_usuario="Hola",
            usuario_nombre=None,
            contexto_reciente=None,  # Primera vez
            db_session=None,
            usuario_id=None
        )
        
        assert 'respuesta' in response
        assert 'esperando_nombre' in response
        assert response['esperando_nombre'] is True
        assert 'Loki' in response['respuesta']
    
    @pytest.mark.asyncio
    async def test_generate_response_extracts_name_second_time(self):
        """Segunda interacción debe extraer y confirmar el nombre."""
        # Simular que ya preguntamos el nombre (hay contexto reciente)
        contexto_reciente = [
            {
                'mensaje_usuario': 'Hola',
                'respuesta_loki': 'Hola! Soy Loki. ¿Cómo te llamas?'
            }
        ]
        
        response = await loki_service.generate_response(
            mensaje_usuario="Diego",
            usuario_nombre=None,  # Aún sin nombre
            contexto_reciente=contexto_reciente,
            db_session=None,
            usuario_id=None
        )
        
        assert 'respuesta' in response
        assert 'nombre_detectado' in response
        assert response['nombre_detectado'] == 'Diego'
        assert 'esperando_nombre' in response
        assert response['esperando_nombre'] is False
        assert 'Diego' in response['respuesta']
    
    @pytest.mark.asyncio
    async def test_generate_response_asks_again_if_invalid_name(self):
        """Si no detecta nombre válido, debe volver a preguntar."""
        contexto_reciente = [
            {
                'mensaje_usuario': 'Hola',
                'respuesta_loki': 'Hola! Soy Loki. ¿Cómo te llamas?'
            }
        ]
        
        response = await loki_service.generate_response(
            mensaje_usuario="123",  # Nombre inválido
            usuario_nombre=None,
            contexto_reciente=contexto_reciente,
            db_session=None,
            usuario_id=None
        )
        
        assert 'respuesta' in response
        assert 'esperando_nombre' in response
        assert response['esperando_nombre'] is True
        assert 'nombre_detectado' in response
        assert response['nombre_detectado'] is None
        # Debe pedir el nombre de nuevo
        assert any(word in response['respuesta'].lower() for word in ["nombre", "entendido"])
    
    @pytest.mark.asyncio
    async def test_generate_response_normal_flow_with_name(self):
        """Con nombre válido debe proceder con flujo normal."""
        response = await loki_service.generate_response(
            mensaje_usuario="Hola, ¿cómo estás?",
            usuario_nombre="Diego",  # Ya tiene nombre
            contexto_reciente=None,
            db_session=None,
            usuario_id=None
        )
        
        assert 'respuesta' in response
        assert 'context_extracted' in response
        # No debe estar esperando nombre
        assert response.get('esperando_nombre', False) is False
