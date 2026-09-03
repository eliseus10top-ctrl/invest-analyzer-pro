# ================================================================
# 🚀 PROPOSTA EXCLUSIVA 5.0
# ================================================================
# 📄 Propostas profissionais
# 💼 Currículos profissionais
# 🧾 Orçamentos profissionais
# 📝 Contratos
# 📱 Mensagens profissionais para WhatsApp
# 💳 Cartão digital
# 👤 Perfil profissional
# 🔗 Página profissional compartilhável
# 📚 Histórico de documentos
# 📱 Interface responsiva
# 🚀 Compatível com Render
# 💰 Sem pagamento
# ================================================================

import os
import re
import uuid
from datetime import datetime
from urllib.parse import quote

from flask import (
    Flask,
    request,
    render_template_string,
    send_file,
    redirect,
    url_for
)

from flask_sqlalchemy import SQLAlchemy

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
    HRFlowable
)


# ================================================================
# CONFIGURAÇÃO
# ================================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "proposta-exclusiva-5-secret"
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
# BANCO DE DADOS
# ================================================================

class UserProfile(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    slug = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    nome = db.Column(
        db.String(150),
        nullable=False
    )

    profissao = db.Column(
        db.String(150)
    )

    telefone = db.Column(
        db.String(50)
    )

    email = db.Column(
        db.String(150)
    )

    cidade = db.Column(
        db.String(150)
    )

    descricao = db.Column(
        db.Text
    )

    habilidades = db.Column(
        db.Text
    )

    experiencia = db.Column(
        db.Text
    )

    servicos = db.Column(
        db.Text
    )

    instagram = db.Column(
        db.String(300)
    )

    criado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class DocumentHistory(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    tipo = db.Column(
        db.String(80),
        nullable=False
    )

    cliente = db.Column(
        db.String(150)
    )

    descricao = db.Column(
        db.Text
    )

    valor = db.Column(
        db.Float,
        default=0
    )

    criado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


with app.app_context():

    db.create_all()


# ================================================================
# PROFISSÕES
# ================================================================

PROFISSOES = [
    "Pedreiro",
    "Eletricista",
    "Encanador",
    "Pintor",
    "Mecânico",
    "Técnico de celular",
    "Informática",
    "Fotógrafo",
    "Designer",
    "Jardineiro",
    "Instalador",
    "Marceneiro",
    "Professor",
    "Artista",
    "Outro"
]


# ================================================================
# FUNÇÕES AUXILIARES
# ================================================================

def dinheiro(valor):

    if not valor:
        return 0.0

    valor = str(valor).strip()

    valor = re.sub(
        r"[^\d,.-]",
        "",
        valor
    )

    if "," in valor:

        valor = valor.replace(
            ".",
            ""
        )

        valor = valor.replace(
            ",",
            "."
        )

    try:

        return float(valor)

    except Exception:

        return 0.0


def moeda(valor):

    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def telefone_whatsapp(numero):

    if not numero:
        return ""

    numero = re.sub(
        r"\D",
        "",
        numero
    )

    if numero.startswith("55"):

        return numero

    if len(numero) in [10, 11]:

        return "55" + numero

    return numero


def criar_slug(nome):

    slug = re.sub(
        r"[^a-zA-Z0-9]+",
        "-",
        nome.lower()
    ).strip("-")

    if not slug:

        slug = "profissional"

    original = slug

    contador = 1

    while UserProfile.query.filter_by(
        slug=slug
    ).first():

        contador += 1

        slug = (
            original
            + "-"
            + str(contador)
        )

    return slug


def registrar_documento(
    tipo,
    cliente="",
    descricao="",
    valor=0
):

    try:

        documento = DocumentHistory(

            tipo=tipo,

            cliente=cliente,

            descricao=descricao,

            valor=valor

        )

        db.session.add(
            documento
        )

        db.session.commit()

    except Exception:

        db.session.rollback()


# ================================================================
# ESTILOS PDF
# ================================================================

def estilos_pdf():

    estilos = getSampleStyleSheet()

    estilos.add(
        ParagraphStyle(
            name="TituloPrincipal",
            parent=estilos["Title"],
            fontSize=22,
            leading=26,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#111111"),
            spaceAfter=8
        )
    )

    estilos.add(
        ParagraphStyle(
            name="Subtitulo",
            parent=estilos["Normal"],
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#555555"),
            spaceAfter=12
        )
    )

    estilos.add(
        ParagraphStyle(
            name="Secao",
            parent=estilos["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#B8860B"),
            spaceBefore=12,
            spaceAfter=7
        )
    )

    estilos.add(
        ParagraphStyle(
            name="NormalCustom",
            parent=estilos["Normal"],
            fontSize=10,
            leading=15,
            textColor=colors.HexColor("#222222")
        )
    )

    estilos.add(
        ParagraphStyle(
            name="Pequeno",
            parent=estilos["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#666666")
        )
    )

    return estilos


def cabecalho_pdf(
    elementos,
    titulo,
    subtitulo
):

    estilos = estilos_pdf()

    elementos.append(
        Paragraph(
            titulo,
            estilos["TituloPrincipal"]
        )
    )

    elementos.append(
        Paragraph(
            subtitulo,
            estilos["Subtitulo"]
        )
    )

    elementos.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#B8860B"),
            spaceAfter=12
        )
    )


# ================================================================
# PDF — PROPOSTA
# ================================================================

def criar_pdf_proposta(dados):

    arquivo = "/tmp/proposta_exclusiva.pdf"

    documento = SimpleDocTemplate(
        arquivo,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm
    )

    estilos = estilos_pdf()

    elementos = []

    valor = dinheiro(
        dados.get("valor")
    )

    desconto = dinheiro(
        dados.get("desconto")
    )

    total = max(
        valor - desconto,
        0
    )

    cabecalho_pdf(
        elementos,
        "PROPOSTA COMERCIAL",
        "PROPOSTA EXCLUSIVA"
    )

    tabela_info = Table(
        [
            [
                Paragraph(
                    "<b>Prestador</b><br/>"
                    + str(
                        dados.get(
                            "prestador",
                            ""
                        )
                    ),
                    estilos["NormalCustom"]
                ),

                Paragraph(
                    "<b>Data</b><br/>"
                    + datetime.now().strftime(
                        "%d/%m/%Y"
                    ),
                    estilos["NormalCustom"]
                )
            ],

            [
                Paragraph(
                    "<b>Profissão</b><br/>"
                    + str(
                        dados.get(
                            "profissao",
                            ""
                        )
                    ),
                    estilos["NormalCustom"]
                ),

                Paragraph(
                    "<b>Cliente</b><br/>"
                    + str(
                        dados.get(
                            "cliente",
                            ""
                        )
                    ),
                    estilos["NormalCustom"]
                )
            ]
        ],

        colWidths=[
            9 * cm,
            8 * cm
        ]
    )

    tabela_info.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#F7F7F7")
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#DDDDDD")
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.HexColor("#DDDDDD")
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                )
            ]
        )
    )

    elementos.append(
        tabela_info
    )

    elementos.append(
        Paragraph(
            "DADOS DO CLIENTE",
            estilos["Secao"]
        )
    )

    elementos.append(
        Paragraph(
            f"<b>Nome:</b> "
            f"{dados.get('cliente', '')}<br/>"
            f"<b>Telefone:</b> "
            f"{dados.get('telefone', '')}<br/>"
            f"<b>Endereço:</b> "
            f"{dados.get('endereco', '')}",
            estilos["NormalCustom"]
        )
    )

    elementos.append(
        Paragraph(
            "DESCRIÇÃO DO SERVIÇO",
            estilos["Secao"]
        )
    )

    descricao = dados.get(
        "descricao",
        ""
    ).replace(
        "\n",
        "<br/>"
    )

    elementos.append(
        Paragraph(
            descricao or
            "Serviço conforme combinado.",
            estilos["NormalCustom"]
        )
    )

    elementos.append(
        Paragraph(
            "VALORES",
            estilos["Secao"]
        )
    )

    tabela_valores = Table(
        [
            [
                "Valor do serviço",
                moeda(valor)
            ],
            [
                "Desconto",
                moeda(desconto)
            ],
            [
                "TOTAL",
                moeda(total)
            ]
        ],
        colWidths=[
            11 * cm,
            6 * cm
        ]
    )

    tabela_valores.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#DDDDDD")
                ),
                (
                    "BACKGROUND",
                    (0, 2),
                    (-1, 2),
                    colors.HexColor("#F2F2F2")
                ),
                (
                    "FONTNAME",
                    (0, 2),
                    (-1, 2),
                    "Helvetica-Bold"
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT"
                )
            ]
        )
    )

    elementos.append(
        tabela_valores
    )

    elementos.append(
        Paragraph(
            "CONDIÇÕES COMERCIAIS",
            estilos["Secao"]
        )
    )

    elementos.append(
        Paragraph(
            dados.get(
                "condicoes",
                "Condições conforme combinado."
            ).replace(
                "\n",
                "<br/>"
            ),
            estilos["NormalCustom"]
        )
    )

    elementos.append(
        Paragraph(
            "OBSERVAÇÕES",
            estilos["Secao"]
        )
    )

    elementos.append(
        Paragraph(
            dados.get(
                "observacoes",
                "Sem observações."
            ).replace(
                "\n",
                "<br/>"
            ),
            estilos["NormalCustom"]
        )
    )

    elementos.append(
        Spacer(
            1,
            25
        )
    )

    assinatura = Table(
        [
            [
                "____________________________",
                "____________________________"
            ],
            [
                "Prestador",
                "Cliente"
            ]
        ],
        colWidths=[
            8.5 * cm,
            8.5 * cm
        ]
    )

    assinatura.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER"
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, 1),
                    "Helvetica-Bold"
                )
            ]
        )
    )

    elementos.append(
        assinatura
    )

    elementos.append(
        Spacer(
            1,
            15
        )
    )

    elementos.append(
        Paragraph(
            "Documento gerado pelo Proposta Exclusiva 5.0.",
            estilos["Pequeno"]
        )
    )

    documento.build(
        elementos
    )

    return arquivo


# ================================================================
# PDF — CURRÍCULO
# ================================================================

def criar_pdf_curriculo(dados):

    arquivo = "/tmp/curriculo_profissional.pdf"

    documento = SimpleDocTemplate(
        arquivo,
        pagesize=A4,
        rightMargin=1.6 * cm,
        leftMargin=1.6 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    estilos = estilos_pdf()

    elementos = []

    nome = dados.get("nome", "")
    profissao = dados.get("profissao", "")
    telefone = dados.get("telefone", "")
    email = dados.get("email", "")
    cidade = dados.get("cidade", "")
    objetivo = dados.get("objetivo", "")
    resumo = dados.get("resumo", "")
    experiencia = dados.get("experiencia", "")
    formacao = dados.get("formacao", "")
    cursos = dados.get("cursos", "")
    habilidades = dados.get("habilidades", "")
    idiomas = dados.get("idiomas", "")

    elementos.append(
        Paragraph(
            nome.upper() or "SEU NOME",
            estilos["TituloPrincipal"]
        )
    )

    if profissao:

        elementos.append(
            Paragraph(
                profissao,
                estilos["Subtitulo"]
            )
        )

    contato = " | ".join(
        x for x in [
            telefone,
            email,
            cidade
        ]
        if x
    )

    if contato:

        elementos.append(
            Paragraph(
                contato,
                estilos["Subtitulo"]
            )
        )

    elementos.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#B8860B"),
            spaceAfter=12
        )
    )

    secoes = [

        (
            "OBJETIVO PROFISSIONAL",
            objetivo
        ),

        (
            "PERFIL PROFISSIONAL",
            resumo
        ),

        (
            "EXPERIÊNCIA PROFISSIONAL",
            experiencia
        ),

        (
            "FORMAÇÃO ACADÊMICA",
            formacao
        ),

        (
            "CURSOS E CERTIFICAÇÕES",
            cursos
        )
    ]

    for titulo, texto in secoes:

        if texto:

            elementos.append(
                Paragraph(
                    titulo,
                    estilos["Secao"]
                )
            )

            elementos.append(
                Paragraph(
                    texto.replace(
                        "\n",
                        "<br/>"
                    ),
                    estilos["NormalCustom"]
                )
            )

    if habilidades:

        elementos.append(
            Paragraph(
                "HABILIDADES",
                estilos["Secao"]
            )
        )

        for item in habilidades.split(","):

            item = item.strip()

            if item:

                elementos.append(
                    Paragraph(
                        "• " + item,
                        estilos["NormalCustom"]
                    )
                )

    if idiomas:

        elementos.append(
            Paragraph(
                "IDIOMAS",
                estilos["Secao"]
            )
        )

        elementos.append(
            Paragraph(
                idiomas.replace(
                    "\n",
                    "<br/>"
                ),
                estilos["NormalCustom"]
            )
        )

    elementos.append(
        Spacer(
            1,
            20
        )
    )

    elementos.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.HexColor("#CCCCCC")
        )
    )

    elementos.append(
        Spacer(
            1,
            8
        )
    )

    elementos.append(
        Paragraph(
            "Currículo criado com o Proposta Exclusiva 5.0.",
            estilos["Pequeno"]
        )
    )

    documento.build(
        elementos
    )

    return arquivo


# ================================================================
# PDF — ORÇAMENTO
# ================================================================

def criar_pdf_orcamento(dados):

    arquivo = "/tmp/orcamento_profissional.pdf"

    documento = SimpleDocTemplate(
        arquivo,
        pagesize=A4,
        rightMargin=1.4 * cm,
        leftMargin=1.4 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm
    )

    estilos = estilos_pdf()

    elementos = []

    prestador = dados.get(
        "prestador",
        ""
    )

    profissao = dados.get(
        "profissao",
        ""
    )

    cliente = dados.get(
        "cliente",
        ""
    )

    telefone = dados.get(
        "telefone",
        ""
    )

    endereco = dados.get(
        "endereco",
        ""
    )

    materiais = dados.get(
        "materiais",
        ""
    )

    mao_obra = dinheiro(
        dados.get(
            "mao_obra"
        )
    )

    desconto = dinheiro(
        dados.get(
            "desconto"
        )
    )

    condicoes = dados.get(
        "condicoes",
        ""
    )

    observacoes = dados.get(
        "observacoes",
        ""
    )

    cabecalho_pdf(
        elementos,
        "ORÇAMENTO PROFISSIONAL",
        "PROPOSTA EXCLUSIVA 5.0"
    )

    dados_tabela = Table(
        [
            [
                Paragraph(
                    f"<b>Prestador:</b><br/>"
                    f"{prestador}",
                    estilos["NormalCustom"]
                ),

                Paragraph(
                    f"<b>Data:</b><br/>"
                    f"{datetime.now().strftime('%d/%m/%Y')}",
                    estilos["NormalCustom"]
                )
            ],

            [
                Paragraph(
                    f"<b>Profissão:</b><br/>"
                    f"{profissao}",
                    estilos["NormalCustom"]
                ),

                Paragraph(
                    f"<b>Cliente:</b><br/>"
                    f"{cliente}",
                    estilos["NormalCustom"]
                )
            ]
        ],
        colWidths=[
            9 * cm,
            8 * cm
        ]
    )

    dados_tabela.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#F7F7F7")
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#DDDDDD")
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.HexColor("#DDDDDD")
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                )
            ]
        )
    )

    elementos.append(
        dados_tabela
    )

    elementos.append(
        Paragraph(
            "DADOS DO CLIENTE",
            estilos["Secao"]
        )
    )

    elementos.append(
        Paragraph(
            f"<b>Nome:</b> {cliente}<br/>"
            f"<b>Telefone:</b> {telefone}<br/>"
            f"<b>Endereço:</b> {endereco}",
            estilos["NormalCustom"]
        )
    )

    elementos.append(
        Paragraph(
            "MATERIAIS / SERVIÇOS",
            estilos["Secao"]
        )
    )

    linhas = []

    total_materiais = 0.0

    if materiais:

        for linha in materiais.splitlines():

            linha = linha.strip()

            if not linha:
                continue

            partes = linha.split("|")

            descricao = partes[0].strip()

            quantidade = 1.0

            valor_unitario = 0.0

            if len(partes) >= 2:

                quantidade = dinheiro(
                    partes[1]
                )

                if quantidade == 0:

                    quantidade = 1.0

            if len(partes) >= 3:

                valor_unitario = dinheiro(
                    partes[2]
                )

            subtotal = (
                quantidade *
                valor_unitario
            )

            total_materiais += subtotal

            linhas.append(
                [
                    descricao,
                    str(quantidade),
                    moeda(valor_unitario),
                    moeda(subtotal)
                ]
            )

    if not linhas:

        linhas.append(
            [
                "Serviço",
                "1",
                moeda(mao_obra),
                moeda(mao_obra)
            ]
        )

    tabela_itens = Table(
        [
            [
                "Descrição",
                "Qtd.",
                "Valor unit.",
                "Subtotal"
            ]
        ] + linhas,

        colWidths=[
            7.5 * cm,
            2 * cm,
            3.5 * cm,
            4 * cm
        ],

        repeatRows=1
    )

    tabela_itens.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#EEEEEE")
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#DDDDDD")
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "RIGHT"
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                )
            ]
        )
    )

    elementos.append(
        tabela_itens
    )

    elementos.append(
        Paragraph(
            "RESUMO DO ORÇAMENTO",
            estilos["Secao"]
        )
    )

    total_bruto = (
        total_materiais +
        mao_obra
    )

    total_final = max(
        total_bruto - desconto,
        0
    )

    tabela_resumo = Table(
        [
            [
                "Materiais",
                moeda(total_materiais)
            ],
            [
                "Mão de obra",
                moeda(mao_obra)
            ],
            [
                "Desconto",
                moeda(desconto)
            ],
            [
                "TOTAL",
                moeda(total_final)
            ]
        ],
        colWidths=[
            11 * cm,
            6 * cm
        ]
    )

    tabela_resumo.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#DDDDDD")
                ),
                (
                    "BACKGROUND",
                    (0, 3),
                    (-1, 3),
                    colors.HexColor("#F2F2F2")
                ),
                (
                    "FONTNAME",
                    (0, 3),
                    (-1, 3),
                    "Helvetica-Bold"
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT"
                )
            ]
        )
    )

    elementos.append(
        tabela_resumo
    )

    elementos.append(
        Paragraph(
            "CONDIÇÕES DE PAGAMENTO",
            estilos["Secao"]
        )
    )

    elementos.append(
        Paragraph(
            condicoes or
            "Condições conforme combinado.",
            estilos["NormalCustom"]
        )
    )

    elementos.append(
        Paragraph(
            "OBSERVAÇÕES",
            estilos["Secao"]
        )
    )

    elementos.append(
        Paragraph(
            observacoes or
            "Sem observações.",
            estilos["NormalCustom"]
        )
    )

    elementos.append(
        Spacer(
            1,
            25
        )
    )

    assinatura = Table(
        [
            [
                "____________________________",
                "____________________________"
            ],
            [
                "Prestador",
                "Cliente"
            ]
        ],
        colWidths=[
            8.5 * cm,
            8.5 * cm
        ]
    )

    assinatura.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER"
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, 1),
                    "Helvetica-Bold"
                )
            ]
        )
    )

    elementos.append(
        assinatura
    )

    elementos.append(
        Spacer(
            1,
            15
        )
    )

    elementos.append(
        Paragraph(
            "Orçamento criado com o Proposta Exclusiva 5.0.",
            estilos["Pequeno"]
        )
    )

    documento.build(
        elementos
    )

    return arquivo


# ================================================================
# PDF — CONTRATO
# ================================================================

def criar_pdf_contrato(dados):

    arquivo = "/tmp/contrato_profissional.pdf"

    documento = SimpleDocTemplate(
        arquivo,
        pagesize=A4,
        rightMargin=1.7 * cm,
        leftMargin=1.7 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    estilos = estilos_pdf()

    elementos = []

    prestador = dados.get(
        "prestador",
        ""
    )

    cliente = dados.get(
        "cliente",
        ""
    )

    telefone_prestador = dados.get(
        "telefone_prestador",
        ""
    )

    telefone_cliente = dados.get(
        "telefone_cliente",
        ""
    )

    endereco_cliente = dados.get(
        "endereco_cliente",
        ""
    )

    servico = dados.get(
        "servico",
        ""
    )

    valor = dinheiro(
        dados.get(
            "valor"
        )
    )

    prazo = dados.get(
        "prazo",
        ""
    )

    pagamento = dados.get(
        "pagamento",
        ""
    )

    observacoes = dados.get(
        "observacoes",
        ""
    )

    cabecalho_pdf(
        elementos,
        "CONTRATO DE PRESTAÇÃO DE SERVIÇOS",
        "PROPOSTA EXCLUSIVA 5.0"
    )

    elementos.append(
        Paragraph(
            "IDENTIFICAÇÃO DAS PARTES",
            estilos["Secao"]
        )
    )

    texto_partes = (
        f"<b>CONTRATANTE:</b> {cliente}<br/>"
        f"Telefone: {telefone_cliente}<br/>"
        f"Endereço: {endereco_cliente}<br/><br/>"
        f"<b>CONTRATADO:</b> {prestador}<br/>"
        f"Telefone: {telefone_prestador}"
    )

    elementos.append(
        Paragraph(
            texto_partes,
            estilos["NormalCustom"]
        )
    )

    elementos.append(
        Paragraph(
            "CLÁUSULA 1ª — DO OBJETO",
            estilos["Secao"]
        )
    )

    elementos.append(
        Paragraph(
            "O presente contrato tem como objeto a prestação "
            "do seguinte serviço: "
            f"<b>{servico}</b>.",
            estilos["NormalCustom"]
        )
    )

    elementos.append(
        Paragraph(
            "CLÁUSULA 2ª — DO VALOR",
            estilos["Secao"]
        )
    )

    elementos.append(
        Paragraph(
            "Pela execução dos serviços descritos neste contrato, "
            "o CONTRATANTE pagará ao CONTRATADO o valor total de "
            f"<b>{moeda(valor)}</b>.",
            estilos["NormalCustom"]
        )
    )

    elementos.append(
        Paragraph(
            "CLÁUSULA 3ª — DO PAGAMENTO",
            estilos["Secao"]
        )
    )

    elementos.append(
        Paragraph(
            pagamento.replace(
                "\n",
                "<br/>"
            )
            if pagamento
            else
            "O pagamento será realizado conforme acordado "
            "entre as partes.",
            estilos["NormalCustom"]
        )
    )

    elementos.append(
        Paragraph(
            "CLÁUSULA 4ª — DO PRAZO",
            estilos["Secao"]
        )
    )

    elementos.append(
        Paragraph(
            prazo.replace(
                "\n",
                "<br/>"
            )
            if prazo
            else
            "O prazo será definido de comum acordo.",
            estilos["NormalCustom"]
        )
    )

    elementos.append(
        Paragraph(
            "CLÁUSULA 5ª — DAS OBRIGAÇÕES",
            estilos["Secao"]
        )
    )

    elementos.append(
        Paragraph(
            "O CONTRATADO compromete-se a executar os serviços "
            "descritos neste documento com zelo e conforme "
            "as condições acordadas. O CONTRATANTE compromete-se "
            "a fornecer as informações necessárias e realizar "
            "os pagamentos nos prazos acordados.",
            estilos["NormalCustom"]
        )
    )

    elementos.append(
        Paragraph(
            "CLÁUSULA 6ª — DAS DISPOSIÇÕES GERAIS",
            estilos["Secao"]
        )
    )

    elementos.append(
        Paragraph(
            "Qualquer alteração nas condições deste contrato "
            "deverá ser acordada entre as partes.",
            estilos["NormalCustom"]
        )
    )

    if observacoes:

        elementos.append(
            Paragraph(
                "OBSERVAÇÕES",
                estilos["Secao"]
            )
        )

        elementos.append(
            Paragraph(
                observacoes.replace(
                    "\n",
                    "<br/>"
                ),
                estilos["NormalCustom"]
            )
        )

    elementos.append(
        Spacer(
            1,
            30
        )
    )

    data = datetime.now().strftime(
        "%d/%m/%Y"
    )

    elementos.append(
        Paragraph(
            f"Local e data: ____________________, {data}.",
            estilos["NormalCustom"]
        )
    )

    elementos.append(
        Spacer(
            1,
            35
        )
    )

    assinatura = Table(
        [
            [
                "____________________________",
                "____________________________"
            ],
            [
                "CONTRATADO",
                "CONTRATANTE"
            ]
        ],
        colWidths=[
            8.5 * cm,
            8.5 * cm
        ]
    )

    assinatura.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER"
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, 1),
                    "Helvetica-Bold"
                )
            ]
        )
    )

    elementos.append(
        assinatura
    )

    elementos.append(
        Spacer(
            1,
            20
        )
    )

    elementos.append(
        Paragraph(
            "Modelo geral de contrato. Recomenda-se revisar "
            "o documento conforme a situação específica e, "
            "quando necessário, buscar orientação jurídica.",
            estilos["Pequeno"]
        )
    )

    documento.build(
        elementos
    )

    return arquivo


# ================================================================
# PÁGINA HTML
# ================================================================

HTML = """

<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1.0"
>

<title>Proposta Exclusiva 5.0</title>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background: #080808;

    color: white;
}

.container {

    width: 92%;

    max-width: 1150px;

    margin: auto;
}

header {

    padding: 25px 0;

    text-align: center;
}

.logo {

    font-size: 28px;

    font-weight: bold;

    color: #d4af37;
}

.logo span {

    color: white;
}

.hero {

    text-align: center;

    padding:
        20px
        0
        40px;
}

.hero h1 {

    font-size: 36px;

    margin-bottom: 10px;
}

.hero p {

    color: #aaa;

    font-size: 17px;

    line-height: 1.5;
}

.cards {

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(
                210px,
                1fr
            )
        );

    gap: 16px;

    margin-bottom: 35px;
}

.card {

    background: #111;

    border:
        1px solid
        #292929;

    border-radius: 18px;

    padding: 22px;

    transition: .2s;
}

.card:hover {

    transform: translateY(-3px);

    border-color: #d4af37;
}

.card-icon {

    font-size: 37px;
}

.card h2 {

    margin-bottom: 7px;
}

.card p {

    color: #aaa;

    line-height: 1.5;

    min-height: 60px;
}

.formulario {

    background: #111;

    border:
        1px solid
        #292929;

    border-radius: 18px;

    padding: 25px;

    margin-bottom: 30px;
}

.formulario h2 {

    color: #d4af37;

    margin-top: 0;
}

label {

    display: block;

    margin-top: 15px;

    margin-bottom: 7px;

    font-weight: bold;
}

input,
textarea,
select {

    width: 100%;

    padding: 13px;

    border-radius: 9px;

    border:
        1px solid
        #333;

    background: #080808;

    color: white;

    font-size: 15px;
}

textarea {

    min-height: 100px;

    resize: vertical;
}

button {

    width: 100%;

    border: none;

    padding: 14px;

    border-radius: 10px;

    background: #d4af37;

    color: #000;

    font-size: 16px;

    font-weight: bold;

    cursor: pointer;
}

button:hover {

    opacity: .9;
}

.btn {

    margin-top: 22px;
}

.btn-whatsapp {

    background: #25D366;

    color: white;

    margin-top: 10px;
}

.btn-secundario {

    background: #292929;

    color: white;

    margin-top: 10px;
}

.btn-perfil {

    background: #7c5cff;

    color: white;

    margin-top: 10px;
}

.info {

    color: #999;

    font-size: 13px;

    margin-top: 7px;

    line-height: 1.5;
}

.hidden {

    display: none;
}

.dashboard {

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(
                200px,
                1fr
            )
        );

    gap: 15px;

    margin-bottom: 30px;
}

.stat {

    background: #111;

    border:
        1px solid
        #292929;

    border-radius: 15px;

    padding: 20px;

    text-align: center;
}

.stat-number {

    font-size: 30px;

    font-weight: bold;

    color: #d4af37;
}

.stat-label {

    color: #999;

    margin-top: 5px;
}

.history {

    overflow-x: auto;
}

.history table {

    width: 100%;

    border-collapse: collapse;
}

.history th,
.history td {

    border-bottom:
        1px solid
        #292929;

    padding: 12px;

    text-align: left;
}

.history th {

    color: #d4af37;
}

.profile-card {

    background: #111;

    border:
        1px solid
        #292929;

    border-radius: 18px;

    padding: 25px;

    margin-bottom: 30px;
}

.profile-name {

    font-size: 29px;

    font-weight: bold;

    color: #d4af37;
}

.profile-profession {

    color: #ccc;

    font-size: 18px;

    margin-top: 5px;
}

.link-box {

    background: #080808;

    border:
        1px solid
        #292929;

    border-radius: 10px;

    padding: 12px;

    margin-top: 15px;

    word-break: break-all;

    color: #aaa;
}

footer {

    text-align: center;

    color: #777;

    padding: 30px 0;
}

@media(max-width:600px) {

    .hero h1 {

        font-size: 28px;
    }

    .logo {

        font-size: 24px;
    }

    .formulario {

        padding: 18px;
    }

}

</style>

</head>

<body>

<div class="container">

<header>

<div class="logo">

PROPOSTA <span>EXCLUSIVA</span>

</div>

</header>


<section class="hero">

<h1>
Sua vida profissional em um só lugar.
</h1>

<p>
Crie documentos profissionais,
divulgue seu trabalho e compartilhe
seu perfil com clientes.
</p>

</section>


<!-- ========================================================= -->
<!-- DASHBOARD -->
<!-- ========================================================= -->

<div class="dashboard">

<div class="stat">

<div class="stat-number">
5
</div>

<div class="stat-label">
Ferramentas profissionais
</div>

</div>

<div class="stat">

<div class="stat-number">
PDF
</div>

<div class="stat-label">
Documentos profissionais
</div>

</div>

<div class="stat">

<div class="stat-number">
📱
</div>

<div class="stat-label">
WhatsApp
</div>

</div>

<div class="stat">

<div class="stat-number">
🔗
</div>

<div class="stat-label">
Página compartilhável
</div>

</div>

</div>


<!-- ========================================================= -->
<!-- CARDS -->
<!-- ========================================================= -->

<div class="cards">


<div class="card">

<div class="card-icon">
📄
</div>

<h2>
Proposta
</h2>

<p>
Crie uma proposta comercial
profissional em PDF.
</p>

<button onclick="mostrar('proposta')">
CRIAR PROPOSTA
</button>

</div>


<div class="card">

<div class="card-icon">
💼
</div>

<h2>
Currículo
</h2>

<p>
Monte um currículo profissional
em poucos minutos.
</p>

<button onclick="mostrar('curriculo')">
CRIAR CURRÍCULO
</button>

</div>


<div class="card">

<div class="card-icon">
🧾
</div>

<h2>
Orçamento
</h2>

<p>
Calcule materiais, mão de obra,
descontos e total.
</p>

<button onclick="mostrar('orcamento')">
CRIAR ORÇAMENTO
</button>

</div>


<div class="card">

<div class="card-icon">
📝
</div>

<h2>
Contrato
</h2>

<p>
Crie um modelo de contrato
de prestação de serviços.
</p>

<button onclick="mostrar('contrato')">
CRIAR CONTRATO
</button>

</div>


<div class="card">

<div class="card-icon">
📱
</div>

<h2>
WhatsApp
</h2>

<p>
Tenha mensagens profissionais
prontas para seus clientes.
</p>

<button onclick="mostrar('whatsapp')">
VER MENSAGENS
</button>

</div>


<div class="card">

<div class="card-icon">
👤
</div>

<h2>
Meu Perfil
</h2>

<p>
Crie sua apresentação profissional
para compartilhar com clientes.
</p>

<button onclick="mostrar('perfil')">
CRIAR PERFIL
</button>

</div>


<div class="card">

<div class="card-icon">
💳
</div>

<h2>
Cartão Digital
</h2>

<p>
Transforme seu perfil em um
cartão profissional online.
</p>

<button onclick="mostrar('cartao')">
CRIAR CARTÃO
</button>

</div>


<div class="card">

<div class="card-icon">
📚
</div>

<h2>
Histórico
</h2>

<p>
Veja os documentos profissionais
gerados pelo sistema.
</p>

<button onclick="mostrar('historico')">
VER HISTÓRICO
</button>

</div>


</div>


<!-- ========================================================= -->
<!-- PROPOSTA -->
<!-- ========================================================= -->

<div
id="proposta"
class="formulario hidden"
>

<h2>
📄 Criar Proposta
</h2>

<form
method="POST"
action="/gerar-pdf"
>

<label>Seu nome</label>

<input
name="prestador"
required
placeholder="Ex: João da Silva"
>

<label>Profissão</label>

<select name="profissao">

{% for profissao in profissoes %}

<option value="{{ profissao }}">
{{ profissao }}
</option>

{% endfor %}

</select>

<label>Nome do cliente</label>

<input
name="cliente"
required
placeholder="Nome do cliente"
>

<label>Telefone</label>

<input
name="telefone"
placeholder="(77) 99999-9999"
>

<label>Endereço</label>

<input
name="endereco"
placeholder="Endereço do serviço"
>

<label>Descrição do serviço</label>

<textarea
name="descricao"
required
placeholder="Descreva o serviço..."
></textarea>

<label>Valor</label>

<input
name="valor"
placeholder="R$ 1.500,00"
>

<label>Desconto</label>

<input
name="desconto"
placeholder="R$ 0,00"
>

<label>Condições comerciais</label>

<textarea
name="condicoes"
placeholder="Ex: 50% na entrada e 50% na conclusão."
></textarea>

<label>Observações</label>

<textarea
name="observacoes"
placeholder="Informações adicionais..."
></textarea>

<button
class="btn"
type="submit"
>
📄 GERAR PROPOSTA EM PDF
</button>

</form>

</div>


<!-- ========================================================= -->
<!-- CURRÍCULO -->
<!-- ========================================================= -->

<div
id="curriculo"
class="formulario hidden"
>

<h2>
💼 Criar Currículo
</h2>

<form
method="POST"
action="/gerar-curriculo"
>

<label>Nome completo</label>

<input
name="nome"
required
placeholder="Ex: João da Silva"
>

<label>Profissão / Área</label>

<input
name="profissao"
placeholder="Ex: Eletricista"
>

<label>Telefone</label>

<input
name="telefone"
placeholder="(77) 99999-9999"
>

<label>E-mail</label>

<input
name="email"
type="email"
placeholder="seuemail@email.com"
>

<label>Cidade / Estado</label>

<input
name="cidade"
placeholder="Vitória da Conquista - BA"
>

<label>🎯 Objetivo profissional</label>

<textarea
name="objetivo"
placeholder="Busco uma oportunidade..."
></textarea>

<label>👤 Perfil profissional</label>

<textarea
name="resumo"
placeholder="Conte brevemente sobre você..."
></textarea>

<label>💼 Experiência profissional</label>

<textarea
name="experiencia"
placeholder="Empresa — Cargo — Período..."
></textarea>

<label>🎓 Formação acadêmica</label>

<textarea
name="formacao"
placeholder="Ex: Ensino Médio Completo"
></textarea>

<label>📚 Cursos</label>

<textarea
name="cursos"
placeholder="Digite seus cursos..."
></textarea>

<label>⭐ Habilidades</label>

<textarea
name="habilidades"
placeholder="Comunicação, organização, informática..."
></textarea>

<label>🌎 Idiomas</label>

<textarea
name="idiomas"
placeholder="Português — Nativo&#10;Inglês — Básico"
></textarea>

<button
class="btn"
type="submit"
>
💼 GERAR CURRÍCULO EM PDF
</button>

</form>

</div>


<!-- ========================================================= -->
<!-- ORÇAMENTO -->
<!-- ========================================================= -->

<div
id="orcamento"
class="formulario hidden"
>

<h2>
🧾 Criar Orçamento
</h2>

<form
method="POST"
action="/gerar-orcamento"
>

<label>Seu nome</label>

<input
name="prestador"
required
placeholder="Ex: João da Silva"
>

<label>Profissão</label>

<select name="profissao">

{% for profissao in profissoes %}

<option value="{{ profissao }}">
{{ profissao }}
</option>

{% endfor %}

</select>

<label>Nome do cliente</label>

<input
name="cliente"
required
placeholder="Nome do cliente"
>

<label>Telefone</label>

<input
name="telefone"
placeholder="(77) 99999-9999"
>

<label>Endereço</label>

<input
name="endereco"
placeholder="Endereço"
>

<label>Materiais / Serviços</label>

<textarea
name="materiais"
placeholder="Cimento | 10 | 35,00
Tinta | 5 | 80,00
Tomada | 4 | 15,00"
></textarea>

<div class="info">

Formato:
Descrição | Quantidade | Valor unitário

</div>

<label>Mão de obra</label>

<input
name="mao_obra"
placeholder="R$ 1.000,00"
>

<label>Desconto</label>

<input
name="desconto"
placeholder="R$ 0,00"
>

<label>Condições de pagamento</label>

<textarea
name="condicoes"
placeholder="50% na entrada e restante na conclusão."
></textarea>

<label>Observações</label>

<textarea
name="observacoes"
placeholder="Prazo, garantia..."
></textarea>

<button
class="btn"
type="submit"
>
🧾 GERAR ORÇAMENTO EM PDF
</button>

</form>

</div>


<!-- ========================================================= -->
<!-- CONTRATO -->
<!-- ========================================================= -->

<div
id="contrato"
class="formulario hidden"
>

<h2>
📝 Criar Contrato
</h2>

<div class="info">

Modelo geral de contrato de prestação de serviços.
Revise antes de utilizar.

</div>

<form
method="POST"
action="/gerar-contrato"
>

<label>
Nome do prestador
</label>

<input
name="prestador"
required
>

<label>
Telefone do prestador
</label>

<input
name="telefone_prestador"
>

<label>
Nome do cliente
</label>

<input
name="cliente"
required
>

<label>
Telefone do cliente
</label>

<input
name="telefone_cliente"
>

<label>
Endereço do cliente
</label>

<input
name="endereco_cliente"
>

<label>
Serviço contratado
</label>

<textarea
name="servico"
required
placeholder="Descreva o serviço..."
></textarea>

<label>
Valor do contrato
</label>

<input
name="valor"
placeholder="R$ 2.000,00"
>

<label>
Prazo
</label>

<textarea
name="prazo"
placeholder="Ex: 15 dias..."
></textarea>

<label>
Forma de pagamento
</label>

<textarea
name="pagamento"
placeholder="Ex: 50% na contratação..."
></textarea>

<label>
Observações
</label>

<textarea
name="observacoes"
></textarea>

<button
class="btn"
type="submit"
>
📝 GERAR CONTRATO EM PDF
</button>

</form>

</div>


<!-- ========================================================= -->
<!-- WHATSAPP -->
<!-- ========================================================= -->

<div
id="whatsapp"
class="formulario hidden"
>

<h2>
📱 Mensagens Profissionais
</h2>

<label>
Telefone do cliente
</label>

<input
id="numeroWhatsApp"
placeholder="(77) 99999-9999"
>

<label>
Tipo de mensagem
</label>

<select
id="tipoMensagem"
onchange="selecionarMensagem()"
>

<option value="primeiro">
👋 Primeiro contato
</option>

<option value="orcamento">
🧾 Envio de orçamento
</option>

<option value="proposta">
📄 Envio de proposta
</option>

<option value="agendamento">
📅 Confirmação de agendamento
</option>

<option value="pagamento">
💰 Lembrete de pagamento
</option>

<option value="servico">
🔧 Confirmação de serviço
</option>

<option value="posvenda">
⭐ Pós-venda
</option>

<option value="avaliacao">
⭐ Pedido de avaliação
</option>

<option value="personalizada">
✍️ Personalizada
</option>

</select>

<label>
Mensagem
</label>

<textarea
id="mensagemWhatsApp"
></textarea>

<button
class="btn-whatsapp"
onclick="abrirWhatsApp()"
>
📱 ABRIR NO WHATSAPP
</button>

</div>


<!-- ========================================================= -->
<!-- PERFIL -->
<!-- ========================================================= -->

<div
id="perfil"
class="formulario hidden"
>

<h2>
👤 Criar Perfil Profissional
</h2>

<p class="info">
Crie uma apresentação profissional que poderá
ser compartilhada com seus clientes.
</p>

<form
method="POST"
action="/salvar-perfil"
>

<label>
Nome profissional
</label>

<input
name="nome"
required
placeholder="Ex: João da Silva"
>

<label>
Profissão
</label>

<input
name="profissao"
placeholder="Ex: Eletricista"
>

<label>
Telefone
</label>

<input
name="telefone"
placeholder="(77) 99999-9999"
>

<label>
E-mail
</label>

<input
name="email"
type="email"
placeholder="seuemail@email.com"
>

<label>
Cidade
</label>

<input
name="cidade"
placeholder="Vitória da Conquista - BA"
>

<label>
Sobre você
</label>

<textarea
name="descricao"
placeholder="Conte sobre seu trabalho..."
></textarea>

<label>
Habilidades
</label>

<textarea
name="habilidades"
placeholder="Experiência, especialidades..."
></textarea>

<label>
Experiência
</label>

<textarea
name="experiencia"
placeholder="Conte sua experiência profissional..."
></textarea>

<label>
Serviços oferecidos
</label>

<textarea
name="servicos"
placeholder="Instalações, reformas, manutenção..."
></textarea>

<label>
Instagram
</label>

<input
name="instagram"
placeholder="@seuinstagram ou link"
>

<button
class="btn"
type="submit"
>
👤 SALVAR MEU PERFIL
</button>

</form>

</div>


<!-- ========================================================= -->
<!-- CARTÃO DIGITAL -->
<!-- ========================================================= -->

<div
id="cartao"
class="formulario hidden"
>

<h2>
💳 Cartão Digital
</h2>

<p class="info">
Seu cartão digital usa os dados do seu perfil profissional.
Primeiro crie ou atualize seu perfil.
</p>

{% if perfil %}

<div class="profile-card">

<div class="profile-name">
{{ perfil.nome }}
</div>

<div class="profile-profession">
{{ perfil.profissao or "Profissional autônomo" }}
</div>

<p>
{{ perfil.descricao or "Profissional disponível para novos serviços." }}
</p>

{% if perfil.telefone %}

<p>
📱 {{ perfil.telefone }}
</p>

{% endif %}

{% if perfil.cidade %}

<p>
📍 {{ perfil.cidade }}
</p>

{% endif %}

<a
href="/p/{{ perfil.slug }}"
target="_blank"
style="color:#d4af37;"
>
🔗 Ver página pública
</a>

</div>

<div class="link-box">

{{ public_url }}

</div>

<button
class="btn-perfil"
onclick="copiarLink()"
>
🔗 COPIAR LINK DO MEU CARTÃO
</button>

<a
href="/p/{{ perfil.slug }}"
target="_blank"
style="text-decoration:none;"
>
<button
type="button"
class="btn-secundario"
>
👁️ VISUALIZAR CARTÃO
</button>
</a>

{% else %}

<p class="info">
Você ainda não possui um perfil.
Crie seu perfil primeiro.
</p>

<button
onclick="mostrar('perfil')"
>
CRIAR MEU PERFIL
</button>

{% endif %}

</div>


<!-- ========================================================= -->
<!-- HISTÓRICO -->
<!-- ========================================================= -->

<div
id="historico"
class="formulario hidden"
>

<h2>
📚 Histórico de Documentos
</h2>

{% if historico %}

<div class="history">

<table>

<tr>

<th>Tipo</th>

<th>Cliente</th>

<th>Valor</th>

<th>Data</th>

</tr>

{% for item in historico %}

<tr>

<td>
{{ item.tipo }}
</td>

<td>
{{ item.cliente or "-" }}
</td>

<td>
{{ "R$ %.2f"|format(item.valor or 0) }}
</td>

<td>
{{ item.criado_em.strftime("%d/%m/%Y %H:%M") }}
</td>

</tr>

{% endfor %}

</table>

</div>

{% else %}

<p class="info">
Nenhum documento registrado ainda.
Depois de gerar propostas, currículos,
orçamentos ou contratos, eles aparecerão aqui.
</p>

{% endif %}

</div>


<footer>

Proposta Exclusiva © 2026

<br><br>

Propostas • Currículos • Orçamentos • Contratos • WhatsApp

</footer>

</div>


<script>

const mensagens = {

    primeiro:
    "Olá! Tudo bem? Meu nome é [SEU NOME]. Trabalho com [SEU SERVIÇO]. Gostaria de saber se posso ajudar você com seu projeto.",

    orcamento:
    "Olá! Tudo bem? Estou enviando o orçamento referente ao serviço solicitado. Qualquer dúvida, estou à disposição.",

    proposta:
    "Olá! Tudo bem? Preparei sua proposta comercial com os detalhes do serviço. Estou enviando para você analisar. Fico à disposição para qualquer dúvida.",

    agendamento:
    "Olá! Passando para confirmar nosso agendamento para [DATA] às [HORÁRIO]. Qualquer alteração, por favor me avise.",

    pagamento:
    "Olá! Tudo bem? Passando para lembrar sobre o pagamento referente ao serviço realizado. Se precisar de alguma informação, estou à disposição.",

    servico:
    "Olá! Confirmando nosso serviço para [DATA]. Estarei disponível no horário combinado. Obrigado pela confiança!",

    posvenda:
    "Olá! Tudo bem? Gostaria de saber se ficou tudo certo com o serviço realizado. Espero que tenha ficado satisfeito!",

    avaliacao:
    "Olá! Tudo bem? Se você ficou satisfeito com meu trabalho, poderia deixar uma avaliação? Sua opinião é muito importante para o meu trabalho. Muito obrigado!",

    personalizada:
    ""

};


function selecionarMensagem() {

    const tipo =
        document.getElementById(
            "tipoMensagem"
        ).value;

    document.getElementById(
        "mensagemWhatsApp"
    ).value = mensagens[tipo];

}


function abrirWhatsApp() {

    let numero =
        document.getElementById(
            "numeroWhatsApp"
        ).value;

    let mensagem =
        document.getElementById(
            "mensagemWhatsApp"
        ).value;

    numero =
        numero.replace(
            /\\D/g,
            ""
        );

    if (
        numero.length === 10 ||
        numero.length === 11
    ) {

        numero = "55" + numero;

    }

    if (!numero) {

        alert(
            "Digite o telefone do cliente."
        );

        return;
    }

    if (!mensagem) {

        alert(
            "Digite uma mensagem."
        );

        return;
    }

    const url =
        "https://wa.me/"
        + numero
        + "?text="
        + encodeURIComponent(
            mensagem
        );

    window.open(
        url,
        "_blank"
    );

}


function mostrar(id) {

    const formularios = [

        "proposta",
        "curriculo",
        "orcamento",
        "contrato",
        "whatsapp",
        "perfil",
        "cartao",
        "historico"

    ];

    formularios.forEach(
        function(nome) {

            const elemento =
                document.getElementById(
                    nome
                );

            if (elemento) {

                elemento.classList.add(
                    "hidden"
                );

            }

        }
    );

    const destino =
        document.getElementById(
            id
        );

    if (destino) {

        destino.classList.remove(
            "hidden"
        );

        destino.scrollIntoView({
            behavior: "smooth"
        });

    }

}


function copiarLink() {

    const texto =
        document.querySelector(
            ".link-box"
        ).innerText;

    navigator.clipboard.writeText(
        texto
    ).then(
        function() {

            alert(
                "Link copiado!"
            );

        }
    );

}


selecionarMensagem();

</script>


</body>

</html>

"""


# ================================================================
# ROTA PRINCIPAL
# ================================================================

@app.route("/")
def home():

    perfil = UserProfile.query.first()

    historico = DocumentHistory.query.order_by(
        DocumentHistory.criado_em.desc()
    ).limit(50).all()

    public_url = ""

    if perfil:

        public_url = request.host_url.rstrip(
            "/"
        ) + "/p/" + perfil.slug

    return render_template_string(

        HTML,

        profissoes=PROFISSOES,

        perfil=perfil,

        historico=historico,

        public_url=public_url

    )


# ================================================================
# PROPOSTA
# ================================================================

@app.route(
    "/gerar-pdf",
    methods=["POST"]
)
def gerar_pdf():

    dados = {

        "prestador":
        request.form.get(
            "prestador",
            ""
        ),

        "profissao":
        request.form.get(
            "profissao",
            ""
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
        request.form.get(
            "valor",
            ""
        ),

        "desconto":
        request.form.get(
            "desconto",
            ""
        ),

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

    valor = dinheiro(
        dados["valor"]
    )

    desconto = dinheiro(
        dados["desconto"]
    )

    total = max(
        valor - desconto,
        0
    )

    registrar_documento(

        "Proposta",

        dados["cliente"],

        dados["descricao"],

        total

    )

    arquivo = criar_pdf_proposta(
        dados
    )

    return send_file(

        arquivo,

        as_attachment=True,

        download_name=
        "proposta-profissional.pdf",

        mimetype=
        "application/pdf"

    )


# ================================================================
# CURRÍCULO
# ================================================================

@app.route(
    "/gerar-curriculo",
    methods=["POST"]
)
def gerar_curriculo():

    dados = {

        "nome":
        request.form.get(
            "nome",
            ""
        ),

        "profissao":
        request.form.get(
            "profissao",
            ""
        ),

        "telefone":
        request.form.get(
            "telefone",
            ""
        ),

        "email":
        request.form.get(
            "email",
            ""
        ),

        "cidade":
        request.form.get(
            "cidade",
            ""
        ),

        "objetivo":
        request.form.get(
            "objetivo",
            ""
        ),

        "resumo":
        request.form.get(
            "resumo",
            ""
        ),

        "experiencia":
        request.form.get(
            "experiencia",
            ""
        ),

        "formacao":
        request.form.get(
            "formacao",
            ""
        ),

        "cursos":
        request.form.get(
            "cursos",
            ""
        ),

        "habilidades":
        request.form.get(
            "habilidades",
            ""
        ),

        "idiomas":
        request.form.get(
            "idiomas",
            ""
        )

    }

    registrar_documento(

        "Currículo",

        dados["nome"],

        dados["profissao"],

        0

    )

    arquivo = criar_pdf_curriculo(
        dados
    )

    return send_file(

        arquivo,

        as_attachment=True,

        download_name=
        "curriculo-profissional.pdf",

        mimetype=
        "application/pdf"

    )


# ================================================================
# ORÇAMENTO
# ================================================================

@app.route(
    "/gerar-orcamento",
    methods=["POST"]
)
def gerar_orcamento():

    dados = {

        "prestador":
        request.form.get(
            "prestador",
            ""
        ),

        "profissao":
        request.form.get(
            "profissao",
            ""
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

        "materiais":
        request.form.get(
            "materiais",
            ""
        ),

        "mao_obra":
        request.form.get(
            "mao_obra",
            ""
        ),

        "desconto":
        request.form.get(
            "desconto",
            ""
        ),

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

    total_materiais = 0.0

    for linha in dados["materiais"].splitlines():

        partes = linha.split("|")

        if len(partes) >= 3:

            quantidade = dinheiro(
                partes[1]
            )

            valor_unitario = dinheiro(
                partes[2]
            )

            total_materiais += (
                quantidade *
                valor_unitario
            )

    mao_obra = dinheiro(
        dados["mao_obra"]
    )

    desconto = dinheiro(
        dados["desconto"]
    )

    total = max(
        total_materiais
        + mao_obra
        - desconto,
        0
    )

    registrar_documento(

        "Orçamento",

        dados["cliente"],

        dados["observacoes"],

        total

    )

    arquivo = criar_pdf_orcamento(
        dados
    )

    return send_file(

        arquivo,

        as_attachment=True,

        download_name=
        "orcamento-profissional.pdf",

        mimetype=
        "application/pdf"

    )


# ================================================================
# CONTRATO
# ================================================================

@app.route(
    "/gerar-contrato",
    methods=["POST"]
)
def gerar_contrato():

    dados = {

        "prestador":
        request.form.get(
            "prestador",
            ""
        ),

        "telefone_prestador":
        request.form.get(
            "telefone_prestador",
            ""
        ),

        "cliente":
        request.form.get(
            "cliente",
            ""
        ),

        "telefone_cliente":
        request.form.get(
            "telefone_cliente",
            ""
        ),

        "endereco_cliente":
        request.form.get(
            "endereco_cliente",
            ""
        ),

        "servico":
        request.form.get(
            "servico",
            ""
        ),

        "valor":
        request.form.get(
            "valor",
            ""
        ),

        "prazo":
        request.form.get(
            "prazo",
            ""
        ),

        "pagamento":
        request.form.get(
            "pagamento",
            ""
        ),

        "observacoes":
        request.form.get(
            "observacoes",
            ""
        )

    }

    valor = dinheiro(
        dados["valor"]
    )

    registrar_documento(

        "Contrato",

        dados["cliente"],

        dados["servico"],

        valor

    )

    arquivo = criar_pdf_contrato(
        dados
    )

    return send_file(

        arquivo,

        as_attachment=True,

        download_name=
        "contrato-prestacao-servicos.pdf",

        mimetype=
        "application/pdf"

    )


# ================================================================
# SALVAR PERFIL
# ================================================================

@app.route(
    "/salvar-perfil",
    methods=["POST"]
)
def salvar_perfil():

    nome = request.form.get(
        "nome",
        ""
    ).strip()

    if not nome:

        return redirect(
            url_for("home")
        )

    perfil = UserProfile.query.first()

    if perfil is None:

        perfil = UserProfile(

            slug=criar_slug(nome),

            nome=nome

        )

        db.session.add(
            perfil
        )

    perfil.nome = nome

    perfil.profissao = request.form.get(
        "profissao",
        ""
    )

    perfil.telefone = request.form.get(
        "telefone",
        ""
    )

    perfil.email = request.form.get(
        "email",
        ""
    )

    perfil.cidade = request.form.get(
        "cidade",
        ""
    )

    perfil.descricao = request.form.get(
        "descricao",
        ""
    )

    perfil.habilidades = request.form.get(
        "habilidades",
        ""
    )

    perfil.experiencia = request.form.get(
        "experiencia",
        ""
    )

    perfil.servicos = request.form.get(
        "servicos",
        ""
    )

    perfil.instagram = request.form.get(
        "instagram",
        ""
    )

    db.session.commit()

    return redirect(
        url_for("home")
        + "#cartao"
    )


# ================================================================
# PÁGINA PROFISSIONAL PÚBLICA
# ================================================================

@app.route(
    "/p/<slug>"
)
def pagina_publica(slug):

    perfil = UserProfile.query.filter_by(
        slug=slug
    ).first_or_404()

    whatsapp = telefone_whatsapp(
        perfil.telefone
    )

    mensagem = quote(
        "Olá! Vi seu perfil profissional e gostaria de saber mais sobre seus serviços."
    )

    whatsapp_url = ""

    if whatsapp:

        whatsapp_url = (
            "https://wa.me/"
            + whatsapp
            + "?text="
            + mensagem
        )

    return render_template_string(
        """

<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1.0"
>

<title>
{{ perfil.nome }} - Perfil Profissional
</title>

<style>

body {

    margin: 0;

    background: #080808;

    color: white;

    font-family: Arial, sans-serif;

}

.box {

    width: 90%;

    max-width: 650px;

    margin: 40px auto;

}

.card {

    background: #111;

    border:
        1px solid
        #292929;

    border-radius: 22px;

    padding: 30px;

    text-align: center;

}

.nome {

    color: #d4af37;

    font-size: 32px;

    font-weight: bold;

}

.profissao {

    color: #ddd;

    font-size: 19px;

    margin-top: 8px;

}

.secao {

    text-align: left;

    margin-top: 25px;

    border-top:
        1px solid
        #292929;

    padding-top: 20px;

}

.secao h3 {

    color: #d4af37;

}

.botao {

    display: block;

    text-decoration: none;

    padding: 15px;

    border-radius: 10px;

    margin-top: 12px;

    background: #d4af37;

    color: #000;

    font-weight: bold;

}

.whatsapp {

    background: #25D366;

    color: white;

}

.info {

    color: #aaa;

    line-height: 1.6;

}

footer {

    text-align: center;

    color: #666;

    margin-top: 25px;

}

</style>

</head>

<body>

<div class="box">

<div class="card">

<div class="nome">

{{ perfil.nome }}

</div>

<div class="profissao">

{{ perfil.profissao or "Profissional autônomo" }}

</div>


{% if perfil.cidade %}

<p class="info">
📍 {{ perfil.cidade }}
</p>

{% endif %}


{% if perfil.descricao %}

<div class="secao">

<h3>
Sobre mim
</h3>

<p class="info">
{{ perfil.descricao }}
</p>

</div>

{% endif %}


{% if perfil.servicos %}

<div class="secao">

<h3>
Serviços
</h3>

<p class="info">
{{ perfil.servicos }}
</p>

</div>

{% endif %}


{% if perfil.habilidades %}

<div class="secao">

<h3>
Habilidades
</h3>

<p class="info">
{{ perfil.habilidades }}
</p>

</div>

{% endif %}


{% if perfil.experiencia %}

<div class="secao">

<h3>
Experiência
</h3>

<p class="info">
{{ perfil.experiencia }}
</p>

</div>

{% endif %}


{% if perfil.email %}

<a
class="botao"
href="mailto:{{ perfil.email }}"
>
📧 ENVIAR E-MAIL
</a>

{% endif %}


{% if whatsapp_url %}

<a
class="botao whatsapp"
href="{{ whatsapp_url }}"
target="_blank"
>
📱 FALAR PELO WHATSAPP
</a>

{% endif %}


{% if perfil.instagram %}

<a
class="botao"
href="{{ perfil.instagram }}"
target="_blank"
>
📸 INSTAGRAM
</a>

{% endif %}


<footer>

Proposta Exclusiva

</footer>

</div>

</div>

</body>

</html>

""",
        perfil=perfil,
        whatsapp_url=whatsapp_url
    )


# ================================================================
# WHATSAPP
# ================================================================

@app.route(
    "/whatsapp",
    methods=["POST"]
)
def whatsapp():

    numero = request.form.get(
        "telefone",
        ""
    )

    mensagem = request.form.get(
        "mensagem",
        ""
    )

    numero = telefone_whatsapp(
        numero
    )

    if not numero:

        return (
            "Telefone inválido.",
            400
        )

    url = (
        "https://wa.me/"
        + numero
        + "?text="
        + quote(mensagem)
    )

    return redirect(
        url
    )


# ================================================================
# HEALTH CHECK
# ================================================================

@app.route(
    "/health"
)
def health():

    return {

        "status": "ok",

        "app":
        "Proposta Exclusiva",

        "version":
        "5.0"

    }


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
