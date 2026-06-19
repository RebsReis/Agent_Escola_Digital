#Gerenciam o ciclo de vida do aluno e matérias.
import os
from typing import Optional

import psycopg2
from dotenv import load_dotenv
from langchain_core.tools import tool
from psycopg2.extras import RealDictCursor

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://usuario:senha@localhost:5432/escola_digital")


def executar_query_postgres(sql: str, params: tuple = ()) -> list[dict]:
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        cursor.execute(sql, params)

        resultados = []
        if cursor.description is not None:
            resultados = [dict(row) for row in cursor.fetchall()]

        conn.commit()
        return resultados
    except Exception as e:
        print(f"Erro ao executar query no PostgreSQL: {e}")
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def executar_comando_postgres(sql: str, params: tuple = ()) -> bool:
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao executar comando no PostgreSQL: {e}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def buscar_aluno_raw(aluno_id: Optional[int] = None, matricula: Optional[str] = None) -> Optional[dict]:
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
        return None
    return resultado[0] if resultado else None


def criar_aluno_raw(nome: str, matricula: str) -> Optional[dict]:
    existente = buscar_aluno_raw(matricula=matricula)
    if existente:
        return existente

    resultado = executar_query_postgres(
        """
        INSERT INTO aluno (nome, matricula)
        VALUES (%s, %s)
        RETURNING id, nome, matricula;
        """,
        (nome, matricula),
    )
    return resultado[0] if resultado else None


def listar_materias_disponiveis_raw() -> list[dict]:
    return executar_query_postgres("SELECT id, nome, descricao FROM materia ORDER BY id ASC;")


def consultar_matriculas_aluno_raw(aluno_id: int) -> list[dict]:
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
    resultado = executar_query_postgres(
        "SELECT 1 FROM matricula WHERE aluno_id = %s AND materia_id = %s LIMIT 1;",
        (aluno_id, materia_id),
    )
    return bool(resultado)


def matricular_aluno_raw(aluno_id: int, materia_id: int) -> str:
    if not buscar_aluno_raw(aluno_id=aluno_id):
        return "Aluno nao localizado."

    materia = executar_query_postgres("SELECT id, nome FROM materia WHERE id = %s;", (materia_id,))
    if not materia:
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
        return f"Matricula criada com sucesso em {materia[0]['nome']}."
    return f"O aluno ja estava matriculado em {materia[0]['nome']}."


def remover_matricula_raw(aluno_id: int, materia_id: int) -> str:
    materia = executar_query_postgres("SELECT id, nome FROM materia WHERE id = %s;", (materia_id,))
    if not materia:
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
        return f"Matricula removida com sucesso de {materia[0]['nome']}."
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
