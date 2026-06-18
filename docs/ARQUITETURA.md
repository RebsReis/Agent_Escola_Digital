# Arquitetura

## Proposito arquitetural

O projeto foi organizado para separar responsabilidades entre:

- roteamento e regras globais;
- operacoes administrativas;
- ensino por materia;
- ferramentas de banco;
- memoria;
- grafo de execucao.

Essa separacao permite demonstrar os conceitos centrais do escopo: agentes independentes, tools, memoria contextual, regras de negocio e persistencia.

## Visao geral do fluxo

```text
Usuario
  |
  v
main.py
  |
  v
LangGraph app
  |
  v
no_orquestrador
  |
  +--> no_secretario
  |
  +--> no_prof_sql
  |
  +--> no_prof_engenharia
  |
  +--> no_prof_ia
  |
  +--> no_prof_bpo
  |
  `--> END
```

Cada turno passa obrigatoriamente pelo orquestrador. O orquestrador nao responde conteudo pedagogico; ele decide a rota e aplica bloqueios.

## Grafo LangGraph

Arquivo: `workflows/graph.py`.

O grafo contem:

| No | Funcao |
| --- | --- |
| `no_orquestrador` | Entrada logica do fluxo. Classifica a mensagem e define `proxima_acao`. |
| `no_secretario` | Responde demandas administrativas. |
| `no_prof_sql` | Professor de Banco de Dados SQL. |
| `no_prof_engenharia` | Professor de Engenharia de Dados. |
| `no_prof_ia` | Professor de Inteligencia Artificial. |
| `no_prof_bpo` | Professor de Estrategia de Negocios BPO. |
| `END` | Finaliza o turno. |

O roteamento condicional usa `rotear_pos_orquestrador`.

Valores esperados de `proxima_acao`:

| Valor | Destino |
| --- | --- |
| `sql` | `no_prof_sql` |
| `engenharia` | `no_prof_engenharia` |
| `ia` | `no_prof_ia` |
| `bpo` | `no_prof_bpo` |
| `secretario` | `no_secretario` |
| `finalizar` | `END` |

Qualquer valor desconhecido tambem cai em `END`, evitando execucao indevida.

## Estado do workflow

Tipo: `EscolaDigitalState`.

| Campo | Tipo esperado | Descricao |
| --- | --- | --- |
| `messages` | lista de mensagens | Historico global mantido pelo LangGraph. |
| `historico_sql` | lista de mensagens | Historico isolado do professor SQL. |
| `historico_engenharia` | lista de mensagens | Historico isolado de Engenharia de Dados. |
| `historico_ia` | lista de mensagens | Historico isolado de IA. |
| `historico_bpo` | lista de mensagens | Historico isolado de BPO. |
| `aluno_id` | inteiro | Aluno logado. |
| `aluno_nome` | texto | Nome do aluno logado. |
| `materia_id` | inteiro | Materia ativa. |
| `topico_atual_id` | inteiro | Topico ativo ou proximo topico pendente. |
| `proxima_acao` | texto | Rota definida pelo orquestrador. |
| `last_agent` | texto | Ultimo agente que respondeu. |
| `current_subject` | texto/nulo | Materia corrente. |
| `completed_topics` | lista | Topicos concluidos na sessao. |
| `avaliacao_id` | inteiro/nulo | Avaliacao gerada no turno. |

## Agente Orquestrador

Arquivo: `agents/orquestrador.py`.

Responsabilidades:

- Receber a mensagem do aluno.
- Ler as ultimas mensagens globais persistidas.
- Chamar `ChatOpenAI` com saida estruturada via Pydantic.
- Normalizar aliases de rota.
- Definir a materia destino.
- Bloquear acesso a materia sem matricula.
- Bloquear troca de materia antes da conclusao de um topico.

### Saida estruturada

O orquestrador espera um objeto `Roteamento`:

```python
class Roteamento(BaseModel):
    proximo_agente: str
    justificativa: str
    materia_id: int
```

### Regras aplicadas

1. Mensagem administrativa vai para `secretario`.
2. Mensagem pedagogica vai para o professor correto.
3. Despedida ou encerramento vai para `finalizar`.
4. Materia sem matricula e bloqueada.
5. Troca de materia sem topico concluido e bloqueada.

## Agente Secretario

Arquivo: `agents/secretario.py`.

O secretario interpreta comandos administrativos com regras simples de texto e chama tools.

Operacoes suportadas:

- buscar aluno;
- criar aluno;
- listar materias;
- consultar matriculas;
- matricular aluno;
- remover matricula;
- consultar progresso;
- consultar desempenho;
- consultar historico de avaliacoes.

O secretario usa a LLM apenas para formatar a resposta final com tom administrativo. A informacao factual vem das tools.

## Professores

Arquivos especificos:

- `agents/agent_Banco_de_dados.py`
- `agents/agent_Engenharia_dados.py`
- `agents/agent_IA.py`
- `agents/agent_Estrategia_BPO.py`

Arquivo comum:

- `agents/professor_base.py`

Cada professor informa:

- `materia_id`;
- titulo/persona;
- instrucoes especificas;
- temperatura da LLM.

`professor_base.py` faz o trabalho comum:

- seleciona historico isolado da materia;
- busca topicos;
- busca progresso;
- identifica proximo topico pendente;
- monta prompt pedagogico;
- detecta pedido de conclusao de topico;
- marca topico como concluido;
- gera avaliacao automatica;
- atualiza o estado do grafo.

## Memoria

Arquivo: `memoria/gerenteMemoria.py`.

Existem tres niveis de memoria:

1. Memoria do turno em `messages`.
2. Memoria isolada por materia em `historico_sql`, `historico_engenharia`, `historico_ia`, `historico_bpo`.
3. Memoria persistida em `historico_conversa`.

O orquestrador consulta as ultimas mensagens globais persistidas. Os professores usam o historico isolado da materia no estado.

## Persistencia

Dados persistidos:

- matriculas;
- progresso de topicos;
- avaliacoes;
- notas;
- feedbacks;
- historico de conversa.

O final de cada turno chama:

```python
GerenteMemoriaDB.persistir_novas_mensagens_grafo(...)
```

Quando o turno gera avaliacao, `avaliacao_id` vincula a conversa a essa avaliacao.
