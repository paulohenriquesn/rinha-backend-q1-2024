import json
from db.pg import engine
from sqlalchemy import text
import datetime


def handler(event, context):

    if (int(event['pathParameters']['id']) <= 0 or int(event['pathParameters']['id']) > 5):
        return {
            "statusCode": 404,
            "body": None
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

    return {
        "statusCode": 200,
        "body": json.dumps({
            "saldo": {
                "data_extrato": str(datetime.datetime.now()),
                "total": saldo_cliente,
                "limite": limite_cliente
            },
            "ultimas_transacoes": transactions
        })
    }
