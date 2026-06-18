from typing import Optional

from langchain_core.tools import tool

from tools.database_tools import executar_query_postgres


def _avaliacao_tem_coluna_topico() -> bool:
    resultado = executar_query_postgres(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'avaliacao'
          AND column_name = 'topico_id'
        LIMIT 1;
        """
    )
    return bool(resultado)


def criar_avaliacao_raw(
    aluno_id: int,
    materia_id: int,
    titulo: str,
    topico_id: Optional[int] = None,
    status: str = "em_andamento",
) -> Optional[int]:
    if topico_id is not None and _avaliacao_tem_coluna_topico():
        resultado = executar_query_postgres(
            """
            INSERT INTO avaliacao (aluno_id, materia_id, topico_id, titulo, status, data_envio)
            VALUES (%s, %s, %s, %s, %s::status_avaliacao, NOW())
            RETURNING id;
            """,
            (aluno_id, materia_id, topico_id, titulo, status),
        )
    else:
        resultado = executar_query_postgres(
            """
            INSERT INTO avaliacao (aluno_id, materia_id, titulo, status, data_envio)
            VALUES (%s, %s, %s, %s::status_avaliacao, NOW())
            RETURNING id;
            """,
            (aluno_id, materia_id, titulo, status),
        )
    return resultado[0]["id"] if resultado else None


def atualizar_nota_feedback_raw(avaliacao_id: int, nota: float, feedback_ia: str) -> bool:
    resultado = executar_query_postgres(
        """
        UPDATE avaliacao
        SET nota = %s,
            feedback_ia = %s,
            status = 'corrigida'::status_avaliacao
        WHERE id = %s
        RETURNING id;
        """,
        (nota, feedback_ia, avaliacao_id),
    )
    return bool(resultado)


def gerar_avaliacao_automatica_raw(
    aluno_id: int,
    materia_id: int,
    topico_id: int,
    titulo_topico: str,
    resposta_aluno: str,
) -> dict:
    titulo = f"Avaliacao automatica - {titulo_topico}"
    avaliacao_id = criar_avaliacao_raw(
        aluno_id=aluno_id,
        materia_id=materia_id,
        topico_id=topico_id,
        titulo=titulo,
        status="em_andamento",
    )
    if not avaliacao_id:
        return {"ok": False, "mensagem": "Nao foi possivel criar a avaliacao automatica."}

    nota = 8.0
    if len(resposta_aluno.strip()) >= 120:
        nota = 9.0
    elif len(resposta_aluno.strip()) < 30:
        nota = 7.0

    feedback = (
        f"Avaliacao automatica do topico '{titulo_topico}'. "
        "O aluno demonstrou progresso suficiente para concluir o bloco. "
        "Recomenda-se revisar os pontos conceituais principais antes de avancar."
    )
    atualizar_nota_feedback_raw(avaliacao_id, nota, feedback)
    return {
        "ok": True,
        "avaliacao_id": avaliacao_id,
        "nota": nota,
        "feedback": feedback,
    }


def buscar_historico_avaliacoes_raw(
    aluno_id: int,
    materia_id: Optional[int] = None,
    limite: int = 10,
) -> list[dict]:
    params: list = [aluno_id]
    filtro_materia = ""
    if materia_id is not None:
        filtro_materia = "AND av.materia_id = %s"
        params.append(materia_id)
    params.append(limite)

    return executar_query_postgres(
        f"""
        SELECT av.id, av.aluno_id, av.materia_id, m.nome AS materia, av.titulo,
               av.nota, av.feedback_ia, av.status, av.data_envio
        FROM avaliacao av
        JOIN materia m ON m.id = av.materia_id
        WHERE av.aluno_id = %s
        {filtro_materia}
        ORDER BY av.data_envio DESC
        LIMIT %s;
        """,
        tuple(params),
    )


@tool
def criar_avaliacao(aluno_id: int, materia_id: int, titulo: str, topico_id: Optional[int] = None) -> str:
    """Cria uma avaliacao pendente/em andamento para aluno, materia e opcionalmente topico."""
    avaliacao_id = criar_avaliacao_raw(aluno_id, materia_id, titulo, topico_id)
    if not avaliacao_id:
        return "Nao foi possivel criar a avaliacao."
    return f"Avaliacao criada com ID {avaliacao_id}."


@tool
def atualizar_nota(avaliacao_id: int, nota: float) -> str:
    """Atualiza a nota de uma avaliacao."""
    ok = executar_query_postgres(
        "UPDATE avaliacao SET nota = %s WHERE id = %s RETURNING id;",
        (nota, avaliacao_id),
    )
    return "Nota atualizada." if ok else "Avaliacao nao localizada."


@tool
def atualizar_feedback(avaliacao_id: int, feedback_ia: str) -> str:
    """Atualiza o feedback de uma avaliacao."""
    ok = executar_query_postgres(
        "UPDATE avaliacao SET feedback_ia = %s WHERE id = %s RETURNING id;",
        (feedback_ia, avaliacao_id),
    )
    return "Feedback atualizado." if ok else "Avaliacao nao localizada."


@tool
def registrar_avaliacao_banco(
    aluno_id: int,
    materia_id: int,
    titulo: str,
    nota: float,
    feedback_ia: str,
    topico_id: Optional[int] = None,
) -> str:
    """Cria e corrige uma avaliacao com nota e feedback."""
    avaliacao_id = criar_avaliacao_raw(aluno_id, materia_id, titulo, topico_id)
    if not avaliacao_id:
        return "Erro: nao foi possivel criar o registro da avaliacao."
    if atualizar_nota_feedback_raw(avaliacao_id, nota, feedback_ia):
        return f"Sucesso: avaliacao {avaliacao_id} corrigida com nota {nota}."
    return "Erro: nao foi possivel corrigir a avaliacao."


@tool
def buscar_historico_avaliacoes(aluno_id: int, materia_id: Optional[int] = None, limite: int = 10) -> str:
    """Busca o historico de avaliacoes do aluno."""
    avaliacoes = buscar_historico_avaliacoes_raw(aluno_id, materia_id, limite)
    if not avaliacoes:
        return "Nenhuma avaliacao localizada."
    linhas = []
    for av in avaliacoes:
        linhas.append(
            f"- ID {av['id']} | {av['materia']} | {av['titulo']} | "
            f"nota={av['nota']} | status={av['status']} | feedback={av.get('feedback_ia') or 'sem feedback'}"
        )
    return "Historico de avaliacoes:\n" + "\n".join(linhas)


@tool
def calcular_desempenho_aluno(aluno_id: int) -> str:
    """Calcula media geral, total de avaliacoes e situacao academica."""
    resultado = executar_query_postgres(
        """
        SELECT
            a.nome,
            a.matricula,
            COALESCE(ROUND(AVG(av.nota), 1), 0.0) AS media_aluno,
            COUNT(av.id) AS total_avaliacoes,
            CASE
                WHEN COUNT(av.id) = 0 THEN 'SEM AVALIACAO'
                WHEN AVG(av.nota) >= 6 THEN 'APROVADO'
                ELSE 'REPROVADO'
            END AS status_academico
        FROM aluno a
        LEFT JOIN avaliacao av ON a.id = av.aluno_id AND av.status = 'corrigida'::status_avaliacao
        WHERE a.id = %s
        GROUP BY a.id, a.nome, a.matricula;
        """,
        (aluno_id,),
    )

    if not resultado:
        return "Prontuario ou dados academicos do aluno nao localizados."

    dados = resultado[0]
    return (
        "Ficha de Rendimento Escolar:\n"
        f"- Estudante: {dados['nome']} ({dados['matricula']})\n"
        f"- Media Geral Acumulada: {dados['media_aluno']}\n"
        f"- Quantidade de Avaliacoes Corrigidas: {dados['total_avaliacoes']}\n"
        f"- Situacao Atual: {dados['status_academico']}"
    )
