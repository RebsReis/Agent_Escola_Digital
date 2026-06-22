"""
Ferramentas para gerenciamento do ciclo de vida do aluno e matérias.

Este módulo fornece funções para gerenciamento de alunos, matrículas,
matérias e consultas de progresso no banco de dados PostgreSQL.
"""

import logging
from typing import Optional

import psycopg2
from langchain_core.tools import tool
from psycopg2.extras import RealDictCursor

from config import get_config

logger = logging.getLogger(__name__)


def _get_connection():
    """
    Obtém uma conexão com o banco de dados PostgreSQL.
    
    Returns:
        Conexão ativa com o banco de dados.
    
    Raises:
        psycopg2.Error: Se não conseguir conectar ao banco.
    """
    config = get_config()
    return psycopg2.connect(config.database.url, cursor_factory=RealDictCursor)


def executar_query_postgres(sql: str, params: tuple = ()) -> list[dict]:
    """
    Executa uma query (SELECT) no PostgreSQL e retorna os resultados.
    
    Args:
        sql: Comando SQL a executar.
        params: Parâmetros para evitar SQL injection.
    
    Returns:
        Lista de dicionários com os resultados, ou lista vazia em caso de erro.
    """
    conn = None
    cursor = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)

        resultados = []
        if cursor.description is not None:
            resultados = [dict(row) for row in cursor.fetchall()]

        conn.commit()
        logger.debug(f"Query executada com sucesso. Retornou {len(resultados)} linhas.")
        return resultados
    except psycopg2.Error as e:
        logger.error(f"Erro ao executar query no PostgreSQL: {e}", exc_info=True)
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def executar_comando_postgres(sql: str, params: tuple = ()) -> bool:
    """
    Executa um comando (INSERT, UPDATE, DELETE) no PostgreSQL.
    
    Args:
        sql: Comando SQL a executar.
        params: Parâmetros para evitar SQL injection.
    
    Returns:
        True se o comando foi bem-sucedido, False caso contrário.
    """
    conn = None
    cursor = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        logger.debug(f"Comando SQL executado com sucesso. Linhas afetadas: {cursor.rowcount}")
        return True
    except psycopg2.Error as e:
        logger.error(f"Erro ao executar comando no PostgreSQL: {e}", exc_info=True)
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def buscar_aluno_raw(aluno_id: Optional[int] = None, matricula: Optional[str] = None) -> Optional[dict]:
    """
    Busca um aluno no banco de dados por ID ou matrícula.
    
    Args:
        aluno_id: ID do aluno (opcional).
        matricula: Matrícula do aluno (opcional).
    
    Returns:
        Dicionário com dados do aluno ou None se não encontrado.
    """
    if aluno_id is not None:
        resultado = executar_query_postgres(
            "SELECT id, nome, matricula FROM aluno WHERE id = %s;",
            (aluno_id,),
        )
    elif matricula:
        resultado = executar_query_postgres(
            "SELECT id, nome, matricula FROM aluno WHERE matricula = %s;",
            (matricula,),
        )
    else:
        logger.warning("buscar_aluno_raw chamado sem aluno_id ou matricula")
        return None
    
    return resultado[0] if resultado else None


def criar_aluno_raw(nome: str, matricula: str) -> Optional[dict]:
    """
    Cria um novo aluno ou retorna o cadastro existente para a matrícula.
    
    Args:
        nome: Nome completo do aluno.
        matricula: Matrícula única do aluno.
    
    Returns:
        Dicionário com dados do aluno ou None em caso de erro.
    """
    existente = buscar_aluno_raw(matricula=matricula)
    if existente:
        logger.info(f"Aluno com matrícula {matricula} já existe no banco")
        return existente

    resultado = executar_query_postgres(
        """
        INSERT INTO aluno (nome, matricula)
        VALUES (%s, %s)
        RETURNING id, nome, matricula;
        """,
        (nome, matricula),
    )
    
    if resultado:
        logger.info(f"Aluno criado com sucesso: {nome} ({matricula})")
    return resultado[0] if resultado else None


def listar_materias_disponiveis_raw() -> list[dict]:
    """
    Lista todas as matérias cadastradas no sistema.
    
    Returns:
        Lista de dicionários com as matérias disponíveis.
    """
    return executar_query_postgres("SELECT id, nome, descricao FROM materia ORDER BY id ASC;")


def consultar_matriculas_aluno_raw(aluno_id: int) -> list[dict]:
    """
    Consulta todas as matrículas ativas de um aluno.
    
    Args:
        aluno_id: ID do aluno.
    
    Returns:
        Lista de dicionários com as matérias do aluno.
    """
    return executar_query_postgres(
        """
        SELECT m.id, m.nome, m.descricao
        FROM matricula mat
        JOIN materia m ON mat.materia_id = m.id
        WHERE mat.aluno_id = %s
        ORDER BY m.id;
        """,
        (aluno_id,),
    )


def aluno_esta_matriculado_raw(aluno_id: int, materia_id: int) -> bool:
    """
    Verifica se um aluno está matriculado em uma matéria específica.
    
    Args:
        aluno_id: ID do aluno.
        materia_id: ID da matéria.
    
    Returns:
        True se matriculado, False caso contrário.
    """
    resultado = executar_query_postgres(
        "SELECT 1 FROM matricula WHERE aluno_id = %s AND materia_id = %s LIMIT 1;",
        (aluno_id, materia_id),
    )
    return bool(resultado)


def matricular_aluno_raw(aluno_id: int, materia_id: int) -> str:
    """
    Matricula um aluno em uma matéria.
    
    Args:
        aluno_id: ID do aluno.
        materia_id: ID da matéria.
    
    Returns:
        Mensagem de sucesso ou erro.
    """
    if not buscar_aluno_raw(aluno_id=aluno_id):
        logger.warning(f"Tentativa de matricular aluno inexistente: {aluno_id}")
        return "Aluno nao localizado."

    materia = executar_query_postgres("SELECT id, nome FROM materia WHERE id = %s;", (materia_id,))
    if not materia:
        logger.warning(f"Tentativa de matricular em matéria inexistente: {materia_id}")
        return "Materia nao localizada."

    resultado = executar_query_postgres(
        """
        INSERT INTO matricula (aluno_id, materia_id, data_matricula)
        VALUES (%s, %s, NOW())
        ON CONFLICT (aluno_id, materia_id) DO NOTHING
        RETURNING id;
        """,
        (aluno_id, materia_id),
    )

    if resultado:
        logger.info(f"Aluno {aluno_id} matriculado em {materia[0]['nome']}")
        return f"Matricula criada com sucesso em {materia[0]['nome']}."
    return f"O aluno ja estava matriculado em {materia[0]['nome']}."


def remover_matricula_raw(aluno_id: int, materia_id: int) -> str:
    """
    Remove a matrícula de um aluno em uma matéria.
    
    Args:
        aluno_id: ID do aluno.
        materia_id: ID da matéria.
    
    Returns:
        Mensagem de sucesso ou erro.
    """
    materia = executar_query_postgres("SELECT id, nome FROM materia WHERE id = %s;", (materia_id,))
    if not materia:
        logger.warning(f"Tentativa de remover matrícula em matéria inexistente: {materia_id}")
        return "Materia nao localizada."

    resultado = executar_query_postgres(
        """
        DELETE FROM matricula
        WHERE aluno_id = %s AND materia_id = %s
        RETURNING id;
        """,
        (aluno_id, materia_id),
    )

    if resultado:
        logger.info(f"Matrícula removida: aluno {aluno_id} de {materia[0]['nome']}")
        return f"Matricula removida com sucesso de {materia[0]['nome']}."
    
    logger.warning(f"Nenhuma matrícula encontrada para remover: aluno {aluno_id}, matéria {materia_id}")
    return f"Nao havia matricula ativa em {materia[0]['nome']}."



def buscar_diretrizes_materia(materia_id: int) -> str:
    resultado = executar_query_postgres(
        "SELECT prompt_ia, nome FROM materia WHERE id = %s;",
        (materia_id,),
    )

    if resultado:
        return f"Diretrizes para a Materia {resultado[0]['nome']}: {resultado[0]['prompt_ia']}"
    return "Voce e um professor tutor dedicado de uma Escola Digital."


def _formatar_materias(materias: list[dict], vazio: str) -> str:
    if not materias:
        return vazio
    linhas = [f"- ID {mat['id']}: {mat['nome']} ({mat.get('descricao') or 'sem descricao'})" for mat in materias]
    return "\n".join(linhas)


@tool
def buscar_aluno(aluno_id: Optional[int] = None, matricula: Optional[str] = None) -> str:
    """Busca aluno por id ou matricula."""
    aluno = buscar_aluno_raw(aluno_id=aluno_id, matricula=matricula)
    if not aluno:
        return "Aluno nao localizado."
    return f"Aluno localizado: ID {aluno['id']} - {aluno['nome']} ({aluno['matricula']})."


@tool
def criar_aluno(nome: str, matricula: str) -> str:
    """Cria um aluno ou retorna o cadastro existente para a matricula informada."""
    aluno = criar_aluno_raw(nome=nome, matricula=matricula)
    if not aluno:
        return "Nao foi possivel criar o aluno."
    return f"Aluno cadastrado/localizado: ID {aluno['id']} - {aluno['nome']} ({aluno['matricula']})."


@tool
def listar_materias_disponiveis() -> str:
    """Busca todas as materias cadastradas na instituicao."""
    materias = listar_materias_disponiveis_raw()
    return "Materias cadastradas no sistema institucional:\n" + _formatar_materias(
        materias,
        "Nenhuma materia localizada no sistema de secretaria.",
    )


@tool
def consultar_matriculas_aluno(aluno_id: int) -> str:
    """Consulta em quais materias um aluno possui vinculo de matricula ativa."""
    materias = consultar_matriculas_aluno_raw(aluno_id)
    return "Disciplinas vinculadas ao prontuario do aluno:\n" + _formatar_materias(
        materias,
        "O aluno nao possui nenhuma matricula ativa registrada neste momento.",
    )


@tool
def matricular_aluno(aluno_id: int, materia_id: int) -> str:
    """Matricula um aluno em uma materia."""
    return matricular_aluno_raw(aluno_id, materia_id)


@tool
def remover_matricula(aluno_id: int, materia_id: int) -> str:
    """Remove a matricula de um aluno em uma materia."""
    return remover_matricula_raw(aluno_id, materia_id)


@tool
def buscar_progresso_geral_aluno(aluno_id: int) -> str:
    """Busca o progresso geral do aluno em todas as materias matriculadas."""
    resultado = executar_query_postgres(
        """
        SELECT
            m.nome AS materia,
            COUNT(DISTINCT t.id) AS total_topicos,
            COUNT(DISTINCT ta.topico_id) AS topicos_concluidos,
            CASE
                WHEN COUNT(DISTINCT t.id) = 0 THEN 0.0
                ELSE ROUND((COUNT(DISTINCT ta.topico_id) * 100.0) / COUNT(DISTINCT t.id), 1)
            END AS percentual_conclusao
        FROM matricula mat
        JOIN aluno a ON mat.aluno_id = a.id
        JOIN materia m ON mat.materia_id = m.id
        LEFT JOIN topico t ON m.id = t.materia_id
        LEFT JOIN topico_aluno ta ON t.id = ta.topico_id AND ta.aluno_id = a.id
        WHERE a.id = %s
        GROUP BY a.id, a.nome, m.id, m.nome
        ORDER BY materia ASC;
        """,
        (aluno_id,),
    )

    if not resultado:
        return "Nenhum historico de progresso de topicos foi localizado para este aluno."

    linhas = []
    for prog in resultado:
        linhas.append(
            f"- {prog['materia']}: {prog['topicos_concluidos']}/{prog['total_topicos']} concluidos "
            f"({prog['percentual_conclusao']}% do plano de estudos)"
        )
    return "Demonstrativo de Progresso Academico:\n" + "\n".join(linhas)
