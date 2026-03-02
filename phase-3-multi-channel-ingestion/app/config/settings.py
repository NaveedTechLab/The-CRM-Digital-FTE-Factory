from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database settings (from Phase 2)
    database_url: str = "postgresql://postgres:postgres@localhost:5432/internal_crm"

    # Kafka settings (from Phase 2)
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_inbound_events: str = "inbound_events"

    # Twilio settings for WhatsApp
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_number: Optional[str] = None

    # Gmail API settings
    gmail_client_id: Optional[str] = None
    gmail_client_secret: Optional[str] = None
    gmail_refresh_token: Optional[str] = None
    gmail_polling_interval: int = 30  # seconds

    # Web Form API Key
    web_form_api_key: Optional[str] = None

    # Meta WhatsApp Cloud API
    whatsapp_access_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_business_account_id: Optional[str] = None
    whatsapp_webhook_verify_token: str = "crm_fte_webhook_2026"

    # Security settings
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Logging
    log_level: str = "INFO"

    # Performance
    max_concurrent_connections: int = 10000
    message_normalization_timeout_ms: int = 100
    identity_lookup_timeout_ms: int = 200

    class Config:
        env_file = "../.env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()