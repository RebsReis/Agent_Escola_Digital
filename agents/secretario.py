import os
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from tools.database_tools import (
    buscar_aluno,
    buscar_progresso_geral_aluno,
    consultar_matriculas_aluno,
    criar_aluno,
    listar_materias_disponiveis,
    matricular_aluno,
    remover_matricula,
)
from tools.evaluation_tools import buscar_historico_avaliacoes, calcular_desempenho_aluno


MATERIAS = {
    "sql": 1,
    "banco": 1,
    "banco de dados": 1,
    "engenharia": 2,
    "dados": 2,
    "spark": 2,
    "pyspark": 2,
    "ia": 3,
    "inteligencia": 3,
    "inteligência": 3,
    "nlp": 3,
    "bpo": 4,
    "negocios": 4,
    "negócios": 4,
}


def _extrair_materia_id(texto: str) -> int | None:
    texto = texto.lower()
    match = re.search(r"\b(?:materia|matéria|id)\s*(\d+)\b", texto)
    if match:
        return int(match.group(1))
    for termo, materia_id in MATERIAS.items():
        if termo in texto:
            return materia_id
    return None


def _extrair_cadastro(texto: str) -> tuple[str | None, str | None]:
    nome = None
    matricula = None

    nome_match = re.search(r"nome\s*[:=-]\s*([^,;]+)", texto, flags=re.IGNORECASE)
    matricula_match = re.search(r"matr[ií]cula\s*[:=-]\s*([A-Za-z0-9_-]+)", texto, flags=re.IGNORECASE)

    if nome_match:
        nome = nome_match.group(1).strip().title()
    if matricula_match:
        matricula = matricula_match.group(1).strip().upper()

    return nome, matricula


def _contexto_administrativo(texto: str, aluno_id: int) -> str:
    if any(p in texto for p in ["cadastrar aluno", "criar aluno", "novo aluno"]):
        nome, matricula = _extrair_cadastro(texto)
        if not nome or not matricula:
            return (
                "Para cadastrar aluno, informe no formato: "
                "cadastrar aluno nome: Nome Completo, matricula: MAT123."
            )
        return criar_aluno.invoke({"nome": nome, "matricula": matricula})

    if any(p in texto for p in ["buscar aluno", "consultar aluno"]):
        matricula_match = re.search(r"matr[ií]cula\s*[:=-]?\s*([A-Za-z0-9_-]+)", texto, flags=re.IGNORECASE)
        if matricula_match:
            return buscar_aluno.invoke({"matricula": matricula_match.group(1).strip().upper()})
        return buscar_aluno.invoke({"aluno_id": aluno_id})

    if any(p in texto for p in ["matricular", "fazer matricula", "fazer matrícula"]):
        materia_id = _extrair_materia_id(texto)
        if not materia_id:
            return "Informe a materia para matricula. Exemplo: matricular em BPO ou matricular materia 4."
        return matricular_aluno.invoke({"aluno_id": aluno_id, "materia_id": materia_id})

    if any(p in texto for p in ["remover matricula", "remover matrícula", "trancar", "cancelar matricula", "cancelar matrícula"]):
        materia_id = _extrair_materia_id(texto)
        if not materia_id:
            return "Informe a materia para remover/trancar. Exemplo: remover matricula de IA."
        return remover_matricula.invoke({"aluno_id": aluno_id, "materia_id": materia_id})

    if any(p in texto for p in ["materias disponiveis", "matérias disponíveis", "cursos disponiveis", "cursos disponíveis", "grade", "cursos"]):
        return listar_materias_disponiveis.invoke({})

    if any(p in texto for p in ["minhas matriculas", "minhas matrículas", "matriculado", "minhas materias", "minhas matérias"]):
        return consultar_matriculas_aluno.invoke({"aluno_id": aluno_id})

    if any(p in texto for p in ["progresso", "porcentagem", "conclusao", "conclusão", "plano de estudo"]):
        return buscar_progresso_geral_aluno.invoke({"aluno_id": aluno_id})

    if any(p in texto for p in ["nota", "notas", "desempenho", "aprovado", "media", "média"]):
        return calcular_desempenho_aluno.invoke({"aluno_id": aluno_id})

    if any(p in texto for p in ["historico de avaliacoes", "histórico de avaliações", "avaliacoes", "avaliações"]):
        return buscar_historico_avaliacoes.invoke({"aluno_id": aluno_id})

    return "Solicitacao administrativa geral sem dados adicionais de ferramenta."


def agente_secretario(state):
    print("\n--- [NO] ENTRANDO NO AGENTE SECRETARIO (ADMINISTRATIVO) ---")

    historico_mensagens = state.get("messages", [])
    aluno_id = state.get("aluno_id", 1)
    aluno_nome = state.get("aluno_nome", "Aluno")
    ultima_msg_texto = historico_mensagens[-1].content.lower() if historico_mensagens else ""

    contexto_extra = _contexto_administrativo(ultima_msg_texto, aluno_id)

    caminho_prompt = os.path.join("prompts", "secretario.txt")
    if os.path.exists(caminho_prompt):
        with open(caminho_prompt, "r", encoding="utf-8") as f:
            system_instruction = f.read()
    else:
        system_instruction = "Voce e o Secretario Administrativo da Escola Digital. Seja formal e direto."

    system_prompt_completo = f"""
    {system_instruction}

    Contexto da Operacao:
    - ID do Aluno Logado: {aluno_id}
    - Nome do Aluno Logado: {aluno_nome}

    Resultado das ferramentas administrativas:
    {contexto_extra}

    Restricoes Criticas:
    - Voce NAO corrige provas.
    - Voce NAO explica conteudo tecnico de SQL, Engenharia de Dados, IA ou BPO.
    - Limite-se a responder formalmente a duvida administrativa do aluno com base nos dados fornecidos acima.
    """

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt_completo),
            ("placeholder", "{messages}"),
        ]
    )
    chain = prompt_template | llm
    resposta = chain.invoke({"messages": historico_mensagens})

    return {
        "messages": [resposta],
        "last_agent": "secretario",
    }
