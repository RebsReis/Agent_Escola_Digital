#Controlam o fluxo de ensino

from langchain_core.tools import tool

from tools.database_tools import executar_query_postgres


def buscar_topicos_materia_raw(materia_id: int) -> list[dict]:
    return executar_query_postgres(
        """
        SELECT id, materia_id, titulo, descricao, ordem
        FROM topico
        WHERE materia_id = %s
        ORDER BY ordem;
        """,
        (materia_id,),
    )


def buscar_progresso_materia_raw(aluno_id: int, materia_id: int) -> dict:
    resultado = executar_query_postgres(
        """
        SELECT
            m.id AS materia_id,
            m.nome AS materia,
            COUNT(DISTINCT t.id) AS total_topicos,
            COUNT(DISTINCT ta.topico_id) AS topicos_concluidos,
            CASE
                WHEN COUNT(DISTINCT t.id) = 0 THEN 0.0
                ELSE ROUND((COUNT(DISTINCT ta.topico_id) * 100.0) / COUNT(DISTINCT t.id), 1)
            END AS percentual_conclusao
        FROM materia m
        LEFT JOIN topico t ON m.id = t.materia_id
        LEFT JOIN topico_aluno ta ON t.id = ta.topico_id AND ta.aluno_id = %s
        WHERE m.id = %s
        GROUP BY m.id, m.nome;
        """,
        (aluno_id, materia_id),
    )
    if resultado:
        return resultado[0]
    return {
        "materia_id": materia_id,
        "materia": "Materia nao localizada",
        "total_topicos": 0,
        "topicos_concluidos": 0,
        "percentual_conclusao": 0.0,
    }


def proximo_topico_pendente_raw(aluno_id: int, materia_id: int) -> dict | None:
    resultado = executar_query_postgres(
        """
        SELECT t.id, t.materia_id, t.titulo, t.descricao, t.ordem
        FROM topico t
        LEFT JOIN topico_aluno ta ON ta.topico_id = t.id AND ta.aluno_id = %s
        WHERE t.materia_id = %s AND ta.id IS NULL
        ORDER BY t.ordem
        LIMIT 1;
        """,
        (aluno_id, materia_id),
    )
    return resultado[0] if resultado else None


def topico_foi_concluido_raw(aluno_id: int, topico_id: int) -> bool:
    resultado = executar_query_postgres(
        "SELECT 1 FROM topico_aluno WHERE aluno_id = %s AND topico_id = %s LIMIT 1;",
        (aluno_id, topico_id),
    )
    return bool(resultado)


def marcar_topico_concluido_raw(aluno_id: int, topico_id: int) -> str:
    topico = executar_query_postgres(
        "SELECT id, titulo FROM topico WHERE id = %s;",
        (topico_id,),
    )
    if not topico:
        return "Topico nao localizado."

    resultado = executar_query_postgres(
        """
        INSERT INTO topico_aluno (aluno_id, topico_id, concluido_em)
        VALUES (%s, %s, NOW())
        ON CONFLICT (aluno_id, topico_id) DO NOTHING
        RETURNING id;
        """,
        (aluno_id, topico_id),
    )
    if resultado:
        return f"Topico concluido: {topico[0]['titulo']}."
    return f"O topico {topico[0]['titulo']} ja estava concluido."


@tool
def buscar_topicos_materia(materia_id: int) -> str:
    """Busca os topicos de uma materia."""
    topicos = buscar_topicos_materia_raw(materia_id)
    if not topicos:
        return "Nenhum topico localizado para esta materia."
    return "\n".join(
        f"- ID {t['id']} | Ordem {t['ordem']}: {t['titulo']} ({t.get('descricao') or 'sem descricao'})"
        for t in topicos
    )


@tool
def buscar_progresso_materia(aluno_id: int, materia_id: int) -> str:
    """Busca o progresso do aluno em uma materia especifica."""
    prog = buscar_progresso_materia_raw(aluno_id, materia_id)
    return (
        f"{prog['materia']}: {prog['topicos_concluidos']}/{prog['total_topicos']} "
        f"topicos concluidos ({prog['percentual_conclusao']}%)."
    )


@tool
def marcar_topico_concluido(aluno_id: int, topico_id: int) -> str:
    """Marca um topico como concluido para o aluno."""
    return marcar_topico_concluido_raw(aluno_id, topico_id)
