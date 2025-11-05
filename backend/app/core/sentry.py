"""
Sentry configuration for error tracking and performance monitoring
"""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from app.core.config import settings
from app.core.logger import setup_logger
import os

logger = setup_logger(__name__)


def init_sentry():
    """
    Initialize Sentry SDK for error tracking.
    Only initializes if SENTRY_DSN environment variable is set.
    """
    sentry_dsn = os.getenv("SENTRY_DSN")
    environment = os.getenv("RAILWAY_ENVIRONMENT", "development")
    
    if not sentry_dsn:
        logger.warning("SENTRY_DSN not configured - Sentry error tracking disabled")
        return
    
    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
            # We recommend adjusting this value in production.
            traces_sample_rate=0.1 if environment == "production" else 1.0,
            # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.
            # We recommend adjusting this value in production.
            profiles_sample_rate=0.1 if environment == "production" else 1.0,
            # Integrations
            integrations=[
                FastApiIntegration(transaction_style="url"),
                SqlalchemyIntegration(),
            ],
            # Send default PII (Personally Identifiable Information)
            send_default_pii=False,  # Set to False for privacy
            # Release tracking
            release=f"loki-moodtracker@{settings.VERSION}",
            # Custom tags
            _experiments={
                "profiles_sample_rate": 0.1 if environment == "production" else 1.0,
            },
        )
        
        logger.info(f"✅ Sentry initialized successfully (environment: {environment})")
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def capture_exception(error: Exception, context: dict = None):
    """
    Manually capture an exception to Sentry with additional context.
    
    Args:
        error: The exception to capture
        context: Additional context dictionary to attach to the error
    """
    if context:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_context(key, value)
            sentry_sdk.capture_exception(error)
    else:
        sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", context: dict = None):
    """
    Manually capture a message to Sentry with additional context.
    
    Args:
        message: The message to capture
        level: Severity level ("debug", "info", "warning", "error", "fatal")
        context: Additional context dictionary to attach to the message
    """
    if context:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_context(key, value)
            sentry_sdk.capture_message(message, level=level)
    else:
        sentry_sdk.capture_message(message, level=level)


def set_user_context(user_id: int, phone: str = None):
    """
    Set user context for Sentry error tracking.
    
    Args:
        user_id: User ID
        phone: User phone (optional, will be masked for privacy)
    """
    user_data = {"id": user_id}
    
    if phone:
        # Mask phone number for privacy (show only last 4 digits)
        masked_phone = f"****{phone[-4:]}" if len(phone) >= 4 else "****"
        user_data["phone"] = masked_phone
    
    sentry_sdk.set_user(user_data)
