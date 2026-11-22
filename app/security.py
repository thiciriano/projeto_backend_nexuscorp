import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .models import TokenSessao, Usuario


def hash_senha(senha: str) -> str:
    # guarda uma senha codificada, nunca o texto original
    salt = secrets.token_hex(16)
    dig = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), 100000)
    return salt + ":" + dig.hex()


def conferir_senha(senha: str, senha_guardada: str) -> bool:
    try:
        salt, dig = senha_guardada.split(":")
    except ValueError:
        return False
    novo = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), 100000).hex()
    return secrets.compare_digest(dig, novo)


def criar_token(db: Session, usuario: Usuario) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    db.add(TokenSessao(
        token_hash=token_hash,
        usuario_id=usuario.id,
        expira_em=datetime.utcnow() + timedelta(hours=8),
    ))
    db.commit()
    return token


def usuario_atual(db: Session = Depends(get_db), authorization: str | None = Header(default=None)) -> Usuario:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="login necessario")

    token = authorization.removeprefix("Bearer ").strip()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    sessao = db.query(TokenSessao).filter(
        TokenSessao.token_hash == token_hash,
        TokenSessao.expira_em > datetime.utcnow(),
    ).first()
    if not sessao:
        raise HTTPException(status_code=401, detail="login invalido ou expirado")

    usuario = db.get(Usuario, sessao.usuario_id)
    if not usuario:
        raise HTTPException(status_code=401, detail="usuario nao encontrado")
    return usuario
