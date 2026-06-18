# Escola Digital Multi-Agente com LangGraph

Projeto de workflow multi-agente para uma escola digital com IA. A aplicacao simula um ambiente academico em terminal, no qual um aluno conversa com um orquestrador, um secretario administrativo e professores especialistas por materia.

O projeto foi desenvolvido para atender ao escopo de uma avaliacao com LangChain, LangGraph, OpenAI API e PostgreSQL, incluindo roteamento inteligente, controle de matricula, controle de progresso, conclusao de topicos, avaliacao automatica, memoria global e memoria isolada por materia.

## Sumario

- [Objetivo](#objetivo)
- [Como o sistema funciona](#como-o-sistema-funciona)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Requisitos](#requisitos)
- [Configuracao do ambiente](#configuracao-do-ambiente)
- [Banco de dados](#banco-de-dados)
- [Como executar](#como-executar)
- [Exemplos de uso](#exemplos-de-uso)
- [Testes](#testes)
- [Documentacao detalhada](#documentacao-detalhada)
- [Pontos de atencao](#pontos-de-atencao)

## Objetivo

O sistema representa uma escola digital baseada em agentes de IA. A ideia central e permitir que o aluno escreva uma mensagem no terminal e que o workflow decida automaticamente quem deve responder.

O sistema cobre:

- Cadastro e consulta de alunos.
- Matricula e remocao de matricula.
- Listagem de materias disponiveis.
- Roteamento entre secretario e professores.
- Controle de acesso por matricula.
- Controle de troca de materia.
- Controle de progresso por topico.
- Conclusao de topico.
- Geracao e correcao automatica de avaliacao.
- Persistencia de historico no PostgreSQL.
- Memoria global do orquestrador.
- Historico isolado por materia para os professores.

## Como o sistema funciona

Fluxo resumido:

1. O aluno digita uma mensagem no terminal.
2. `main.py` envia a mensagem para o grafo LangGraph.
3. O grafo chama o agente orquestrador.
4. O orquestrador classifica a intencao da mensagem.
5. O orquestrador aplica regras de negocio:
   - aluno precisa estar matriculado para acessar uma materia;
   - aluno nao deve trocar de materia antes de concluir ao menos um topico da materia atual.
6. O grafo encaminha para:
   - Secretario;
   - Professor SQL;
   - Professor Engenharia de Dados;
   - Professor IA;
   - Professor BPO;
   - ou finalizacao.
7. O agente executado responde.
8. `main.py` imprime a resposta e persiste a conversa.

## Estrutura do projeto

```text
.
|-- agents/
|   |-- orquestrador.py
|   |-- secretario.py
|   |-- professor_base.py
|   |-- agent_Banco_de_dados.py
|   |-- agent_Engenharia_dados.py
|   |-- agent_IA.py
|   `-- agent_Estrategia_BPO.py
|-- database/
|   |-- conexao.py
|   |-- models.py
|   `-- schema_atualizado.sql
|-- docs/
|   |-- ARQUITETURA.md
|   |-- BANCO_DE_DADOS.md
|   |-- ESCOPO.md
|   |-- FLUXOS.md
|   |-- OPERACAO.md
|   |-- TESTES.md
|   `-- TOOLS.md
|-- memoria/
|   `-- gerenteMemoria.py
|-- prompts/
|   |-- orquestrador.txt
|   |-- professor.txt
|   `-- secretario.txt
|-- tools/
|   |-- database_tools.py
|   |-- topic_tools.py
|   `-- evaluation_tools.py
|-- workflows/
|   `-- graph.py
|-- tests/
|   |-- run_all.py
|   |-- test_static_project.py
|   |-- test_database_smoke.py
|   |-- test_admin_write_flow.py
|   `-- test_topic_evaluation_flow.py
|-- main.py
`-- requirements.txt
```

## Principais componentes

| Componente | Arquivo | Responsabilidade |
| --- | --- | --- |
| Entrada da aplicacao | `main.py` | Loop de terminal, estado inicial, execucao do grafo e persistencia do turno. |
| Grafo LangGraph | `workflows/graph.py` | Define estado, nos e roteamento condicional. |
| Orquestrador | `agents/orquestrador.py` | Classifica mensagens, aplica regras e escolhe o proximo agente. |
| Secretario | `agents/secretario.py` | Executa operacoes administrativas. |
| Professores | `agents/agent_*.py` | Especialistas por materia. |
| Base dos professores | `agents/professor_base.py` | Logica comum de contexto, topicos, progresso e avaliacao. |
| Tools de banco | `tools/database_tools.py` | Aluno, matricula, materia e progresso geral. |
| Tools de topicos | `tools/topic_tools.py` | Topicos, progresso por materia e conclusao. |
| Tools de avaliacao | `tools/evaluation_tools.py` | Avaliacao, nota, feedback, historico e desempenho. |
| Memoria | `memoria/gerenteMemoria.py` | Persistencia e consulta do historico. |
| Modelos | `database/models.py` | Representacao SQLAlchemy das tabelas. |
| Schema | `database/schema_atualizado.sql` | DDL atualizado das tabelas. |

## Requisitos

- Python 3.11+
- PostgreSQL
- OpenAI API key
- Dependencias Python:
  - `langchain`
  - `langchain-core`
  - `langchain-openai`
  - `langgraph`
  - `pydantic`
  - `psycopg2-binary`
  - `python-dotenv`
  - `SQLAlchemy`

## Configuracao do ambiente

Crie o ambiente virtual:

```powershell
python -m venv venv
```

Instale as dependencias:

```powershell
venv\Scripts\python.exe -m pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz:

```env
OPENAI_API_KEY=sua_chave_aqui
DATABASE_URL=postgresql://usuario:senha@localhost:5432/Escola_Digital
```

Importante:

- Nunca publique o arquivo `.env`.
- Se uma chave da OpenAI for exposta, revogue a chave e gere outra.
- Use preferencialmente um banco de desenvolvimento, porque os testes de escrita criam registros.

## Banco de dados

O schema atualizado esta em:

```text
database/schema_atualizado.sql
```

Ele contem apenas estrutura, sem inserts:

- enum `status_avaliacao`;
- tabela `aluno`;
- tabela `materia`;
- tabela `topico`;
- tabela `matricula`;
- tabela `topico_aluno`;
- tabela `avaliacao`;
- tabela `historico_conversa`.

Para criar as tabelas em um banco vazio:

```powershell
psql -U seu_usuario -d Escola_Digital -f database/schema_atualizado.sql
```

## Como executar

```powershell
venv\Scripts\python.exe main.py
```

O sistema inicia uma conversa em terminal para o aluno simulado:

```text
Arthur Felipe
aluno_id = 1
```

Esse aluno fixo facilita a demonstracao, mas pode ser evoluido para login por matricula.

## Exemplos de uso

### Fluxo administrativo

```text
minhas matriculas
matricular em BPO
remover matricula de BPO
qual meu progresso?
qual meu desempenho?
historico de avaliacoes
cadastrar aluno nome: Maria Silva, matricula: MAT999
```

### Fluxo pedagogico

```text
Quero estudar IA
Explique embeddings
Entendi o topico, pode avaliar
```

### Fluxo de bloqueio por matricula

```text
Quero estudar BPO
```

Se o aluno nao estiver matriculado em BPO, o orquestrador bloqueia o acesso.

### Fluxo de bloqueio de troca de materia

```text
Quero estudar IA
Agora quero estudar Engenharia de Dados
```

Se o aluno ainda nao concluiu ao menos um topico da materia atual, o orquestrador bloqueia a troca.

## Testes

Rodar todos:

```powershell
venv\Scripts\python.exe tests\run_all.py
```

Rodar testes especificos:

```powershell
venv\Scripts\python.exe -m unittest tests.test_static_project -v
venv\Scripts\python.exe -m unittest tests.test_database_smoke -v
venv\Scripts\python.exe -m unittest tests.test_admin_write_flow -v
venv\Scripts\python.exe -m unittest tests.test_topic_evaluation_flow -v
```

Observacoes:

- `test_static_project` nao depende do banco.
- `test_database_smoke` faz leituras no banco.
- `test_admin_write_flow` cria aluno teste e mexe em matricula.
- `test_topic_evaluation_flow` cria avaliacao automatica.
- Nenhum teste chama a OpenAI.

## Documentacao detalhada

- [Arquitetura](docs/ARQUITETURA.md)
- [Banco de dados](docs/BANCO_DE_DADOS.md)
- [Tools](docs/TOOLS.md)
- [Fluxos funcionais](docs/FLUXOS.md)
- [Testes](docs/TESTES.md)
- [Aderencia ao escopo](docs/ESCOPO.md)
- [Operacao](docs/OPERACAO.md)

## Pontos de atencao

- A avaliacao automatica atual usa uma heuristica simples e pode ser evoluida para uma correcao por LLM com rubrica.
- O aluno logado esta fixo em `main.py`.
- O historico isolado por materia e mantido no estado do LangGraph.
- O historico persistido no banco pode ser evoluido com uma coluna `materia_id` direta em `historico_conversa`.
- O projeto e uma aplicacao de terminal, nao uma interface web.
