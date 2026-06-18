from agents.professor_base import executar_professor_materia


def prof_ia(state):
    print("\n--- [NO] ENTRANDO NO AGENTE PROFESSOR DE IA ---")
    return executar_professor_materia(
        state=state,
        materia_id=3,
        titulo_professor="Professor de Inteligencia Artificial",
        temperature=0.3,
        instrucoes_especificas=(
            "Responda com foco em IA, NLP, LLMs, prompts, embeddings e agentes. "
            "Estimule raciocinio conceitual e exemplos praticos."
        ),
    )
