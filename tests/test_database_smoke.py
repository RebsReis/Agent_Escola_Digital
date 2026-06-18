import os
import unittest

from dotenv import load_dotenv


load_dotenv()


@unittest.skipUnless(os.getenv("DATABASE_URL"), "DATABASE_URL nao configurada")
class DatabaseSmokeTests(unittest.TestCase):
    def test_read_student_and_subjects(self):
        from tools.database_tools import (
            buscar_aluno,
            consultar_matriculas_aluno,
            listar_materias_disponiveis,
        )

        aluno = buscar_aluno.invoke({"aluno_id": 1})
        materias = listar_materias_disponiveis.invoke({})
        matriculas = consultar_matriculas_aluno.invoke({"aluno_id": 1})

        self.assertIn("Arthur", aluno)
        self.assertIn("Banco de Dados SQL", materias)
        self.assertIn("Disciplinas vinculadas", matriculas)

    def test_topic_progress_and_evaluations(self):
        from tools.evaluation_tools import calcular_desempenho_aluno
        from tools.topic_tools import buscar_progresso_materia, buscar_topicos_materia

        topicos = buscar_topicos_materia.invoke({"materia_id": 1})
        progresso = buscar_progresso_materia.invoke({"aluno_id": 1, "materia_id": 1})
        desempenho = calcular_desempenho_aluno.invoke({"aluno_id": 1})

        self.assertIn("Modelagem", topicos)
        self.assertIn("topicos concluidos", progresso)
        self.assertIn("Ficha de Rendimento", desempenho)

    def test_schema_has_evaluation_topic_id(self):
        from tools.database_tools import executar_query_postgres

        result = executar_query_postgres(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'avaliacao'
              AND column_name = 'topico_id'
            LIMIT 1;
            """
        )

        self.assertTrue(result, "A tabela avaliacao deve possuir topico_id")


if __name__ == "__main__":
    unittest.main()
