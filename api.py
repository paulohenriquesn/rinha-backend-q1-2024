from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from sqlalchemy import text
import datetime

from sqlalchemy import create_engine
from sqlalchemy.engine import URL

url = URL.create(
    drivername='postgresql',
    username='dev',
    password='dev',
    host='localhost',
    database='dev'
)

engine = create_engine(url)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path_parts = self.path.split('/')
        if len(path_parts) == 4 and path_parts[1] == 'clientes' and path_parts[3] == 'extrato':
            id = path_parts[2]

            if (int(id) <= 0 or int(id) > 5):
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                return

            limite_cliente = 0
            saldo_cliente = 0
            transactions = []

            with engine.connect() as conn:
                query = conn.execute(
                    text("SELECT transfer_limit, balance, transactions FROM clients WHERE id = :id"), {
                        'id': id}
                )

                for row in query:
                    limite_cliente = row[0]
                    saldo_cliente = row[1]
                    transactions = row[2]

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "saldo": {
                    "data_extrato": str(datetime.datetime.now()),
                    "total": saldo_cliente,
                    "limite": limite_cliente
                },
                "ultimas_transacoes": transactions
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

            return

    def do_POST(self):
        path_parts = self.path.split('/')
        id = path_parts[2]
        if len(path_parts) == 4 and path_parts[1] == 'clientes' and path_parts[3] == 'transacoes':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode('utf-8')
            parsed_body = json.loads(body)
            print(parsed_body)

            if (int(id) <= 0 or int(id) > 5):
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                return

        required_fields = ["valor", "tipo", "descricao"]

        if parsed_body is None:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            return

        for field in required_fields:
            if field not in parsed_body:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                break

        limite_cliente = 0
        saldo_cliente = 0
        transactions = []

        with engine.connect() as conn:
            query = conn.execute(
                text("SELECT transfer_limit, balance, transactions FROM clients WHERE id = :id"), {
                    'id': id}
            )

            for row in query:
                limite_cliente = row[0]
                saldo_cliente = row[1]
                transactions = row[2]

            if parsed_body['tipo'] == 'd':
                valor = parsed_body['valor']
                if (saldo_cliente - valor < -limite_cliente):
                    self.send_response(422)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()

            new_balance = 0

            if (parsed_body['tipo'] == 'c'):
                new_balance = saldo_cliente + parsed_body['valor']
            else:
                new_balance = saldo_cliente - parsed_body['valor']

            if (len(transactions) == 10):
                transactions.pop()

            transactions.insert(0, {
                'descricao': parsed_body['descricao'],
                'tipo': parsed_body['tipo'],
                'valor': parsed_body['valor'],
                'realizada_em': str(datetime.datetime.now()),
            })

            conn.execute(text("UPDATE clients SET balance=:balance, transactions=:transactions WHERE id=:id"), {
                'balance': new_balance, 'id': id, 'transactions': json.dumps(transactions)})

            conn.commit()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "limite": limite_cliente,
                "saldo": new_balance
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))


if __name__ == '__main__':
    host = 'localhost'
    port = 7070

    server = HTTPServer((host, port), handler)
    print(f'Servidor rodando em http://{host}:{port}')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()
    print('Servidor encerrado')
