from app.database import Base, SessionLocal, engine
from app.models import Departamento, Usuario
from app.security import hash_senha


Base.metadata.create_all(bind=engine)
db = SessionLocal()

if not db.query(Departamento).first():
    comercial = Departamento(nome="comercial")
    tecnologia = Departamento(nome="tecnologia")
    financeiro = Departamento(nome="financeiro")
    db.add_all([comercial, tecnologia, financeiro])
    db.commit()

    db.refresh(comercial)
    db.refresh(tecnologia)
    db.refresh(financeiro)

    usuarios = [
        Usuario(nome="ana", email="ana@nexuscorp.com", senha_hash=hash_senha("123456"),
                perfil="colaborador", departamento_id=comercial.id),
        Usuario(nome="bruno", email="bruno@nexuscorp.com", senha_hash=hash_senha("123456"),
                perfil="colaborador", departamento_id=tecnologia.id),
        Usuario(nome="patricia", email="patricia@nexuscorp.com", senha_hash=hash_senha("123456"),
                perfil="gestor", departamento_id=comercial.id),
        Usuario(nome="carlos", email="carlos@nexuscorp.com", senha_hash=hash_senha("123456"),
                perfil="gestor", departamento_id=tecnologia.id),
        Usuario(nome="financeiro", email="financeiro@nexuscorp.com", senha_hash=hash_senha("123456"),
                perfil="financeiro", departamento_id=financeiro.id),
    ]
    db.add_all(usuarios)
    db.commit()
    print("dados iniciais criados")
else:
    print("banco ja possui dados")

db.close()
