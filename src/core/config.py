from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List, Union
import os

class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente."""
    
    # Aplicação
    app_name: str = "TextFile Manager API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str
    database_pool_min_size: int = 5
    database_pool_max_size: int = 20
    
    # JWT / Segurança
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://github.com",
        "https://teste-phi-eosin.vercel.app",
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json ou text
    
    # Ambiente
    environment: str = "development"  # development, staging, production
    
    # A configuração agora usa o model_config moderno do Pydantic V2
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore" # Isso aqui é ouro: evita que o app quebre se tiver lixo no seu .env
    )

    @property
    def is_production(self) -> bool:
        """Verifica se está em produção."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Verifica se está em desenvolvimento."""
        return self.environment == "development"


# Singleton da configuração
settings = Settings()