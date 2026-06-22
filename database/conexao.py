"""
Gerenciador de Conexões com o Banco de Dados.

Este módulo configura e fornece fábricas de sessão para acesso
ao banco de dados PostgreSQL usando SQLAlchemy.
"""

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import get_config

logger = logging.getLogger(__name__)

# Obtém configuração centralizada
config = get_config()

# Cria o motor de conexão com pool configurável
engine = create_engine(
    config.database.url,
    pool_size=config.database.pool_size,
    max_overflow=config.database.max_overflow,
    echo=config.database.echo,
)

# Fábrica de Sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger.info("Engine do banco de dados criado com sucesso")


def get_db():
    """
    Função geradora que fornece uma sessão do banco de dados.
    
    Yields:
        Sessão ativa do SQLAlchemy.
    
    Example:
        ```python
        for db in get_db():
            db.query(Model).all()
        ```
    """
    db = SessionLocal()
    try:
        logger.debug("Sessão de banco de dados criada")
        yield db
    except Exception as e:
        logger.error(f"Erro durante sessão de banco de dados: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        logger.debug("Sessão de banco de dados fechada")
        db.close()
