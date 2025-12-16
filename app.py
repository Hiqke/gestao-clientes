from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from validate_docbr import CPF, CNPJ

app = Flask(__name__)
app.config['SECRET_KEY'] = 'projeto-cliente-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost:5432/meu_projeto'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(10), default='cliente')

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    documento = db.Column(db.String(20), nullable=False)
    endereco = db.Column(db.String(200))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    cadastrado_por = db.Column(db.String(14))

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route('/')
def inicial():
    return render_template('index_inicial.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf_login = request.form.get('cpf').replace('.', '').replace('-', '')
        senha = request.form.get('senha')

        user = Usuario.query.filter_by(cpf=cpf_login).first()

        if user:
            if user.senha.startswith('$2b$'):
                if bcrypt.check_password_hash(user.senha, senha):
                    login_user(user)
                    return redirect(url_for('dashboard'))
            else:
                if user.senha == senha:
                    user.senha = bcrypt.generate_password_hash(senha).decode('utf-8')
                    db.session.commit()
                    login_user(user)
                    return redirect(url_for('dashboard'))

            flash('CPF ou senha inválidos.', 'error')

    return render_template('login.html')


@app.route('/registrar_conta', methods=['GET', 'POST'])
def registrar_conta():
    if request.method == 'POST':
        cpf_raw = request.form.get('cpf').replace('.', '').replace('-', '')

        if not CPF().validate(cpf_raw):
            flash('CPF inválido!')
            return redirect(url_for('registrar_conta'))

        if Usuario.query.filter_by(cpf=cpf_raw).first():
            flash('Este CPF já possui cadastro.')
            return redirect(url_for('registrar_conta'))

        senha_hash = bcrypt.generate_password_hash(
            request.form.get('senha')
        ).decode('utf-8')

        novo_user = Usuario(
            cpf=cpf_raw,
            senha=senha_hash,
            tipo=request.form.get('tipo', 'cliente')
        )

        db.session.add(novo_user)
        db.session.commit()

        flash('Conta criada com sucesso!')
        return redirect(url_for('login'))

    return render_template('registrar_conta.html')

@app.route('/esqueci_senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'POST':
        doc = request.form.get('documento').replace('.', '').replace('-', '').replace('/', '')
        nova_senha = request.form.get('nova_senha')

        user = Usuario.query.filter_by(cpf=doc).first()

        if user:
            user.senha = bcrypt.generate_password_hash(nova_senha).decode('utf-8')
            db.session.commit()
            flash('Senha alterada com sucesso!')
            return redirect(url_for('login'))

        flash('Documento não encontrado.')

    return render_template('esqueci_senha.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.tipo == 'adm':
        clientes = Cliente.query.all()
    else:
        clientes = Cliente.query.filter_by(cadastrado_por=current_user.cpf).all()

    return render_template('index.html', clientes=clientes)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('inicial'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not Usuario.query.filter_by(cpf='111').first():
            admin = Usuario(
                cpf='111',
                senha=bcrypt.generate_password_hash('111').decode('utf-8'),
                tipo='adm'
            )
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True)
