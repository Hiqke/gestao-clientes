-- init_db.sql
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    documento VARCHAR(20) NOT NULL,
    rua VARCHAR(100),
    numero VARCHAR(20),
    bairro VARCHAR(50),
    cidade VARCHAR(100),
    estado VARCHAR(2),
    cep VARCHAR(20)
);
