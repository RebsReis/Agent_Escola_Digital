import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

load_dotenv()

from memoria.gerenteMemoria import GerenteMemoriaDB
from workflows.graph import app


def exibir_cabecalho():
    print("=" * 60)
    print("      SISTEMA ESCOLA DIGITAL - VERSAO MULTI-AGENTES      ")
    print("=" * 60)
    print("Diretrizes de teste:")
    print("- Digite 'sair' para encerrar a sessao.")
    print("- Pergunte sobre SQL, Spark, IA ou BPO para testar os professores.")
    print("- Pergunte sobre notas, progresso ou matricula para a Secretaria.")
    print("=" * 60)


def simular_escola_digital():
    gerente_memoria = GerenteMemoriaDB()

    estado_inicial = {
        "messages": [],
        "historico_sql": [],
        "historico_engenharia": [],
        "historico_ia": [],
        "historico_bpo": [],
        "aluno_id": 1,
        "aluno_nome": "Arthur Felipe",
        "materia_id": 1,
        "topico_atual_id": 1,
        "proxima_acao": "",
        "last_agent": "",
        "current_subject": None,
        "completed_topics": [],
        "avaliacao_id": None,
    }

    config = {"configurable": {"thread_id": "sessao_arthur_2026"}}

    exibir_cabecalho()
    print(f"Bem-vindo de volta, {estado_inicial['aluno_nome']}!\n")

    while True:
        try:
            entrada_usuario = input("Aluno: ")

            if entrada_usuario.strip().lower() == "sair":
                print("\nEncerrando sessao academica. Ate logo!")
                break

            if not entrada_usuario.strip():
                continue

            estado_inicial["messages"] = [HumanMessage(content=entrada_usuario)]

            print("\n[Grafo] Processando fluxo de agentes...")
            estado_final = app.invoke(estado_inicial, config)

            if not estado_final.get("messages"):
                print("\nSistema: Nao houve resposta do grafo.")
                print("-" * 60)
                continue

            ultima_mensagem_sistema = estado_final["messages"][-1].content

            print(f"\nSistema: {ultima_mensagem_sistema}")
            print("-" * 60)

            gerente_memoria.persistir_novas_mensagens_grafo(
                estado_final,
                estado_final.get("avaliacao_id"),
            )

            estado_inicial = estado_final

        except Exception as e:
            print(f"\n[Erro no Sistema]: {e}")
            break


if __name__ == "__main__":
    if "OPENAI_API_KEY" not in os.environ:
        print("Aviso: configure a OPENAI_API_KEY no ambiente ou arquivo .env")

    simular_escola_digital()
