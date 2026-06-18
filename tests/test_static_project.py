import unittest


class StaticProjectTests(unittest.TestCase):
    def test_project_imports(self):
        import main
        from workflows.graph import app

        self.assertIsNotNone(main)
        self.assertIsNotNone(app)

    def test_graph_routes(self):
        from workflows.graph import rotear_pos_orquestrador

        cases = {
            "sql": "no_prof_sql",
            "engenharia": "no_prof_engenharia",
            "ia": "no_prof_ia",
            "bpo": "no_prof_bpo",
            "secretario": "no_secretario",
            "finalizar": "__end__",
            "rota_invalida": "__end__",
        }

        for action, expected_node in cases.items():
            with self.subTest(action=action):
                self.assertEqual(
                    rotear_pos_orquestrador({"proxima_acao": action}),
                    expected_node,
                )

    def test_secretary_subject_parser(self):
        from agents.secretario import _extrair_materia_id

        cases = {
            "matricular em SQL": 1,
            "matricular em PySpark": 2,
            "remover matricula de IA": 3,
            "matricular em BPO": 4,
            "matricular materia 4": 4,
        }

        for text, expected_id in cases.items():
            with self.subTest(text=text):
                self.assertEqual(_extrair_materia_id(text), expected_id)


if __name__ == "__main__":
    unittest.main()
