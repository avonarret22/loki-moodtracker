"""
Tests para el sistema de logging estructurado.
"""
import pytest
import logging
import json
from pathlib import Path
from app.core.logging_config import (
    setup_logging,
    get_logger,
    set_request_context,
    clear_request_context,
    StructuredFormatter,
    SimpleFormatter,
    AuditLogger,
)


class TestStructuredFormatter:
    """Tests para el formatter JSON."""
    
    def test_basic_json_format(self):
        """Verifica que genera JSON válido."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data['level'] == 'INFO'
        assert data['logger'] == 'test'
        assert data['message'] == 'Test message'
        assert 'timestamp' in data
    
    def test_includes_request_context(self):
        """Verifica que incluye contexto de request."""
        formatter = StructuredFormatter()
        
        # Establecer contexto
        set_request_context(request_id='req-123', user_id=42)
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='With context',
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data['request_id'] == 'req-123'
        assert data['user_id'] == 42
        
        # Limpiar contexto
        clear_request_context()
    
    def test_includes_exception_info(self):
        """Verifica que incluye información de exception."""
        formatter = StructuredFormatter()
        
        try:
            1 / 0
        except ZeroDivisionError:
            import sys
            exc_info = sys.exc_info()
            
            record = logging.LogRecord(
                name='test',
                level=logging.ERROR,
                pathname='test.py',
                lineno=10,
                msg='Error occurred',
                args=(),
                exc_info=exc_info,
            )
            
            result = formatter.format(record)
            data = json.loads(result)
            
            assert 'exception' in data
            assert 'ZeroDivisionError' in data['exception']


class TestSimpleFormatter:
    """Tests para el formatter simple."""
    
    def test_basic_format(self):
        """Verifica formato básico."""
        formatter = SimpleFormatter()
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        
        assert 'INFO' in result
        assert 'test' in result
        assert 'Test message' in result
    
    def test_includes_context_in_brackets(self):
        """Verifica que incluye contexto en corchetes."""
        formatter = SimpleFormatter()
        
        set_request_context(request_id='req-456', user_id=99)
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Message',
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        
        assert 'request_id=req-456' in result
        assert 'user_id=99' in result
        
        clear_request_context()


class TestSetupLogging:
    """Tests para la función setup_logging."""
    
    def test_creates_log_directory(self, tmp_path):
        """Verifica que crea el directorio de logs."""
        log_dir = tmp_path / 'test_logs'
        
        logger, audit_logger = setup_logging(
            environment='development',
            log_dir=log_dir,
            enable_console=False,
            enable_file=True,
        )
        
        assert log_dir.exists()
    
    def test_creates_audit_logger_when_enabled(self, tmp_path):
        """Verifica que crea audit logger."""
        log_dir = tmp_path / 'test_logs'
        
        logger, audit_logger = setup_logging(
            environment='development',
            log_dir=log_dir,
            enable_audit=True,
        )
        
        assert audit_logger is not None
        assert isinstance(audit_logger, AuditLogger)
    
    def test_no_audit_logger_when_disabled(self, tmp_path):
        """Verifica que no crea audit logger si está deshabilitado."""
        log_dir = tmp_path / 'test_logs'
        
        logger, audit_logger = setup_logging(
            environment='development',
            log_dir=log_dir,
            enable_audit=False,
        )
        
        assert audit_logger is None
    
    def test_production_uses_json_format(self, tmp_path):
        """Verifica que producción usa JSON formatter."""
        log_dir = tmp_path / 'test_logs'
        
        logger, _ = setup_logging(
            environment='production',
            log_dir=log_dir,
            enable_console=True,
        )
        
        # Verificar que al menos un handler usa StructuredFormatter
        has_json_formatter = any(
            isinstance(h.formatter, StructuredFormatter)
            for h in logger.handlers
        )
        assert has_json_formatter
    
    def test_development_uses_simple_format(self, tmp_path):
        """Verifica que desarrollo usa SimpleFormatter."""
        log_dir = tmp_path / 'test_logs'
        
        logger, _ = setup_logging(
            environment='development',
            log_dir=log_dir,
            enable_console=True,
        )
        
        # Verificar que al menos un handler usa SimpleFormatter
        has_simple_formatter = any(
            isinstance(h.formatter, SimpleFormatter)
            for h in logger.handlers
        )
        assert has_simple_formatter


class TestAuditLogger:
    """Tests para AuditLogger."""
    
    @pytest.fixture
    def audit_logger(self, tmp_path):
        """Fixture que crea un audit logger."""
        log_dir = tmp_path / 'test_logs'
        _, audit = setup_logging(
            environment='development',
            log_dir=log_dir,
            enable_audit=True,
        )
        return audit
    
    def test_log_user_created(self, audit_logger):
        """Verifica log de creación de usuario."""
        # No debe lanzar error
        audit_logger.log_user_created(
            user_id=1,
            telefono='+1234567890',
            ip='127.0.0.1'
        )
    
    def test_log_habito_created(self, audit_logger):
        """Verifica log de creación de hábito."""
        audit_logger.log_habito_created(
            user_id=1,
            habito_id=10,
            nombre='Meditar'
        )
    
    def test_log_habito_updated(self, audit_logger):
        """Verifica log de actualización de hábito."""
        audit_logger.log_habito_updated(
            user_id=1,
            habito_id=10,
            changes={'activo': False}
        )
    
    def test_log_habito_deleted(self, audit_logger):
        """Verifica log de eliminación de hábito."""
        audit_logger.log_habito_deleted(
            user_id=1,
            habito_id=10
        )
    
    def test_log_auth_failure(self, audit_logger):
        """Verifica log de fallo de autenticación."""
        audit_logger.log_auth_failure(
            telefono='+9999999999',
            reason='Invalid token'
        )
    
    def test_log_rate_limit_exceeded(self, audit_logger):
        """Verifica log de rate limit excedido."""
        audit_logger.log_rate_limit_exceeded(
            endpoint='/api/v1/users',
            identifier='127.0.0.1'
        )


class TestRequestContext:
    """Tests para contexto de request."""
    
    def test_set_and_get_request_id(self):
        """Verifica que se puede establecer y obtener request_id."""
        from app.core.logging_config import request_id_var
        
        set_request_context(request_id='test-123')
        assert request_id_var.get() == 'test-123'
        
        clear_request_context()
        assert request_id_var.get() is None
    
    def test_set_and_get_user_id(self):
        """Verifica que se puede establecer y obtener user_id."""
        from app.core.logging_config import user_id_var
        
        set_request_context(user_id=42)
        assert user_id_var.get() == 42
        
        clear_request_context()
        assert user_id_var.get() is None
    
    def test_set_both_context_values(self):
        """Verifica que se pueden establecer ambos valores."""
        from app.core.logging_config import request_id_var, user_id_var
        
        set_request_context(request_id='req-999', user_id=123)
        
        assert request_id_var.get() == 'req-999'
        assert user_id_var.get() == 123
        
        clear_request_context()


class TestGetLogger:
    """Tests para get_logger."""
    
    def test_returns_logger_with_name(self):
        """Verifica que retorna logger con el nombre correcto."""
        logger = get_logger('test.module')
        assert logger.name == 'test.module'
    
    def test_returns_logging_logger(self):
        """Verifica que retorna instancia de logging.Logger."""
        logger = get_logger('test')
        assert isinstance(logger, logging.Logger)


class TestLogLevels:
    """Tests para niveles de log configurables."""
    
    def test_different_log_levels(self, tmp_path):
        """Verifica que se pueden configurar diferentes niveles."""
        log_dir = tmp_path / 'test_logs'
        
        # Debug level
        logger_debug, _ = setup_logging(
            environment='development',
            log_dir=log_dir,
            log_level='DEBUG',
        )
        assert logger_debug.level == logging.DEBUG
        
        # Info level
        logger_info, _ = setup_logging(
            environment='development',
            log_dir=log_dir / 'info',
            log_level='INFO',
        )
        assert logger_info.level == logging.INFO
        
        # Warning level
        logger_warning, _ = setup_logging(
            environment='development',
            log_dir=log_dir / 'warning',
            log_level='WARNING',
        )
        assert logger_warning.level == logging.WARNING
