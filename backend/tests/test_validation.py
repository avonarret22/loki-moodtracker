"""
Tests para el módulo de validación y sanitización de inputs.
"""
import pytest
from app.core.validation import (
    sanitize_html,
    sanitize_phone_number,
    sanitize_json_string,
    validate_no_sql_injection,
    validate_no_xss,
    sanitize_user_input,
    validate_email,
    validate_url
)


class TestSanitizeHTML:
    """Tests para sanitize_html"""
    
    def test_sanitize_basic_html(self):
        """Debe escapar tags HTML básicos"""
        input_text = "<script>alert('xss')</script>Hello"
        result = sanitize_html(input_text)
        assert "&lt;script&gt;" in result
        assert "&lt;/script&gt;" in result
        assert "Hello" in result
    
    def test_sanitize_with_max_length(self):
        """Debe respetar el límite de longitud"""
        input_text = "A" * 1000
        result = sanitize_html(input_text, max_length=100)
        assert len(result) == 100
    
    def test_sanitize_empty_string(self):
        """Debe manejar strings vacíos"""
        assert sanitize_html("") == ""
        assert sanitize_html(None) == ""
    
    def test_sanitize_special_chars(self):
        """Debe escapar caracteres especiales HTML"""
        input_text = "<>&\"'"
        result = sanitize_html(input_text)
        assert "&lt;" in result
        assert "&gt;" in result


class TestSanitizePhoneNumber:
    """Tests para sanitize_phone_number"""
    
    def test_normalize_phone_with_parentheses(self):
        """Debe remover paréntesis y espacios"""
        phone = "+1 (555) 123-4567"
        result = sanitize_phone_number(phone)
        assert result == "+15551234567"
    
    def test_add_plus_prefix(self):
        """Debe agregar + si no existe"""
        phone = "525512345678"
        result = sanitize_phone_number(phone)
        assert result.startswith("+")
        assert result == "+525512345678"
    
    def test_remove_whatsapp_prefix(self):
        """Debe remover prefijo whatsapp:"""
        phone = "whatsapp:+525512345678"
        result = sanitize_phone_number(phone)
        assert "whatsapp:" not in result
        assert result == "+525512345678"
    
    def test_empty_phone(self):
        """Debe manejar teléfonos vacíos"""
        assert sanitize_phone_number("") == ""
        assert sanitize_phone_number(None) == ""


class TestSanitizeJSONString:
    """Tests para sanitize_json_string"""
    
    def test_remove_control_chars(self):
        """Debe remover caracteres de control"""
        input_text = "Hello\x00World\x1F"
        result = sanitize_json_string(input_text)
        assert "\x00" not in result
        assert "\x1F" not in result
        assert "HelloWorld" == result
    
    def test_escape_double_quotes(self):
        """Debe escapar comillas dobles"""
        input_text = 'Say "Hello"'
        result = sanitize_json_string(input_text)
        assert '\\"' in result
    
    def test_preserve_newlines(self):
        """Debe preservar newlines y tabs"""
        input_text = "Line1\nLine2\tTab"
        result = sanitize_json_string(input_text)
        assert "\n" in result
        assert "\t" in result


class TestValidateNoSQLInjection:
    """Tests para validate_no_sql_injection"""
    
    def test_detect_or_1_equals_1(self):
        """Debe detectar OR 1=1"""
        assert validate_no_sql_injection("OR 1=1") is False
        assert validate_no_sql_injection("' OR '1'='1") is False
    
    def test_detect_drop_table(self):
        """Debe detectar DROP TABLE"""
        assert validate_no_sql_injection("; DROP TABLE usuarios") is False
    
    def test_detect_union_select(self):
        """Debe detectar UNION SELECT"""
        assert validate_no_sql_injection("UNION SELECT * FROM usuarios") is False
    
    def test_detect_sql_comments(self):
        """Debe detectar comentarios SQL"""
        assert validate_no_sql_injection("admin' --") is False
        assert validate_no_sql_injection("admin' /* comment */") is False
    
    def test_allow_safe_text(self):
        """Debe permitir texto seguro"""
        assert validate_no_sql_injection("Me siento feliz") is True
        assert validate_no_sql_injection("Hoy corrí 5km") is True
        assert validate_no_sql_injection("") is True


class TestValidateNoXSS:
    """Tests para validate_no_xss"""
    
    def test_detect_script_tag(self):
        """Debe detectar tags <script>"""
        assert validate_no_xss("<script>alert('xss')</script>") is False
    
    def test_detect_javascript_protocol(self):
        """Debe detectar javascript: protocol"""
        assert validate_no_xss("javascript:alert(1)") is False
    
    def test_detect_event_handlers(self):
        """Debe detectar event handlers"""
        assert validate_no_xss("<img onclick='alert(1)'>") is False
        assert validate_no_xss("<div onload='alert(1)'>") is False
    
    def test_detect_iframe(self):
        """Debe detectar iframes"""
        assert validate_no_xss("<iframe src='evil.com'></iframe>") is False
    
    def test_allow_safe_text(self):
        """Debe permitir texto seguro"""
        assert validate_no_xss("Me siento feliz") is True
        assert validate_no_xss("Hoy es un buen día") is True
        assert validate_no_xss("") is True


class TestSanitizeUserInput:
    """Tests para sanitize_user_input (función principal)"""
    
    def test_reject_sql_injection(self):
        """Debe rechazar SQL injection"""
        with pytest.raises(ValueError, match="SQL injection"):
            sanitize_user_input("admin' OR '1'='1", check_sql=True)
    
    def test_reject_xss(self):
        """Debe rechazar XSS"""
        with pytest.raises(ValueError, match="XSS"):
            sanitize_user_input("<script>alert(1)</script>", check_xss=True)
    
    def test_sanitize_html_by_default(self):
        """Debe sanitizar HTML por defecto"""
        result = sanitize_user_input("<b>Hello</b>", allow_html=False)
        assert "<b>" not in result
        assert "&lt;b&gt;" in result
    
    def test_respect_max_length(self):
        """Debe respetar límite de longitud"""
        input_text = "A" * 1000
        result = sanitize_user_input(input_text, max_length=100)
        assert len(result) <= 100
    
    def test_allow_safe_text(self):
        """Debe permitir texto seguro sin modificar"""
        safe_text = "Me siento muy feliz hoy"
        result = sanitize_user_input(safe_text)
        # El texto puede estar escapado, pero debe contener el contenido
        assert "feliz" in result.lower()
    
    def test_skip_validations_when_disabled(self):
        """Debe permitir omitir validaciones"""
        # No debe lanzar error si las validaciones están deshabilitadas
        result = sanitize_user_input(
            "<script>alert(1)</script>",
            check_sql=False,
            check_xss=False,
            allow_html=True
        )
        assert result is not None


class TestValidateEmail:
    """Tests para validate_email"""
    
    def test_valid_emails(self):
        """Debe aceptar emails válidos"""
        assert validate_email("user@example.com") is True
        assert validate_email("test.user+tag@domain.co.uk") is True
    
    def test_invalid_emails(self):
        """Debe rechazar emails inválidos"""
        assert validate_email("invalid") is False
        assert validate_email("@domain.com") is False
        assert validate_email("user@") is False
        assert validate_email("") is False


class TestValidateURL:
    """Tests para validate_url"""
    
    def test_valid_urls(self):
        """Debe aceptar URLs válidas"""
        assert validate_url("https://example.com") is True
        assert validate_url("http://subdomain.example.com/path") is True
    
    def test_invalid_urls(self):
        """Debe rechazar URLs inválidas"""
        assert validate_url("not-a-url") is False
        assert validate_url("ftp://example.com") is False
        assert validate_url("") is False
