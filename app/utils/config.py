from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Governance Engine Configuration."""
    
    # Service
    service_name: str = "governance-engine"
    service_version: str = "1.0.0"
    port: int = 8033
    
    # RabbitMQ
    rabbitmq_url: str = "amqp://localhost:5672"
    rabbitmq_exchange: str = "autonomy.events"
    rabbitmq_exchange_type: str = "topic"
    
    # Knowledge Graph
    kg_service_url: str = "http://localhost:8034"
    
    # Event Consumers
    consumer_prefetch_count: int = 10
    consumer_auto_ack: bool = False
    dlq_enabled: bool = True
    
    # Rule Engine
    rule_cache_ttl: int = 300  # seconds
    rule_reload_interval: int = 60  # seconds
    
    # Decision Defaults
    default_confidence_threshold: float = 0.7
    decision_ttl: int = 3600  # seconds
    
    # OpenTelemetry
    otel_enabled: bool = True
    otel_endpoint: str = "http://localhost:4318"
    otel_service_name: str = "governance-engine"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Override Settings
    override_requires_approval: bool = True
    override_max_duration: int = 3600  # seconds
    
    # Emergency Settings
    emergency_stop_requires_reason: bool = True
    emergency_stop_auto_rollback: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
