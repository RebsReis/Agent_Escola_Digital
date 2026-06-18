# Aderencia ao Escopo

Este documento mapeia os requisitos do escopo para a implementacao atual.

## Resumo

O projeto atende ao objetivo principal: construir um workflow multi-agente com LangGraph, agentes especializados, secretario, tools, PostgreSQL, memoria e controle de progresso.

A implementacao atual cobre os fluxos principais:

- administrativo;
- pedagogico;
- bloqueio por matricula;
- bloqueio de troca de materia;
- conclusao de topico;
- avaliacao automatica;
- persistencia de historico.

## Mapeamento de requisitos

| Requisito do escopo | Status | Implementacao |
| --- | --- | --- |
| Aplicacao em Python | Atendido | Projeto Python executavel via `main.py`. |
| LangChain | Atendido | Prompts, messages, tools e `ChatOpenAI`. |
| LangGraph | Atendido | Grafo em `workflows/graph.py`. |
| OpenAI API | Atendido | Agentes usam `ChatOpenAI`. |
| PostgreSQL | Atendido | Tools usam `psycopg2`; modelos em SQLAlchemy. |
| Agente orquestrador | Atendido | `agents/orquestrador.py`. |
| Agente secretario | Atendido | `agents/secretario.py`. |
| Subagentes por materia | Atendido | SQL, Engenharia, IA e BPO. |
| Prompts/personas por materia | Atendido | `prompt_ia` da tabela `materia` + prompt base. |
| Tools para aluno | Atendido | Buscar e criar aluno. |
| Tools para matricula | Atendido | Matricular, remover e listar. |
| Tools para topicos | Atendido | Buscar, progresso e concluir. |
| Tools para avaliacoes | Atendido | Criar, nota, feedback, historico e desempenho. |
| Historico persistido | Atendido | `historico_conversa`. |
| Memoria global | Atendido | Orquestrador busca ultimas mensagens globais. |
| Memoria isolada por materia | Atendido no estado | `historico_sql`, `historico_engenharia`, `historico_ia`, `historico_bpo`. |
| Controle de progresso | Atendido | `topico_aluno` e tools de progresso. |
| Bloqueio sem matricula | Atendido | Orquestrador verifica matricula antes de rotear. |
| Bloqueio de troca de materia | Atendido | Orquestrador exige um topico concluido. |
| Conclusao de topico | Atendido | Professor marca topico concluido. |
| Avaliacao automatica | Atendido | Criacao e correcao automatica apos conclusao. |
| Avaliacao vinculada a aluno, materia e topico | Atendido | `avaliacao.topico_id`. |
| Projeto executavel via terminal | Atendido | `venv\Scripts\python.exe main.py`. |
| Testes | Atendido | Pasta `tests/`. |

## Regras de negocio implementadas

### Regra 1: aluno nao acessa materia sem matricula

Implementada no orquestrador:

```python
aluno_esta_matriculado_raw(aluno_id, materia_destino)
```

Se nao houver matricula, o orquestrador retorna mensagem de bloqueio.

### Regra 2: aluno nao conclui o mesmo topico duas vezes

Implementada no banco:

```sql
UNIQUE (aluno_id, topico_id)
```

E no codigo:

```sql
ON CONFLICT (aluno_id, topico_id) DO NOTHING
```

### Regra 3: avaliacao vinculada a aluno, materia e topico

Implementada em `avaliacao`:

- `aluno_id`
- `materia_id`
- `topico_id`

### Regra 4: avaliacao possui nota, feedback e data

Campos usados:

- `nota`
- `feedback_ia`
- `data_envio`
- `status`

### Regra 5: impedir vazamento de contexto entre materias

Cada professor recebe apenas o historico isolado da propria materia:

- `historico_sql`
- `historico_engenharia`
- `historico_ia`
- `historico_bpo`

## Demonstracao minima obrigatoria

### Administrativo

```text
cadastrar aluno nome: Maria Silva, matricula: MAT999
minhas matriculas
matricular em BPO
remover matricula de BPO
qual meu progresso?
```

### Pedagogico

```text
Quero estudar IA
Explique embeddings
Entendi o topico, pode avaliar
```

### Bloqueio

```text
remover matricula de BPO
Quero estudar BPO
```

## Pontos de atencao e evolucoes

### Avaliacao automatica

Status atual: funcional, mas simplificada.

Hoje a nota e gerada por heuristica. Uma evolucao natural seria criar uma rubrica por materia e usar LLM para corrigir semanticamente a resposta do aluno.

### Login de aluno

Status atual: aluno fixo no `main.py`.

Evolucao:

- pedir matricula no inicio;
- buscar aluno no banco;
- montar estado inicial dinamico.

### Historico persistido por materia

Status atual: historico isolado por materia fica no estado do LangGraph; no banco, o historico pode ser vinculado a avaliacao quando existe `avaliacao_id`.

Evolucao:

- adicionar `materia_id` em `historico_conversa`;
- consultar ultimas N mensagens por materia diretamente do banco.

### Interface

Status atual: terminal.

Evolucao:

- API HTTP;
- interface web;
- painel de secretaria;
- dashboard de progresso.
