from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import datetime
from psycopg_pool import ConnectionPool

pool = ConnectionPool(
    f"host={'db'} port={'5432'} dbname={'dev'} user={'dev'} password={'dev'}",
    min_size=14,
    max_size=50,
)
pool.wait()


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

            with pool.connection() as conn:
                result = conn.execute(
                    f"SELECT transfer_limit, balance FROM clients WHERE id = {id}"
                ).fetchone()

                print(result)

                limite_cliente = result[0]
                saldo_cliente = result[1]
                ultimas_transacoes = []

                transactions = conn.execute(
                    f"SELECT valor, tipo, descricao, realizada_em FROM transactions WHERE client_id = {id} ORDER BY realizada_em DESC LIMIT 10"
                ).fetchall()

                for transaction in transactions:
                    ultimas_transacoes.append({
                        "valor": transaction[0],
                        "tipo": transaction[1],
                        "descricao": transaction[2],
                        "realizada_em": transaction[3].isoformat().replace("+00:00", "Z"),
                    })

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            response = {
                "saldo": {
                    "data_extrato": str(datetime.datetime.now()),
                    "total": saldo_cliente,
                    "limite": limite_cliente
                },
                "ultimas_transacoes": ultimas_transacoes
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
                self.send_response(422)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                return

            for field in required_fields:
                if field not in parsed_body:
                    self.send_response(422)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    break

            if parsed_body['valor'] <= 0 or not type(parsed_body['valor']) is int or not type(parsed_body['descricao']) is str or len(parsed_body['descricao']) <= 0 or len(parsed_body['descricao']) > 10 or parsed_body['tipo'] not in ["c", "d"]:
                self.send_response(422)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                return

            limite_cliente = 0
            saldo_cliente = 0

            with pool.connection() as conn:
                conn.execute('BEGIN')
                result = conn.execute(
                    f"SELECT transfer_limit, balance FROM clients WHERE id = {id} FOR UPDATE"
                ).fetchone()

                limite_cliente = result[0]
                saldo_cliente = result[1]

                if parsed_body['tipo'] == 'd':
                    valor = parsed_body['valor']
                    if (saldo_cliente - valor < -limite_cliente):
                        conn.execute('ROLLBACK')
                        self.send_response(422)
                        self.send_header(
                            'Content-type', 'application/json')
                        self.end_headers()
                        return

                new_balance = 0

                if (parsed_body['tipo'] == 'c'):
                    new_balance = saldo_cliente + parsed_body['valor']
                else:
                    new_balance = saldo_cliente - parsed_body['valor']

                # 1 2 3

                    # 12 3 4

                conn.execute(
                    "INSERT INTO transactions(client_id, valor, tipo, descricao, realizada_em) VALUES (%s, %s, %s, %s, %s)", (id, parsed_body['valor'], parsed_body['tipo'], parsed_body['descricao'], str(datetime.datetime.now())))

                conn.execute("UPDATE clients SET balance=%s WHERE id=%s",
                             (new_balance, id))

                conn.execute('COMMIT')

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    "limite": limite_cliente,
                    "saldo": new_balance
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))


if __name__ == '__main__':
    host = '0.0.0.0'
    port = 3000

    server = HTTPServer((host, port), handler)
    print(f'Servidor rodando em http://{host}:{port}')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()
    print('Servidor encerrado')
