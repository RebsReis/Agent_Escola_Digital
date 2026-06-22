"""
Arquivo de configuração centralizado para o sistema Escola Digital.

Este módulo carrega e valida todas as variáveis de ambiente necessárias
para o funcionamento da aplicação, garantindo que o sistema falhe rápido
se alguma configuração obrigatória estiver faltando.
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()


@dataclass
class DatabaseConfig:
    """Configurações de banco de dados."""
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False
    
    def validate(self) -> None:
        """Valida a configuração do banco de dados."""
        if not self.url:
            raise ValueError("DATABASE_URL não foi configurada no arquivo .env")
        if not self.url.startswith(('postgresql://', 'postgres://')):
            raise ValueError(f"DATABASE_URL inválida. Esperado PostgreSQL, recebido: {self.url[:20]}")


@dataclass
class LLMConfig:
    """Configurações para o modelo de IA (LLM)."""
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    api_key: Optional[str] = None
    
    def validate(self) -> None:
        """Valida a configuração do LLM."""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY não foi configurada no arquivo .env")


@dataclass
class AppConfig:
    """Configuração completa da aplicação."""
    database: DatabaseConfig
    llm: LLMConfig
    debug: bool = False
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Cria a configuração a partir das variáveis de ambiente."""
        database = DatabaseConfig(
            url=os.getenv("DATABASE_URL", ""),
            pool_size=int(os.getenv("DB_POOL_SIZE", 10)),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", 20)),
            echo=os.getenv("DB_ECHO", "False").lower() == "true",
        )
        database.validate()
        
        llm = LLMConfig(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("LLM_TEMPERATURE", 0.0)),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        llm.validate()
        
        return cls(
            database=database,
            llm=llm,
            debug=os.getenv("DEBUG", "False").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
    
    def validate(self) -> None:
        """Valida toda a configuração."""
        self.database.validate()
        self.llm.validate()


# Instância global da configuração
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Obtém a instância global de configuração, criando-a se necessário."""
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config


def configure_logging(config: Optional[AppConfig] = None) -> logging.Logger:
    """
    Configura o sistema de logging da aplicação.
    
    Args:
        config: Configuração da aplicação. Se None, usa a global.
    
    Returns:
        Logger raiz configurado.
    """
    if config is None:
        config = get_config()
    
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    
    # Formata de log estruturado
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para console
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    # Configura o logger raiz
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(handler)
    
    return logger
