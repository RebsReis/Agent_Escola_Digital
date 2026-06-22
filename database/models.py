"""
Modelos de Dados do Sistema Escola Digital.

Define todas as entidades do banco de dados com relacionamentos,
restrições e integridade referencial utilizando SQLAlchemy ORM.
"""

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Classe base para todos os modelos ORM."""
    pass


class StatusAvaliacao(enum.Enum):
    """Enum para os possíveis status de uma avaliação."""
    pendente = "pendente"
    em_andamento = "em_andamento"
    corrigida = "corrigida"


class Aluno(Base):
    """
    Modelo de Aluno.
    
    Representa um aluno do sistema com seus dados pessoais
    e relacionamentos com matrículas, tópicos concluídos e avaliações.
    """
    __tablename__ = "aluno"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    matricula: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    
    # Relacionamentos
    matriculas: Mapped[List["Matricula"]] = relationship(back_populates="aluno")
    topicos_concluidos: Mapped[List["TopicoAluno"]] = relationship(back_populates="aluno")
    avaliacoes: Mapped[List["Avaliacao"]] = relationship(back_populates="aluno")


class Materia(Base):
    """
    Modelo de Matéria.
    
    Representa uma disciplina do sistema com tópicos, matrículas
    e um prompt específico para o agente professor especialista.
    """
    __tablename__ = "materia"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text)
    prompt_ia: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Relacionamentos
    topicos: Mapped[List["Topico"]] = relationship(back_populates="materia")
    matriculas: Mapped[List["Matricula"]] = relationship(back_populates="materia")
    avaliacoes: Mapped[List["Avaliacao"]] = relationship(back_populates="materia")


class Topico(Base):
    """
    Modelo de Tópico.
    
    Representa um tópico/unidade de aprendizado dentro de uma matéria,
    com ordenação para garantir sequência pedagógica.
    """
    __tablename__ = "topico"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    materia_id: Mapped[int] = mapped_column(ForeignKey("materia.id"))
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text)
    ordem: Mapped[int] = mapped_column(nullable=False)
    
    # Relacionamentos
    materia: Mapped["Materia"] = relationship(back_populates="topicos")
    conclusoes_alunos: Mapped[List["TopicoAluno"]] = relationship(back_populates="topico")
    
    # Restrição: Ordem única por matéria
    __table_args__ = (
        UniqueConstraint("materia_id", "ordem", name="unique_materia_ordem"),
    )


class TopicoAluno(Base):
    """
    Modelo de Progresso do Aluno.
    
    Rastreia quais tópicos cada aluno completou e quando,
    permitindo análise de progresso e recomendação de próximos passos.
    """
    __tablename__ = "topico_aluno"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("aluno.id"))
    topico_id: Mapped[int] = mapped_column(ForeignKey("topico.id"))
    concluido_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    
    # Relacionamentos
    aluno: Mapped["Aluno"] = relationship(back_populates="topicos_concluidos")
    topico: Mapped["Topico"] = relationship(back_populates="conclusoes_alunos")
    
    # Restrição: Impede marcar o mesmo tópico como concluído duas vezes
    __table_args__ = (
        UniqueConstraint("aluno_id", "topico_id", name="unique_aluno_topico"),
    )


class Matricula(Base):
    """
    Modelo de Matrícula.
    
    Representa o vínculo de um aluno em uma matéria,
    registrando a data de inscrição.
    """
    __tablename__ = "matricula"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("aluno.id"))
    materia_id: Mapped[int] = mapped_column(ForeignKey("materia.id"))
    data_matricula: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    
    # Relacionamentos
    aluno: Mapped["Aluno"] = relationship(back_populates="matriculas")
    materia: Mapped["Materia"] = relationship(back_populates="matriculas")
    
    # Restrição: Impede matrícula duplicada no mesmo aluno+matéria
    __table_args__ = (
        UniqueConstraint("aluno_id", "materia_id", name="unique_aluno_materia"),
    )


class Avaliacao(Base):
    """
    Modelo de Avaliação.
    
    Registra uma avaliação enviada por um aluno em uma matéria,
    incluindo nota, feedback e status de correção.
    """
    __tablename__ = "avaliacao"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("aluno.id"))
    materia_id: Mapped[int] = mapped_column(ForeignKey("materia.id"))
    topico_id: Mapped[Optional[int]] = mapped_column(ForeignKey("topico.id"))
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    nota: Mapped[Optional[float]] = mapped_column(Numeric(4, 1))
    feedback_ia: Mapped[Optional[str]] = mapped_column(Text)
    data_envio: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status: Mapped[StatusAvaliacao] = mapped_column(
        Enum(StatusAvaliacao), default=StatusAvaliacao.pendente, nullable=False
    )
    
    # Relacionamentos
    aluno: Mapped["Aluno"] = relationship(back_populates="avaliacoes")
    materia: Mapped["Materia"] = relationship(back_populates="avaliacoes")
    historico_conversas: Mapped[List["HistoricoConversa"]] = relationship(back_populates="avaliacao")
    
    # Restrições: Nota entre 0 e 10
    __table_args__ = (
        CheckConstraint("nota >= 0 AND nota <= 10", name="check_nota_range"),
    )


class HistoricoConversa(Base):
    """
    Modelo de Histórico de Conversa.
    
    Armazena todas as mensagens de conversas entre aluno e agentes,
    permitindo análise de histórico e contexto para futuras interações.
    """
    __tablename__ = "historico_conversa"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    avaliacao_id: Mapped[Optional[int]] = mapped_column(ForeignKey("avaliacao.id"))
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    conteudo: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    avaliacao: Mapped["Avaliacao"] = relationship(back_populates="historico_conversas")
    
    # Restrições: Apenas user ou assistant
    __table_args__ = (
        CheckConstraint("role = 'user' OR role = 'assistant'", name="check_role_type"),
    )

