from datetime import date
from pydantic import BaseModel, Field


class Login(BaseModel):
    email: str
    senha: str


class UsuarioCriar(BaseModel):
    nome: str = Field(min_length=2)
    email: str
    senha: str = Field(min_length=6)
    departamento_id: int
    perfil: str = "colaborador"


class UsuarioSaida(BaseModel):
    id: int
    nome: str
    email: str
    perfil: str
    departamento_id: int

    model_config = {"from_attributes": True}


class DepartamentoCriar(BaseModel):
    nome: str = Field(min_length=2)


class DepartamentoSaida(BaseModel):
    id: int
    nome: str

    model_config = {"from_attributes": True}


class SolicitacaoCriar(BaseModel):
    categoria: str = Field(min_length=2)
    valor: float = Field(gt=0)
    data_despesa: date
    justificativa: str = Field(min_length=3)
    referencia_comprovante: str = Field(min_length=1)


class SolicitacaoAlterar(BaseModel):
    categoria: str | None = None
    valor: float | None = None
    data_despesa: date | None = None
    justificativa: str | None = None
    referencia_comprovante: str | None = None


class Decisao(BaseModel):
    observacao: str | None = None
