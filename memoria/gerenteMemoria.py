"""
Gerenciador de Memória do Sistema Escola Digital.

Este módulo implementa persistência de conversas e contexto em banco de dados
PostgreSQL, permitindo que o sistema mantenha histórico de interações e
forneça contexto relevante para os agentes.
"""

import logging
from typing import Optional

import psycopg2
from langchain_core.messages import AIMessage, HumanMessage
from psycopg2.extras import RealDictCursor

from config import get_config

logger = logging.getLogger(__name__)


class GerenteMemoriaDB:
    """
    Gerenciador de persistência de memória em banco de dados.
    
    Responsável por salvar e recuperar conversas, contexto de matérias
    e histórico de interações dos alunos com o sistema.
    """
    
    def __init__(self):
        """Inicializa o gerente de memória com a URL de conexão do banco."""
        config = get_config()
        self.database_url = config.database.url
        logger.debug("GerenteMemoriaDB inicializado")

    def _executar_query(self, sql: str, params: tuple = ()) -> list[dict]:
        """
        Executa uma query no banco de dados.
        
        Args:
            sql: Comando SQL a executar.
            params: Parâmetros para evitar SQL injection.
        
        Returns:
            Lista de dicionários com os resultados.
        """
        conn = None
        cursor = None
        try:
            conn = psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
            cursor = conn.cursor()
            cursor.execute(sql, params)
            resultados = []
            if cursor.description is not None:
                resultados = [dict(row) for row in cursor.fetchall()]
            conn.commit()
            logger.debug(f"Query executada com sucesso. Retornou {len(resultados)} linhas.")
            return resultados
        except psycopg2.Error as e:
            logger.error(f"Erro ao acessar memória no PostgreSQL: {e}", exc_info=True)
            return []
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()

    def salvar_turno_conversa(
        self,
        role: str,
        conteudo: str,
        avaliacao_id: Optional[int] = None,
    ) -> bool:
        """
        Salva um turno de conversa no banco de dados.
        
        Args:
            role: Tipo de mensagem ('user' ou 'assistant').
            conteudo: Texto da mensagem.
            avaliacao_id: ID da avaliação (opcional).
        
        Returns:
            True se salvo com sucesso, False caso contrário.
        """
        if role not in ["user", "assistant"]:
            logger.warning(f"Role '{role}' inválida para salvar conversa")
            return False

        resultado = self._executar_query(
            """
            INSERT INTO historico_conversa (avaliacao_id, role, conteudo, criado_em)
            VALUES (%s, %s, %s, NOW())
            RETURNING id;
            """,
            (avaliacao_id, role, conteudo),
        )
        
        if resultado:
            logger.info(f"Turno de conversa salvo: {role}")
        return bool(resultado)

    def persistir_novas_mensagens_grafo(
        self,
        state: dict,
        avaliacao_id: Optional[int] = None,
    ) -> None:
        """
        Persiste as duas últimas mensagens do estado do grafo no banco.
        
        Args:
            state: Dicionário de estado do grafo LangGraph.
            avaliacao_id: ID da avaliação (opcional).
        """
        historico_mensagens = state.get("messages", [])
        if not historico_mensagens:
            logger.debug("Nenhuma mensagem para persistir")
            return

        for msg in historico_mensagens[-2:]:
            if isinstance(msg, HumanMessage):
                self.salvar_turno_conversa("user", msg.content, avaliacao_id)
            elif isinstance(msg, AIMessage):
                self.salvar_turno_conversa("assistant", msg.content, avaliacao_id)

    def buscar_ultimas_mensagens_globais(self, limite: int = 10) -> list[dict]:
        """
        Busca as últimas mensagens globais do sistema.
        
        Args:
            limite: Número máximo de mensagens a recuperar.
        
        Returns:
            Lista de dicionários com as mensagens em ordem cronológica.
        """
        resultado = self._executar_query(
            """
            SELECT id, role, conteudo, criado_em, avaliacao_id
            FROM historico_conversa
            ORDER BY criado_em DESC, id DESC
            LIMIT %s;
            """,
            (limite,),
        )
        return resultado[::-1]  # Retorna em ordem cronológica

    def buscar_contexto_materia(
        self,
        aluno_id: int,
        materia_id: int,
        limite: int = 10,
    ) -> list[dict]:
        """
        Busca o contexto histórico de conversas de um aluno em uma matéria.
        
        Args:
            aluno_id: ID do aluno.
            materia_id: ID da matéria.
            limite: Número máximo de mensagens a recuperar.
        
        Returns:
            Lista de dicionários com as mensagens em ordem cronológica.
        """
        resultado = self._executar_query(
            """
            SELECT hc.id, hc.role, hc.conteudo, hc.criado_em, hc.avaliacao_id
            FROM historico_conversa hc
            JOIN avaliacao av ON av.id = hc.avaliacao_id
            WHERE av.aluno_id = %s AND av.materia_id = %s
            ORDER BY hc.criado_em DESC, hc.id DESC
            LIMIT %s;
            """,
            (aluno_id, materia_id, limite),
        )
        return resultado[::-1]  # Retorna em ordem cronológica


def mensagens_para_texto(mensagens: list[dict]) -> str:
    """
    Converte uma lista de mensagens em formato texto para contexto.
    
    Args:
        mensagens: Lista de dicionários com as mensagens.
    
    Returns:
        String formatada com as mensagens ou mensagem padrão se vazio.
    """
    if not mensagens:
        return "Sem mensagens anteriores registradas."
    return "\n".join(f"{m['role']}: {m['conteudo']}" for m in mensagens)
