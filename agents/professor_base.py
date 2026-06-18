import os
from typing import Any, Dict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from tools.database_tools import buscar_diretrizes_materia
from tools.evaluation_tools import gerar_avaliacao_automatica_raw
from tools.topic_tools import (
    buscar_progresso_materia_raw,
    buscar_topicos_materia_raw,
    marcar_topico_concluido_raw,
    proximo_topico_pendente_raw,
)


HISTORICO_POR_MATERIA = {
    1: "historico_sql",
    2: "historico_engenharia",
    3: "historico_ia",
    4: "historico_bpo",
}

ROTA_POR_MATERIA = {
    1: "sql",
    2: "engenharia",
    3: "ia",
    4: "bpo",
}


def _carregar_prompt_professor() -> str:
    caminho_prompt = os.path.join("prompts", "professor.txt")
    if os.path.exists(caminho_prompt):
        with open(caminho_prompt, "r", encoding="utf-8") as f:
            return f.read()
    return "Voce e um professor tutor dedicado de uma Escola Digital."


def _deve_concluir_topico(texto: str) -> bool:
    texto = texto.lower()
    gatilhos = [
        "concluir topico",
        "concluir tópico",
        "finalizar topico",
        "finalizar tópico",
        "terminei o topico",
        "terminei o tópico",
        "entendi o topico",
        "entendi o tópico",
        "pode avaliar",
        "fazer avaliacao",
        "fazer avaliação",
    ]
    return any(gatilho in texto for gatilho in gatilhos)


def _historico_limitado(state: Dict[str, Any], materia_id: int, limite: int = 10) -> list[BaseMessage]:
    chave = HISTORICO_POR_MATERIA[materia_id]
    historico = list(state.get(chave, []))
    return historico[-limite:]


def executar_professor_materia(
    state: Dict[str, Any],
    materia_id: int,
    titulo_professor: str,
    instrucoes_especificas: str,
    temperature: float = 0.3,
) -> dict:
    historico_global = state.get("messages", [])
    aluno_id = state.get("aluno_id", 1)
    aluno_nome = state.get("aluno_nome", "Aluno")
    ultima_msg = historico_global[-1] if historico_global else HumanMessage(content="")
    texto_aluno = ultima_msg.content

    topicos = buscar_topicos_materia_raw(materia_id)
    progresso = buscar_progresso_materia_raw(aluno_id, materia_id)
    proximo_topico = proximo_topico_pendente_raw(aluno_id, materia_id)
    topico_atual = proximo_topico or (topicos[-1] if topicos else None)

    chave_historico = HISTORICO_POR_MATERIA[materia_id]
    historico_materia = _historico_limitado(state, materia_id)

    if _deve_concluir_topico(texto_aluno) and topico_atual:
        mensagem_conclusao = marcar_topico_concluido_raw(aluno_id, topico_atual["id"])
        avaliacao = gerar_avaliacao_automatica_raw(
            aluno_id=aluno_id,
            materia_id=materia_id,
            topico_id=topico_atual["id"],
            titulo_topico=topico_atual["titulo"],
            resposta_aluno=texto_aluno,
        )
        if avaliacao.get("ok"):
            conteudo = (
                f"{mensagem_conclusao}\n"
                f"Avaliacao automatica gerada e corrigida.\n"
                f"Nota: {avaliacao['nota']}\n"
                f"Feedback: {avaliacao['feedback']}"
            )
            avaliacao_id = avaliacao.get("avaliacao_id")
        else:
            conteudo = f"{mensagem_conclusao}\n{avaliacao.get('mensagem')}"
            avaliacao_id = None

        resposta = AIMessage(content=conteudo)
        novo_historico = (historico_materia + [ultima_msg, resposta])[-10:]
        completed_topics = list(state.get("completed_topics", []))
        if topico_atual["id"] not in completed_topics:
            completed_topics.append(topico_atual["id"])
        return {
            "messages": [resposta],
            chave_historico: novo_historico,
            "materia_id": materia_id,
            "topico_atual_id": topico_atual["id"],
            "last_agent": ROTA_POR_MATERIA[materia_id],
            "current_subject": str(materia_id),
            "completed_topics": completed_topics,
            "avaliacao_id": avaliacao_id,
        }

    prompt_base = _carregar_prompt_professor()
    persona_banco = buscar_diretrizes_materia(materia_id)
    lista_topicos = "\n".join(
        f"- ID {t['id']} | Ordem {t['ordem']}: {t['titulo']} - {t.get('descricao') or ''}"
        for t in topicos
    )
    topico_atual_texto = (
        f"ID {topico_atual['id']} - {topico_atual['titulo']}: {topico_atual.get('descricao') or ''}"
        if topico_atual
        else "Todos os topicos desta materia ja foram concluidos."
    )

    system_instruction = f"""
    {persona_banco}

    Diretrizes Gerais de Tutoria:
    {prompt_base}

    Professor especialista:
    {titulo_professor}

    Contexto do Aluno Atual:
    - ID do Aluno: {aluno_id}
    - Nome do Aluno: {aluno_nome}

    Progresso da materia:
    - {progresso['topicos_concluidos']}/{progresso['total_topicos']} topicos concluidos ({progresso['percentual_conclusao']}%).

    Topico atual:
    {topico_atual_texto}

    Topicos da materia:
    {lista_topicos}

    Regras de contexto:
    - Use apenas o historico desta materia e a mensagem atual do aluno.
    - Nao use mensagens de outras materias.
    - Para concluir um topico, oriente o aluno a dizer que deseja concluir/fazer avaliacao do topico.

    Instrucoes especificas:
    {instrucoes_especificas}
    """

    llm = ChatOpenAI(model="gpt-4o", temperature=temperature)
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_instruction),
            ("placeholder", "{messages}"),
        ]
    )
    chain = prompt_template | llm
    mensagens_para_professor = historico_materia + [ultima_msg]
    resposta = chain.invoke({"messages": mensagens_para_professor})

    novo_historico = (historico_materia + [ultima_msg, resposta])[-10:]
    return {
        "messages": [resposta],
        chave_historico: novo_historico,
        "materia_id": materia_id,
        "topico_atual_id": topico_atual["id"] if topico_atual else state.get("topico_atual_id"),
        "last_agent": ROTA_POR_MATERIA[materia_id],
        "current_subject": str(materia_id),
    }
