"""
Sistema Escola Digital - Versão Multi-Agentes com LangGraph.

Este módulo implementa um sistema de tutoria inteligente que oferece
suporte educacional através de múltiplos agentes especializados,
orquestrados por um sistema central de roteamento.
"""

import logging
import sys

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from config import configure_logging, get_config
from memoria.gerenteMemoria import GerenteMemoriaDB
from workflows.graph import app

# Carrega configuração e inicializa logging
load_dotenv()
logger = configure_logging()
logger = logging.getLogger(__name__)


def exibir_cabecalho() -> None:
    """Exibe o cabeçalho de boas-vindas do sistema."""
    print("=" * 60)
    print("      SISTEMA ESCOLA DIGITAL - VERSAO MULTI-AGENTES      ")
    print("=" * 60)
    print("Diretrizes de teste:")
    print("- Digite 'sair' para encerrar a sessao.")
    print("- Pergunte sobre SQL, Spark, IA ou BPO para testar os professores.")
    print("- Pergunte sobre notas, progresso ou matricula para a Secretaria.")
    print("=" * 60)


def validar_entrada_usuario(entrada: str) -> bool:
    """
    Valida a entrada do usuário.
    
    Args:
        entrada: Texto inserido pelo usuário.
    
    Returns:
        False se entrada for vazia ou apenas espaços, True caso contrário.
    """
    if not entrada or not entrada.strip():
        print("Por favor, digite uma pergunta ou comando válido.")
        return False
    return True


def simular_escola_digital() -> None:
    """
    Função principal que simula a interação com o sistema Escola Digital.
    
    Gerencia o loop de conversação, validação de entrada e persistência de histórico.
    """
    try:
        # Valida configuração antes de iniciar
        config = get_config()
        logger.info("Configuração carregada com sucesso")
        
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

        config_sessao = {"configurable": {"thread_id": "sessao_arthur_2026"}}

        exibir_cabecalho()
        print(f"Bem-vindo de volta, {estado_inicial['aluno_nome']}!\n")
        logger.info(f"Sessão iniciada para aluno: {estado_inicial['aluno_nome']}")

        while True:
            try:
                entrada_usuario = input("Aluno: ").strip()
                
                if not validar_entrada_usuario(entrada_usuario):
                    continue
                
                if entrada_usuario.lower() == "sair":
                    print("\nAte proxima sessao! Bom estudo!")
                    logger.info("Sessão encerrada pelo usuário")
                    break

                # Adiciona mensagem do usuário ao estado
                estado_inicial["messages"].append(HumanMessage(content=entrada_usuario))
                
                logger.debug(f"Entrada do usuário: {entrada_usuario}")
                
                # Executa o grafo de agentes
                resposta = app.invoke(estado_inicial, config=config_sessao)
                
                # Extrai última mensagem do assistente
                mensagens = resposta.get("messages", [])
                if mensagens:
                    ultima_mensagem = mensagens[-1]
                    print(f"\nAssistente: {ultima_mensagem.content}\n")
                    logger.debug(f"Resposta do assistente: {ultima_mensagem.content[:100]}...")
                
                # Persiste conversa no banco de dados
                gerente_memoria.persistir_novas_mensagens_grafo(resposta)
                
                # Atualiza estado para próxima iteração
                estado_inicial.update(resposta)
                
            except KeyboardInterrupt:
                print("\n\nSessão interrompida pelo usuário.")
                logger.info("Sessão interrompida por KeyboardInterrupt")
                break
            except Exception as e:
                logger.error(f"Erro durante iteração: {e}", exc_info=True)
                print(f"Erro ao processar sua mensagem: {str(e)}")
                print("Por favor, tente novamente.\n")
                
    except ValueError as e:
        logger.critical(f"Erro de configuração: {e}")
        print(f"Erro ao inicializar sistema: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Erro não tratado no sistema: {e}", exc_info=True)
        print(f"Erro crítico no sistema: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    simular_escola_digital()

