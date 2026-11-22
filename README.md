# nexuscorp reembolsos

api simples para controlar reembolsos de uma empresa.

## instalar

```bash
python -m pip install -r requirements.txt
```

## rodar

```bash
uvicorn main:app --reload
```

para criar usuários de exemplo:

```bash
python seed.py
```

abra a documentação em `http://127.0.0.1:8000/docs`.

## banco

o projeto usa sqlite. o arquivo `nexuscorp.db` é criado sozinho na primeira execução.

## perfis

- colaborador: cria, edita, exclui e envia suas solicitações
- gestor: analisa solicitações do próprio departamento
- financeiro: faz a análise financeira e registra o pagamento

## principais rotas

- `POST /auth/register`: cria colaborador
- `POST /auth/login`: faz login e devolve token
- `POST /departamentos`: cria departamento (financeiro)
- `POST /users`: cria usuário (financeiro)
- `POST /solicitacoes`: cria solicitação
- `GET /solicitacoes`: lista respeitando o perfil
- `GET /solicitacoes/{id}`: detalhes
- `PATCH /solicitacoes/{id}`: altera rascunho
- `DELETE /solicitacoes/{id}`: exclui rascunho
- `POST /solicitacoes/{id}/enviar`: envia para o gestor
- `POST /solicitacoes/{id}/gestor/aprovar`: aprova no gestor
- `POST /solicitacoes/{id}/gestor/recusar`: recusa no gestor
- `POST /solicitacoes/{id}/financeiro/aprovar`: aprova no financeiro
- `POST /solicitacoes/{id}/financeiro/recusar`: recusa no financeiro
- `POST /solicitacoes/{id}/pagar`: registra pagamento
- `GET /solicitacoes/{id}/historico`: mostra decisões

para usar rotas privadas envie o header `Authorization: Bearer SEU_TOKEN`.

## modelo

- departamento tem vários usuários
- usuário tem várias solicitações
- solicitação tem vários registros no histórico
- token de sessão pertence a um usuário

## segurança

as senhas são guardadas com hash e salt. os tokens são números aleatórios, somente o hash do token fica no banco. cada token dura oito horas.