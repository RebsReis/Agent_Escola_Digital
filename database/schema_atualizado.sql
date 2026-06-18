-- Schema atualizado - Escola Digital
-- Apenas estrutura de tabelas, sem dados.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_avaliacao') THEN
        CREATE TYPE status_avaliacao AS ENUM ('pendente', 'em_andamento', 'corrigida');
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS aluno (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    matricula VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS materia (
    id SERIAL PRIMARY KEY,
    aluno_id INTEGER NULL,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT NULL,
    prompt_ia TEXT NOT NULL,
    CONSTRAINT materia_aluno_id_fkey
        FOREIGN KEY (aluno_id) REFERENCES aluno(id)
);

CREATE TABLE IF NOT EXISTS topico (
    id SERIAL PRIMARY KEY,
    materia_id INTEGER NULL,
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT NULL,
    ordem INTEGER NOT NULL,
    CONSTRAINT topico_materia_id_fkey
        FOREIGN KEY (materia_id) REFERENCES materia(id),
    CONSTRAINT unique_materia_ordem
        UNIQUE (materia_id, ordem)
);

CREATE TABLE IF NOT EXISTS matricula (
    id SERIAL PRIMARY KEY,
    aluno_id INTEGER NULL,
    materia_id INTEGER NULL,
    data_matricula TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT matricula_aluno_id_fkey
        FOREIGN KEY (aluno_id) REFERENCES aluno(id),
    CONSTRAINT matricula_materia_id_fkey
        FOREIGN KEY (materia_id) REFERENCES materia(id),
    CONSTRAINT unique_aluno_materia
        UNIQUE (aluno_id, materia_id)
);

CREATE TABLE IF NOT EXISTS topico_aluno (
    id SERIAL PRIMARY KEY,
    aluno_id INTEGER NULL,
    topico_id INTEGER NULL,
    concluido_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT topico_aluno_aluno_id_fkey
        FOREIGN KEY (aluno_id) REFERENCES aluno(id),
    CONSTRAINT topico_aluno_topico_id_fkey
        FOREIGN KEY (topico_id) REFERENCES topico(id),
    CONSTRAINT unique_aluno_topico
        UNIQUE (aluno_id, topico_id)
);

CREATE TABLE IF NOT EXISTS avaliacao (
    id SERIAL PRIMARY KEY,
    aluno_id INTEGER NULL,
    materia_id INTEGER NULL,
    titulo TEXT NOT NULL,
    nota NUMERIC(4, 1) NULL,
    feedback_ia TEXT NULL,
    data_envio TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    status status_avaliacao NOT NULL DEFAULT 'pendente',
    topico_id INTEGER NULL,
    CONSTRAINT avaliacao_aluno_id_fkey
        FOREIGN KEY (aluno_id) REFERENCES aluno(id),
    CONSTRAINT avaliacao_materia_id_fkey
        FOREIGN KEY (materia_id) REFERENCES materia(id),
    CONSTRAINT avaliacao_topico_id_fkey
        FOREIGN KEY (topico_id) REFERENCES topico(id),
    CONSTRAINT avaliacao_nota_check
        CHECK (nota >= 0 AND nota <= 10)
);

CREATE TABLE IF NOT EXISTS historico_conversa (
    id SERIAL PRIMARY KEY,
    avaliacao_id INTEGER NULL,
    role VARCHAR(20) NULL,
    conteudo TEXT NOT NULL,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT historico_conversa_avaliacao_id_fkey
        FOREIGN KEY (avaliacao_id) REFERENCES avaliacao(id),
    CONSTRAINT historico_conversa_role_check
        CHECK (role = 'user' OR role = 'assistant')
);
