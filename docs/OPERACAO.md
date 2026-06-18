# Operacao

Este guia resume como preparar, executar, testar e solucionar problemas comuns do projeto.

## 1. Preparar ambiente

Criar venv:

```powershell
python -m venv venv
```

Instalar dependencias:

```powershell
venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. Configurar `.env`

Arquivo esperado na raiz do projeto:

```env
OPENAI_API_KEY=sua_chave
DATABASE_URL=postgresql://usuario:senha@localhost:5432/Escola_Digital
```

Cuidados:

- nao commitar `.env`;
- nao colar chave em chats ou documentos;
- revogar chave exposta.

## 3. Criar banco

Com PostgreSQL rodando:

```powershell
createdb -U seu_usuario Escola_Digital
psql -U seu_usuario -d Escola_Digital -f database/schema_atualizado.sql
```

Se o banco ja existir, o script usa `CREATE TABLE IF NOT EXISTS` para as tabelas.

## 4. Executar aplicacao

```powershell
venv\Scripts\python.exe main.py
```

Saida esperada:

```text
SISTEMA ESCOLA DIGITAL - VERSAO MULTI-AGENTES
Bem-vindo de volta, Arthur Felipe!
Aluno:
```

## 5. Comandos uteis na conversa

Administrativo:

```text
minhas matriculas
matricular em BPO
remover matricula de BPO
qual meu progresso?
qual meu desempenho?
historico de avaliacoes
```

Pedagogico:

```text
Quero estudar IA
Explique embeddings
Entendi o topico, pode avaliar
```

Encerrar:

```text
sair
```

## 6. Rodar testes

Todos:

```powershell
venv\Scripts\python.exe tests\run_all.py
```

Somente testes seguros:

```powershell
venv\Scripts\python.exe -m unittest tests.test_static_project -v
venv\Scripts\python.exe -m unittest tests.test_database_smoke -v
```

## 7. Troubleshooting

### `OPENAI_API_KEY` ausente

Sintoma:

```text
Aviso: configure a OPENAI_API_KEY no ambiente ou arquivo .env
```

Solucao:

- preencher `OPENAI_API_KEY` no `.env`;
- reiniciar o terminal se necessario.

### Erro de conexao com PostgreSQL

Verifique:

- PostgreSQL esta rodando;
- banco existe;
- usuario/senha estao corretos;
- `DATABASE_URL` aponta para o banco certo;
- firewall/porta local nao bloqueia `5432`.

### Aluno sem acesso a materia

Sintoma:

```text
Nao posso encaminhar voce para essa materia ainda...
```

Solucao:

```text
matricular em BPO
```

ou trocar `BPO` pela materia desejada.

### Troca de materia bloqueada

Sintoma:

```text
Troca de materia bloqueada...
```

Solucao:

- concluir ao menos um topico da materia atual:

```text
Entendi o topico, pode avaliar
```

### Testes criaram dados

Esperado:

- `test_admin_write_flow` cria aluno de teste;
- `test_topic_evaluation_flow` cria avaliacao.

Recomendacao:

- rodar testes em banco de desenvolvimento.

## 8. Checklist antes de demonstrar

1. `.env` configurado.
2. PostgreSQL rodando.
3. Banco com schema atualizado.
4. Aluno demo existe.
5. Materias e topicos cadastrados.
6. Testes seguros passando.
7. Chave OpenAI valida.

