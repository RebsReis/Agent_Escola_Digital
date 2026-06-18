# Fluxos Funcionais

Este documento descreve os fluxos principais da aplicacao em nivel de comportamento.

## 1. Fluxo geral de uma mensagem

```text
Aluno digita mensagem
  |
main.py cria HumanMessage
  |
app.invoke(estado, config)
  |
no_orquestrador
  |
roteamento condicional
  |
secretario ou professor
  |
resposta do agente
  |
persistencia do turno
```

Passo a passo:

1. O usuario digita uma mensagem no terminal.
2. `main.py` cria uma `HumanMessage`.
3. O estado atual e enviado para o grafo.
4. O grafo executa o orquestrador.
5. O orquestrador decide `proxima_acao`.
6. O grafo roteia para o agente adequado.
7. O agente responde.
8. `main.py` imprime a resposta.
9. O historico do turno e salvo no banco.

## 2. Fluxo administrativo

Exemplos de entrada:

```text
minhas matriculas
matricular em BPO
remover matricula de BPO
qual meu progresso?
qual meu desempenho?
historico de avaliacoes
cadastrar aluno nome: Maria Silva, matricula: MAT999
```

Passo a passo:

1. O orquestrador classifica a mensagem como administrativa.
2. A rota definida e `secretario`.
3. O Secretario identifica a intencao administrativa.
4. O Secretario chama a tool apropriada.
5. A tool consulta ou atualiza o PostgreSQL.
6. O resultado da tool entra no prompt do Secretario.
7. O Secretario responde com linguagem formal e administrativa.

Tools mais usadas nesse fluxo:

| Acao | Tool |
| --- | --- |
| Buscar aluno | `buscar_aluno` |
| Cadastrar aluno | `criar_aluno` |
| Listar materias | `listar_materias_disponiveis` |
| Consultar matriculas | `consultar_matriculas_aluno` |
| Matricular | `matricular_aluno` |
| Remover matricula | `remover_matricula` |
| Consultar progresso | `buscar_progresso_geral_aluno` |
| Consultar desempenho | `calcular_desempenho_aluno` |
| Historico de avaliacoes | `buscar_historico_avaliacoes` |

## 3. Fluxo pedagogico

Exemplo:

```text
Quero estudar IA
Explique embeddings
```

Passo a passo:

1. Orquestrador identifica materia de IA.
2. Orquestrador verifica se o aluno esta matriculado.
3. Se estiver matriculado, `proxima_acao = ia`.
4. O grafo chama `no_prof_ia`.
5. O professor busca:
   - topicos da materia;
   - progresso do aluno;
   - proximo topico pendente;
   - historico isolado de IA.
6. O professor monta um prompt com persona, topico atual e progresso.
7. A LLM gera uma resposta pedagogica.
8. O historico isolado da materia e atualizado no estado.

## 4. Conclusao de topico

Exemplo:

```text
Entendi o topico, pode avaliar
```

Frases que podem disparar conclusao:

- `concluir topico`
- `finalizar topico`
- `terminei o topico`
- `entendi o topico`
- `pode avaliar`
- `fazer avaliacao`

Passo a passo:

1. Professor detecta gatilho de conclusao.
2. Busca o topico atual/proximo pendente.
3. Insere registro em `topico_aluno`.
4. Atualiza `completed_topics` no estado.
5. Gera avaliacao automatica.
6. Corrige com nota e feedback.
7. Retorna a resposta ao aluno.

## 5. Avaliacao automatica

A avaliacao automatica ocorre logo apos a conclusao de um topico.

Dados gravados:

- `aluno_id`;
- `materia_id`;
- `topico_id`;
- `titulo`;
- `nota`;
- `feedback_ia`;
- `status = corrigida`;
- `data_envio`.

Observacao: a nota automatica atual e uma heuristica simples. Ela pode ser evoluida para uma correcao semantica por LLM.

## 6. Bloqueio por matricula

Exemplo:

```text
Quero estudar BPO
```

Se o aluno nao estiver matriculado:

1. Orquestrador identifica materia destino.
2. Consulta `aluno_esta_matriculado_raw`.
3. Retorna mensagem de bloqueio.
4. Orienta o aluno a procurar o Secretario.

Mensagem esperada:

```text
Nao posso encaminhar voce para essa materia ainda, pois nao encontrei matricula ativa nela.
```

## 7. Bloqueio de troca de materia

Exemplo:

```text
Quero estudar IA
Agora quero estudar Engenharia de Dados
```

Se o aluno ainda nao concluiu topico na materia atual:

1. Orquestrador identifica tentativa de troca.
2. Consulta progresso da materia ativa.
3. Se `topicos_concluidos < 1`, bloqueia.
4. Mantem consistencia do contexto pedagogico.

## 8. Persistencia de conversa

Ao final de cada turno:

1. `main.py` chama `persistir_novas_mensagens_grafo`.
2. A ultima mensagem do usuario e a resposta do agente sao salvas.
3. Se houve avaliacao automatica, o historico e vinculado ao `avaliacao_id`.

Tabela usada:

```text
historico_conversa
```

Campos relevantes:

- `role`
- `conteudo`
- `avaliacao_id`
- `criado_em`

## 9. Demonstracao completa sugerida

Fluxo recomendado para demonstracao:

```text
minhas matriculas
Quero estudar IA
Explique embeddings
Entendi o topico, pode avaliar
qual meu desempenho?
historico de avaliacoes
```

Fluxo de bloqueio:

```text
remover matricula de BPO
Quero estudar BPO
matricular em BPO
Quero estudar BPO
```
