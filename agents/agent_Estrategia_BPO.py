from agents.professor_base import executar_professor_materia


def prof_bpo(state):
    print("\n--- [NO] ENTRANDO NO AGENTE PROFESSOR DE ESTRATEGIA BPO ---")
    return executar_professor_materia(
        state=state,
        materia_id=4,
        titulo_professor="Professor de Estrategia de Negocios BPO",
        temperature=0.4,
        instrucoes_especificas=(
            "Responda com foco em modelos operacionais, terceirizacao, propostas comerciais, "
            "rate cards, ABM, ROI e viabilidade financeira."
        ),
    )
