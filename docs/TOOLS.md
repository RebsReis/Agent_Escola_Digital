# Tools

As tools sao a ponte entre os agentes e o banco de dados. O escopo exige que os agentes consultem e atualizem o PostgreSQL por meio de ferramentas; por isso, a regra do projeto e evitar SQL diretamente dentro dos agentes sempre que possivel.

## Convencao usada

Existem dois tipos de funcao:

| Tipo | Exemplo | Quando usar |
| --- | --- | --- |
| Funcao `raw` | `matricular_aluno_raw(...)` | Uso interno no codigo Python. |
| Tool LangChain | `matricular_aluno.invoke({...})` | Uso por agentes ou testes simulando tool. |

Funcoes com `@tool` viram `StructuredTool`. Por isso, devem ser chamadas com `.invoke(...)`.

Exemplo:

```python
consultar_matriculas_aluno.invoke({"aluno_id": 1})
```

## `tools/database_tools.py`

Modulo responsavel por aluno, materia, matricula e progresso geral.

### Funcoes de infraestrutura

| Funcao | Descricao |
| --- | --- |
| `executar_query_postgres` | Abre conexao, executa SQL, retorna lista de dicionarios e fecha conexao. |
| `executar_comando_postgres` | Executa comando sem retorno de linhas. |

### Aluno

| Funcao/Tool | Entrada | Saida |
| --- | --- | --- |
| `buscar_aluno_raw` | `aluno_id` ou `matricula` | Dicionario do aluno ou `None`. |
| `criar_aluno_raw` | `nome`, `matricula` | Dicionario do aluno criado/existente. |
| `buscar_aluno` | `aluno_id` ou `matricula` | Texto formatado. |
| `criar_aluno` | `nome`, `matricula` | Texto formatado. |

Exemplo:

```python
criar_aluno.invoke({
    "nome": "Maria Silva",
    "matricula": "MAT999"
})
```

### Materia

| Funcao/Tool | Entrada | Saida |
| --- | --- | --- |
| `listar_materias_disponiveis_raw` | nenhuma | Lista de materias. |
| `listar_materias_disponiveis` | nenhuma | Texto com materias. |
| `buscar_diretrizes_materia` | `materia_id` | Persona/prompt da materia. |

`buscar_diretrizes_materia` e usado pelos professores para carregar a personalidade da materia direto do banco.

### Matricula

| Funcao/Tool | Entrada | Saida |
| --- | --- | --- |
| `consultar_matriculas_aluno_raw` | `aluno_id` | Lista de materias matriculadas. |
| `aluno_esta_matriculado_raw` | `aluno_id`, `materia_id` | Booleano. |
| `matricular_aluno_raw` | `aluno_id`, `materia_id` | Mensagem de resultado. |
| `remover_matricula_raw` | `aluno_id`, `materia_id` | Mensagem de resultado. |
| `consultar_matriculas_aluno` | `aluno_id` | Texto formatado. |
| `matricular_aluno` | `aluno_id`, `materia_id` | Texto formatado. |
| `remover_matricula` | `aluno_id`, `materia_id` | Texto formatado. |

### Progresso geral

| Tool | Entrada | Saida |
| --- | --- | --- |
| `buscar_progresso_geral_aluno` | `aluno_id` | Texto com progresso por materia. |

## `tools/topic_tools.py`

Modulo responsavel por topicos e progresso pedagogico por materia.

| Funcao/Tool | Entrada | Saida |
| --- | --- | --- |
| `buscar_topicos_materia_raw` | `materia_id` | Lista de topicos. |
| `buscar_progresso_materia_raw` | `aluno_id`, `materia_id` | Dicionario de progresso. |
| `proximo_topico_pendente_raw` | `aluno_id`, `materia_id` | Proximo topico ou `None`. |
| `topico_foi_concluido_raw` | `aluno_id`, `topico_id` | Booleano. |
| `marcar_topico_concluido_raw` | `aluno_id`, `topico_id` | Mensagem de resultado. |
| `buscar_topicos_materia` | `materia_id` | Texto com topicos. |
| `buscar_progresso_materia` | `aluno_id`, `materia_id` | Texto de progresso. |
| `marcar_topico_concluido` | `aluno_id`, `topico_id` | Texto de resultado. |

Uso dentro dos professores:

1. Buscar topicos da materia.
2. Buscar progresso do aluno.
3. Identificar proximo topico pendente.
4. Marcar topico como concluido quando o aluno pedir avaliacao/conclusao.

## `tools/evaluation_tools.py`

Modulo responsavel por avaliacao, correcao, feedback e desempenho.

| Funcao/Tool | Entrada | Saida |
| --- | --- | --- |
| `criar_avaliacao_raw` | aluno, materia, titulo, topico | ID da avaliacao. |
| `atualizar_nota_feedback_raw` | avaliacao, nota, feedback | Booleano. |
| `gerar_avaliacao_automatica_raw` | aluno, materia, topico, resposta | Dicionario com nota e feedback. |
| `buscar_historico_avaliacoes_raw` | aluno, materia opcional | Lista de avaliacoes. |
| `criar_avaliacao` | aluno, materia, titulo, topico | Texto. |
| `atualizar_nota` | avaliacao, nota | Texto. |
| `atualizar_feedback` | avaliacao, feedback | Texto. |
| `registrar_avaliacao_banco` | dados completos | Texto. |
| `buscar_historico_avaliacoes` | aluno, materia opcional | Texto. |
| `calcular_desempenho_aluno` | aluno | Texto com media e status. |

## Fluxo interno da avaliacao automatica

```text
gerar_avaliacao_automatica_raw
  |
  +--> criar_avaliacao_raw
  |
  +--> calcular nota heuristica
  |
  +--> gerar feedback
  |
  `--> atualizar_nota_feedback_raw
```

## Onde as tools sao usadas

| Local | Tools usadas |
| --- | --- |
| `agents/orquestrador.py` | `aluno_esta_matriculado_raw`, `buscar_progresso_materia_raw`. |
| `agents/secretario.py` | Tools administrativas e de desempenho. |
| `agents/professor_base.py` | Topicos, progresso, conclusao e avaliacao automatica. |
| `tests/` | Smoke tests e testes de escrita. |

