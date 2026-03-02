from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from root .env file
_env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(_env_path)

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/internal_crm")

    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    INBOUND_EVENTS_TOPIC: str = os.getenv("INBOUND_EVENTS_TOPIC", "inbound_events")
    OUTBOUND_RESPONSES_TOPIC: str = os.getenv("OUTBOUND_RESPONSES_TOPIC", "outbound_responses")

    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: Optional[str] = os.getenv("OPENAI_BASE_URL", None)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # Agent settings
    AGENT_TIMEOUT_SECONDS: int = int(os.getenv("AGENT_TIMEOUT_SECONDS", "60"))
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
    MAX_CONVERSATION_HISTORY: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "50"))

    # Escalation settings
    ESCALATION_KEYWORDS: str = os.getenv("ESCALATION_KEYWORDS", "urgent,critical,complaint,unsatisfied,escalate,manager")
    ESCALATION_ENABLED: bool = os.getenv("ESCALATION_ENABLED", "true").lower() == "true"

    # Application settings
    APP_NAME: str = "Customer Success Agent"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    class Config:
        env_file = "../.env"
        case_sensitive = False
        extra = "ignore"

settings = Settings()