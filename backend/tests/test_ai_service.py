"""
Tests for AI service
"""
import pytest
from app.services.ai_service import LokiAIService
from app.models.mood import Usuario


def test_ai_service_initialization():
    """Test AI service can be initialized"""
    ai_service = LokiAIService()
    assert ai_service is not None
    assert hasattr(ai_service, 'generate_response')


# NOTE: Los siguientes tests están comentados temporalmente porque requieren
# configuración específica de la API de Claude y pueden fallar en CI/CD
# sin las credenciales correctas. Descomentar para pruebas locales.

# @pytest.mark.asyncio
# async def test_generate_response_basic():
#     """Test basic response generation"""
#     ai_service = LokiAIService()
#     
#     response = await ai_service.generate_response(
#         mensaje_usuario="Hola, ¿cómo estás?",
#         usuario_nombre="Test User",
#         contexto_reciente=[],
#         user_context={}
#     )
#     
#     assert 'respuesta' in response
#     assert isinstance(response['respuesta'], str)
#     assert len(response['respuesta']) > 0
