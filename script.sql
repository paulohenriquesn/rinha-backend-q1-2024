CREATE UNLOGGED TABLE clients (
    id SERIAL PRIMARY KEY,
    transfer_limit INTEGER NOT NULL,
    balance INTEGER NOT NULL,
    transactions jsonb NOT NULL DEFAULT '[]'
);

CREATE UNIQUE INDEX idx_clients_id ON clients USING btree (id);

INSERT INTO clients (transfer_limit, balance)
VALUES
    (100000, 0),
    (80000, 0),
    (1000000, 0),
    (10000000, 0),
    (500000, 0);        