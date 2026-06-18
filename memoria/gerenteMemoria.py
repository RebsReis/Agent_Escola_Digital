import os
from typing import Optional

import psycopg2
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from psycopg2.extras import RealDictCursor

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://usuario:senha@localhost:5432/escola_digital")


class GerenteMemoriaDB:
    def __init__(self):
        self.database_url = DATABASE_URL

    def _executar_query(self, sql: str, params: tuple = ()) -> list[dict]:
        conn = None
        cursor = None
        try:
            conn = psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
            cursor = conn.cursor()
            cursor.execute(sql, params)
            resultados = []
            if cursor.description is not None:
                resultados = [dict(row) for row in cursor.fetchall()]
            conn.commit()
            return resultados
        except Exception as e:
            print(f"Erro ao acessar memoria no PostgreSQL: {e}")
            return []
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()

    def salvar_turno_conversa(
        self,
        role: str,
        conteudo: str,
        avaliacao_id: Optional[int] = None,
    ) -> bool:
        if role not in ["user", "assistant"]:
            print(f"Role '{role}' invalida ignorada pelo banco.")
            return False

        resultado = self._executar_query(
            """
            INSERT INTO historico_conversa (avaliacao_id, role, conteudo, criado_em)
            VALUES (%s, %s, %s, NOW())
            RETURNING id;
            """,
            (avaliacao_id, role, conteudo),
        )
        return bool(resultado)

    def persistir_novas_mensagens_grafo(
        self,
        state: dict,
        avaliacao_id: Optional[int] = None,
    ):
        historico_mensagens = state.get("messages", [])
        if not historico_mensagens:
            return

        for msg in historico_mensagens[-2:]:
            if isinstance(msg, HumanMessage):
                self.salvar_turno_conversa("user", msg.content, avaliacao_id)
            elif isinstance(msg, AIMessage):
                self.salvar_turno_conversa("assistant", msg.content, avaliacao_id)

    def buscar_ultimas_mensagens_globais(self, limite: int = 10) -> list[dict]:
        return self._executar_query(
            """
            SELECT id, role, conteudo, criado_em, avaliacao_id
            FROM historico_conversa
            ORDER BY criado_em DESC, id DESC
            LIMIT %s;
            """,
            (limite,),
        )[::-1]

    def buscar_contexto_materia(
        self,
        aluno_id: int,
        materia_id: int,
        limite: int = 10,
    ) -> list[dict]:
        return self._executar_query(
            """
            SELECT hc.id, hc.role, hc.conteudo, hc.criado_em, hc.avaliacao_id
            FROM historico_conversa hc
            JOIN avaliacao av ON av.id = hc.avaliacao_id
            WHERE av.aluno_id = %s AND av.materia_id = %s
            ORDER BY hc.criado_em DESC, hc.id DESC
            LIMIT %s;
            """,
            (aluno_id, materia_id, limite),
        )[::-1]


def mensagens_para_texto(mensagens: list[dict]) -> str:
    if not mensagens:
        return "Sem mensagens anteriores registradas."
    return "\n".join(f"{m['role']}: {m['conteudo']}" for m in mensagens)
