import json
from db.pg import engine
from sqlalchemy import text
import datetime


def handler(event, context):
    body = json.loads(event['body'])
    if (int(event['pathParameters']['id']) <= 0 or int(event['pathParameters']['id']) > 5):
        return {
            "statusCode": 404,
            "body": None
        }

    required_fields = ["valor", "tipo", "descricao"]

    if event['body'] is None:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Missing body"
            })
        }

    for field in required_fields:
        if field not in event['body']:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "message": "Missing field: " + field
                })
            }

    limite_cliente = 0
    saldo_cliente = 0
    transactions = []

    with engine.connect() as conn:
        query = conn.execute(
            text("SELECT transfer_limit, balance, transactions FROM clients WHERE id = :id"), {
                'id': event['pathParameters']['id']}
        )

        for row in query:
            limite_cliente = row[0]
            saldo_cliente = row[1]
            transactions = row[2]

        if body['tipo'] == 'd':
            valor = body['valor']
            if (saldo_cliente - valor < -limite_cliente):
                return {
                    "statusCode": 422,
                    "body": None}

        new_balance = 0

        if (body['tipo'] == 'c'):
            new_balance = saldo_cliente + body['valor']
        else:
            new_balance = saldo_cliente - body['valor']

        if (len(transactions) == 10):
            transactions.pop()

        transactions.insert(0, {
            'descricao': body['descricao'],
            'tipo': body['tipo'],
            'valor': body['valor'],
            'realizada_em': str(datetime.datetime.now()),
        })

        conn.execute(text("UPDATE clients SET balance=:balance, transactions=:transactions WHERE id=:id"), {
                     'balance': new_balance, 'id': event['pathParameters']['id'], 'transactions': json.dumps(transactions)})

        conn.commit()
    return {
        "statusCode": 200,
        "body": json.dumps({
            "limite": limite_cliente,
            "saldo": new_balance
        })
    }
