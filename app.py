from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, login_required,
    logout_user, current_user
)
from flask_bcrypt import Bcrypt
from validate_docbr import CPF, CNPJ
from sqlalchemy import or_

# ===================== CONFIG =====================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'projeto-cliente-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost:5432/meu_projeto'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# ===================== MODELOS =====================

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(10), default='cliente')

class Cliente(db.Model):
    __tablename__ = "clientes"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150))
    documento = db.Column(db.String(50))
    rua = db.Column(db.String(255))  # <--- importante
    numero = db.Column(db.String(50))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    cep = db.Column(db.String(20))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    cadastrado_por = db.Column(db.String(20))



# ===================== LOGIN MANAGER =====================

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ===================== ROTAS =====================

@app.route('/')
def inicial():
    return render_template('index_inicial.html')

# ---------- REGISTRO ----------
from validate_docbr import CPF, CNPJ

# ---------- CADASTRAR CLIENTE ----------
@app.route('/cadastrar_cliente', methods=['GET', 'POST'])
@login_required
def cadastrar_cliente():
    if request.method == 'POST':

        # 🔎 trata CPF / CNPJ
        doc_raw = request.form['documento']
        doc = doc_raw.replace('.', '').replace('-', '').replace('/', '')

        cpf = CPF()
        cnpj = CNPJ()

        # ❌ valida documento
        if not (cpf.validate(doc) or cnpj.validate(doc)):
            flash('CPF ou CNPJ inválido!', 'danger')
            return redirect(url_for('cadastrar_cliente'))

        # ✅ cria cliente
        novo = Cliente(
            nome=request.form['nome'],
            documento=doc,  # salva tratado
            rua=request.form['rua'],
            numero=request.form['numero'],
            bairro=request.form['bairro'],
            cidade=request.form['cidade'],
            estado=request.form['estado'],
            cep=request.form['cep'],
            telefone=request.form['telefone'],
            email=request.form['email'],
            cadastrado_por=current_user.cpf
        )

        db.session.add(novo)
        db.session.commit()

        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('cadastrar_cliente.html')

# ---------- EXCLUIR CLIENTE ----------
@app.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_cliente(id):
    cliente = Cliente.query.get_or_404(id)

    # 🔒 segurança
    if current_user.tipo != 'adm' and cliente.cadastrado_por != current_user.cpf:
        flash('Ação não permitida.', 'danger')
        return redirect(url_for('dashboard'))

    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente excluído com sucesso.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/registrar_conta', methods=['GET', 'POST'])
def registrar_conta():
    if request.method == 'POST':
        cpf_raw = request.form.get('cpf', '').replace('.', '').replace('-', '')
        senha = request.form.get('senha')
        confirmar_senha = request.form.get('confirmar_senha')

        # 🔐 valida senha igual
        if senha != confirmar_senha:
            flash('As senhas não coincidem.', 'danger')
            return redirect(url_for('registrar_conta'))

        # 🧾 valida CPF
        if not CPF().validate(cpf_raw):
            flash('CPF inválido!', 'danger')
            return redirect(url_for('registrar_conta'))

        # 🔍 verifica se já existe
        if Usuario.query.filter_by(cpf=cpf_raw).first():
            flash('Este CPF já possui cadastro.', 'warning')
            return redirect(url_for('registrar_conta'))

        # 🔐 hash da senha
        senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')

        novo_user = Usuario(
            cpf=cpf_raw,
            senha=senha_hash,
            tipo='cliente'
        )

        db.session.add(novo_user)
        db.session.commit()

        flash('Conta criada com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))

    return render_template('registrar_conta.html')

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf_login = request.form.get('cpf', '').replace('.', '').replace('-', '')
        senha = request.form.get('senha')

        user = Usuario.query.filter_by(cpf=cpf_login).first()

        if user and bcrypt.check_password_hash(user.senha, senha):
            login_user(user)

            # 🔁 redireciona por tipo
            if user.tipo == 'adm':
                return redirect(url_for('dashboard'))

            return redirect(url_for('perfil'))

        flash('CPF ou senha incorretos.', 'danger')

    return render_template('login.html')

@app.route('/esqueci_senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'POST':
        documento = request.form.get('documento', '').replace('.', '').replace('-', '')
        nova_senha = request.form.get('nova_senha')

        # valida CPF
        if not CPF().validate(documento):
            flash('CPF inválido.', 'danger')
            return redirect(url_for('esqueci_senha'))

        usuario = Usuario.query.filter_by(cpf=documento).first()

        if not usuario:
            flash('Usuário não encontrado.', 'danger')
            return redirect(url_for('esqueci_senha'))

        # gera novo hash
        usuario.senha = bcrypt.generate_password_hash(nova_senha).decode('utf-8')
        db.session.commit()

        flash('Senha alterada com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))

    return render_template('esqueci_senha.html')


# ---------- PERFIL ----------
@app.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html')

# ---------- DASHBOARD ----------
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.tipo == 'adm':
        clientes = Cliente.query.all()
    else:
        clientes = Cliente.query.filter_by(
            cadastrado_por=current_user.cpf
        ).all()

    return render_template('index.html', clientes=clientes)

@app.route('/buscar_cliente', methods=['POST'])
@login_required
def buscar_cliente():
    if current_user.tipo != 'adm':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('dashboard'))

    termo_raw = request.form.get('termo', '').strip()

    if not termo_raw:
        flash('Digite algo para buscar.', 'warning')
        return redirect(url_for('dashboard'))

    # 🔧 Limpa para CPF / CNPJ / telefone
    termo_limpo = (
        termo_raw
        .replace('.', '')
        .replace('-', '')
        .replace('/', '')
        .replace('(', '')
        .replace(')', '')
        .replace(' ', '')
    )

    # 🔍 BUSCA FLEXÍVEL
    clientes = Cliente.query.filter(
        (Cliente.nome.ilike(f"%{termo_raw}%")) |
        (Cliente.documento == termo_limpo) |
        (Cliente.telefone.ilike(f"%{termo_limpo}%"))
    ).all()

    if not clientes:
        flash('Nenhum cliente encontrado.', 'warning')

    return render_template('index.html', clientes=clientes)



# ---------- LOGOUT ----------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('inicial'))

# ===================== INIT =====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # 👑 cria admin padrão (apenas se não existir)
        if not Usuario.query.filter_by(cpf='111').first():
            admin = Usuario(
                cpf='111',
                senha=bcrypt.generate_password_hash('111').decode('utf-8'),
                tipo='adm'
            )
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True)
