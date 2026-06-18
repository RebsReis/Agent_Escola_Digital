# Banco de Dados

O projeto usa PostgreSQL como fonte de verdade para alunos, materias, topicos, progresso, matriculas, avaliacoes e historico de conversa.

O acesso operacional e feito com `psycopg2`, principalmente nas tools. Os modelos SQLAlchemy em `database/models.py` documentam a estrutura relacional dentro do codigo Python.

## Arquivos relacionados

| Arquivo | Finalidade |
| --- | --- |
| `database/schema_atualizado.sql` | DDL atualizado com apenas tabelas, enum e constraints. |
| `database/models.py` | Modelos SQLAlchemy das entidades. |
| `database/conexao.py` | Engine e sessao SQLAlchemy. |
| `tools/database_tools.py` | Consultas e comandos de aluno, materia e matricula. |
| `tools/topic_tools.py` | Consultas e comandos de topicos/progresso. |
| `tools/evaluation_tools.py` | Consultas e comandos de avaliacoes. |
| `memoria/gerenteMemoria.py` | Persistencia do historico de conversa. |

## Configuracao

A conexao vem da variavel `DATABASE_URL` no `.env`:

```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/Escola_Digital
```

## Criacao das tabelas

Para criar as tabelas em um banco vazio:

```powershell
psql -U seu_usuario -d Escola_Digital -f database/schema_atualizado.sql
```

O arquivo `schema_atualizado.sql` nao contem dados de exemplo. Ele cria apenas:

- enum `status_avaliacao`;
- tabelas;
- chaves primarias;
- chaves estrangeiras;
- restricoes `UNIQUE`;
- restricoes `CHECK`.

## Tabelas

### `aluno`

Representa o aluno cadastrado na plataforma.

| Coluna | Tipo | Obrigatoria | Observacao |
| --- | --- | --- | --- |
| `id` | `SERIAL` | sim | Chave primaria. |
| `nome` | `VARCHAR(150)` | sim | Nome do aluno. |
| `matricula` | `VARCHAR(20)` | sim | Identificador academico unico. |

Restricoes:

- `PRIMARY KEY (id)`
- `UNIQUE (matricula)`

### `materia`

Representa as materias disponiveis.

| Coluna | Tipo | Obrigatoria | Observacao |
| --- | --- | --- | --- |
| `id` | `SERIAL` | sim | Chave primaria. |
| `aluno_id` | `INTEGER` | nao | Campo existente no schema real; nao e usado para matricula. |
| `nome` | `VARCHAR(100)` | sim | Nome da materia. |
| `descricao` | `TEXT` | nao | Descricao curta. |
| `prompt_ia` | `TEXT` | sim | Persona/instrucao do professor. |

Observacao: matricula e controlada pela tabela `matricula`, nao por `materia.aluno_id`.

### `topico`

Representa topicos pedagogicos dentro de uma materia.

| Coluna | Tipo | Obrigatoria | Observacao |
| --- | --- | --- | --- |
| `id` | `SERIAL` | sim | Chave primaria. |
| `materia_id` | `INTEGER` | nao | FK para `materia`. |
| `titulo` | `VARCHAR(200)` | sim | Titulo do topico. |
| `descricao` | `TEXT` | nao | Conteudo/resumo do topico. |
| `ordem` | `INTEGER` | sim | Ordem pedagogica. |

Restricoes:

- `UNIQUE (materia_id, ordem)`

### `matricula`

Representa o vinculo aluno-materia.

| Coluna | Tipo | Obrigatoria | Observacao |
| --- | --- | --- | --- |
| `id` | `SERIAL` | sim | Chave primaria. |
| `aluno_id` | `INTEGER` | nao | FK para `aluno`. |
| `materia_id` | `INTEGER` | nao | FK para `materia`. |
| `data_matricula` | `TIMESTAMP` | sim | Default `NOW()`. |

Restricoes:

- `UNIQUE (aluno_id, materia_id)`

Regra atendida:

- impede matricula duplicada do mesmo aluno na mesma materia.

### `topico_aluno`

Representa a conclusao de topicos por aluno.

| Coluna | Tipo | Obrigatoria | Observacao |
| --- | --- | --- | --- |
| `id` | `SERIAL` | sim | Chave primaria. |
| `aluno_id` | `INTEGER` | nao | FK para `aluno`. |
| `topico_id` | `INTEGER` | nao | FK para `topico`. |
| `concluido_em` | `TIMESTAMP` | sim | Default `NOW()`. |

Restricoes:

- `UNIQUE (aluno_id, topico_id)`

Regra atendida:

- impede que o mesmo aluno conclua o mesmo topico duas vezes.

### `avaliacao`

Representa avaliacoes criadas e corrigidas pelo sistema.

| Coluna | Tipo | Obrigatoria | Observacao |
| --- | --- | --- | --- |
| `id` | `SERIAL` | sim | Chave primaria. |
| `aluno_id` | `INTEGER` | nao | FK para `aluno`. |
| `materia_id` | `INTEGER` | nao | FK para `materia`. |
| `topico_id` | `INTEGER` | nao | FK para `topico`. |
| `titulo` | `TEXT` | sim | Nome da avaliacao. |
| `nota` | `NUMERIC(4,1)` | nao | Nota de 0 a 10. |
| `feedback_ia` | `TEXT` | nao | Feedback gerado. |
| `data_envio` | `TIMESTAMP` | sim | Default `NOW()`. |
| `status` | `status_avaliacao` | sim | Default `pendente`. |

Enum `status_avaliacao`:

- `pendente`
- `em_andamento`
- `corrigida`

Restricoes:

- `CHECK (nota >= 0 AND nota <= 10)`

Regra atendida:

- avaliacao fica vinculada ao aluno, materia e topico.

### `historico_conversa`

Representa mensagens persistidas da conversa.

| Coluna | Tipo | Obrigatoria | Observacao |
| --- | --- | --- | --- |
| `id` | `SERIAL` | sim | Chave primaria. |
| `avaliacao_id` | `INTEGER` | nao | FK opcional para `avaliacao`. |
| `role` | `VARCHAR(20)` | nao | `user` ou `assistant`. |
| `conteudo` | `TEXT` | sim | Texto da mensagem. |
| `criado_em` | `TIMESTAMP` | sim | Default `NOW()`. |

Restricoes:

- `CHECK (role = 'user' OR role = 'assistant')`

## Relacionamentos principais

```text
aluno 1---N matricula N---1 materia
materia 1---N topico
aluno 1---N topico_aluno N---1 topico
aluno 1---N avaliacao
materia 1---N avaliacao
topico 1---N avaliacao
avaliacao 1---N historico_conversa
```

## Consultas uteis

Listar materias:

```sql
SELECT id, nome, descricao
FROM materia
ORDER BY id;
```

Ver matriculas de um aluno:

```sql
SELECT m.id, m.nome
FROM matricula mat
JOIN materia m ON mat.materia_id = m.id
WHERE mat.aluno_id = 1
ORDER BY m.id;
```

Ver progresso por materia:

```sql
SELECT
    m.nome AS materia,
    COUNT(DISTINCT t.id) AS total_topicos,
    COUNT(DISTINCT ta.topico_id) AS topicos_concluidos
FROM materia m
LEFT JOIN topico t ON m.id = t.materia_id
LEFT JOIN topico_aluno ta ON t.id = ta.topico_id AND ta.aluno_id = 1
GROUP BY m.id, m.nome
ORDER BY m.id;
```

Historico de avaliacoes:

```sql
SELECT av.id, m.nome AS materia, t.titulo AS topico, av.titulo, av.nota, av.status
FROM avaliacao av
JOIN materia m ON m.id = av.materia_id
LEFT JOIN topico t ON t.id = av.topico_id
WHERE av.aluno_id = 1
ORDER BY av.data_envio DESC;
```
