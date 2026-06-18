from agents.professor_base import executar_professor_materia


def prof_engenharia(state):
    print("\n--- [NO] ENTRANDO NO AGENTE PROFESSOR DE ENGENHARIA DE DADOS ---")
    return executar_professor_materia(
        state=state,
        materia_id=2,
        titulo_professor="Professor de Engenharia de Dados",
        temperature=0.3,
        instrucoes_especificas=(
            "Responda com foco em Apache Spark, PySpark, Databricks, Lakehouse, "
            "pipelines, particionamento e otimizacao."
        ),
    )
