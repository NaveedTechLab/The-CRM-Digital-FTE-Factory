"""
Security configuration for the Response Delivery & Egress system
"""

import os
from typing import List, Optional
from dataclasses import dataclass
from ..config.settings import settings


@dataclass
class SecurityConfig:
    """
    Security configuration settings
    """
    # API Key validation
    require_api_key: bool = True
    api_key_header: str = "X-API-Key"

    # Credential validation
    validate_credentials_on_startup: bool = True
    require_encrypted_credentials: bool = True

    # Rate limiting security
    enable_rate_limiting: bool = True
    rate_limit_storage_encrypted: bool = True

    # Logging security
    mask_sensitive_data_in_logs: bool = True
    log_security_events: bool = True

    # API access controls
    allowed_origins: List[str] = None
    enable_cors: bool = True
    cors_allow_credentials: bool = True

    # Encryption settings
    encryption_algorithm: str = "Fernet"
    encryption_key_rotation_days: int = 30

    # Audit trail
    enable_audit_logging: bool = True
    audit_log_retention_days: int = 90


# Initialize security configuration
security_config = SecurityConfig(
    allowed_origins=getattr(settings, 'allowed_origins', ['*']) if hasattr(settings, 'allowed_origins') else ['*']
)


def validate_gmail_credentials() -> bool:
    """
    Validate Gmail API credentials

    Returns:
        bool: True if credentials are valid, False otherwise
    """
    required_vars = [
        'GMAIL_CREDENTIALS_PATH',
        'GMAIL_TOKEN_PATH',
        'GMAIL_SENDER_EMAIL'
    ]

    for var in required_vars:
        value = getattr(settings, var.lower(), None) or os.getenv(var)
        if not value:
            print(f"Warning: {var} not configured")
            return False

    # Additional validation can be added here
    sender_email = getattr(settings, 'gmail_sender_email', None) or os.getenv('GMAIL_SENDER_EMAIL')
    if sender_email:
        # Basic email format validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, sender_email):
            print(f"Warning: Invalid email format for GMAIL_SENDER_EMAIL: {sender_email}")
            return False

    return True


def validate_twilio_credentials() -> bool:
    """
    Validate Twilio API credentials

    Returns:
        bool: True if credentials are valid, False otherwise
    """
    required_vars = [
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN',
        'TWILIO_WHATSAPP_NUMBER'
    ]

    for var in required_vars:
        value = getattr(settings, var.lower(), None) or os.getenv(var)
        if not value:
            print(f"Warning: {var} not configured")
            return False

    # Additional validation can be added here
    whatsapp_number = getattr(settings, 'twilio_whatsapp_number', None) or os.getenv('TWILIO_WHATSAPP_NUMBER')
    if whatsapp_number:
        # Basic phone number validation
        import re
        # Accept various phone number formats
        phone_pattern = r'^\+[1-9]\d{1,14}$|^whatsapp:\+[1-9]\d{1,14}$'
        if not re.match(phone_pattern, whatsapp_number):
            print(f"Warning: Invalid phone number format for TWILIO_WHATSAPP_NUMBER: {whatsapp_number}")
            return False

    return True


def validate_database_credentials() -> bool:
    """
    Validate database credentials

    Returns:
        bool: True if credentials are valid, False otherwise
    """
    required_vars = [
        'DATABASE_URL'
    ]

    for var in required_vars:
        value = getattr(settings, var.lower(), None) or os.getenv(var)
        if not value:
            print(f"Warning: {var} not configured")
            return False

    # Additional validation can be added here
    db_url = getattr(settings, 'database_url', None) or os.getenv('DATABASE_URL')
    if db_url and 'localhost' not in db_url and '127.0.0.1' not in db_url:
        # For production, ensure SSL is enabled
        if 'sslmode=require' not in db_url.lower() and 'ssl=true' not in db_url.lower():
            print("Warning: SSL not enabled in database URL for production use")
            # Note: This is just a warning, not a hard failure

    return True


def validate_all_credentials() -> bool:
    """
    Validate all API credentials

    Returns:
        bool: True if all credentials are valid, False otherwise
    """
    gmail_valid = validate_gmail_credentials()
    twilio_valid = validate_twilio_credentials()
    database_valid = validate_database_credentials()

    all_valid = gmail_valid and twilio_valid and database_valid

    if not all_valid:
        print("WARNING: Some credentials are not properly configured.")
        print("Please check your .env file and configuration settings.")

    return all_valid


def get_security_headers() -> dict:
    """
    Get recommended security headers

    Returns:
        dict: Security headers to apply
    """
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    }


def sanitize_log_data(data: dict) -> dict:
    """
    Sanitize sensitive data from logs

    Args:
        data: Dictionary containing log data

    Returns:
        dict: Sanitized log data with sensitive information masked
    """
    sanitized = data.copy()

    # Fields to mask in logs
    sensitive_fields = [
        'auth_token', 'token', 'password', 'secret', 'key',
        'credentials', 'api_key', 'access_token', 'refresh_token',
        'gmail_token_path', 'gmail_credentials_path'
    ]

    for key, value in sanitized.items():
        if isinstance(key, str) and any(field.lower() in key.lower() for field in sensitive_fields):
            sanitized[key] = "***MASKED***"
        elif isinstance(value, str) and any(field.lower() in value.lower() for field in sensitive_fields):
            sanitized[key] = "***MASKED***"
        elif isinstance(value, dict):
            # Recursively sanitize nested dictionaries
            sanitized[key] = sanitize_log_data(value)

    return sanitized


def check_security_config() -> dict:
    """
    Check security configuration and return status

    Returns:
        dict: Security configuration status
    """
    return {
        "api_keys_configured": validate_all_credentials(),
        "rate_limiting_enabled": security_config.enable_rate_limiting,
        "cors_enabled": security_config.enable_cors,
        "audit_logging_enabled": security_config.enable_audit_logging,
        "credential_validation_enabled": security_config.validate_credentials_on_startup
    }


# Validate credentials on module import if configured to do so
if security_config.validate_credentials_on_startup:
    validate_all_credentials()