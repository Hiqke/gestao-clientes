from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from validate_docbr import CPF, CNPJ

app = Flask(__name__)
app.config['SECRET_KEY'] = 'projeto-cliente-2025'

# --- CONEXÃO POSTGRESQL ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost:5432/meu_projeto'
db = SQLAlchemy(app)

# --- MODELOS DE DADOS ---
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(10), default='cliente') # 'adm' ou 'cliente'

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    documento = db.Column(db.String(20), nullable=False) # Armazena CPF ou CNPJ
    endereco = db.Column(db.String(200))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    cadastrado_por = db.Column(db.String(14))

# --- CONFIGURAÇÃO DE LOGIN ---
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# --- ROTAS DE ACESSO ---

@app.route('/')
def inicial():
    return render_template('index_inicial.html')

@app.route('/registrar_conta', methods=['GET', 'POST'])
def registrar_conta():
    if request.method == 'POST':
        cpf_raw = request.form.get('cpf').replace(".", "").replace("-", "")
        
        # Valida o CPF antes de criar a conta
        if not CPF().validate(cpf_raw):
            flash('CPF inválido!')
            return redirect(url_for('registrar_conta'))
            
        if Usuario.query.filter_by(cpf=cpf_raw).first():
            flash('Este CPF já possui cadastro.')
            return redirect(url_for('registrar_conta'))
            
        novo_user = Usuario(cpf=cpf_raw, senha=request.form.get('senha'), tipo='cliente')
        db.session.add(novo_user)
        db.session.commit()
        flash('Conta criada com sucesso!')
        return redirect(url_for('login'))
        
    return render_template('registrar_conta.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf_login = request.form.get('cpf').replace(".", "").replace("-", "")
        user = Usuario.query.filter_by(cpf=cpf_login).first()
        if user and user.senha == request.form.get('senha'):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Credenciais inválidas.')
    return render_template('login.html')

# --- PAINEL PRINCIPAL ---

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.tipo == 'adm':
        clientes = Cliente.query.all()
    else:
        clientes = Cliente.query.filter_by(cadastrado_por=current_user.cpf).all()
    return render_template('index.html', clientes=clientes)

@app.route('/cadastrar', methods=['POST'])
@login_required
def cadastrar():
    doc_original = request.form.get('documento')
    doc_limpo = doc_original.replace(".", "").replace("-", "").replace("/", "")
    
    # Valida se é um CPF ou CNPJ real
    if not (CPF().validate(doc_limpo) or CNPJ().validate(doc_limpo)):
        flash('Documento (CPF/CNPJ) inválido!')
        return redirect(url_for('dashboard'))

    novo_cliente = Cliente(
        nome=request.form.get('nome'),
        documento=doc_original,
        endereco=request.form.get('endereco'),
        telefone=request.form.get('telefone'),
        email=request.form.get('email'),
        cadastrado_por=current_user.cpf
    )
    db.session.add(novo_cliente)
    db.session.commit()
    flash('Cliente cadastrado com sucesso!')
    return redirect(url_for('dashboard'))

@app.route('/excluir/<int:id>')
@login_required
def excluir(id):
    if current_user.tipo == 'adm':
        cliente = Cliente.query.get(id)
        if cliente:
            db.session.delete(cliente)
            db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('inicial'))

# --- INICIALIZAÇÃO ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
        # Garante que exista um Administrador padrão
        if not Usuario.query.filter_by(cpf='111').first():
            db.session.add(Usuario(cpf='111', senha='111', tipo='adm'))
            db.session.commit()
    app.run(debug=True)