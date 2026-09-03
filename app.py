# ================================================================
# 🚀 PROPOSTA EXCLUSIVA 7.0
# SISTEMA PROFISSIONAL PARA AUTÔNOMOS
# ================================================================
#
# ✔ Cadastro de usuário
# ✔ Login / Logout
# ✔ Senha protegida
# ✔ Dados separados por usuário
# ✔ Clientes
# ✔ Propostas
# ✔ Orçamentos
# ✔ Contratos
# ✔ Currículos
# ✔ WhatsApp
# ✔ Recibos
# ✔ Agenda
# ✔ Financeiro
# ✔ Histórico
# ✔ PDFs
# ✔ PostgreSQL / SQLite
# ✔ Render / Gunicorn
# ✔ Interface responsiva para celular
#
# ================================================================

import os
import re
import secrets
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    session,
    render_template_string,
    send_file,
    flash
)

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)


# ================================================================
# CONFIGURAÇÃO
# ================================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    secrets.token_hex(32)
)

database_url = os.environ.get(
    "DATABASE_URL",
    "sqlite:///propostas.db"
)

if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ================================================================
# MODELOS DO BANCO
# ================================================================

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(160),
        unique=True,
        nullable=False,
        index=True
    )

    senha = db.Column(
        db.String(255),
        nullable=False
    )

    criado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False,
        index=True
    )

    nome = db.Column(
        db.String(150),
        nullable=False
    )

    telefone = db.Column(
        db.String(40)
    )

    email = db.Column(
        db.String(160)
    )

    endereco = db.Column(
        db.String(250)
    )

    observacoes = db.Column(
        db.Text
    )

    criado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Servico(db.Model):
    __tablename__ = "servicos"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False,
        index=True
    )

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id"),
        nullable=True
    )

    titulo = db.Column(
        db.String(200),
        nullable=False
    )

    descricao = db.Column(
        db.Text
    )

    data = db.Column(
        db.String(30)
    )

    valor = db.Column(
        db.Float,
        default=0
    )

    status = db.Column(
        db.String(50),
        default="Agendado"
    )

    criado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Movimento(db.Model):
    __tablename__ = "movimentos"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False,
        index=True
    )

    tipo = db.Column(
        db.String(20),
        nullable=False
    )

    descricao = db.Column(
        db.String(250),
        nullable=False
    )

    valor = db.Column(
        db.Float,
        nullable=False
    )

    data = db.Column(
        db.String(30)
    )

    criado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Documento(db.Model):
    __tablename__ = "documentos"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False,
        index=True
    )

    tipo = db.Column(
        db.String(50),
        nullable=False
    )

    cliente = db.Column(
        db.String(150)
    )

    titulo = db.Column(
        db.String(250)
    )

    criado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ================================================================
# CRIAÇÃO DAS TABELAS
# ================================================================

with app.app_context():
    db.create_all()


# ================================================================
# FUNÇÕES AUXILIARES
# ================================================================

def usuario_atual():
    user_id = session.get("usuario_id")

    if not user_id:
        return None

    return db.session.get(
        Usuario,
        user_id
    )


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if not session.get("usuario_id"):
            flash("Faça login para continuar.")
            return redirect(url_for("login"))

        return func(*args, **kwargs)

    return wrapper


def limpar_telefone(numero):
    if not numero:
        return ""

    numero = re.sub(
        r"\D",
        "",
        numero
    )

    if numero.startswith("55"):
        return numero

    return "55" + numero


def dinheiro(valor):
    if valor is None:
        return 0.0

    valor = str(valor).strip()

    if not valor:
        return 0.0

    valor = valor.replace("R$", "")
    valor = valor.replace(" ", "")

    if "," in valor:
        valor = valor.replace(".", "")
        valor = valor.replace(",", ".")

    try:
        return float(valor)
    except:
        return 0.0


def brl(valor):
    try:
        return (
            "R$ "
            + f"{float(valor):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    except:
        return "R$ 0,00"


def escape_pdf(texto):
    if texto is None:
        return ""

    texto = str(texto)

    texto = texto.replace("&", "&amp;")
    texto = texto.replace("<", "&lt;")
    texto = texto.replace(">", "&gt;")

    return texto


def registrar_documento(tipo, cliente="", titulo=""):

    documento = Documento(
        usuario_id=session["usuario_id"],
        tipo=tipo,
        cliente=cliente,
        titulo=titulo
    )

    db.session.add(documento)
    db.session.commit()


def gerar_pdf_base(nome_arquivo, titulo):

    caminho = os.path.join(
        "/tmp",
        nome_arquivo
    )

    doc = SimpleDocTemplate(
        caminho,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    estilos = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        "TituloCustom",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        leading=24,
        spaceAfter=20
    )

    normal = ParagraphStyle(
        "NormalCustom",
        parent=estilos["Normal"],
        fontSize=10,
        leading=15
    )

    return caminho, doc, titulo_style, normal


# ================================================================
# HTML BASE
# ================================================================

STYLE = """
<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #080808;
    color: #f5f5f5;
}

.container {
    width: 94%;
    max-width: 1100px;
    margin: auto;
    padding: 20px 0 50px;
}

.header {
    background: #101010;
    border-bottom: 1px solid #292929;
    padding: 15px;
}

.header-inner {
    max-width: 1100px;
    margin: auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
}

.logo {
    color: #d4af37;
    font-weight: bold;
    font-size: 20px;
}

.user-info {
    font-size: 13px;
    color: #aaa;
}

h1, h2, h3 {
    color: #d4af37;
}

.card {
    background: #111;
    border: 1px solid #292929;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 16px;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 15px;
}

.menu-card {
    background: #111;
    border: 1px solid #292929;
    border-radius: 15px;
    padding: 20px;
    transition: .2s;
}

.menu-card:hover {
    border-color: #d4af37;
    transform: translateY(-2px);
}

.menu-card h3 {
    margin-top: 0;
}

.menu-card p {
    color: #aaa;
    line-height: 1.5;
}

a {
    color: #d4af37;
    text-decoration: none;
}

.btn {
    display: inline-block;
    background: #d4af37;
    color: #080808;
    border: none;
    padding: 12px 16px;
    border-radius: 9px;
    font-weight: bold;
    cursor: pointer;
    text-decoration: none;
    margin: 4px 2px;
}

.btn:hover {
    opacity: .9;
}

.btn-secondary {
    background: #222;
    color: #fff;
    border: 1px solid #444;
}

.btn-danger {
    background: #8b2222;
    color: white;
}

input,
textarea,
select {
    width: 100%;
    padding: 12px;
    margin: 7px 0 14px;
    background: #191919;
    color: white;
    border: 1px solid #383838;
    border-radius: 8px;
}

textarea {
    min-height: 100px;
    resize: vertical;
}

label {
    color: #ccc;
    font-size: 14px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}

th,
td {
    border-bottom: 1px solid #292929;
    padding: 10px;
    text-align: left;
}

th {
    color: #d4af37;
}

.alert {
    padding: 12px;
    border-radius: 8px;
    background: #24200f;
    border: 1px solid #5e5019;
    margin-bottom: 15px;
}

.stat {
    font-size: 28px;
    font-weight: bold;
    color: #d4af37;
}

.center {
    text-align: center;
}

.login-box {
    max-width: 450px;
    margin: 50px auto;
}

.small {
    color: #999;
    font-size: 13px;
}

@media(max-width:600px) {

    .header-inner {
        flex-direction: column;
        align-items: flex-start;
    }

    .container {
        width: 92%;
    }

    table {
        display: block;
        overflow-x: auto;
        white-space: nowrap;
    }

    .btn {
        width: 100%;
        text-align: center;
    }
}

</style>
"""


# ================================================================
# PÁGINA DE LOGIN
# ================================================================

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport"
content="width=device-width, initial-scale=1.0">
<title>Proposta Exclusiva 7.0</title>
""" + STYLE + """
</head>

<body>

<div class="container">

<div class="login-box">

<div class="card center">

<h1>PROPOSTA EXCLUSIVA</h1>

<p class="small">
Sistema profissional para autônomos
</p>

{% with messages = get_flashed_messages() %}
{% for message in messages %}
<div class="alert">{{ message }}</div>
{% endfor %}
{% endwith %}

<form method="POST">

<label>E-mail</label>

<input
type="email"
name="email"
placeholder="seu@email.com"
required
>

<label>Senha</label>

<input
type="password"
name="senha"
placeholder="Sua senha"
required
>

<button class="btn" type="submit">
ENTRAR
</button>

</form>

<hr style="border-color:#292929;margin:25px 0">

<p>
Ainda não possui uma conta?
</p>

<a class="btn btn-secondary"
href="{{ url_for('cadastro') }}">
CRIAR CONTA
</a>

</div>

</div>

</div>

</body>
</html>
"""


# ================================================================
# PÁGINA DE CADASTRO
# ================================================================

CADASTRO_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport"
content="width=device-width, initial-scale=1.0">
<title>Criar conta</title>
""" + STYLE + """
</head>

<body>

<div class="container">

<div class="login-box">

<div class="card">

<h1>Criar conta</h1>

<p class="small">
Comece gratuitamente no Proposta Exclusiva.
</p>

{% with messages = get_flashed_messages() %}
{% for message in messages %}
<div class="alert">{{ message }}</div>
{% endfor %}
{% endwith %}

<form method="POST">

<label>Nome</label>

<input
type="text"
name="nome"
placeholder="Seu nome"
required
>

<label>E-mail</label>

<input
type="email"
name="email"
placeholder="seu@email.com"
required
>

<label>Senha</label>

<input
type="password"
name="senha"
placeholder="Mínimo 6 caracteres"
required
>

<label>Confirmar senha</label>

<input
type="password"
name="confirmar"
placeholder="Digite novamente"
required
>

<button class="btn" type="submit">
CRIAR MINHA CONTA
</button>

</form>

<a href="{{ url_for('login') }}">
Já tenho uma conta
</a>

</div>

</div>

</div>

</body>
</html>
"""


# ================================================================
# DASHBOARD
# ================================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Proposta Exclusiva 7.0</title>

""" + STYLE + """

</head>

<body>

<div class="header">

<div class="header-inner">

<div class="logo">
PROPOSTA EXCLUSIVA 7.0
</div>

<div>

<span class="user-info">
Olá, {{ usuario.nome }}
</span>

<a class="btn btn-secondary"
href="{{ url_for('logout') }}">
Sair
</a>

</div>

</div>

</div>


<div class="container">

{% with messages = get_flashed_messages() %}
{% for message in messages %}
<div class="alert">{{ message }}</div>
{% endfor %}
{% endwith %}


<h1>Painel</h1>

<p>
Gerencie seu trabalho em um só lugar.
</p>


<div class="grid">

<div class="card">
<div class="small">Clientes</div>
<div class="stat">{{ total_clientes }}</div>
</div>

<div class="card">
<div class="small">Serviços</div>
<div class="stat">{{ total_servicos }}</div>
</div>

<div class="card">
<div class="small">Documentos</div>
<div class="stat">{{ total_documentos }}</div>
</div>

<div class="card">
<div class="small">Saldo</div>
<div class="stat">{{ saldo }}</div>
</div>

</div>


<h2>Ferramentas</h2>

<div class="grid">

<div class="menu-card">
<h3>👥 Clientes</h3>
<p>Cadastre e organize seus clientes.</p>
<a class="btn"
href="{{ url_for('clientes') }}">
Abrir
</a>
</div>


<div class="menu-card">
<h3>📄 Proposta</h3>
<p>Crie uma proposta profissional em PDF.</p>
<a class="btn"
href="{{ url_for('proposta') }}">
Criar
</a>
</div>


<div class="menu-card">
<h3>🧾 Orçamento</h3>
<p>Monte orçamentos com materiais e serviços.</p>
<a class="btn"
href="{{ url_for('orcamento') }}">
Criar
</a>
</div>


<div class="menu-card">
<h3>📝 Contrato</h3>
<p>Gere um modelo de contrato.</p>
<a class="btn"
href="{{ url_for('contrato') }}">
Criar
</a>
</div>


<div class="menu-card">
<h3>💼 Currículo</h3>
<p>Crie um currículo profissional.</p>
<a class="btn"
href="{{ url_for('curriculo') }}">
Criar
</a>
</div>


<div class="menu-card">
<h3>📱 WhatsApp</h3>
<p>Gere mensagens profissionais.</p>
<a class="btn"
href="{{ url_for('whatsapp') }}">
Abrir
</a>
</div>


<div class="menu-card">
<h3>🧾 Recibo</h3>
<p>Gere recibos em PDF.</p>
<a class="btn"
href="{{ url_for('recibo') }}">
Criar
</a>
</div>


<div class="menu-card">
<h3>📅 Agenda</h3>
<p>Organize seus serviços.</p>
<a class="btn"
href="{{ url_for('agenda') }}">
Abrir
</a>
</div>


<div class="menu-card">
<h3>💰 Financeiro</h3>
<p>Controle entradas e saídas.</p>
<a class="btn"
href="{{ url_for('financeiro') }}">
Abrir
</a>
</div>


<div class="menu-card">
<h3>📊 Histórico</h3>
<p>Veja os documentos criados.</p>
<a class="btn"
href="{{ url_for('historico') }}">
Abrir
</a>
</div>

</div>

</div>

</body>
</html>
"""


# ================================================================
# LOGIN
# ================================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if session.get("usuario_id"):
        return redirect(url_for("home"))

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        senha = request.form.get(
            "senha",
            ""
        )

        usuario = Usuario.query.filter_by(
            email=email
        ).first()

        if not usuario or not check_password_hash(
            usuario.senha,
            senha
        ):
            flash("E-mail ou senha incorretos.")
            return redirect(url_for("login"))

        session.clear()

        session["usuario_id"] = usuario.id

        return redirect(url_for("home"))

    return render_template_string(
        LOGIN_HTML
    )


# ================================================================
# CADASTRO
# ================================================================

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if session.get("usuario_id"):
        return redirect(url_for("home"))

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        senha = request.form.get(
            "senha",
            ""
        )

        confirmar = request.form.get(
            "confirmar",
            ""
        )

        if not nome or not email or not senha:
            flash("Preencha todos os campos.")
            return redirect(url_for("cadastro"))

        if len(senha) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.")
            return redirect(url_for("cadastro"))

        if senha != confirmar:
            flash("As senhas não são iguais.")
            return redirect(url_for("cadastro"))

        existente = Usuario.query.filter_by(
            email=email
        ).first()

        if existente:
            flash("Este e-mail já está cadastrado.")
            return redirect(url_for("login"))

        usuario = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha)
        )

        db.session.add(usuario)
        db.session.commit()

        session.clear()

        session["usuario_id"] = usuario.id

        flash("Conta criada com sucesso!")

        return redirect(url_for("home"))

    return render_template_string(
        CADASTRO_HTML
    )


# ================================================================
# LOGOUT
# ================================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ================================================================
# HOME
# ================================================================

@app.route("/")
def home():

    if not session.get("usuario_id"):
        return redirect(url_for("login"))

    usuario = usuario_atual()

    clientes = Cliente.query.filter_by(
        usuario_id=usuario.id
    ).count()

    servicos = Servico.query.filter_by(
        usuario_id=usuario.id
    ).count()

    documentos = Documento.query.filter_by(
        usuario_id=usuario.id
    ).count()

    entradas = db.session.query(
        db.func.sum(Movimento.valor)
    ).filter(
        Movimento.usuario_id == usuario.id,
        Movimento.tipo == "entrada"
    ).scalar() or 0

    saidas = db.session.query(
        db.func.sum(Movimento.valor)
    ).filter(
        Movimento.usuario_id == usuario.id,
        Movimento.tipo == "saida"
    ).scalar() or 0

    saldo = brl(
        float(entradas) - float(saidas)
    )

    return render_template_string(
        DASHBOARD_HTML,
        usuario=usuario,
        total_clientes=clientes,
        total_servicos=servicos,
        total_documentos=documentos,
        saldo=saldo
    )


# ================================================================
# CLIENTES
# ================================================================

@app.route("/clientes")
@login_required
def clientes():

    lista = Cliente.query.filter_by(
        usuario_id=session["usuario_id"]
    ).order_by(
        Cliente.id.desc()
    ).all()

    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport"
    content="width=device-width, initial-scale=1.0">
    <title>Clientes</title>
    """ + STYLE + """
    </head>

    <body>

    <div class="container">

    <a href="/">← Painel</a>

    <h1>👥 Clientes</h1>

    <div class="card">

    <h2>Novo cliente</h2>

    <form method="POST"
    action="/cliente/adicionar">

    <label>Nome</label>
    <input name="nome" required>

    <label>Telefone</label>
    <input name="telefone">

    <label>E-mail</label>
    <input type="email" name="email">

    <label>Endereço</label>
    <input name="endereco">

    <label>Observações</label>
    <textarea name="observacoes"></textarea>

    <button class="btn">
    SALVAR CLIENTE
    </button>

    </form>

    </div>


    <div class="card">

    <h2>Meus clientes</h2>

    {% if lista %}

    <table>

    <tr>
    <th>Nome</th>
    <th>Telefone</th>
    <th>Ações</th>
    </tr>

    {% for cliente in lista %}

    <tr>

    <td>{{ cliente.nome }}</td>

    <td>{{ cliente.telefone or "-" }}</td>

    <td>

    <a class="btn btn-danger"
    href="/cliente/excluir/{{ cliente.id }}"
    onclick="return confirm('Excluir cliente?')">
    Excluir
    </a>

    </td>

    </tr>

    {% endfor %}

    </table>

    {% else %}

    <p>Nenhum cliente cadastrado.</p>

    {% endif %}

    </div>

    </div>

    </body>
    </html>
    """

    return render_template_string(
        html,
        lista=lista
    )


@app.route(
    "/cliente/adicionar",
    methods=["POST"]
)
@login_required
def adicionar_cliente():

    cliente = Cliente(
        usuario_id=session["usuario_id"],
        nome=request.form.get(
            "nome",
            ""
        ).strip(),
        telefone=request.form.get(
            "telefone",
            ""
        ).strip(),
        email=request.form.get(
            "email",
            ""
        ).strip(),
        endereco=request.form.get(
            "endereco",
            ""
        ).strip(),
        observacoes=request.form.get(
            "observacoes",
            ""
        ).strip()
    )

    if not cliente.nome:
        flash("Informe o nome do cliente.")
        return redirect(url_for("clientes"))

    db.session.add(cliente)
    db.session.commit()

    flash("Cliente cadastrado!")

    return redirect(
        url_for("clientes")
    )


@app.route(
    "/cliente/excluir/<int:id>"
)
@login_required
def excluir_cliente(id):

    cliente = Cliente.query.filter_by(
        id=id,
        usuario_id=session["usuario_id"]
    ).first()

    if cliente:

        db.session.delete(cliente)

        db.session.commit()

        flash("Cliente excluído.")

    return redirect(
        url_for("clientes")
    )


# ================================================================
# PROPOSTA
# ================================================================

@app.route("/proposta", methods=["GET", "POST"])
@login_required
def proposta():

    clientes = Cliente.query.filter_by(
        usuario_id=session["usuario_id"]
    ).all()

    if request.method == "POST":

        usuario = usuario_atual()

        cliente_nome = request.form.get(
            "cliente",
            ""
        )

        servico = request.form.get(
            "servico",
            ""
        )

        descricao = request.form.get(
            "descricao",
            ""
        )

        valor = dinheiro(
            request.form.get("valor")
        )

        validade = request.form.get(
            "validade",
            ""
        )

        caminho, doc, titulo_style, normal = gerar_pdf_base(
            "proposta.pdf",
            "Proposta Comercial"
        )

        elementos = []

        elementos.append(
            Paragraph(
                "PROPOSTA COMERCIAL",
                titulo_style
            )
        )

        elementos.append(
            Paragraph(
                f"<b>Profissional:</b> {escape_pdf(usuario.nome)}",
                normal
            )
        )

        elementos.append(
            Paragraph(
                f"<b>Cliente:</b> {escape_pdf(cliente_nome)}",
                normal
            )
        )

        elementos.append(Spacer(1, 12))

        elementos.append(
            Paragraph(
                f"<b>Serviço:</b> {escape_pdf(servico)}",
                normal
            )
        )

        elementos.append(
            Paragraph(
                f"<b>Descrição:</b> {escape_pdf(descricao)}",
                normal
            )
        )

        elementos.append(Spacer(1, 12))

        tabela = Table([
            ["Valor", "Validade"],
            [brl(valor), validade or "A combinar"]
        ], colWidths=[8 * cm, 8 * cm])

        tabela.setStyle(
            TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#222222")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#D4AF37")),
                ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
                ("PADDING", (0,0), (-1,-1), 8)
            ])
        )

        elementos.append(tabela)

        elementos.append(Spacer(1, 20))

        elementos.append(
            Paragraph(
                "Obrigado pela oportunidade. "
                "Fico à disposição para esclarecer qualquer dúvida.",
                normal
            )
        )

        doc.build(elementos)

        registrar_documento(
            "Proposta",
            cliente_nome,
            servico
        )

        return send_file(
            caminho,
            as_attachment=True,
            download_name="proposta.pdf"
        )

    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport"
    content="width=device-width, initial-scale=1.0">
    <title>Proposta</title>
    """ + STYLE + """
    </head>

    <body>

    <div class="container">

    <a href="/">← Painel</a>

    <h1>📄 Criar proposta</h1>

    <div class="card">

    <form method="POST">

    <label>Cliente</label>

    <select name="cliente">

    <option value="">
Digite o nome abaixo ou escolha um cliente
    </option>

    {% for cliente in clientes %}

    <option value="{{ cliente.nome }}">
    {{ cliente.nome }}
    </option>

    {% endfor %}

    </select>

    <input
    name="cliente"
    placeholder="Nome do cliente"
    >

    <label>Serviço</label>

    <input
    name="servico"
    placeholder="Ex: Pintura residencial"
    required
    >

    <label>Descrição</label>

    <textarea
    name="descricao"
    placeholder="Descreva o serviço..."
    ></textarea>

    <label>Valor</label>

    <input
    name="valor"
    placeholder="Ex: 1500,00"
    >

    <label>Validade da proposta</label>

    <input
    name="validade"
    placeholder="Ex: 7 dias"
    >

    <button class="btn">
    GERAR PDF
    </button>

    </form>

    </div>

    </div>

    </body>
    </html>
    """

    return render_template_string(
        html,
        clientes=clientes
    )


# ================================================================
# ORÇAMENTO
# ================================================================

@app.route("/orcamento", methods=["GET", "POST"])
@login_required
def orcamento():

    if request.method == "POST":

        usuario = usuario_atual()

        cliente = request.form.get(
            "cliente",
            ""
        )

        linhas = request.form.get(
            "materiais",
            ""
        )

        observacoes = request.form.get(
            "observacoes",
            ""
        )

        total = 0

        tabela_dados = [
            ["Item", "Qtd.", "Unitário", "Total"]
        ]

        for linha in linhas.splitlines():

            partes = [
                x.strip()
                for x in linha.split("|")
            ]

            if len(partes) != 3:
                continue

            descricao = partes[0]

            try:
                quantidade = float(
                    partes[1].replace(",", ".")
                )
            except:
                quantidade = 0

            preco = dinheiro(
                partes[2]
            )

            subtotal = quantidade * preco

            total += subtotal

            tabela_dados.append([
                descricao,
                str(quantidade),
                brl(preco),
                brl(subtotal)
            ])

        caminho, doc, titulo_style, normal = gerar_pdf_base(
            "orcamento.pdf",
            "Orçamento"
        )

        elementos = []

        elementos.append(
            Paragraph(
                "ORÇAMENTO",
                titulo_style
            )
        )

        elementos.append(
            Paragraph(
                f"<b>Profissional:</b> {escape_pdf(usuario.nome)}",
                normal
            )
        )

        elementos.append(
            Paragraph(
                f"<b>Cliente:</b> {escape_pdf(cliente)}",
                normal
            )
        )

        elementos.append(Spacer(1, 15))

        tabela = Table(
            tabela_dados,
            colWidths=[
                7 * cm,
                2 * cm,
                3.5 * cm,
                3.5 * cm
            ]
        )

        tabela.setStyle(
            TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#222222")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#D4AF37")),
                ("GRID", (0,0), (-1,-1), .5, colors.grey),
                ("PADDING", (0,0), (-1,-1), 6)
            ])
        )

        elementos.append(tabela)

        elementos.append(Spacer(1, 15))

        elementos.append(
            Paragraph(
                f"<b>TOTAL: {brl(total)}</b>",
                normal
            )
        )

        elementos.append(
            Paragraph(
                escape_pdf(observacoes),
                normal
            )
        )

        doc.build(elementos)

        registrar_documento(
            "Orçamento",
            cliente,
            f"Orçamento - {brl(total)}"
        )

        return send_file(
            caminho,
            as_attachment=True,
            download_name="orcamento.pdf"
        )

    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport"
    content="width=device-width, initial-scale=1.0">
    <title>Orçamento</title>
    """ + STYLE + """
    </head>

    <body>

    <div class="container">

    <a href="/">← Painel</a>

    <h1>🧾 Criar orçamento</h1>

    <div class="card">

    <form method="POST">

    <label>Cliente</label>

    <input
    name="cliente"
    placeholder="Nome do cliente"
    required
    >

    <label>Materiais / serviços</label>

    <p class="small">
    Use uma linha para cada item:<br>
    Cimento | 10 | 35,00<br>
    Tinta | 5 | 80,00
    </p>

    <textarea
    name="materiais"
    placeholder="Cimento | 10 | 35,00
Tinta | 5 | 80,00"
    required
    ></textarea>

    <label>Observações</label>

    <textarea
    name="observacoes"
    ></textarea>

    <button class="btn">
    GERAR ORÇAMENTO PDF
    </button>

    </form>

    </div>

    </div>

    </body>
    </html>
    """

    return render_template_string(
        html
    )


# ================================================================
# CONTRATO
# ================================================================

@app.route("/contrato", methods=["GET", "POST"])
@login_required
def contrato():

    if request.method == "POST":

        usuario = usuario_atual()

        cliente = request.form.get(
            "cliente",
            ""
        )

        servico = request.form.get(
            "servico",
            ""
        )

        valor = dinheiro(
            request.form.get("valor")
        )

        prazo = request.form.get(
            "prazo",
            ""
        )

        forma_pagamento = request.form.get(
            "pagamento",
            ""
        )

        caminho, doc, titulo_style, normal = gerar_pdf_base(
            "contrato.pdf",
            "Contrato"
        )

        elementos = []

        elementos.append(
            Paragraph(
                "CONTRATO DE PRESTAÇÃO DE SERVIÇOS",
                titulo_style
            )
        )

        texto = f"""
        <b>CONTRATANTE:</b> {escape_pdf(cliente)}<br/><br/>

        <b>CONTRATADO:</b> {escape_pdf(usuario.nome)}<br/><br/>

        <b>SERVIÇO:</b> {escape_pdf(servico)}<br/><br/>

        <b>VALOR:</b> {brl(valor)}<br/><br/>

        <b>PRAZO:</b> {escape_pdf(prazo)}<br/><br/>

        <b>FORMA DE PAGAMENTO:</b>
        {escape_pdf(forma_pagamento)}<br/><br/>

        As partes concordam com a prestação do serviço
        descrito acima, observando as condições acordadas.
        """

        elementos.append(
            Paragraph(
                texto,
                normal
            )
        )

        elementos.append(Spacer(1, 20))

        elementos.append(
            Paragraph(
                "Este é um modelo geral e não substitui "
                "orientação jurídica profissional.",
                normal
            )
        )

        elementos.append(Spacer(1, 50))

        elementos.append(
            Paragraph(
                "__________________________________<br/>"
                + escape_pdf(usuario.nome),
                normal
            )
        )

        elementos.append(Spacer(1, 30))

        elementos.append(
            Paragraph(
                "__________________________________<br/>"
                + escape_pdf(cliente),
                normal
            )
        )

        doc.build(elementos)

        registrar_documento(
            "Contrato",
            cliente,
            servico
        )

        return send_file(
            caminho,
            as_attachment=True,
            download_name="contrato.pdf"
        )

    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport"
    content="width=device-width, initial-scale=1.0">
    <title>Contrato</title>
    """ + STYLE + """
    </head>

    <body>

    <div class="container">

    <a href="/">← Painel</a>

    <h1>📝 Contrato</h1>

    <div class="card">

    <form method="POST">

    <label>Cliente</label>
    <input name="cliente" required>

    <label>Serviço</label>
    <textarea name="servico" required></textarea>

    <label>Valor</label>
    <input name="valor" placeholder="Ex: 1500,00">

    <label>Prazo</label>
    <input name="prazo" placeholder="Ex: 15 dias">

    <label>Forma de pagamento</label>
    <input
    name="pagamento"
    placeholder="Ex: 50% entrada e 50% conclusão"
    >

    <button class="btn">
    GERAR CONTRATO PDF
    </button>

    </form>

    </div>

    </div>

    </body>
    </html>
    """

    return render_template_string(
        html
    )


# ================================================================
# CURRÍCULO
# ================================================================

@app.route("/curriculo", methods=["GET", "POST"])
@login_required
def curriculo():

    if request.method == "POST":

        usuario = usuario_atual()

        nome = request.form.get(
            "nome",
            usuario.nome
        )

        profissao = request.form.get(
            "profissao",
            ""
        )

        telefone = request.form.get(
            "telefone",
            ""
        )

        email = request.form.get(
            "email",
            usuario.email
        )

        experiencia = request.form.get(
            "experiencia",
            ""
        )

        habilidades = request.form.get(
            "habilidades",
            ""
        )

        formacao = request.form.get(
            "formacao",
            ""
        )

        objetivo = request.form.get(
            "objetivo",
            ""
        )

        caminho, doc, titulo_style, normal = gerar_pdf_base(
            "curriculo.pdf",
            "Currículo"
        )

        elementos = []

        elementos.append(
            Paragraph(
                escape_pdf(nome),
                titulo_style
            )
        )

        elementos.append(
            Paragraph(
                f"<b>{escape_pdf(profissao)}</b>",
                normal
            )
        )

        elementos.append(
            Paragraph(
                f"Telefone: {escape_pdf(telefone)}<br/>"
                f"E-mail: {escape_pdf(email)}",
                normal
            )
        )

        elementos.append(Spacer(1, 18))

        secoes = [
            ("OBJETIVO PROFISSIONAL", objetivo),
            ("EXPERIÊNCIA", experiencia),
            ("FORMAÇÃO", formacao),
            ("HABILIDADES", habilidades)
        ]

        for titulo, texto in secoes:

            elementos.append(
                Paragraph(
                    f"<b>{titulo}</b>",
                    normal
                )
            )

            elementos.append(
                Paragraph(
                    escape_pdf(texto),
                    normal
                )
            )

            elementos.append(
                Spacer(1, 12)
            )

        doc.build(elementos)

        registrar_documento(
            "Currículo",
            "",
            nome
        )

        return send_file(
            caminho,
            as_attachment=True,
            download_name="curriculo.pdf"
        )

    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport"
    content="width=device-width, initial-scale=1.0">
    <title>Currículo</title>
    """ + STYLE + """
    </head>

    <body>

    <div class="container">

    <a href="/">← Painel</a>

    <h1>💼 Currículo</h1>

    <div class="card">

    <form method="POST">

    <label>Nome</label>
    <input name="nome" value="{{ usuario.nome }}" required>

    <label>Profissão</label>
    <input name="profissao">

    <label>Telefone</label>
    <input name="telefone">

    <label>E-mail</label>
    <input name="email" value="{{ usuario.email }}">

    <label>Objetivo profissional</label>
    <textarea name="objetivo"></textarea>

    <label>Experiência</label>
    <textarea name="experiencia"></textarea>

    <label>Formação</label>
    <textarea name="formacao"></textarea>

    <label>Habilidades</label>
    <textarea name="habilidades"></textarea>

    <button class="btn">
    GERAR CURRÍCULO PDF
    </button>

    </form>

    </div>

    </div>

    </body>
    </html>
    """

    return render_template_string(
        html,
        usuario=usuario_atual()
    )


# ================================================================
# WHATSAPP
# ================================================================

@app.route("/whatsapp", methods=["GET", "POST"])
@login_required
def whatsapp():

    link = None

    if request.method == "POST":

        telefone = limpar_telefone(
            request.form.get(
                "telefone",
                ""
            )
        )

        tipo = request.form.get(
            "tipo",
            ""
        )

        cliente = request.form.get(
            "cliente",
            "cliente"
        )

        servico = request.form.get(
            "servico",
            ""
        )

        valor = request.form.get(
            "valor",
            ""
        )

        mensagens = {

            "Primeiro contato":
            f"Olá, {cliente}! Tudo bem? "
            "Meu nome é "
            + usuario_atual().nome
            + ". Entrei em contato para apresentar "
              "meus serviços. Posso enviar mais informações?",

            "Envio de proposta":
            f"Olá, {cliente}! Conforme conversamos, "
            f"preparei a proposta para o serviço de "
            f"{servico}. O valor é {valor}. "
            "Fico à disposição para qualquer dúvida.",

            "Envio de orçamento":
            f"Olá, {cliente}! Segue o orçamento referente "
            f"ao serviço de {servico}. "
            f"Valor: {valor}. "
            "Qualquer dúvida estou à disposição.",

            "Confirmação de serviço":
            f"Olá, {cliente}! Confirmando nosso serviço "
            f"de {servico}. "
            "Obrigado pela confiança!",

            "Lembrete de pagamento":
            f"Olá, {cliente}! Tudo bem? "
            "Passando para lembrar sobre o pagamento "
            f"referente ao serviço de {servico}. "
            f"Valor: {valor}. Obrigado!",

            "Confirmação de agendamento":
            f"Olá, {cliente}! Seu serviço de {servico} "
            "está confirmado. "
            "Qualquer alteração, por favor me avise.",

            "Pós-venda":
            f"Olá, {cliente}! Gostaria de saber se ficou "
            "tudo certo com o serviço realizado. "
            "Muito obrigado pela confiança!",

            "Pedido de avaliação":
            f"Olá, {cliente}! Espero que tenha gostado "
            "do serviço. Se puder, deixe uma avaliação "
            "sobre meu trabalho. Isso me ajuda muito!"
        }

        mensagem = mensagens.get(
            tipo,
            "Olá! Tudo bem?"
        )

        from urllib.parse import quote

        link = (
            "https://wa.me/"
            + telefone
            + "?text="
            + quote(mensagem)
        )

    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">

    <head>

    <meta charset="UTF-8">

    <meta name="viewport"
    content="width=device-width, initial-scale=1.0">

    <title>WhatsApp</title>

    """ + STYLE + """

    </head>

    <body>

    <div class="container">

    <a href="/">← Painel</a>

    <h1>📱 WhatsApp</h1>

    <div class="card">

    <form method="POST">

    <label>Telefone</label>

    <input
    name="telefone"
    placeholder="77999999999"
    required
    >

    <label>Cliente</label>

    <input
    name="cliente"
    placeholder="Nome do cliente"
    >

    <label>Tipo de mensagem</label>

    <select name="tipo">

    <option>Primeiro contato</option>
    <option>Envio de proposta</option>
    <option>Envio de orçamento</option>
    <option>Confirmação de serviço</option>
    <option>Lembrete de pagamento</option>
    <option>Confirmação de agendamento</option>
    <option>Pós-venda</option>
    <option>Pedido de avaliação</option>

    </select>

    <label>Serviço</label>

    <input name="servico">

    <label>Valor</label>

    <input name="valor">

    <button class="btn">
    GERAR MENSAGEM
    </button>

    </form>

    {% if link %}

    <div class="alert">

    Mensagem pronta!

    </div>

    <a
    class="btn"
    href="{{ link }}"
    target="_blank"
    >
    ABRIR NO WHATSAPP
    </a>

    {% endif %}

    </div>

    </div>

    </body>
    </html>
    """

    return render_template_string(
        html,
        link=link
    )


# ================================================================
# RECIBO
# ================================================================

@app.route("/recibo", methods=["GET", "POST"])
@login_required
def recibo():

    if request.method == "POST":

        usuario = usuario_atual()

        cliente = request.form.get(
            "cliente",
            ""
        )

        valor = dinheiro(
            request.form.get("valor")
        )

        descricao = request.form.get(
            "descricao",
            ""
        )

        forma_pagamento = request.form.get(
            "pagamento",
            ""
        )

        caminho, doc, titulo_style, normal = gerar_pdf_base(
            "recibo.pdf",
            "Recibo"
        )

        elementos = []

        elementos.append(
            Paragraph(
                "RECIBO",
                titulo_style
            )
        )

        elementos.append(
            Paragraph(
                f"Recebi de <b>{escape_pdf(cliente)}</b> "
                f"a quantia de <b>{brl(valor)}</b>.",
                normal
            )
        )

        elementos.append(Spacer(1, 15))

        elementos.append(
            Paragraph(
                f"<b>Referente a:</b> "
                f"{escape_pdf(descricao)}",
                normal
            )
        )

        elementos.append(
            Paragraph(
                f"<b>Forma de pagamento:</b> "
                f"{escape_pdf(forma_pagamento)}",
                normal
            )
        )

        elementos.append(Spacer(1, 30))

        elementos.append(
            Paragraph(
                escape_pdf(usuario.nome),
                normal
            )
        )

        elementos.append(
            Paragraph(
                datetime.now().strftime(
                    "%d/%m/%Y"
                ),
                normal
            )
        )

        doc.build(elementos)

        registrar_documento(
            "Recibo",
            cliente,
            descricao
        )

        return send_file(
            caminho,
            as_attachment=True,
            download_name="recibo.pdf"
        )

    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">

    <head>

    <meta charset="UTF-8">

    <meta name="viewport"
    content="width=device-width, initial-scale=1.0">

    <title>Recibo</title>

    """ + STYLE + """

    </head>

    <body>

    <div class="container">

    <a href="/">← Painel</a>

    <h1>🧾 Recibo</h1>

    <div class="card">

    <form method="POST">

    <label>Cliente</label>
    <input name="cliente" required>

    <label>Valor</label>
    <input
    name="valor"
    placeholder="Ex: 500,00"
    required
    >

    <label>Referente a</label>

    <textarea
    name="descricao"
    required
    ></textarea>

    <label>Forma de pagamento</label>

    <input
    name="pagamento"
    placeholder="PIX, dinheiro, cartão..."
    >

    <button class="btn">
    GERAR RECIBO PDF
    </button>

    </form>

    </div>

    </div>

    </body>

    </html>
    """

    return render_template_string(
        html
    )


# ================================================================
# AGENDA
# ================================================================

@app.route("/agenda", methods=["GET", "POST"])
@login_required
def agenda():

    if request.method == "POST":

        cliente_id = request.form.get(
            "cliente_id"
        )

        cliente = None

        if cliente_id:

            cliente = Cliente.query.filter_by(
                id=cliente_id,
                usuario_id=session["usuario_id"]
            ).first()

        servico = Servico(
            usuario_id=session["usuario_id"],
            cliente_id=cliente.id if cliente else None,
            titulo=request.form.get(
                "titulo",
                ""
            ),
            descricao=request.form.get(
                "descricao",
                ""
            ),
            data=request.form.get(
                "data",
                ""
            ),
            valor=dinheiro(
                request.form.get("valor")
            ),
            status="Agendado"
        )

        if not servico.titulo:
            flash("Informe o serviço.")
            return redirect(url_for("agenda"))

        db.session.add(servico)
        db.session.commit()

        flash("Serviço adicionado à agenda.")

        return redirect(
            url_for("agenda")
        )

    clientes_lista = Cliente.query.filter_by(
        usuario_id=session["usuario_id"]
    ).all()

    servicos = Servico.query.filter_by(
        usuario_id=session["usuario_id"]
    ).order_by(
        Servico.id.desc()
    ).all()

    html = """
    <!DOCTYPE html>

    <html lang="pt-BR">

    <head>

    <meta charset="UTF-8">

    <meta name="viewport"
    content="width=device-width, initial-scale=1.0">

    <title>Agenda</title>

    """ + STYLE + """

    </head>

    <body>

    <div class="container">

    <a href="/">← Painel</a>

    <h1>📅 Agenda</h1>

    {% with messages = get_flashed_messages() %}
    {% for message in messages %}
    <div class="alert">{{ message }}</div>
    {% endfor %}
    {% endwith %}

    <div class="card">

    <h2>Novo serviço</h2>

    <form method="POST">

    <label>Cliente</label>

    <select name="cliente_id">

    <option value="">
Sem cliente
    </option>

    {% for cliente in clientes_lista %}

    <option value="{{ cliente.id }}">
    {{ cliente.nome }}
    </option>

    {% endfor %}

    </select>

    <label>Serviço</label>

    <input
    name="titulo"
    required
    >

    <label>Descrição</label>

    <textarea name="descricao"></textarea>

    <label>Data e horário</label>

    <input
    type="datetime-local"
    name="data"
    >

    <label>Valor</label>

    <input name="valor">

    <button class="btn">
    AGENDAR
    </button>

    </form>

    </div>


    <div class="card">

    <h2>Meus serviços</h2>

    {% for item in servicos %}

    <div class="card">

    <h3>{{ item.titulo }}</h3>

    <p>
    {{ item.descricao or "" }}
    </p>

    <p>
    📅 {{ item.data or "Data não informada" }}
    </p>

    <p>
    💰 {{ "%.2f"|format(item.valor)|replace(".", ",") }}
    </p>

    <p>
    Status: <b>{{ item.status }}</b>
    </p>

    <a
    class="btn"
    href="/servico/status/{{ item.id }}"
    >
    ALTERAR STATUS
    </a>

    <a
    class="btn btn-danger"
    href="/servico/excluir/{{ item.id }}"
    onclick="return confirm('Excluir serviço?')"
    >
    EXCLUIR
    </a>

    </div>

    {% else %}

    <p>Nenhum serviço agendado.</p>

    {% endfor %}

    </div>

    </div>

    </body>

    </html>
    """

    return render_template_string(
        html,
        clientes_lista=clientes_lista,
        servicos=servicos
    )


@app.route(
    "/servico/status/<int:id>"
)
@login_required
def status_servico(id):

    servico = Servico.query.filter_by(
        id=id,
        usuario_id=session["usuario_id"]
    ).first()

    if servico:

        estados = [
            "Agendado",
            "Em andamento",
            "Concluído",
            "Cancelado"
        ]

        atual = servico.status

        try:
            posicao = estados.index(atual)
            servico.status = estados[
                (posicao + 1) % len(estados)
            ]
        except:
            servico.status = "Agendado"

        db.session.commit()

    return redirect(
        url_for("agenda")
    )


@app.route(
    "/servico/excluir/<int:id>"
)
@login_required
def excluir_servico(id):

    servico = Servico.query.filter_by(
        id=id,
        usuario_id=session["usuario_id"]
    ).first()

    if servico:

        db.session.delete(servico)

        db.session.commit()

    return redirect(
        url_for("agenda")
    )


# ================================================================
# FINANCEIRO
# ================================================================

@app.route(
    "/financeiro",
    methods=["GET", "POST"]
)
@login_required
def financeiro():

    if request.method == "POST":

        tipo = request.form.get(
            "tipo",
            "entrada"
        )

        movimento = Movimento(
            usuario_id=session["usuario_id"],
            tipo=tipo,
            descricao=request.form.get(
                "descricao",
                ""
            ),
            valor=dinheiro(
                request.form.get("valor")
            ),
            data=request.form.get(
                "data",
                ""
            )
        )

        if not movimento.descricao:
            flash("Informe a descrição.")
            return redirect(
                url_for("financeiro")
            )

        db.session.add(movimento)

        db.session.commit()

        flash("Movimento financeiro registrado.")

        return redirect(
            url_for("financeiro")
        )

    movimentos = Movimento.query.filter_by(
        usuario_id=session["usuario_id"]
    ).order_by(
        Movimento.id.desc()
    ).all()

    entradas = sum(
        m.valor
        for m in movimentos
        if m.tipo == "entrada"
    )

    saidas = sum(
        m.valor
        for m in movimentos
        if m.tipo == "saida"
    )

    saldo = entradas - saidas

    html = """
    <!DOCTYPE html>

    <html lang="pt-BR">

    <head>

    <meta charset="UTF-8">

    <meta name="viewport"
    content="width=device-width, initial-scale=1.0">

    <title>Financeiro</title>

    """ + STYLE + """

    </head>

    <body>

    <div class="container">

    <a href="/">← Painel</a>

    <h1>💰 Financeiro</h1>

    {% with messages = get_flashed_messages() %}
    {% for message in messages %}
    <div class="alert">{{ message }}</div>
    {% endfor %}
    {% endwith %}

    <div class="grid">

    <div class="card">
    <div class="small">Entradas</div>
    <div class="stat">
    R$ {{ "%.2f"|format(entradas)|replace(".", ",") }}
    </div>
    </div>

    <div class="card">
    <div class="small">Saídas</div>
    <div class="stat">
    R$ {{ "%.2f"|format(saidas)|replace(".", ",") }}
    </div>
    </div>

    <div class="card">
    <div class="small">Saldo</div>
    <div class="stat">
    R$ {{ "%.2f"|format(saldo)|replace(".", ",") }}
    </div>
    </div>

    </div>


    <div class="card">

    <h2>Novo lançamento</h2>

    <form method="POST">

    <label>Tipo</label>

    <select name="tipo">

    <option value="entrada">
    Entrada
    </option>

    <option value="saida">
    Saída
    </option>

    </select>

    <label>Descrição</label>

    <input
    name="descricao"
    placeholder="Ex: Pagamento cliente"
    required
    >

    <label>Valor</label>

    <input
    name="valor"
    placeholder="Ex: 500,00"
    required
    >

    <label>Data</label>

    <input
    type="date"
    name="data"
    >

    <button class="btn">
    SALVAR
    </button>

    </form>

    </div>


    <div class="card">

    <h2>Movimentos</h2>

    <table>

    <tr>
    <th>Tipo</th>
    <th>Descrição</th>
    <th>Valor</th>
    <th>Ação</th>
    </tr>

    {% for m in movimentos %}

    <tr>

    <td>{{ m.tipo }}</td>

    <td>{{ m.descricao }}</td>

    <td>
    R$ {{ "%.2f"|format(m.valor)|replace(".", ",") }}
    </td>

    <td>

    <a
    class="btn btn-danger"
    href="/financeiro/excluir/{{ m.id }}"
    onclick="return confirm('Excluir lançamento?')"
    >
    Excluir
    </a>

    </td>

    </tr>

    {% endfor %}

    </table>

    </div>

    </div>

    </body>

    </html>
    """

    return render_template_string(
        html,
        movimentos=movimentos,
        entradas=entradas,
        saidas=saidas,
        saldo=saldo
    )


@app.route(
    "/financeiro/excluir/<int:id>"
)
@login_required
def excluir_movimento(id):

    movimento = Movimento.query.filter_by(
        id=id,
        usuario_id=session["usuario_id"]
    ).first()

    if movimento:

        db.session.delete(movimento)

        db.session.commit()

    return redirect(
        url_for("financeiro")
    )


# ================================================================
# HISTÓRICO
# ================================================================

@app.route("/historico")
@login_required
def historico():

    documentos = Documento.query.filter_by(
        usuario_id=session["usuario_id"]
    ).order_by(
        Documento.id.desc()
    ).all()

    html = """
    <!DOCTYPE html>

    <html lang="pt-BR">

    <head>

    <meta charset="UTF-8">

    <meta name="viewport"
    content="width=device-width, initial-scale=1.0">

    <title>Histórico</title>

    """ + STYLE + """

    </head>

    <body>

    <div class="container">

    <a href="/">← Painel</a>

    <h1>📊 Histórico</h1>

    <div class="card">

    {% if documentos %}

    <table>

    <tr>

    <th>Tipo</th>
    <th>Cliente</th>
    <th>Título</th>
    <th>Data</th>

    </tr>

    {% for d in documentos %}

    <tr>

    <td>{{ d.tipo }}</td>

    <td>{{ d.cliente or "-" }}</td>

    <td>{{ d.titulo or "-" }}</td>

    <td>
    {{ d.criado_em.strftime("%d/%m/%Y %H:%M") }}
    </td>

    </tr>

    {% endfor %}

    </table>

    {% else %}

    <p>
    Você ainda não criou documentos.
    </p>

    {% endif %}

    </div>

    </div>

    </body>

    </html>
    """

    return render_template_string(
        html,
        documentos=documentos
    )


# ================================================================
# HEALTH CHECK
# ================================================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "app": "Proposta Exclusiva",
        "version": "7.0",
        "login": True,
        "database": True
    }


# ================================================================
# ERROS
# ================================================================

@app.errorhandler(404)
def erro_404(error):

    return """
    <div style="
        font-family:Arial;
        background:#080808;
        color:white;
        padding:40px;
        text-align:center;
    ">

    <h1 style="color:#d4af37">
    Página não encontrada
    </h1>

    <p>
    A página que você procurou não existe.
    </p>

    <a
    href="/"
    style="color:#d4af37"
    >
    Voltar ao início
    </a>

    </div>
    """, 404


@app.errorhandler(500)
def erro_500(error):

    db.session.rollback()

    return """
    <div style="
        font-family:Arial;
        background:#080808;
        color:white;
        padding:40px;
        text-align:center;
    ">

    <h1 style="color:#d4af37">
    Ocorreu um erro
    </h1>

    <p>
    Tente novamente.
    </p>

    <a
    href="/"
    style="color:#d4af37"
    >
    Voltar ao início
    </a>

    </div>
    """, 500


# ================================================================
# EXECUÇÃO
# ================================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
