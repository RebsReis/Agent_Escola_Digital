
from typing import Annotated, Sequence, TypedDict, List
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

# ------------------------------------------------------------------------
# 1. DEFINIÇÃO DO ESTADO 
# ------------------------------------------------------------------------
class EscolaDigitalState(TypedDict, total=False):
    # Histórico Global da Conversa (usado pelo Orquestrador e Secretário)
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # HISTÓRICOS ISOLADOS POR MATÉRIA (Garante contexto e histórico próprios)
    historico_sql: List[BaseMessage]
    historico_engenharia: List[BaseMessage]
    historico_ia: List[BaseMessage]
    historico_bpo: List[BaseMessage]
    
    # Dados de Contexto do Aluno e Sessão
    aluno_id: int
    aluno_nome: str
    materia_id: int          # ID da matéria ativa
    topico_atual_id: int     # ID do tópico ativo no momento
    
    # Controle de Roteamento Estrito
    proxima_acao: str        # "sql", "engenharia", "ia", "bpo", "secretario", "finalizar"
    last_agent: str
    current_subject: str | None
    completed_topics: list

# ------------------------------------------------------------------------
# 2. IMPORTAÇÃO DOS NÓS (AGENTES)
# ------------------------------------------------------------------------
from agents.orquestrador import agente_orquestrador
from agents.secretario import agente_secretario
from agents.agent_Banco_de_dados import prof_sql
from agents.agent_Engenharia_dados import prof_engenharia
from agents.agent_IA import prof_ia
from agents.agent_Estrategia_BPO import prof_bpo

# ------------------------------------------------------------------------
# 3. FUNÇÃO DE ROTEAMENTO (Borda Condicional)
# ------------------------------------------------------------------------
def rotear_pos_orquestrador(state: EscolaDigitalState) -> str:
    acao = state.get("proxima_acao", "finalizar")
    
    MAPEAMENTO_ROTAS = {
        "sql": "no_prof_sql",
        "engenharia": "no_prof_engenharia",
        "ia": "no_prof_ia",
        "bpo": "no_prof_bpo",
        "secretario": "no_secretario",
        "finalizar": END
    }
    return MAPEAMENTO_ROTAS.get(acao, END)

# ------------------------------------------------------------------------
# 4. CONSTRUÇÃO E MONTAGEM DO GRAFO
# ------------------------------------------------------------------------
builder = StateGraph(EscolaDigitalState)

# Adicionando os Nós
builder.add_node("no_orquestrador", agente_orquestrador)
builder.add_node("no_secretario", agente_secretario)
builder.add_node("no_prof_sql", prof_sql)
builder.add_node("no_prof_engenharia", prof_engenharia)
builder.add_node("no_prof_ia", prof_ia)
builder.add_node("no_prof_bpo", prof_bpo)

# Definindo Ponto de Entrada
builder.set_entry_point("no_orquestrador")

# Mapeando Bordas Condicionais saindo do Orquestrador
builder.add_conditional_edges(
    "no_orquestrador",
    rotear_pos_orquestrador,
    {
        "no_prof_sql": "no_prof_sql",
        "no_prof_engenharia": "no_prof_engenharia",
        "no_prof_ia": "no_prof_ia",
        "no_prof_bpo": "no_prof_bpo",
        "no_secretario": "no_secretario",
        END: END
    }
)

# Bordas de Retorno para Encerramento do Turno Atual
builder.add_edge("no_prof_sql", END)
builder.add_edge("no_prof_engenharia", END)
builder.add_edge("no_prof_ia", END)
builder.add_edge("no_prof_bpo", END)
builder.add_edge("no_secretario", END)

# Compilação do Grafo com Persistência Volátil
memory = MemorySaver()
app = builder.compile(checkpointer=memory)
