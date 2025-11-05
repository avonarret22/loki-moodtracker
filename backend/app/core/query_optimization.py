"""
Utilidades para análisis y optimización de queries de base de datos.
"""
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from typing import List, Dict, Any
import time
import logging

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """
    Analizador de queries para detectar slow queries y optimizar rendimiento.
    """
    
    def __init__(self, slow_query_threshold: float = 0.1):
        """
        Args:
            slow_query_threshold: Umbral en segundos para considerar una query lenta
        """
        self.slow_query_threshold = slow_query_threshold
        self.slow_queries: List[Dict[str, Any]] = []
    
    def enable_query_logging(self, engine: Engine):
        """
        Habilita logging de queries lentas en el engine de SQLAlchemy.
        
        Args:
            engine: Engine de SQLAlchemy
        """
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
        
        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total_time = time.time() - conn.info['query_start_time'].pop()
            
            if total_time > self.slow_query_threshold:
                slow_query = {
                    'query': statement,
                    'parameters': parameters,
                    'duration': total_time,
                    'timestamp': time.time()
                }
                self.slow_queries.append(slow_query)
                logger.warning(
                    f"Slow query detected ({total_time:.3f}s): {statement[:100]}..."
                )
    
    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """
        Retorna lista de queries lentas detectadas.
        """
        return sorted(
            self.slow_queries,
            key=lambda x: x['duration'],
            reverse=True
        )
    
    def clear_slow_queries(self):
        """
        Limpia el registro de queries lentas.
        """
        self.slow_queries = []
    
    def print_report(self):
        """
        Imprime reporte de queries lentas.
        """
        if not self.slow_queries:
            print("✅ No se detectaron queries lentas")
            return
        
        print(f"\n⚠️  {len(self.slow_queries)} queries lentas detectadas:\n")
        for i, query in enumerate(self.get_slow_queries()[:10], 1):
            print(f"{i}. Duración: {query['duration']:.3f}s")
            print(f"   Query: {query['query'][:200]}...")
            print()


# Recomendaciones de índices basadas en análisis de queries
INDEX_RECOMMENDATIONS = {
    "estados_animo": [
        {
            "name": "ix_estados_animo_usuario_timestamp",
            "columns": ["usuario_id", "timestamp"],
            "description": "Optimiza búsqueda de estados de ánimo por usuario ordenados por fecha",
            "status": "✅ Implementado"
        }
    ],
    "habitos": [
        {
            "name": "ix_habitos_usuario_activo",
            "columns": ["usuario_id", "activo"],
            "description": "Optimiza filtrado de hábitos activos/inactivos por usuario",
            "status": "✅ Implementado"
        },
        {
            "name": "ix_habitos_usuario_nombre",
            "columns": ["usuario_id", "nombre_habito"],
            "description": "Optimiza búsqueda de hábitos por nombre",
            "status": "✅ Implementado"
        }
    ],
    "registros_habitos": [
        {
            "name": "ix_registros_habitos_usuario_timestamp",
            "columns": ["usuario_id", "timestamp"],
            "description": "Optimiza búsqueda de registros por usuario ordenados por fecha",
            "status": "✅ Implementado"
        },
        {
            "name": "ix_registros_habitos_habito_timestamp",
            "columns": ["habito_id", "timestamp"],
            "description": "Optimiza búsqueda de registros por hábito ordenados por fecha",
            "status": "✅ Implementado"
        }
    ],
    "conversaciones_contexto": [
        {
            "name": "ix_conversaciones_usuario_timestamp_desc",
            "columns": ["usuario_id", "timestamp"],
            "description": "Optimiza búsqueda de conversaciones recientes por usuario",
            "status": "✅ Implementado"
        }
    ],
    "correlaciones": [
        {
            "name": "ix_correlaciones_usuario_fecha",
            "columns": ["usuario_id", "fecha_calculo"],
            "description": "Optimiza búsqueda de correlaciones por usuario y fecha",
            "status": "✅ Implementado"
        }
    ],
    "resumenes_conversacion": [
        {
            "name": "ix_resumenes_usuario_fecha",
            "columns": ["usuario_id", "fecha_resumen"],
            "description": "Optimiza búsqueda de resúmenes por usuario y fecha",
            "status": "✅ Implementado"
        }
    ],
    "feedback_respuestas": [
        {
            "name": "ix_feedback_usuario_timestamp",
            "columns": ["usuario_id", "timestamp"],
            "description": "Optimiza búsqueda de feedback por usuario y fecha",
            "status": "✅ Implementado"
        },
        {
            "name": "ix_feedback_usuario_rating",
            "columns": ["usuario_id", "utilidad_rating"],
            "description": "Optimiza análisis de ratings por usuario",
            "status": "✅ Implementado"
        }
    ],
    "respuestas_exitosas": [
        {
            "name": "ix_respuestas_usuario_patron",
            "columns": ["usuario_id", "patron_pregunta"],
            "description": "Optimiza búsqueda de respuestas efectivas por patrón",
            "status": "✅ Implementado (Nueva)"
        },
        {
            "name": "ix_respuestas_usuario_utilidad",
            "columns": ["usuario_id", "utilidad_promedio"],
            "description": "Optimiza búsqueda de mejores respuestas por utilidad",
            "status": "✅ Implementado (Nueva)"
        }
    ]
}


def print_index_recommendations():
    """
    Imprime recomendaciones de índices implementadas.
    """
    print("\n📊 Índices Compuestos Implementados\n")
    print("=" * 80)
    
    for table, indexes in INDEX_RECOMMENDATIONS.items():
        print(f"\n📁 Tabla: {table}")
        print("-" * 80)
        for idx in indexes:
            print(f"  {idx['status']} {idx['name']}")
            print(f"     Columnas: {', '.join(idx['columns'])}")
            print(f"     Uso: {idx['description']}")
            print()
    
    total_indexes = sum(len(indexes) for indexes in INDEX_RECOMMENDATIONS.values())
    print(f"\n✅ Total: {total_indexes} índices compuestos implementados")


# Query patterns para análisis
QUERY_PATTERNS = {
    "frequent_queries": [
        {
            "pattern": "SELECT * FROM estados_animo WHERE usuario_id = ? ORDER BY timestamp DESC",
            "optimization": "Usa ix_estados_animo_usuario_timestamp",
            "crud_function": "get_estados_animo_by_usuario()"
        },
        {
            "pattern": "SELECT * FROM habitos WHERE usuario_id = ? AND activo = ?",
            "optimization": "Usa ix_habitos_usuario_activo",
            "crud_function": "get_habitos_by_usuario(activo=True)"
        },
        {
            "pattern": "SELECT * FROM registros_habitos WHERE usuario_id = ? ORDER BY timestamp DESC",
            "optimization": "Usa ix_registros_habitos_usuario_timestamp",
            "crud_function": "get_registros_by_usuario()"
        },
        {
            "pattern": "SELECT * FROM conversaciones_contexto WHERE usuario_id = ? ORDER BY timestamp DESC",
            "optimization": "Usa ix_conversaciones_usuario_timestamp_desc",
            "crud_function": "get_conversaciones_by_usuario()"
        },
        {
            "pattern": "SELECT * FROM respuestas_exitosas WHERE usuario_id = ? AND patron_pregunta = ?",
            "optimization": "Usa ix_respuestas_usuario_patron (NUEVO)",
            "crud_function": "Búsqueda de respuestas efectivas"
        }
    ]
}


def analyze_query_coverage():
    """
    Analiza cobertura de índices para queries frecuentes.
    """
    print("\n🔍 Análisis de Cobertura de Índices\n")
    print("=" * 80)
    
    for query_info in QUERY_PATTERNS["frequent_queries"]:
        print(f"Query: {query_info['pattern']}")
        print(f"  ✅ {query_info['optimization']}")
        print(f"  📍 Función: {query_info['crud_function']}")
        print()
    
    print(f"✅ {len(QUERY_PATTERNS['frequent_queries'])} queries frecuentes optimizadas")


if __name__ == "__main__":
    """
    Modo standalone para ver recomendaciones de índices.
    """
    print_index_recommendations()
    print()
    analyze_query_coverage()
