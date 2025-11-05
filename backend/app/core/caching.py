"""
Sistema de caching in-memory con TTL para mejorar performance.

Este módulo provee caching inteligente con Time-To-Live (TTL) configurable
para datos frecuentemente accedidos. Soporta tanto caching in-memory (cachetools)
como Redis (opcional) para ambientes de producción.
"""
from typing import Optional, Any, Callable
from functools import wraps
from cachetools import TTLCache
import logging
import time

logger = logging.getLogger(__name__)


# ===== Configuración de Caches =====

# Cache para usuarios (TTL: 5 minutos, max 1000 usuarios)
usuario_cache = TTLCache(maxsize=1000, ttl=300)

# Cache para hábitos activos (TTL: 1 minuto, max 500 conjuntos)
habitos_activos_cache = TTLCache(maxsize=500, ttl=60)

# Cache para trust level (TTL: 10 minutos, max 1000 usuarios)
trust_level_cache = TTLCache(maxsize=1000, ttl=600)

# Cache para resúmenes de conversación (TTL: 15 minutos, max 100)
resumenes_cache = TTLCache(maxsize=100, ttl=900)

# Cache para correlaciones (TTL: 30 minutos, max 100)
correlaciones_cache = TTLCache(maxsize=100, ttl=1800)

# Cache para dashboard stats (TTL: 2 minutos, max 100)
dashboard_cache = TTLCache(maxsize=100, ttl=120)


# ===== Estadísticas de Cache =====

class CacheStats:
    """
    Contador de estadísticas de cache para monitoreo.
    """
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.invalidations = 0
    
    def hit(self):
        self.hits += 1
    
    def miss(self):
        self.misses += 1
    
    def invalidate(self):
        self.invalidations += 1
    
    @property
    def hit_rate(self) -> float:
        """Calcula el hit rate del cache."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    def reset(self):
        """Resetea las estadísticas."""
        self.hits = 0
        self.misses = 0
        self.invalidations = 0
    
    def __repr__(self):
        return (
            f"CacheStats(hits={self.hits}, misses={self.misses}, "
            f"invalidations={self.invalidations}, hit_rate={self.hit_rate:.2f}%)"
        )


# Estadísticas por tipo de cache
stats = {
    'usuario': CacheStats(),
    'habitos_activos': CacheStats(),
    'trust_level': CacheStats(),
    'resumenes': CacheStats(),
    'correlaciones': CacheStats(),
    'dashboard': CacheStats(),
}


# ===== Decoradores de Cache =====

def cached_usuario(func: Callable) -> Callable:
    """
    Decorator para cachear resultados de get_usuario.
    
    Cache key: f"usuario:{usuario_id}"
    TTL: 5 minutos
    """
    @wraps(func)
    def wrapper(db, usuario_id: int, *args, **kwargs):
        cache_key = f"usuario:{usuario_id}"
        
        # Intentar obtener del cache
        if cache_key in usuario_cache:
            stats['usuario'].hit()
            logger.debug(f"Cache HIT: {cache_key}")
            return usuario_cache[cache_key]
        
        # Cache miss - ejecutar función
        stats['usuario'].miss()
        logger.debug(f"Cache MISS: {cache_key}")
        result = func(db, usuario_id, *args, **kwargs)
        
        # Guardar en cache solo si hay resultado
        if result is not None:
            usuario_cache[cache_key] = result
        
        return result
    
    return wrapper


def cached_habitos_activos(func: Callable) -> Callable:
    """
    Decorator para cachear hábitos activos de un usuario.
    
    Cache key: f"habitos_activos:{usuario_id}"
    TTL: 1 minuto
    """
    @wraps(func)
    def wrapper(db, usuario_id: int, activo: Optional[bool] = None, *args, **kwargs):
        # Solo cachear cuando se piden hábitos activos
        if activo is True:
            cache_key = f"habitos_activos:{usuario_id}"
            
            if cache_key in habitos_activos_cache:
                stats['habitos_activos'].hit()
                logger.debug(f"Cache HIT: {cache_key}")
                return habitos_activos_cache[cache_key]
            
            stats['habitos_activos'].miss()
            logger.debug(f"Cache MISS: {cache_key}")
            result = func(db, usuario_id, activo, *args, **kwargs)
            
            if result is not None:
                habitos_activos_cache[cache_key] = result
            
            return result
        
        # Si no es activo=True, no cachear
        return func(db, usuario_id, activo, *args, **kwargs)
    
    return wrapper


def cached_trust_level(func: Callable) -> Callable:
    """
    Decorator para cachear nivel de confianza de un usuario.
    
    Cache key: f"trust_level:{usuario_id}"
    TTL: 10 minutos
    
    Funciona tanto con funciones como con métodos de clase.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Detectar si es método de clase (args[0] es self) o función
        if len(args) >= 2 and hasattr(args[0], '__class__'):
            # Es método: args[0] = self, args[1] = usuario_id
            usuario_id = args[1]
        elif len(args) >= 1:
            # Es función: args[0] = usuario_id
            usuario_id = args[0]
        else:
            # No hay usuario_id posicional, ejecutar sin cache
            return func(*args, **kwargs)
        
        cache_key = f"trust_level:{usuario_id}"
        
        if cache_key in trust_level_cache:
            stats['trust_level'].hit()
            logger.debug(f"Cache HIT: {cache_key}")
            return trust_level_cache[cache_key]
        
        stats['trust_level'].miss()
        logger.debug(f"Cache MISS: {cache_key}")
        result = func(*args, **kwargs)
        
        if result is not None:
            trust_level_cache[cache_key] = result
        
        return result
    
    return wrapper


# ===== Funciones de Invalidación =====

def invalidate_usuario_cache(usuario_id: int):
    """
    Invalida cache de usuario específico.
    
    Args:
        usuario_id: ID del usuario a invalidar
    """
    cache_key = f"usuario:{usuario_id}"
    if cache_key in usuario_cache:
        del usuario_cache[cache_key]
        stats['usuario'].invalidate()
        logger.info(f"Cache invalidated: {cache_key}")


def invalidate_habitos_cache(usuario_id: int):
    """
    Invalida cache de hábitos activos de un usuario.
    
    Args:
        usuario_id: ID del usuario a invalidar
    """
    cache_key = f"habitos_activos:{usuario_id}"
    if cache_key in habitos_activos_cache:
        del habitos_activos_cache[cache_key]
        stats['habitos_activos'].invalidate()
        logger.info(f"Cache invalidated: {cache_key}")


def invalidate_trust_level_cache(usuario_id: int):
    """
    Invalida cache de trust level de un usuario.
    
    Args:
        usuario_id: ID del usuario a invalidar
    """
    cache_key = f"trust_level:{usuario_id}"
    if cache_key in trust_level_cache:
        del trust_level_cache[cache_key]
        stats['trust_level'].invalidate()
        logger.info(f"Cache invalidated: {cache_key}")


def invalidate_all_user_caches(usuario_id: int):
    """
    Invalida todos los caches relacionados con un usuario.
    
    Args:
        usuario_id: ID del usuario a invalidar
    """
    invalidate_usuario_cache(usuario_id)
    invalidate_habitos_cache(usuario_id)
    invalidate_trust_level_cache(usuario_id)
    logger.info(f"All caches invalidated for usuario_id={usuario_id}")


def clear_all_caches():
    """
    Limpia todos los caches. Útil para testing o mantenimiento.
    """
    usuario_cache.clear()
    habitos_activos_cache.clear()
    trust_level_cache.clear()
    resumenes_cache.clear()
    correlaciones_cache.clear()
    dashboard_cache.clear()
    
    # Reset stats
    for stat in stats.values():
        stat.reset()
    
    logger.info("All caches cleared")


# ===== Funciones de Monitoreo =====

def get_cache_stats() -> dict:
    """
    Retorna estadísticas de todos los caches.
    
    Returns:
        Dict con estadísticas por cache
    """
    return {
        'usuario': {
            'size': len(usuario_cache),
            'maxsize': usuario_cache.maxsize,
            'ttl': 300,
            'stats': str(stats['usuario'])
        },
        'habitos_activos': {
            'size': len(habitos_activos_cache),
            'maxsize': habitos_activos_cache.maxsize,
            'ttl': 60,
            'stats': str(stats['habitos_activos'])
        },
        'trust_level': {
            'size': len(trust_level_cache),
            'maxsize': trust_level_cache.maxsize,
            'ttl': 600,
            'stats': str(stats['trust_level'])
        },
        'resumenes': {
            'size': len(resumenes_cache),
            'maxsize': resumenes_cache.maxsize,
            'ttl': 900,
            'stats': str(stats['resumenes'])
        },
        'correlaciones': {
            'size': len(correlaciones_cache),
            'maxsize': correlaciones_cache.maxsize,
            'ttl': 1800,
            'stats': str(stats['correlaciones'])
        },
        'dashboard': {
            'size': len(dashboard_cache),
            'maxsize': dashboard_cache.maxsize,
            'ttl': 120,
            'stats': str(stats['dashboard'])
        }
    }


def print_cache_stats():
    """
    Imprime estadísticas de cache en formato legible.
    """
    print("\n📊 Cache Statistics\n")
    print("=" * 80)
    
    cache_stats = get_cache_stats()
    
    for cache_name, cache_info in cache_stats.items():
        print(f"\n🔹 {cache_name.upper()}")
        print(f"   Size: {cache_info['size']}/{cache_info['maxsize']}")
        print(f"   TTL: {cache_info['ttl']}s")
        print(f"   {cache_info['stats']}")
    
    # Calcular totales
    total_hits = sum(s.hits for s in stats.values())
    total_misses = sum(s.misses for s in stats.values())
    total_invalidations = sum(s.invalidations for s in stats.values())
    total_requests = total_hits + total_misses
    overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
    
    print("\n" + "=" * 80)
    print(f"📈 OVERALL STATS")
    print(f"   Total Requests: {total_requests}")
    print(f"   Total Hits: {total_hits}")
    print(f"   Total Misses: {total_misses}")
    print(f"   Total Invalidations: {total_invalidations}")
    print(f"   Hit Rate: {overall_hit_rate:.2f}%")
    print()


# ===== Configuración de TTL =====

CACHE_CONFIG = {
    'usuario': {
        'maxsize': 1000,
        'ttl': 300,  # 5 minutos
        'description': 'Datos completos de usuario'
    },
    'habitos_activos': {
        'maxsize': 500,
        'ttl': 60,  # 1 minuto
        'description': 'Lista de hábitos activos por usuario'
    },
    'trust_level': {
        'maxsize': 1000,
        'ttl': 600,  # 10 minutos
        'description': 'Nivel de confianza del usuario'
    },
    'resumenes': {
        'maxsize': 100,
        'ttl': 900,  # 15 minutos
        'description': 'Resúmenes de conversación'
    },
    'correlaciones': {
        'maxsize': 100,
        'ttl': 1800,  # 30 minutos
        'description': 'Correlaciones calculadas'
    },
    'dashboard': {
        'maxsize': 100,
        'ttl': 120,  # 2 minutos
        'description': 'Estadísticas de dashboard'
    }
}


def print_cache_config():
    """
    Imprime configuración de caches.
    """
    print("\n⚙️  Cache Configuration\n")
    print("=" * 80)
    
    for cache_name, config in CACHE_CONFIG.items():
        print(f"\n🔹 {cache_name.upper()}")
        print(f"   Max Size: {config['maxsize']} items")
        print(f"   TTL: {config['ttl']}s ({config['ttl'] // 60}min)")
        print(f"   Description: {config['description']}")
    
    print()


if __name__ == "__main__":
    """
    Modo standalone para ver configuración de caches.
    """
    print_cache_config()
    print_cache_stats()
