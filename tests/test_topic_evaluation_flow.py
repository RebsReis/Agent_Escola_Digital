import os
import unittest

from dotenv import load_dotenv


load_dotenv()


@unittest.skipUnless(os.getenv("DATABASE_URL"), "DATABASE_URL nao configurada")
class TopicEvaluationFlowTests(unittest.TestCase):
    def test_generate_automatic_evaluation_without_llm(self):
        from tools.evaluation_tools import buscar_historico_avaliacoes_raw, gerar_avaliacao_automatica_raw
        from tools.topic_tools import buscar_topicos_materia_raw

        topicos = buscar_topicos_materia_raw(1)
        self.assertTrue(topicos)

        topico = topicos[0]
        result = gerar_avaliacao_automatica_raw(
            aluno_id=1,
            materia_id=1,
            topico_id=topico["id"],
            titulo_topico=topico["titulo"],
            resposta_aluno=(
                "Expliquei o conceito com detalhes suficientes para validar o fluxo "
                "automatico de avaliacao do projeto."
            ),
        )

        self.assertTrue(result["ok"])
        self.assertIn("avaliacao_id", result)
        self.assertGreaterEqual(result["nota"], 0)
        self.assertLessEqual(result["nota"], 10)

        historico = buscar_historico_avaliacoes_raw(aluno_id=1, materia_id=1, limite=5)
        self.assertTrue(any(av["id"] == result["avaliacao_id"] for av in historico))


if __name__ == "__main__":
    unittest.main()
