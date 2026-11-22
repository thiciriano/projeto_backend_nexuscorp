from fastapi.testclient import TestClient

from app.database import Base, engine, SessionLocal
from app.models import Departamento
from app.main import app


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)


def test_fluxo_e_regras():
    db = SessionLocal()
    comercial = Departamento(nome="comercial")
    tecnologia = Departamento(nome="tecnologia")
    db.add_all([comercial, tecnologia])
    db.commit()
    db.refresh(comercial)
    db.refresh(tecnologia)
    db.close()

    ana = client.post("/auth/register", json={
        "nome": "ana", "email": "ana@teste.com", "senha": "123456",
        "departamento_id": comercial.id,
    })
    assert ana.status_code == 200

    login = client.post("/auth/login", json={"email": "ana@teste.com", "senha": "123456"})
    assert login.status_code == 200
    ana_token = login.json()["access_token"]
    ana_header = {"Authorization": "Bearer " + ana_token}

    criada = client.post("/solicitacoes", headers=ana_header, json={
        "categoria": "alimentacao",
        "valor": 180,
        "data_despesa": "2026-11-20",
        "justificativa": "almoco",
        "referencia_comprovante": "cupom-1",
    })
    assert criada.status_code == 200
    solicitacao_id = criada.json()["id"]

    enviada = client.post(f"/solicitacoes/{solicitacao_id}/enviar", headers=ana_header)
    assert enviada.status_code == 200

    alterada = client.patch(f"/solicitacoes/{solicitacao_id}", headers=ana_header, json={"valor": 1800})
    assert alterada.status_code == 409

    senha_errada = client.post("/auth/login", json={"email": "ana@teste.com", "senha": "errada"})
    assert senha_errada.status_code == 401
