import os
import unittest

from dotenv import load_dotenv


load_dotenv()


@unittest.skipUnless(os.getenv("DATABASE_URL"), "DATABASE_URL nao configurada")
class AdminWriteFlowTests(unittest.TestCase):
    def test_create_student_enroll_and_remove_enrollment(self):
        from tools.database_tools import (
            buscar_aluno_raw,
            criar_aluno_raw,
            matricular_aluno_raw,
            remover_matricula_raw,
        )

        matricula = "TESTE_CODEX_001"
        aluno = criar_aluno_raw("Aluno Teste Codex", matricula)
        self.assertIsNotNone(aluno)

        aluno_encontrado = buscar_aluno_raw(matricula=matricula)
        self.assertIsNotNone(aluno_encontrado)

        aluno_id = aluno_encontrado["id"]
        matricula_msg = matricular_aluno_raw(aluno_id, 4)
        self.assertTrue(
            "sucesso" in matricula_msg.lower() or "ja estava" in matricula_msg.lower()
        )

        remocao_msg = remover_matricula_raw(aluno_id, 4)
        self.assertTrue(
            "removida" in remocao_msg.lower() or "nao havia" in remocao_msg.lower()
        )


if __name__ == "__main__":
    unittest.main()
