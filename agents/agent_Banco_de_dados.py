from agents.professor_base import executar_professor_materia


def prof_sql(state):
    print("\n--- [NO] ENTRANDO NO AGENTE PROFESSOR DE BANCO DE DADOS ---")
    return executar_professor_materia(
        state=state,
        materia_id=1,
        titulo_professor="Professor de Banco de Dados SQL",
        temperature=0.1,
        instrucoes_especificas=(
            "Responda com foco em modelagem, DDL, DML, PK, FK, joins e integridade. "
            "Quando houver codigo SQL, analise sintaxe, chaves e relacoes."
        ),
    )
