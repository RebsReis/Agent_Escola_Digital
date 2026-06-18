from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from memoria.gerenteMemoria import GerenteMemoriaDB, mensagens_para_texto
from tools.database_tools import aluno_esta_matriculado_raw
from tools.topic_tools import buscar_progresso_materia_raw


class Roteamento(BaseModel):
    proximo_agente: str = Field(
        description="Obrigatorio ser um destes: sql, engenharia, ia, bpo, secretario ou finalizar."
    )
    justificativa: str = Field(description="Breve explicacao da escolha do roteamento.")
    materia_id: int = Field(
        default=0,
        description="ID da materia quando o destino for um professor: 1 SQL, 2 Engenharia, 3 IA, 4 BPO. Caso contrario, 0.",
    )


def agente_orquestrador(state: Dict[str, Any]) -> dict:
    mensagens = state.get("messages", [])
    user_input = mensagens[-1].content if mensagens else ""
    memoria = GerenteMemoriaDB()
    memoria_global = mensagens_para_texto(memoria.buscar_ultimas_mensagens_globais(limite=10))

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

    prompt_sistema = """
    Voce e o Orquestrador Central da Escola Digital de Tecnologia.
    Sua unica funcao e analisar a ultima mensagem do aluno e o historico de conversas para determinar para qual subagente especialista a mensagem deve ser enviada.

    Subagentes disponiveis:
    - 'secretario': assuntos administrativos, matriculas, cursos, notas, progresso e triagem inicial.
    - 'sql': duvidas, aulas ou testes de Banco de Dados SQL (ID: 1).
    - 'engenharia': duvidas, aulas ou testes de Engenharia de Dados / PySpark (ID: 2).
    - 'ia': duvidas, aulas ou testes de Inteligencia Artificial e NLP (ID: 3).
    - 'bpo': duvidas, aulas ou testes de Estrategia de Negocios BPO / ABM (ID: 4).
    - 'finalizar': conversa encerrada ou despedida sem nova demanda.

    Regras:
    1. Saudacao sem contexto de aula: 'secretario'.
    2. Despedida sem nova demanda: 'finalizar'.
    3. Materia especifica: envie ao professor correto e preencha materia_id.
    4. Assunto vago ou ambiguo: 'secretario'.
    5. Continue no mesmo professor quando o aluno pedir continuacao do assunto atual.
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt_sistema),
            ("system", "Ultimas mensagens globais registradas no banco:\n{memoria_global}"),
            ("placeholder", "{chat_history}"),
            ("human", "Mensagem Atual do Aluno: {user_input}"),
        ]
    )

    chain = prompt | llm.with_structured_output(Roteamento)
    resultado: Roteamento = chain.invoke(
        {
            "chat_history": mensagens,
            "memoria_global": memoria_global,
            "user_input": user_input,
        }
    )

    aliases = {
        "secretary": "secretario",
        "professor_sql": "sql",
        "professor_data_eng": "engenharia",
        "professor_ai": "ia",
        "professor_bpo": "bpo",
        "end": "finalizar",
    }
    proxima_acao = aliases.get(resultado.proximo_agente, resultado.proximo_agente)
    materia_destino = resultado.materia_id if resultado.materia_id > 0 else state.get("materia_id", 1)

    materias_por_rota = {
        "sql": 1,
        "engenharia": 2,
        "ia": 3,
        "bpo": 4,
    }
    if proxima_acao in materias_por_rota:
        materia_destino = materias_por_rota[proxima_acao]
        aluno_id = state.get("aluno_id", 1)

        if not aluno_esta_matriculado_raw(aluno_id, materia_destino):
            return {
                "messages": [
                    AIMessage(
                        content=(
                            "Nao posso encaminhar voce para essa materia ainda, pois nao encontrei "
                            "matricula ativa nela. Fale com o Secretario para realizar a matricula."
                        )
                    )
                ],
                "proxima_acao": "finalizar",
                "last_agent": "orquestrador",
            }

        materia_ativa = state.get("materia_id")
        ultimo_agente = state.get("last_agent", "")
        estava_em_materia = ultimo_agente in {"sql", "engenharia", "ia", "bpo"}
        if estava_em_materia and materia_ativa and materia_ativa != materia_destino:
            progresso = buscar_progresso_materia_raw(aluno_id, materia_ativa)
            if int(progresso.get("topicos_concluidos") or 0) < 1:
                return {
                    "messages": [
                        AIMessage(
                            content=(
                                "Troca de materia bloqueada: primeiro conclua ao menos um topico "
                                "da materia atual para manter a consistencia do contexto pedagogico."
                            )
                        )
                    ],
                    "proxima_acao": "finalizar",
                    "last_agent": "orquestrador",
                }

    return {
        "proxima_acao": proxima_acao,
        "materia_id": materia_destino,
        "last_agent": "orquestrador",
    }


orchestrator_node = agente_orquestrador
