from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Departamento(Base):
    __tablename__ = "departamentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String, unique=True)

    usuarios = relationship("Usuario", back_populates="departamento")


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True)
    senha_hash: Mapped[str] = mapped_column(String)
    perfil: Mapped[str] = mapped_column(String)
    departamento_id: Mapped[int] = mapped_column(ForeignKey("departamentos.id"))

    departamento = relationship("Departamento", back_populates="usuarios")
    solicitacoes = relationship("Solicitacao", back_populates="solicitante")


class TokenSessao(Base):
    __tablename__ = "tokens_sessao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String, unique=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    expira_em: Mapped[datetime] = mapped_column(DateTime)


class Solicitacao(Base):
    __tablename__ = "solicitacoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    solicitante_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    categoria: Mapped[str] = mapped_column(String)
    valor: Mapped[float] = mapped_column(Float)
    data_despesa: Mapped[date] = mapped_column(Date)
    justificativa: Mapped[str] = mapped_column(String)
    referencia_comprovante: Mapped[str] = mapped_column(String)
    situacao: Mapped[str] = mapped_column(String, default="rascunho")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    solicitante = relationship("Usuario", back_populates="solicitacoes")
    historicos = relationship("HistoricoAnalise", back_populates="solicitacao")


class HistoricoAnalise(Base):
    __tablename__ = "historicos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    solicitacao_id: Mapped[int] = mapped_column(ForeignKey("solicitacoes.id"))
    responsavel_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    etapa: Mapped[str] = mapped_column(String)
    decisao: Mapped[str] = mapped_column(String)
    data: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    observacao: Mapped[str | None] = mapped_column(String, nullable=True)

    solicitacao = relationship("Solicitacao", back_populates="historicos")
    responsavel = relationship("Usuario")
