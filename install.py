import os
import subprocess
import sys
from sqlalchemy import create_engine, text

# CONFIGURAÇÕES DO BANCO - ajuste aqui
DB_USER = "postgres"
DB_PASSWORD = "sua_senha_aqui"   # Coloque a senha do postgres
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "meu_projeto"          # Banco que você quer criar
SQL_FILE = "init_db.sql"          # Caminho do seu script SQL

# Função para instalar dependências
def instalar_dependencias():
    print("Instalando dependências...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("Dependências instaladas!")

# Função para criar o banco, se não existir
def criar_banco():
    print(f"Criando banco {DB_NAME} (se não existir)...")
    engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres")
    conn = engine.connect()
    conn.execute(text("commit"))
    # Verifica se o banco já existe
    result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'"))
    if result.fetchone() is None:
        conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
        print(f"Banco {DB_NAME} criado!")
    else:
        print(f"Banco {DB_NAME} já existe, pulando criação.")
    conn.close()


# Função para executar o script SQL
def rodar_sql():
    print(f"Rodando script {SQL_FILE}...")
    engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    conn = engine.connect()
    with open(SQL_FILE, "r", encoding="utf-8") as f:
        sql_commands = f.read()
        conn.execute(text(sql_commands))
    conn.close()
    print("Script SQL executado com sucesso!")

# Função principal
def main():
    instalar_dependencias()
    criar_banco()
    rodar_sql()
    print("Instalação completa! Agora você pode rodar 'python app.py'.")

if __name__ == "__main__":
    main()
