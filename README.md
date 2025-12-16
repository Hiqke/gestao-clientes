# 🚀 Sistema de Gestão de Clientes (Flask + PostgreSQL)

Sistema profissional para gestão e monitorização de clientes, com níveis de acesso diferenciados e validação documental rigorosa.

## 🛠️ Funcionalidades
- **Login e Segurança**: Sistema de autenticação completo.
- **Níveis de Acesso**: 
  - `ADM`: Visão total e gestão de registos.
  - `Cliente`: Cadastro individual e privacidade.
- **Validação Real**: Impede o cadastro de CPF/CNPJ inválidos (biblioteca `validate-docbr`).
- **Persistência**: Integração total com base de dados PostgreSQL.

## 📋 Pré-requisitos
Para rodar o código fonte, instale as dependências:
```bash
pip install -r requirements.txt