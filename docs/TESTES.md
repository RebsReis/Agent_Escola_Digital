# Testes

Os testes usam `unittest`, biblioteca padrao do Python. Nao ha dependencia de `pytest`.

## Objetivo da suite

A suite cobre:

- imports principais;
- roteamento estatico do grafo;
- parser de materia do secretario;
- leitura do banco;
- existencia de `avaliacao.topico_id`;
- fluxo administrativo com escrita;
- fluxo de avaliacao automatica sem OpenAI.

Nenhum teste chama a API da OpenAI.

## Rodar tudo

```powershell
venv\Scripts\python.exe tests\run_all.py
```

## Rodar por modulo

```powershell
venv\Scripts\python.exe -m unittest tests.test_static_project -v
venv\Scripts\python.exe -m unittest tests.test_database_smoke -v
venv\Scripts\python.exe -m unittest tests.test_admin_write_flow -v
venv\Scripts\python.exe -m unittest tests.test_topic_evaluation_flow -v
```

## `tests/test_static_project.py`

Tipo: seguro, sem banco, sem escrita, sem OpenAI.

Valida:

- `import main`;
- import do grafo;
- rotas:
  - `sql`;
  - `engenharia`;
  - `ia`;
  - `bpo`;
  - `secretario`;
  - `finalizar`;
- parser de materia do secretario.

Quando usar:

- sempre depois de alterar grafo, orquestrador ou secretario.

## `tests/test_database_smoke.py`

Tipo: leitura no banco.

Valida:

- busca do aluno Arthur;
- listagem de materias;
- consulta de matriculas;
- topicos;
- progresso;
- desempenho;
- existencia da coluna `avaliacao.topico_id`.

Quando usar:

- depois de alterar schema;
- depois de alterar tools de consulta;
- antes de demonstrar o projeto.

## `tests/test_admin_write_flow.py`

Tipo: escrita no banco.

Valida:

- criacao de aluno teste;
- busca por matricula;
- matricula em BPO;
- remocao da matricula.

Observacao:

- cria ou reutiliza a matricula `TESTE_CODEX_001`;
- remove a matricula em BPO ao final;
- nao apaga o aluno teste.

## `tests/test_topic_evaluation_flow.py`

Tipo: escrita no banco.

Valida:

- busca de topico;
- criacao de avaliacao automatica;
- nota entre 0 e 10;
- avaliacao aparece no historico.

Observacao:

- cria registro em `avaliacao`;
- nao chama OpenAI.

## Interpretando resultado

Sucesso:

```text
OK
```

Falha comum:

```text
DATABASE_URL nao configurada
```

Solucao:

- conferir arquivo `.env`;
- conferir se o terminal esta rodando a partir da raiz do projeto.

Falha de conexao:

- PostgreSQL desligado;
- banco inexistente;
- usuario ou senha incorretos;
- `DATABASE_URL` apontando para banco errado.

## Ordem recomendada antes da entrega

```powershell
venv\Scripts\python.exe -m unittest tests.test_static_project -v
venv\Scripts\python.exe -m unittest tests.test_database_smoke -v
venv\Scripts\python.exe tests\run_all.py
```

Se quiser evitar escrita no banco, rode apenas:

```powershell
venv\Scripts\python.exe -m unittest tests.test_static_project -v
venv\Scripts\python.exe -m unittest tests.test_database_smoke -v
```

