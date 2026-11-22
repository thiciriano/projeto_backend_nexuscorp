from datetime import date, datetime

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Departamento, HistoricoAnalise, Solicitacao, Usuario
from .schemas import (
    Decisao,
    DepartamentoCriar,
    Login,
    SolicitacaoAlterar,
    SolicitacaoCriar,
    UsuarioCriar,
)
from .security import conferir_senha, criar_token, hash_senha, usuario_atual


app = FastAPI(title="nexuscorp reembolsos", version="1.0")
Base.metadata.create_all(bind=engine)


@app.get("/")
def inicio():
    return {"mensagem": "api nexuscorp funcionando"}


@app.post("/departamentos")
def criar_departamento(dados: DepartamentoCriar, db: Session = Depends(get_db), atual: Usuario = Depends(usuario_atual)):
    if atual.perfil != "financeiro":
        raise HTTPException(403, "apenas financeiro pode criar departamentos")
    if db.query(Departamento).filter(Departamento.nome == dados.nome).first():
        raise HTTPException(409, "departamento ja existe")
    departamento = Departamento(nome=dados.nome)
    db.add(departamento)
    db.commit()
    db.refresh(departamento)
    return {"id": departamento.id, "nome": departamento.nome}


@app.get("/departamentos")
def listar_departamentos(db: Session = Depends(get_db), atual: Usuario = Depends(usuario_atual)):
    return [{"id": d.id, "nome": d.nome} for d in db.query(Departamento).all()]


@app.post("/auth/register")
def registrar(dados: UsuarioCriar, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == dados.email).first():
        raise HTTPException(409, "email ja cadastrado")
    if not db.get(Departamento, dados.departamento_id):
        raise HTTPException(404, "departamento nao encontrado")
    # cadastro publico sempre cria colaborador
    perfil = "colaborador"
    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        perfil=perfil,
        departamento_id=dados.departamento_id,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return {"id": usuario.id, "nome": usuario.nome, "email": usuario.email, "perfil": usuario.perfil}


@app.post("/users")
def criar_usuario(dados: UsuarioCriar, db: Session = Depends(get_db), atual: Usuario = Depends(usuario_atual)):
    if atual.perfil != "financeiro":
        raise HTTPException(403, "apenas financeiro pode criar usuarios")
    if dados.perfil not in ("colaborador", "gestor", "financeiro"):
        raise HTTPException(422, "perfil invalido")
    if db.query(Usuario).filter(Usuario.email == dados.email).first():
        raise HTTPException(409, "email ja cadastrado")
    if not db.get(Departamento, dados.departamento_id):
        raise HTTPException(404, "departamento nao encontrado")
    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        perfil=dados.perfil,
        departamento_id=dados.departamento_id,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return {"id": usuario.id, "nome": usuario.nome, "email": usuario.email, "perfil": usuario.perfil}


@app.post("/usuarios")
def criar_usuario_pt(dados: UsuarioCriar, db: Session = Depends(get_db), atual: Usuario = Depends(usuario_atual)):
    return criar_usuario(dados=dados, db=db, atual=atual)


@app.post("/auth/login")
def login(dados: Login, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if not usuario or not conferir_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(401, "email ou senha incorretos")
    token = criar_token(db, usuario)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/login")
def login_curto(dados: Login, db: Session = Depends(get_db)):
    return login(dados=dados, db=db)


@app.post("/solicitacoes")
def criar_solicitacao(dados: SolicitacaoCriar, db: Session = Depends(get_db), atual: Usuario = Depends(usuario_atual)):
    if atual.perfil != "colaborador":
        raise HTTPException(403, "somente colaborador cria solicitacao")
    if dados.data_despesa > date.today():
        raise HTTPException(422, "data da despesa nao pode ser futura")
    existente = db.query(Solicitacao).filter(
        Solicitacao.solicitante_id == atual.id,
        Solicitacao.referencia_comprovante == dados.referencia_comprovante,
    ).first()
    if existente:
        raise HTTPException(409, "comprovante ja usado")

    solicitacao = Solicitacao(
        solicitante_id=atual.id,
        categoria=dados.categoria,
        valor=dados.valor,
        data_despesa=dados.data_despesa,
        justificativa=dados.justificativa,
        referencia_comprovante=dados.referencia_comprovante,
        situacao="rascunho",
    )
    db.add(solicitacao)
    db.commit()
    db.refresh(solicitacao)
    return saida_solicitacao(solicitacao)


@app.post("/reembolsos")
def criar_reembolso(dados: SolicitacaoCriar, db: Session = Depends(get_db), atual: Usuario = Depends(usuario_atual)):
    return criar_solicitacao(dados=dados, db=db, atual=atual)


def pode_ver(atual: Usuario, solicitacao: Solicitacao) -> bool:
    if atual.perfil == "colaborador":
        return solicitacao.solicitante_id == atual.id
    if atual.perfil == "gestor":
        solicitante = solicitacao.solicitante
        return solicitante.departamento_id == atual.departamento_id
    return True


def saida_solicitacao(s: Solicitacao):
    return {
        "id": s.id,
        "solicitante_id": s.solicitante_id,
        "categoria": s.categoria,
        "valor": s.valor,
        "data_despesa": s.data_despesa,
        "justificativa": s.justificativa,
        "referencia_comprovante": s.referencia_comprovante,
        "situacao": s.situacao,
    }


@app.get("/solicitacoes")
def listar_solicitacoes(
    situacao: str | None = None,
    categoria: str | None = None,
    departamento: int | None = None,
    db: Session = Depends(get_db),
    atual: Usuario = Depends(usuario_atual),
):
    consulta = db.query(Solicitacao)
    join_usuario = False
    if atual.perfil == "colaborador":
        consulta = consulta.filter(Solicitacao.solicitante_id == atual.id)
    elif atual.perfil == "gestor":
        consulta = consulta.join(Usuario, Solicitacao.solicitante_id == Usuario.id).filter(
            Usuario.departamento_id == atual.departamento_id
        )
        join_usuario = True
    if situacao:
        consulta = consulta.filter(Solicitacao.situacao == situacao)
    if categoria:
        consulta = consulta.filter(Solicitacao.categoria == categoria)
    if departamento:
        if not join_usuario:
            consulta = consulta.join(Usuario, Solicitacao.solicitante_id == Usuario.id)
        consulta = consulta.filter(Usuario.departamento_id == departamento)
        if atual.perfil == "gestor" and departamento != atual.departamento_id:
            consulta = consulta.filter(False)
    return [saida_solicitacao(s) for s in consulta.all()]


@app.get("/solicitacoes/{solicitacao_id}")
def detalhe_solicitacao(solicitacao_id: int, db: Session = Depends(get_db), atual: Usuario = Depends(usuario_atual)):
    s = db.get(Solicitacao, solicitacao_id)
    if not s:
        raise HTTPException(404, "solicitacao nao encontrada")
    if not pode_ver(atual, s):
        raise HTTPException(403, "voce nao pode ver esta solicitacao")
    return saida_solicitacao(s)


@app.patch("/solicitacoes/{solicitacao_id}")
def alterar_solicitacao(solicitacao_id: int, dados: SolicitacaoAlterar, db: Session = Depends(get_db), atual: Usuario = Depends(usuario_atual)):
    s = db.get(Solicitacao, solicitacao_id)
    if not s:
        raise HTTPException(404, "solicitacao nao encontrada")
    if s.solicitante_id != atual.id:
        raise HTTPException(403, "somente o solicitante pode alterar")
    if s.situacao != "rascunho":
        raise HTTPException(409, "solicitacao nao esta mais em rascunho")

    novos = dados.model_dump(exclude_unset=True)
    if "valor" in novos and novos["valor"] <= 0:
        raise HTTPException(422, "valor deve ser maior que zero")
    if "data_despesa" in novos and novos["data_despesa"] > date.today():
        raise HTTPException(422, "data da despesa nao pode ser futura")
    if "referencia_comprovante" in novos:
        duplicada = db.query(Solicitacao).filter(
            Solicitacao.solicitante_id == atual.id,
            Solicitacao.referencia_comprovante == novos["referencia_comprovante"],
            Solicitacao.id != s.id,
        ).first()
        if duplicada:
            raise HTTPException(409, "comprovante ja usado")
    for campo, valor in novos.items():
        setattr(s, campo, valor)
    s.atualizado_em = datetime.utcnow()
    db.commit()
    db.refresh(s)
    return saida_solicitacao(s)


@app.delete("/solicitacoes/{solicitacao_id}")
def excluir_solicitacao(solicitacao_id: int, db: Session = Depends(get_db), atual: Usuario = Depends(usuario_atual)):
    s = db.get(Solicitacao, solicitacao_id)
    if not s:
        raise HTTPException(404, "solicitacao nao encontrada")
    if s.solicitante_id != atual.id:
        raise HTTPException(403, "somente o solicitante pode excluir")
    if s.situacao != "rascunho":
        raise HTTPException(409, "solicitacao nao esta mais em rascunho")
    db.delete(s)
    db.commit()
    return {"mensagem": "solicitacao excluida"}


@app.post("/solicitacoes/{solicitacao_id}/enviar")
def enviar_solicitacao(solicitacao_id: int, db: Session = Depends(get_db), atual: Usuario = Depends(usuario_atual)):
    s = db.get(Solicitacao, solicitacao_id)
    if not s:
        raise HTTPException(404, "solicitacao nao encontrada")
    if s.solicitante_id != atual.id:
        raise HTTPException(403, "somente o solicitante pode enviar")
    if s.situacao != "rascunho":
        raise HTTPException(409, "esta solicitacao ja foi enviada")
    s.situacao = "aguardando_gestor"
    s.atualizado_em = datetime.utcnow()
    db.commit()
    return saida_solicitacao(s)


def decidir(solicitacao_id: int, etapa: str, decisao: str, dados: Decisao, db: Session, atual: Usuario):
    s = db.get(Solicitacao, solicitacao_id)
    if not s:
        raise HTTPException(404, "solicitacao nao encontrada")
    if s.solicitante_id == atual.id:
        raise HTTPException(403, "nao pode analisar solicitacao propria")

    if etapa == "gestor":
        if atual.perfil != "gestor":
            raise HTTPException(403, "somente gestor pode fazer esta analise")
        solicitante = db.get(Usuario, s.solicitante_id)
        if solicitante.departamento_id != atual.departamento_id:
            raise HTTPException(403, "solicitacao pertence a outro departamento")
        if s.situacao != "aguardando_gestor":
            raise HTTPException(409, "solicitacao nao aguarda gestor")
        s.situacao = "aguardando_financeiro" if decisao == "aprovada" else "recusada"
    else:
        if atual.perfil != "financeiro":
            raise HTTPException(403, "somente financeiro pode fazer esta analise")
        if s.situacao != "aguardando_financeiro":
            raise HTTPException(409, "solicitacao nao aguarda financeiro")
        s.situacao = "aprovada" if decisao == "aprovada" else "recusada"

    if decisao == "recusada" and not dados.observacao:
        raise HTTPException(422, "recusa precisa de justificativa")

    historico = HistoricoAnalise(
        solicitacao_id=s.id,
        responsavel_id=atual.id,
        etapa=etapa,
        decisao=decisao,
        observacao=dados.observacao,
    )
    s.atualizado_em = datetime.utcnow()
    db.add(historico)
    db.commit()
    db.refresh(s)
    return saida_solicitacao(s)


@app.post("/solicitacoes/{solicitacao_id}/gestor/aprovar")
def aprovar_gestor(solicitacao_id: int, dados: Decisao, db: Session = Depends(get_db), atual: Usuario = Depends(usuario_atual)):
    return decidir(solicitacao_id, "gestor", "aprovada", dados, db, atual)


@app.post("/solicitacoes/{solicitacao_id}/gestor/recusar")
def recusar_gestor(solicitacao_id: int, dados: Decisao, db: Session = Depends(get_db), atual: Usuario = Depends(usuario_atual)):
    return decidir(solicitacao_id, "gestor", "recusada", dados, db, atual)


@app.post("/solicitacoes/{solicitacao_id}/financeiro/aprovar")
def aprovar_financeiro(solicitacao_id: int, dados: Decisao, db: Session = Depends(get_db), atual: Usuario = Depends(usuario_atual)):
    return decidir(solicitacao_id, "financeiro", "aprovada", dados, db, atual)


@app.post("/solicitacoes/{solicitacao_id}/financeiro/recusar")
def recusar_financeiro(solicitacao_id: int, dados: Decisao, db: Session = Depends(get_db), atual: Usuario = Depends(usuario_atual)):
    return decidir(solicitacao_id, "financeiro", "recusada", dados, db, atual)


@app.post("/solicitacoes/{solicitacao_id}/pagar")
def pagar(solicitacao_id: int, dados: Decisao, db: Session = Depends(get_db), atual: Usuario = Depends(usuario_atual)):
    s = db.get(Solicitacao, solicitacao_id)
    if not s:
        raise HTTPException(404, "solicitacao nao encontrada")
    if atual.perfil != "financeiro":
        raise HTTPException(403, "somente financeiro pode registrar pagamento")
    if s.solicitante_id == atual.id:
        raise HTTPException(403, "nao pode pagar solicitacao propria")
    if s.situacao != "aprovada":
        raise HTTPException(409, "solicitacao ainda nao foi aprovada")
    s.situacao = "paga"
    s.atualizado_em = datetime.utcnow()
    db.add(HistoricoAnalise(
        solicitacao_id=s.id,
        responsavel_id=atual.id,
        etapa="pagamento",
        decisao="paga",
        observacao=dados.observacao,
    ))
    db.commit()
    db.refresh(s)
    return saida_solicitacao(s)


@app.get("/solicitacoes/{solicitacao_id}/historico")
def historico(solicitacao_id: int, db: Session = Depends(get_db), atual: Usuario = Depends(usuario_atual)):
    s = db.get(Solicitacao, solicitacao_id)
    if not s:
        raise HTTPException(404, "solicitacao nao encontrada")
    if not pode_ver(atual, s):
        raise HTTPException(403, "voce nao pode ver esta solicitacao")
    itens = db.query(HistoricoAnalise).filter(HistoricoAnalise.solicitacao_id == s.id).order_by(HistoricoAnalise.id).all()
    return [{
        "id": h.id,
        "responsavel_id": h.responsavel_id,
        "etapa": h.etapa,
        "decisao": h.decisao,
        "data": h.data,
        "observacao": h.observacao,
    } for h in itens]
