import os
import uuid
from datetime import datetime, timedelta
from io import BytesIO

from flask import Flask, request, render_template_string, send_file, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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


# ============================================================
# CONFIGURAÇÃO
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "chave-local-troque-em-producao"
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


# ============================================================
# CONFIGURAÇÕES DO PRODUTO
# ============================================================

PLANO_VALOR = 10.00
LIMITE_GRATIS = 1

PIX = os.environ.get(
    "PIX",
    "eliseusud3@gmail.com"
)

WHATSAPP_SUPORTE = os.environ.get(
    "WHATSAPP_SUPORTE",
    "5577999999999"
)

CODIGO_ATIVACAO = os.environ.get(
    "CODIGO_ATIVACAO",
    "TROQUE-ESTE-CODIGO"
)


# ============================================================
# MODELO DO BANCO
# ============================================================

class UserUsage(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    session_id = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    ip_address = db.Column(
        db.String(100)
    )

    email = db.Column(
        db.String(200)
    )

    free_used = db.Column(
        db.Integer,
        default=0
    )

    is_subscribed = db.Column(
        db.Boolean,
        default=False
    )

    subscription_expires = db.Column(
        db.DateTime
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ============================================================
# BANCO
# ============================================================

with app.app_context():
    db.create_all()


# ============================================================
# PROFISSÕES
# ============================================================

PROFISSOES = {
    "Pedreiro": "Execução de serviços de construção, reforma e acabamento.",
    "Eletricista": "Execução de serviços elétricos e instalações.",
    "Encanador": "Execução de serviços hidráulicos e manutenção.",
    "Pintor": "Execução de pintura residencial e comercial.",
    "Mecânico": "Serviços de manutenção e reparação automotiva.",
    "Técnico de celular": "Manutenção, reparo e diagnóstico de celulares.",
    "Informática": "Manutenção, configuração e suporte em informática.",
    "Fotógrafo": "Serviços profissionais de fotografia.",
    "Designer": "Criação de materiais gráficos e projetos visuais.",
    "Outro": "Prestação de serviço profissional."
}


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def get_session_id():

    if not request.cookies.get("session_id"):
        return str(uuid.uuid4())

    return request.cookies.get("session_id")


def get_or_create_user():

    session_id = get_session_id()

    user = UserUsage.query.filter_by(
        session_id=session_id
    ).first()

    if not user:

        user = UserUsage(
            session_id=session_id,
            ip_address=request.remote_addr,
            free_used=0,
            is_subscribed=False
        )

        db.session.add(user)
        db.session.commit()

    return user


def subscription_active(user):

    if not user.is_subscribed:
        return False

    if not user.subscription_expires:
        return False

    if datetime.utcnow() >= user.subscription_expires:

        user.is_subscribed = False

        db.session.commit()

        return False

    return True


def can_use_free(user):

    if subscription_active(user):
        return True

    return user.free_used < LIMITE_GRATIS


def register_use(user):

    if not subscription_active(user):

        user.free_used += 1

        db.session.commit()


def clean_phone(phone):

    phone = "".join(
        c for c in phone
        if c.isdigit()
    )

    if len(phone) in [10, 11]:

        phone = "55" + phone

    return phone


def parse_money(value):

    if not value:
        return 0.0

    value = str(value)

    value = value.replace(
        "R$",
        ""
    )

    value = value.replace(
        ".",
        ""
    )

    value = value.replace(
        ",",
        "."
    )

    try:

        return float(value)

    except:

        return 0.0


def money_br(value):

    return (
        f"R$ {value:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def pdf_text(text):

    if not text:
        return ""

    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ============================================================
# GERADOR DE PDF
# ============================================================

def generate_pdf(data):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    styles = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "Titulo",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=10
    )

    subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.grey
    )

    normal = ParagraphStyle(
        "NormalCustom",
        parent=styles["Normal"],
        fontSize=10,
        leading=15
    )

    destaque = ParagraphStyle(
        "Destaque",
        parent=styles["Normal"],
        fontSize=13,
        leading=18
    )

    elementos = []

    # --------------------------------------------------------
    # CABEÇALHO
    # --------------------------------------------------------

    elementos.append(
        Paragraph(
            "PROPOSTA EXCLUSIVA",
            titulo
        )
    )

    elementos.append(
        Paragraph(
            "Proposta profissional de prestação de serviços",
            subtitulo
        )
    )

    elementos.append(
        Spacer(1, 20)
    )

    # --------------------------------------------------------
    # INFORMAÇÕES
    # --------------------------------------------------------

    numero = datetime.now().strftime("%Y%m%d%H%M%S")

    dados_proposta = [
        [
            Paragraph("<b>Número</b>", normal),
            numero
        ],
        [
            Paragraph("<b>Data</b>", normal),
            datetime.now().strftime("%d/%m/%Y")
        ],
        [
            Paragraph("<b>Profissão</b>", normal),
            pdf_text(data["profissao"])
        ]
    ]

    tabela = Table(
        dados_proposta,
        colWidths=[4 * cm, 11 * cm]
    )

    tabela.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 8)
        ])
    )

    elementos.append(tabela)

    elementos.append(
        Spacer(1, 20)
    )

    # --------------------------------------------------------
    # CLIENTE
    # --------------------------------------------------------

    elementos.append(
        Paragraph(
            "<b>DADOS DO CLIENTE</b>",
            destaque
        )
    )

    elementos.append(
        Spacer(1, 8)
    )

    cliente = [
        [
            Paragraph("<b>Cliente:</b>", normal),
            pdf_text(data["cliente"])
        ],
        [
            Paragraph("<b>Telefone:</b>", normal),
            pdf_text(data["telefone"])
        ],
        [
            Paragraph("<b>Endereço:</b>", normal),
            pdf_text(data["endereco"])
        ]
    ]

    tabela_cliente = Table(
        cliente,
        colWidths=[4 * cm, 11 * cm]
    )

    tabela_cliente.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("PADDING", (0, 0), (-1, -1), 8)
        ])
    )

    elementos.append(tabela_cliente)

    elementos.append(
        Spacer(1, 20)
    )

    # --------------------------------------------------------
    # SERVIÇO
    # --------------------------------------------------------

    elementos.append(
        Paragraph(
            "<b>SERVIÇO</b>",
            destaque
        )
    )

    elementos.append(
        Spacer(1, 8)
    )

    elementos.append(
        Paragraph(
            f"<b>Descrição:</b><br/>{pdf_text(data['descricao'])}",
            normal
        )
    )

    elementos.append(
        Spacer(1, 20)
    )

    # --------------------------------------------------------
    # VALORES
    # --------------------------------------------------------

    valor = data["valor"]
    desconto = data["desconto"]

    valor_desconto = valor * (
        desconto / 100
    )

    total = valor - valor_desconto

    financeiros = [
        [
            Paragraph("<b>Valor do serviço</b>", normal),
            money_br(valor)
        ],
        [
            Paragraph("<b>Desconto</b>", normal),
            f"{desconto:.2f}%"
        ],
        [
            Paragraph("<b>Total</b>", normal),
            money_br(total)
        ]
    ]

    tabela_financeira = Table(
        financeiros,
        colWidths=[9 * cm, 6 * cm]
    )

    tabela_financeira.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("BACKGROUND", (0, 2), (-1, 2), colors.whitesmoke),
            ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("PADDING", (0, 0), (-1, -1), 10)
        ])
    )

    elementos.append(
        tabela_financeira
    )

    elementos.append(
        Spacer(1, 20)
    )

    # --------------------------------------------------------
    # CONDIÇÕES
    # --------------------------------------------------------

    elementos.append(
        Paragraph(
            "<b>CONDIÇÕES COMERCIAIS</b>",
            destaque
        )
    )

    elementos.append(
        Spacer(1, 8)
    )

    elementos.append(
        Paragraph(
            pdf_text(data["condicoes"]),
            normal
        )
    )

    elementos.append(
        Spacer(1, 20)
    )

    # --------------------------------------------------------
    # OBSERVAÇÕES
    # --------------------------------------------------------

    elementos.append(
        Paragraph(
            "<b>OBSERVAÇÕES</b>",
            destaque
        )
    )

    elementos.append(
        Spacer(1, 8)
    )

    elementos.append(
        Paragraph(
            pdf_text(data["observacoes"]),
            normal
        )
    )

    elementos.append(
        Spacer(1, 40)
    )

    # --------------------------------------------------------
    # ASSINATURAS
    # --------------------------------------------------------

    assinatura = Table(
        [
            [
                "____________________________",
                "____________________________"
            ],
            [
                pdf_text(data["prestador"]),
                pdf_text(data["cliente"])
            ],
            [
                "Prestador de serviço",
                "Cliente"
            ]
        ],
        colWidths=[7.5 * cm, 7.5 * cm]
    )

    assinatura.setStyle(
        TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 1), (-1, 2), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 5)
        ])
    )

    elementos.append(
        assinatura
    )

    elementos.append(
        Spacer(1, 30)
    )

    elementos.append(
        Paragraph(
            "Documento gerado pelo Proposta Exclusiva",
            subtitulo
        )
    )

    doc.build(elementos)

    buffer.seek(0)

    return buffer


# ============================================================
# HTML
# ============================================================

HTML = """

<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Proposta Exclusiva</title>

<style>

*{
    box-sizing:border-box;
}

body{

    margin:0;

    font-family:
    Arial,
    Helvetica,
    sans-serif;

    background:#0b0b0d;

    color:#ffffff;
}

.container{

    width:92%;

    max-width:1100px;

    margin:auto;
}

header{

    padding:22px 0;

    border-bottom:
    1px solid #252525;
}

.logo{

    font-size:23px;

    font-weight:bold;

    color:#d4af37;
}

.hero{

    padding:
    60px 0
    40px;

    text-align:center;
}

.hero h1{

    font-size:
    clamp(32px,6vw,58px);

    margin:
    0 0 20px;

    line-height:1.05;
}

.hero h1 span{

    color:#d4af37;
}

.hero p{

    color:#bbbbbb;

    font-size:18px;

    max-width:700px;

    margin:
    0 auto 30px;
}

.btn{

    display:inline-block;

    background:#d4af37;

    color:#000000;

    text-decoration:none;

    border:0;

    padding:
    15px 25px;

    border-radius:10px;

    font-size:16px;

    font-weight:bold;

    cursor:pointer;
}

.btn:hover{

    opacity:.9;
}

.mockup{

    margin:
    45px auto;

    max-width:650px;

    background:#ffffff;

    color:#111111;

    border-radius:14px;

    padding:30px;

    box-shadow:
    0 20px 60px
    rgba(0,0,0,.4);

    text-align:left;
}

.mockup-title{

    text-align:center;

    font-size:22px;

    font-weight:bold;
}

.linha{

    height:10px;

    background:#eeeeee;

    margin:
    15px 0;

    border-radius:10px;
}

.cards{

    display:grid;

    grid-template-columns:
    repeat(3,1fr);

    gap:18px;

    margin:
    40px 0;
}

.card{

    background:#151518;

    border:
    1px solid #27272b;

    border-radius:14px;

    padding:25px;
}

.card h3{

    margin-top:0;

    color:#d4af37;
}

.form-area{

    background:#111114;

    border:
    1px solid #29292d;

    border-radius:18px;

    padding:30px;

    margin:
    40px 0;
}

.form-area h2{

    margin-top:0;

    font-size:28px;
}

.grid{

    display:grid;

    grid-template-columns:
    repeat(2,1fr);

    gap:16px;
}

input,
select,
textarea{

    width:100%;

    padding:14px;

    margin-top:7px;

    border:
    1px solid #36363b;

    border-radius:9px;

    background:#08080a;

    color:white;

    font-size:15px;
}

textarea{

    min-height:120px;

    resize:vertical;
}

.full{

    grid-column:
    1 / -1;
}

label{

    color:#cccccc;

    font-size:14px;
}

.form-button{

    margin-top:20px;

    width:100%;
}

.plan{

    text-align:center;

    margin:
    60px 0;
}

.price{

    font-size:48px;

    font-weight:bold;

    color:#d4af37;
}

.plan ul{

    list-style:none;

    padding:0;

    color:#bbbbbb;

    line-height:2;
}

footer{

    padding:
    30px 0;

    border-top:
    1px solid #252525;

    text-align:center;

    color:#888888;

    font-size:13px;
}

@media(max-width:700px){

    .cards{

        grid-template-columns:1fr;
    }

    .grid{

        grid-template-columns:1fr;
    }

    .full{

        grid-column:auto;
    }

    .hero{

        padding-top:40px;
    }

    .form-area{

        padding:20px;
    }

}

</style>

</head>


<body>


<header>

<div class="container">

<div class="logo">
PROPOSTA EXCLUSIVA
</div>

</div>

</header>


<section class="hero">

<div class="container">

<h1>
Crie propostas
<span>profissionais</span>
em minutos.
</h1>

<p>
Transforme seus serviços em propostas bonitas,
organizadas e prontas para enviar ao cliente.
</p>

<a
href="#criar"
class="btn"
>
✨ Criar minha proposta grátis
</a>


<div class="mockup">

<div class="mockup-title">
PROPOSTA DE SERVIÇO
</div>

<div class="linha"></div>

<p>
<strong>Cliente:</strong>
João da Silva
</p>

<p>
<strong>Serviço:</strong>
Reforma residencial
</p>

<div class="linha"></div>

<p>
<strong>Valor:</strong>
R$ 2.500,00
</p>

<p>
<strong>Total:</strong>
R$ 2.300,00
</p>

</div>

</div>

</section>


<section class="container">

<div class="cards">

<div class="card">

<h3>📄 PDF profissional</h3>

<p>
Gere propostas organizadas
prontas para apresentar.
</p>

</div>


<div class="card">

<h3>📱 WhatsApp</h3>

<p>
Envie rapidamente a proposta
para seu cliente.
</p>

</div>


<div class="card">

<h3>⚡ Rápido</h3>

<p>
Preencha os dados e gere
sua proposta em poucos minutos.
</p>

</div>

</div>

</section>


<section
class="container"
id="criar"
>

<div class="form-area">

<h2>
Criar nova proposta
</h2>

<p style="color:#999;">
Sua primeira proposta é gratuita.
</p>


<form
method="POST"
action="/gerar-pdf"
>


<div class="grid">


<div>

<label>
Seu nome
</label>

<input
type="text"
name="prestador"
required
placeholder="Ex.: Eliseu Silva"
>

</div>


<div>

<label>
Profissão
</label>

<select
name="profissao"
required
>

<option value="">
Selecione
</option>

{% for profissao in profissoes %}

<option value="{{ profissao }}">
{{ profissao }}
</option>

{% endfor %}

</select>

</div>


<div>

<label>
Nome do cliente
</label>

<input
type="text"
name="cliente"
required
placeholder="Nome do cliente"
>

</div>


<div>

<label>
Telefone do cliente
</label>

<input
type="text"
name="telefone"
placeholder="(77) 99999-9999"
>

</div>


<div class="full">

<label>
Endereço
</label>

<input
type="text"
name="endereco"
placeholder="Endereço do serviço"
>

</div>


<div class="full">

<label>
Descrição do serviço
</label>

<textarea
name="descricao"
required
placeholder="Descreva o serviço que será realizado..."
></textarea>

</div>


<div>

<label>
Valor do serviço
</label>

<input
type="text"
name="valor"
required
placeholder="R$ 1.500,00"
>

</div>


<div>

<label>
Desconto (%)
</label>

<input
type="number"
name="desconto"
value="0"
min="0"
max="100"
step="0.01"
>

</div>


<div class="full">

<label>
Condições comerciais
</label>

<textarea
name="condicoes"
placeholder="Ex.: 50% na contratação e 50% na conclusão."
>Pagamento combinado entre as partes.</textarea>

</div>


<div class="full">

<label>
Observações
</label>

<textarea
name="observacoes"
placeholder="Informações adicionais"
></textarea>

</div>


</div>


<button
class="btn form-button"
type="submit"
>
📄 Gerar minha proposta em PDF
</button>


</form>

</div>

</section>


<section class="plan">

<div class="container">

<h2>
Plano Profissional
</h2>

<div class="price">
R$ 10
</div>

<p>
por mês
</p>

<ul>

<li>✓ Propostas profissionais</li>

<li>✓ Geração de PDF</li>

<li>✓ Envio pelo WhatsApp</li>

<li>✓ Uso para seus serviços</li>

</ul>

<p style="color:#777;font-size:13px;">
Ativação do plano atualmente realizada
manualmente após pagamento.
</p>

</div>

</section>


<footer>

<div class="container">

Proposta Exclusiva © 2026

<br><br>

Suporte:
{{ whatsapp_suporte }}

</div>

</footer>


</body>

</html>

"""


# ============================================================
# PÁGINA INICIAL
# ============================================================

@app.route("/")
def home():

    user = get_or_create_user()

    response = render_template_string(
        HTML,
        profissoes=PROFISSOES.keys(),
        whatsapp_suporte=WHATSAPP_SUPORTE
    )

    if not request.cookies.get("session_id"):

        response_obj = app.make_response(response)

        response_obj.set_cookie(
            "session_id",
            user.session_id,
            max_age=60 * 60 * 24 * 365
        )

        return response_obj

    return response


# ============================================================
# GERAR PDF
# ============================================================

@app.route(
    "/gerar-pdf",
    methods=["POST"]
)
def gerar_pdf():

    user = get_or_create_user()

    if not can_use_free(user):

        return """

        <html>

        <body style="
        font-family:Arial;
        background:#0b0b0d;
        color:white;
        text-align:center;
        padding:50px;
        ">

        <h1>🔒 Limite gratuito atingido</h1>

        <p>
        Sua proposta gratuita já foi utilizada.
        </p>

        <h2 style="color:#d4af37;">
        Plano Profissional — R$ 10/mês
        </h2>

        <p>
        Entre em contato para ativar seu acesso.
        </p>

        <a
        href="/"
        style="
        display:inline-block;
        padding:15px 25px;
        background:#d4af37;
        color:black;
        text-decoration:none;
        border-radius:10px;
        font-weight:bold;
        "
        >
        Voltar
        </a>

        </body>

        </html>

        """

    valor = parse_money(
        request.form.get("valor")
    )

    desconto = parse_money(
        request.form.get("desconto")
    )

    if valor <= 0:

        return "Informe um valor válido."

    if desconto < 0:
        desconto = 0

    if desconto > 100:
        desconto = 100

    data = {

        "prestador":
        request.form.get(
            "prestador",
            ""
        ),

        "profissao":
        request.form.get(
            "profissao",
            "Outro"
        ),

        "cliente":
        request.form.get(
            "cliente",
            ""
        ),

        "telefone":
        request.form.get(
            "telefone",
            ""
        ),

        "endereco":
        request.form.get(
            "endereco",
            ""
        ),

        "descricao":
        request.form.get(
            "descricao",
            ""
        ),

        "valor":
        valor,

        "desconto":
        desconto,

        "condicoes":
        request.form.get(
            "condicoes",
            ""
        ),

        "observacoes":
        request.form.get(
            "observacoes",
            ""
        )
    }

    register_use(user)

    pdf = generate_pdf(data)

    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="proposta-exclusiva.pdf"
    )


# ============================================================
# WHATSAPP
# ============================================================

@app.route(
    "/whatsapp",
    methods=["POST"]
)
def whatsapp():

    user = get_or_create_user()

    if not can_use_free(user):

        return redirect(
            url_for("home")
        )

    cliente = request.form.get(
        "cliente",
        ""
    )

    telefone = clean_phone(
        request.form.get(
            "telefone",
            ""
        )
    )

    prestador = request.form.get(
        "prestador",
        ""
    )

    descricao = request.form.get(
        "descricao",
        ""
    )

    valor = parse_money(
        request.form.get(
            "valor"
        )
    )

    desconto = parse_money(
        request.form.get(
            "desconto"
        )
    )

    total = valor - (
        valor * desconto / 100
    )

    mensagem = f"""
Olá, {cliente}!

Preparei sua proposta de serviço.

Prestador: {prestador}

Serviço:
{descricao}

Valor: {money_br(total)}

Obrigado pela oportunidade!
"""

    from urllib.parse import quote

    url = (
        "https://wa.me/"
        + telefone
        + "?text="
        + quote(mensagem)
    )

    register_use(user)

    return redirect(url)


# ============================================================
# ATIVAÇÃO MANUAL
# ============================================================

@app.route(
    "/ativar-assinatura",
    methods=["POST"]
)
def ativar_assinatura():

    codigo = request.form.get(
        "codigo",
        ""
    )

    if codigo != CODIGO_ATIVACAO:

        return """

        <h2>Código inválido.</h2>

        <a href="/">
        Voltar
        </a>

        """

    user = get_or_create_user()

    user.is_subscribed = True

    user.subscription_expires = (
        datetime.utcnow()
        + timedelta(days=30)
    )

    db.session.commit()

    return """

    <html>

    <body style="
    font-family:Arial;
    text-align:center;
    padding:50px;
    ">

    <h1>
    ✅ Assinatura ativada!
    </h1>

    <p>
    Seu acesso profissional foi ativado
    por 30 dias.
    </p>

    <a href="/">
    Começar a usar
    </a>

    </body>

    </html>

    """


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return {
        "status": "online",
        "app": "Proposta Exclusiva",
        "version": "1.0"
    }


# ============================================================
# EXECUÇÃO
# ============================================================

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
