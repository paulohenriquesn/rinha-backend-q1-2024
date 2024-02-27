import json


def handler(event, context):
    # {
    # "valor": 1000,
    # "tipo" : "c",
    # "descricao" : "descricao"
    # }

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

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "ok"
        })
    }
