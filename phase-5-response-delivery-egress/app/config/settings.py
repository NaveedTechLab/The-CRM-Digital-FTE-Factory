from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # Application settings
    app_name: str = "Response Delivery Service"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8001

    # Database settings
    database_url: str = "postgresql://postgres:postgres@localhost:5432/internal_crm"

    # Kafka settings
    kafka_bootstrap_servers: str = "localhost:9092"

    # Redis settings
    redis_url: str = "redis://localhost:6379/0"

    # Gmail API settings
    gmail_credentials_path: Optional[str] = None
    gmail_token_path: Optional[str] = None
    gmail_sender_email: Optional[str] = None

    # Twilio settings (legacy)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_number: Optional[str] = None

    # Meta WhatsApp Cloud API
    whatsapp_access_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_business_account_id: Optional[str] = None

    # Rate limiting settings
    rate_limit_window_seconds: int = 60
    gmail_max_requests_per_minute: int = 250
    twilio_max_requests_per_minute: int = 100

    # Delivery settings
    delivery_retry_attempts: int = 3
    delivery_retry_delay_base: int = 5
    delivery_timeout_seconds: int = 30

    class Config:
        env_file = "../.env"
        case_sensitive = False
        extra = "ignore"

# Create a singleton instance of settings
settings = Settings()

def get_settings():
    """
    Get the application settings instance

    Returns:
        Settings: The application settings instance
    """
    return settings