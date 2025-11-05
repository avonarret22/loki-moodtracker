"""
Tests para el sistema de caching.

Verifica que los decoradores de cache funcionen correctamente
y que la invalidación funcione como esperado.
"""
import pytest
from app.core.caching import (
    usuario_cache, habitos_activos_cache, trust_level_cache,
    cached_usuario, cached_habitos_activos, cached_trust_level,
    invalidate_usuario_cache, invalidate_habitos_cache, invalidate_trust_level_cache,
    invalidate_all_user_caches, clear_all_caches,
    get_cache_stats, stats
)
from app.crud.mood import (
    get_usuario, get_habitos_by_usuario, create_habito,
    update_habito, delete_habito
)
from app.services.trust_level_service import trust_service
from app.schemas.mood import HabitoCreate, HabitoUpdate


@pytest.fixture
def test_habito(db_session, test_usuario):
    """Fixture que crea un hábito de prueba."""
    habito_data = HabitoCreate(
        nombre_habito="Hábito de prueba",
        categoria="test",
        objetivo_semanal=7,
        activo=True
    )
    return create_habito(db_session, habito_data, test_usuario.id)


class TestUsuarioCache:
    """Tests para el cache de usuarios."""
    
    def test_usuario_cache_hit(self, db_session, test_usuario):
        """Verifica que el segundo acceso venga del cache."""
        # Limpiar cache antes del test
        clear_all_caches()
        
        # Primera llamada - cache miss
        usuario1 = get_usuario(db_session, test_usuario.id)
        assert usuario1 is not None
        assert stats['usuario'].misses == 1
        assert stats['usuario'].hits == 0
        
        # Segunda llamada - cache hit
        usuario2 = get_usuario(db_session, test_usuario.id)
        assert usuario2 is not None
        assert stats['usuario'].hits == 1
        
        # Deben ser el mismo objeto
        assert usuario1.id == usuario2.id
    
    def test_usuario_cache_invalidation(self, db_session, test_usuario):
        """Verifica que la invalidación funcione."""
        clear_all_caches()
        
        # Cargar en cache
        usuario1 = get_usuario(db_session, test_usuario.id)
        assert stats['usuario'].misses == 1
        
        # Invalidar
        invalidate_usuario_cache(test_usuario.id)
        assert stats['usuario'].invalidations == 1
        
        # Siguiente llamada debe ser cache miss
        usuario2 = get_usuario(db_session, test_usuario.id)
        assert stats['usuario'].misses == 2


class TestHabitosCache:
    """Tests para el cache de hábitos activos."""
    
    def test_habitos_activos_cache_hit(self, db_session, test_usuario):
        """Verifica cache de hábitos activos."""
        clear_all_caches()
        
        # Primera llamada - cache miss
        habitos1 = get_habitos_by_usuario(db_session, test_usuario.id, activo=True)
        assert stats['habitos_activos'].misses == 1
        assert stats['habitos_activos'].hits == 0
        
        # Segunda llamada - cache hit
        habitos2 = get_habitos_by_usuario(db_session, test_usuario.id, activo=True)
        assert stats['habitos_activos'].hits == 1
    
    def test_habitos_no_activos_no_cached(self, db_session, test_usuario):
        """Verifica que hábitos no activos no se cacheen."""
        clear_all_caches()
        
        # Llamar con activo=False no debe usar cache
        habitos1 = get_habitos_by_usuario(db_session, test_usuario.id, activo=False)
        assert stats['habitos_activos'].misses == 0
        assert stats['habitos_activos'].hits == 0
        
        # Llamar sin parámetro activo tampoco debe usar cache
        habitos2 = get_habitos_by_usuario(db_session, test_usuario.id)
        assert stats['habitos_activos'].misses == 0
        assert stats['habitos_activos'].hits == 0
    
    def test_habitos_cache_invalidation_on_create(self, db_session, test_usuario):
        """Verifica que crear un hábito invalide el cache."""
        clear_all_caches()
        
        # Cargar en cache
        habitos1 = get_habitos_by_usuario(db_session, test_usuario.id, activo=True)
        initial_count = len(habitos1)
        assert stats['habitos_activos'].misses == 1
        
        # Crear nuevo hábito (debe invalidar cache)
        nuevo_habito = HabitoCreate(
            nombre_habito="Nuevo hábito test",
            categoria="test",
            objetivo_semanal=5,
            activo=True
        )
        create_habito(db_session, nuevo_habito, test_usuario.id)
        
        # Verificar que se invalidó el cache
        assert stats['habitos_activos'].invalidations >= 1
        
        # Siguiente llamada debe ser cache miss y tener el nuevo hábito
        habitos2 = get_habitos_by_usuario(db_session, test_usuario.id, activo=True)
        assert stats['habitos_activos'].misses == 2
        assert len(habitos2) == initial_count + 1
    
    def test_habitos_cache_invalidation_on_update(self, db_session, test_usuario, test_habito):
        """Verifica que actualizar un hábito invalide el cache."""
        clear_all_caches()
        
        # Cargar en cache
        get_habitos_by_usuario(db_session, test_usuario.id, activo=True)
        assert stats['habitos_activos'].misses == 1
        
        # Actualizar hábito (debe invalidar cache)
        update_data = HabitoUpdate(nombre_habito="Nombre actualizado")
        update_habito(db_session, test_habito.id, update_data)
        
        # Verificar invalidación
        assert stats['habitos_activos'].invalidations >= 1
    
    def test_habitos_cache_invalidation_on_delete(self, db_session, test_usuario, test_habito):
        """Verifica que eliminar un hábito invalide el cache."""
        clear_all_caches()
        
        # Cargar en cache
        get_habitos_by_usuario(db_session, test_usuario.id, activo=True)
        assert stats['habitos_activos'].misses == 1
        
        # Eliminar hábito (debe invalidar cache)
        delete_habito(db_session, test_habito.id)
        
        # Verificar invalidación
        assert stats['habitos_activos'].invalidations >= 1


class TestTrustLevelCache:
    """Tests para el cache de trust level."""
    
    def test_trust_level_cache_hit(self, db_session, test_usuario):
        """Verifica cache de trust level."""
        clear_all_caches()
        
        # Primera llamada - cache miss
        trust1 = trust_service.get_user_trust_info(test_usuario.id, db=db_session)
        assert trust1 is not None
        assert stats['trust_level'].misses == 1
        assert stats['trust_level'].hits == 0
        
        # Segunda llamada - cache hit
        trust2 = trust_service.get_user_trust_info(test_usuario.id, db=db_session)
        assert stats['trust_level'].hits == 1
        
        # Deben ser iguales
        assert trust1['nivel_confianza'] == trust2['nivel_confianza']
    
    def test_trust_level_cache_invalidation(self, db_session, test_usuario):
        """Verifica que actualizar trust level invalide el cache."""
        clear_all_caches()
        
        # Cargar en cache
        trust1 = trust_service.get_user_trust_info(test_usuario.id, db=db_session)
        assert stats['trust_level'].misses == 1
        
        # Actualizar trust level (debe invalidar cache)
        trust_service.update_trust_level(db_session, test_usuario.id)
        assert stats['trust_level'].invalidations >= 1
        
        # Siguiente llamada debe ser cache miss con datos actualizados
        trust2 = trust_service.get_user_trust_info(test_usuario.id, db=db_session)
        assert stats['trust_level'].misses == 2
        assert trust2['total_interacciones'] == trust1['total_interacciones'] + 1


class TestCacheInvalidation:
    """Tests para invalidación de caches."""
    
    def test_invalidate_all_user_caches(self, db_session, test_usuario):
        """Verifica que se invaliden todos los caches de un usuario."""
        clear_all_caches()
        
        # Cargar todos los caches
        get_usuario(db_session, test_usuario.id)
        get_habitos_by_usuario(db_session, test_usuario.id, activo=True)
        trust_service.get_user_trust_info(test_usuario.id, db=db_session)
        
        # Verificar que están en cache
        assert stats['usuario'].hits + stats['usuario'].misses > 0
        assert stats['habitos_activos'].hits + stats['habitos_activos'].misses > 0
        assert stats['trust_level'].hits + stats['trust_level'].misses > 0
        
        # Invalidar todos
        invalidate_all_user_caches(test_usuario.id)
        
        # Verificar invalidaciones
        assert stats['usuario'].invalidations >= 1
        assert stats['habitos_activos'].invalidations >= 1
        assert stats['trust_level'].invalidations >= 1
    
    def test_clear_all_caches(self, db_session, test_usuario):
        """Verifica que clear_all_caches limpie todo."""
        # Cargar algunos caches
        get_usuario(db_session, test_usuario.id)
        get_habitos_by_usuario(db_session, test_usuario.id, activo=True)
        
        # Verificar que hay datos en cache
        assert len(usuario_cache) > 0 or len(habitos_activos_cache) > 0
        
        # Limpiar todo
        clear_all_caches()
        
        # Verificar que todos los caches están vacíos
        assert len(usuario_cache) == 0
        assert len(habitos_activos_cache) == 0
        assert len(trust_level_cache) == 0
        
        # Verificar que stats se resetearon
        assert stats['usuario'].hits == 0
        assert stats['usuario'].misses == 0
        assert stats['habitos_activos'].hits == 0
        assert stats['habitos_activos'].misses == 0


class TestCacheStats:
    """Tests para estadísticas de cache."""
    
    def test_cache_hit_rate_calculation(self):
        """Verifica cálculo de hit rate."""
        clear_all_caches()
        
        # Simular hits y misses
        stats['usuario'].hits = 80
        stats['usuario'].misses = 20
        
        # Hit rate debe ser 80%
        assert stats['usuario'].hit_rate == 80.0
        
        # Caso sin requests
        clear_all_caches()
        assert stats['usuario'].hit_rate == 0.0
    
    def test_get_cache_stats(self, db_session, test_usuario):
        """Verifica que get_cache_stats retorne información correcta."""
        clear_all_caches()
        
        # Cargar algunos caches
        get_usuario(db_session, test_usuario.id)
        
        cache_stats = get_cache_stats()
        
        # Verificar estructura
        assert 'usuario' in cache_stats
        assert 'habitos_activos' in cache_stats
        assert 'trust_level' in cache_stats
        
        # Verificar datos de usuario cache
        assert cache_stats['usuario']['maxsize'] == 1000
        assert cache_stats['usuario']['ttl'] == 300
        assert cache_stats['usuario']['size'] >= 0


class TestCacheTTL:
    """Tests para verificar Time-To-Live de caches."""
    
    @pytest.mark.parametrize("cache_name,ttl_seconds", [
        ('usuario', 300),  # 5 minutos
        ('habitos_activos', 60),  # 1 minuto
        ('trust_level', 600),  # 10 minutos
    ])
    def test_cache_ttl_configuration(self, cache_name, ttl_seconds):
        """Verifica que los TTL estén configurados correctamente."""
        cache_stats = get_cache_stats()
        assert cache_stats[cache_name]['ttl'] == ttl_seconds
    
    def test_cache_expires_after_ttl(self, db_session, test_usuario):
        """
        Test que verifica expiración de cache.
        NOTA: Este test no es práctico ejecutarlo porque requiere esperar 5+ minutos.
        Lo dejamos como documentación del comportamiento esperado.
        """
        pytest.skip("Test requiere esperar TTL completo (5 minutos)")
        
        clear_all_caches()
        
        # Cargar en cache
        get_usuario(db_session, test_usuario.id)
        assert stats['usuario'].misses == 1
        
        # Esperar TTL (5 minutos para usuario_cache)
        import time
        time.sleep(301)  # 5 minutos + 1 segundo
        
        # Cache debe haber expirado - siguiente llamada es miss
        get_usuario(db_session, test_usuario.id)
        assert stats['usuario'].misses == 2


class TestCacheMaxSize:
    """Tests para verificar límites de tamaño de cache."""
    
    def test_cache_max_size_configuration(self):
        """Verifica que los maxsize estén configurados correctamente."""
        cache_stats = get_cache_stats()
        
        assert cache_stats['usuario']['maxsize'] == 1000
        assert cache_stats['habitos_activos']['maxsize'] == 500
        assert cache_stats['trust_level']['maxsize'] == 1000
    
    def test_cache_evicts_when_full(self, db_session):
        """
        Verifica que el cache evict correctamente cuando está lleno.
        NOTA: Este test requiere crear 1000+ usuarios, no es práctico.
        Lo dejamos como documentación.
        """
        pytest.skip("Test requiere crear 1000+ usuarios")
