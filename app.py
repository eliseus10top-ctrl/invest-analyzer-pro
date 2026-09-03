from flask import Flask, request, render_template_string, send_file, redirect, flash
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from io import BytesIO
from datetime import datetime
from urllib.parse import quote
import re
import os
import html

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "proposta-exclusiva-secret")

# ============================================================
# INTERFACE WEB — VISUAL PREMIUM / LUXO
# ============================================================

HTML = """
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#111111">
<title>Proposta Exclusiva — Propostas Premium</title>
<style>
*{box-sizing:border-box}
:root{
  --black:#111111;
  --black2:#1c1c1c;
  --gold:#b08d57;
  --gold2:#d6b77a;
  --gold-light:#f7f1e5;
  --ink:#171717;
  --muted:#737373;
  --line:#e5e0d7;
  --bg:#f4f2ee;
  --card:#fff;
}
html{scroll-behavior:smooth}
body{
  margin:0;
  background:
    radial-gradient(circle at 8% 0%,rgba(176,141,87,.13),transparent 30%),
    radial-gradient(circle at 95% 10%,rgba(17,17,17,.07),transparent 28%),
    var(--bg);
  color:var(--ink);
  font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
}
.container{max-width:1040px;margin:auto;padding:18px 14px 48px}
.card{
  background:var(--card);
  border:1px solid rgba(17,17,17,.07);
  border-radius:30px;
  overflow:hidden;
  box-shadow:0 25px 80px rgba(17,17,17,.13);
}
.hero{
  position:relative;
  overflow:hidden;
  padding:31px 30px 34px;
  color:#fff;
  background:
    radial-gradient(circle at 92% -10%,rgba(214,183,122,.30),transparent 32%),
    radial-gradient(circle at 0% 100%,rgba(176,141,87,.13),transparent 34%),
    linear-gradient(135deg,#0b0b0b,#171717 60%,#24201a);
  border-bottom:1px solid rgba(214,183,122,.35);
}
.hero:before{
  content:"";
  position:absolute;
  width:290px;height:290px;
  border:1px solid rgba(214,183,122,.12);
  border-radius:50%;
  right:-145px;top:-175px;
}
.hero:after{
  content:"";
  position:absolute;
  width:170px;height:170px;
  border:1px solid rgba(214,183,122,.08);
  border-radius:50%;
  right:-70px;bottom:-105px;
}
.brand{display:flex;align-items:center;gap:15px;position:relative;z-index:1}
.logo{
  width:58px;height:58px;border-radius:18px;
  display:flex;align-items:center;justify-content:center;
  font-weight:950;font-size:20px;letter-spacing:.5px;
  color:#f7f1e5;
  background:linear-gradient(145deg,#242424,#101010);
  border:1px solid rgba(214,183,122,.55);
  box-shadow:0 12px 30px rgba(0,0,0,.30),inset 0 0 0 1px rgba(255,255,255,.04);
}
.hero h1{margin:0;font-size:30px;letter-spacing:-1px}
.hero p{margin:7px 0 0;color:#d8d4cb;font-size:14px;line-height:1.45}
.hero-badges{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}
.badge{
  font-size:11px;font-weight:800;color:#efe6d6;
  padding:7px 10px;border-radius:999px;
  background:rgba(176,141,87,.13);
  border:1px solid rgba(214,183,122,.25);
}
.body{padding:30px}
.progress{
  display:flex;gap:7px;align-items:center;margin:0 0 28px;
  color:#8a847b;font-size:11px;font-weight:800;
}
.progress span{height:5px;flex:1;border-radius:99px;background:#ece9e3}
.progress span.active{background:linear-gradient(90deg,var(--gold),var(--gold2))}
.section{
  padding:0 0 28px;margin-bottom:28px;
  border-bottom:1px solid var(--line);
}
.section:last-of-type{border-bottom:0;margin-bottom:0}
.section-title{
  display:flex;align-items:center;gap:11px;
  margin:0 0 18px;font-size:18px;letter-spacing:-.35px;
}
.num{
  width:32px;height:32px;border-radius:11px;
  background:linear-gradient(135deg,#f8f2e7,#eee5d6);
  color:#8b6a38;
  display:flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:950;
  box-shadow:inset 0 0 0 1px #e1d2b9;
}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.full{grid-column:1/-1}
.field{min-width:0}
label{
  display:block;font-size:12px;font-weight:850;
  color:#393939;margin:0 0 7px;
}
input,textarea,select{
  width:100%;padding:14px 15px;
  border:1px solid #d9d5ce;border-radius:13px;
  background:#fff;color:#171717;font-size:15px;
  outline:none;transition:.18s;
  box-shadow:0 1px 2px rgba(16,24,40,.02);
}
input:hover,textarea:hover{border-color:#b9aa90}
input:focus,textarea:focus,select:focus{
  border-color:#b08d57;
  box-shadow:0 0 0 4px rgba(176,141,87,.12);
}
textarea{min-height:105px;resize:vertical;line-height:1.5}
.helper{font-size:11px;color:#928c83;margin-top:6px;line-height:1.4}
.value-wrap{position:relative}
.value-wrap span{
  position:absolute;left:14px;top:50%;
  transform:translateY(-50%);
  font-size:12px;font-weight:850;color:#756f67;
}
.value-wrap input{padding-left:42px}
.actions{
  display:grid;grid-template-columns:1fr 1fr;
  gap:12px;margin-top:4px;
}
button{
  border:0;border-radius:14px;padding:15px 18px;
  font-size:14px;font-weight:850;cursor:pointer;
  transition:.18s;
}
.primary{
  background:linear-gradient(135deg,#171717,#29241d);
  color:#f5ead8;
  border:1px solid #b08d57;
  box-shadow:0 12px 25px rgba(17,17,17,.18);
}
.secondary{
  background:#fff;color:#3b3833;border:1px solid #d8d0c2;
}
button:hover{transform:translateY(-1px);box-shadow:0 12px 24px rgba(16,24,40,.12)}
.note{
  margin-top:13px;color:#777169;font-size:11px;
  line-height:1.55;text-align:center;
}
.flash{
  background:#fff1f0;border:1px solid #f0c9c4;
  color:#8d2f25;padding:14px 15px;border-radius:14px;
  margin-bottom:20px;font-size:13px;line-height:1.5;
}
.tip{
  display:flex;gap:10px;align-items:flex-start;
  padding:13px 14px;border-radius:14px;
  background:#faf7f0;border:1px solid #eadfcf;
  color:#625c54;font-size:11px;line-height:1.5;
  margin-top:14px;
}
.tip strong{color:#735628}
.footer-note{text-align:center;color:#918b82;font-size:11px;margin-top:18px}
@media(max-width:700px){
  .container{padding:8px 7px 28px}
  .card{border-radius:23px}
  .hero{padding:24px 19px 27px}
  .hero h1{font-size:26px}
  .hero p{font-size:13px}
  .body{padding:22px 17px}
  .grid{grid-template-columns:1fr}
  .full{grid-column:auto}
  .actions{grid-template-columns:1fr}
}
</style>
</head>
<body>
<div class="container">
<div class="card">
  <div class="hero">
    <div class="brand">
      <div class="logo">PE</div>
      <div>
        <h1>Proposta Exclusiva</h1>
        <p>Crie propostas sofisticadas, claras e prontas para impressionar seus clientes.</p>
      </div>
    </div>
    <div class="hero-badges">
      <span class="badge">✦ PDF Premium</span>
      <span class="badge">◉ WhatsApp</span>
      <span class="badge">✓ Cálculo automático</span>
    </div>
  </div>

  <div class="body">
  {% with messages = get_flashed_messages() %}
    {% if messages %}<div class="flash">⚠ {{ messages[0] }}</div>{% endif %}
  {% endwith %}

  <div class="progress">
    <span class="active"></span><span class="active"></span><span class="active"></span><span class="active"></span>
    <b>Proposta completa</b>
  </div>

  <form method="post" action="/gerar-pdf" id="orcamentoForm">

    <div class="section">
      <h2 class="section-title"><span class="num">01</span> Sua empresa</h2>
      <div class="grid">
        <div class="field">
          <label>Nome da empresa *</label>
          <input name="empresa" required value="{{ data.get('empresa','') }}" placeholder="Ex.: Luana Serviços">
        </div>
        <div class="field">
          <label>Telefone / WhatsApp</label>
          <input name="empresa_whatsapp" value="{{ data.get('empresa_whatsapp','') }}" placeholder="(77) 99999-9999">
        </div>
        <div class="field">
          <label>E-mail</label>
          <input type="email" name="empresa_email" value="{{ data.get('empresa_email','') }}" placeholder="contato@empresa.com">
        </div>
        <div class="field">
          <label>Cidade / Estado</label>
          <input name="empresa_local" value="{{ data.get('empresa_local','') }}" placeholder="Vitória da Conquista - BA">
        </div>
        <div class="field full">
          <label>CPF / CNPJ <span style="font-weight:500;color:#98a2b3">(opcional)</span></label>
          <input name="empresa_doc" value="{{ data.get('empresa_doc','') }}" placeholder="00.000.000/0001-00">
        </div>
      </div>
    </div>

    <div class="section">
      <h2 class="section-title"><span class="num">02</span> Cliente</h2>
      <div class="grid">
        <div class="field">
          <label>Nome do cliente *</label>
          <input name="cliente" required value="{{ data.get('cliente','') }}" placeholder="Nome completo">
        </div>
        <div class="field">
          <label>WhatsApp do cliente</label>
          <input name="whatsapp" value="{{ data.get('whatsapp','') }}" placeholder="(77) 98888-8888">
        </div>
        <div class="field full">
          <label>Endereço</label>
          <input name="endereco" value="{{ data.get('endereco','') }}" placeholder="Rua, número, bairro, cidade">
        </div>
      </div>
    </div>

    <div class="section">
      <h2 class="section-title"><span class="num">03</span> Serviço e valores</h2>
      <div class="grid">
        <div class="field full">
          <label>Serviço / proposta *</label>
          <input name="servico" required value="{{ data.get('servico','') }}" placeholder="Ex.: Instalação e manutenção de porta">
        </div>
        <div class="field full">
          <label>Descrição detalhada</label>
          <textarea name="descricao" maxlength="900" placeholder="Explique claramente o que será realizado...">{{ data.get('descricao','') }}</textarea>
        </div>
        <div class="field">
          <label>Valor do serviço *</label>
          <div class="value-wrap"><span>R$</span><input id="valor" name="valor" required inputmode="decimal" value="{{ data.get('valor','') }}" placeholder="230,00"></div>
          <div class="helper">Aceita 230,00 ou 230.00</div>
        </div>
        <div class="field">
          <label>Desconto (opcional)</label>
          <div class="value-wrap"><span>R$</span><input id="desconto" name="desconto" inputmode="decimal" value="{{ data.get('desconto','') }}" placeholder="0,00"></div>
        </div>
        <div class="field">
          <label>Prazo de execução</label>
          <input name="prazo" value="{{ data.get('prazo','') }}" placeholder="2 dias úteis">
        </div>
        <div class="field">
          <label>Validade da proposta</label>
          <input name="validade" value="{{ data.get('validade','7 dias') }}" placeholder="7 dias">
        </div>
        <div class="field">
          <label>Forma de pagamento</label>
          <input name="pagamento" value="{{ data.get('pagamento','') }}" placeholder="50% na aprovação + 50% na entrega">
        </div>
        <div class="field">
          <label>Garantia</label>
          <input name="garantia" value="{{ data.get('garantia','') }}" placeholder="90 dias">
        </div>
      </div>

      <div class="tip">
        <div>✦</div>
        <div><strong>Importante:</strong> escreva livremente nos campos de serviço e descrição. O campo Valor aceita somente números e valores monetários.</div>
      </div>
    </div>

    <div class="section">
      <h2 class="section-title"><span class="num">04</span> Observações</h2>
      <textarea name="observacoes" maxlength="700" placeholder="Materiais, condições, garantia, horários ou informações importantes...">{{ data.get('observacoes','') }}</textarea>
      <div class="helper">As observações aparecem no PDF e ajudam a deixar a proposta mais clara.</div>
    </div>

    <div class="actions">
      <button class="primary" type="submit">✦ Gerar Proposta Exclusiva</button>
      <button class="secondary" type="button" onclick="enviarWhatsApp()">◉ Enviar pelo WhatsApp</button>
    </div>

    <div class="note">
      Sua proposta recebe número, data, dados do cliente, serviço, valores, condições, garantia, observações e área de aprovação.
    </div>
  </form>
  </div>
</div>
<div class="footer-note">Proposta Exclusiva • apresentação premium para o seu cliente.</div>
</div>

<script>
function enviarWhatsApp(){
  const f=document.getElementById('orcamentoForm');
  if(!f.reportValidity()) return;
  const old=f.action;
  f.action='/whatsapp';
  f.submit();
  f.action=old;
}
</script>
</body>
</html>
"""

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def clean_phone(phone):
    return re.sub(r"\D", "", phone or "")


def parse_money(value, field_name="Valor"):
    """
    Aceita:
      230
      230,00
      230.00
      R$ 230,00
      1.230,50
      1,230.50
    """
    raw = str(value or "").strip()
    if not raw:
        return 0.0

    raw = raw.replace("R$", "").replace("r$", "").replace(" ", "")

    if not re.fullmatch(r"[0-9.,]+", raw):
        raise ValueError(
            f"O campo '{field_name}' deve conter apenas números. "
            f"Exemplo: 230,00."
        )

    try:
        if "," in raw and "." in raw:
            if raw.rfind(",") > raw.rfind("."):
                normalized = raw.replace(".", "").replace(",", ".")
            else:
                normalized = raw.replace(",", "")
        elif "," in raw:
            normalized = raw.replace(".", "").replace(",", ".")
        else:
            if raw.count(".") > 1:
                normalized = raw.replace(".", "")
            else:
                normalized = raw

        number = float(normalized)

        if number < 0:
            raise ValueError(
                f"O campo '{field_name}' não pode ser negativo."
            )

        return number

    except (ValueError, TypeError):
        raise ValueError(
            f"O campo '{field_name}' contém um valor inválido: '{raw}'. "
            f"Use, por exemplo, 230,00."
        )


def money_br(value):
    return (
        f"R$ {float(value):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def pdf_text(value):
    return html.escape(
        str(value or ""), quote=False
    ).replace("\n", "<br/>")


def short(value, max_chars=900):
    value = str(value or "").strip()
    if len(value) <= max_chars:
        return value
    return value[:max_chars-3].rstrip() + "..."


# ============================================================
# PDF PREMIUM / LUXO — PRETO + DOURADO
# ============================================================

def generate_pdf(data):
    buffer = BytesIO()

    numero = datetime.now().strftime("%Y%m%d-%H%M%S")
    data_emissao = datetime.now().strftime("%d/%m/%Y")

    valor = parse_money(data.get("valor"), "Valor do serviço")
    desconto = (
        parse_money(data.get("desconto"), "Desconto")
        if data.get("desconto")
        else 0.0
    )

    if desconto > valor:
        raise ValueError(
            "O desconto não pode ser maior que o valor do serviço."
        )

    total = max(0.0, valor - desconto)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=12*mm,
        leftMargin=12*mm,
        topMargin=10*mm,
        bottomMargin=12*mm,
        title=f"Proposta Exclusiva {numero}",
        author=data.get("empresa", "")
    )

    styles = getSampleStyleSheet()

    # --------------------------------------------------------
    # ESTILOS
    # --------------------------------------------------------

    styles.add(ParagraphStyle(
        name="BrandPro",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=23,
        leading=25,
        textColor=colors.white,
        alignment=TA_LEFT,
        spaceAfter=2
    ))

    styles.add(ParagraphStyle(
        name="TinyPro",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.1,
        leading=9.1,
        textColor=colors.HexColor("#D6D1C8")
    ))

    styles.add(ParagraphStyle(
        name="LabelPro",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.1,
        leading=8.8,
        textColor=colors.HexColor("#6D665C")
    ))

    styles.add(ParagraphStyle(
        name="BodyPro",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.3,
        leading=11.0,
        textColor=colors.HexColor("#34312D")
    ))

    styles.add(ParagraphStyle(
        name="SectionPro",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=9.3,
        leading=11,
        textColor=colors.HexColor("#171717"),
        spaceBefore=2,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        name="BigValuePro",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=24,
        textColor=colors.white,
        alignment=TA_RIGHT
    ))

    styles.add(ParagraphStyle(
        name="CenterPro",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.1,
        leading=8.8,
        textColor=colors.HexColor("#737373"),
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        name="CenterBoldPro",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.0,
        textColor=colors.HexColor("#171717"),
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        name="GoldCenter",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.4,
        leading=9,
        textColor=colors.HexColor("#8A6837"),
        alignment=TA_CENTER
    ))

    # --------------------------------------------------------
    # PALETA
    # --------------------------------------------------------

    black = colors.HexColor("#111111")
    black_soft = colors.HexColor("#1C1C1C")
    gold = colors.HexColor("#B08D57")
    gold_light = colors.HexColor("#D6B77A")
    cream = colors.HexColor("#FAF8F3")
    light_gold = colors.HexColor("#F7F1E5")
    border = colors.HexColor("#D8D0C2")
    soft = colors.HexColor("#F8F7F4")
    gray = colors.HexColor("#737373")
    dark = colors.HexColor("#171717")

    story = []

    # --------------------------------------------------------
    # CABEÇALHO PREMIUM
    # --------------------------------------------------------

    company = pdf_text(data.get("empresa") or "EMPRESA")

    contact_parts = [
        data.get("empresa_whatsapp"),
        data.get("empresa_email"),
        data.get("empresa_local"),
        data.get("empresa_doc")
    ]

    contact = "<br/>".join(
        pdf_text(x) for x in contact_parts
        if str(x or "").strip()
    )

    badge = Table(
        [[
            Paragraph(
                "<b>PROPOSTA<br/>EXCLUSIVA</b>",
                styles["CenterBoldPro"]
            )
        ]],
        colWidths=[34*mm],
        rowHeights=[16*mm]
    )

    badge.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), light_gold),
        ("BOX", (0,0), (-1,-1), 0.9, gold),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 3),
        ("RIGHTPADDING", (0,0), (-1,-1), 3),
    ]))

    header_left = [
        Paragraph(company, styles["BrandPro"]),
        Paragraph(
            f"Proposta nº <b>{numero}</b> &nbsp; • &nbsp; Emitida em {data_emissao}",
            styles["TinyPro"]
        )
    ]

    header = Table(
        [[
            header_left,
            Paragraph(contact or " ", styles["TinyPro"]),
            badge
        ]],
        colWidths=[88*mm, 52*mm, 34*mm]
    )

    header.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), black),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (1,0), (1,0), "RIGHT"),
        ("ALIGN", (2,0), (2,0), "RIGHT"),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 9),
        ("BOTTOMPADDING", (0,0), (-1,-1), 9),
        ("BOX", (0,0), (-1,-1), 0.8, gold),
    ]))

    story += [
        header,
        Spacer(1, 1.8*mm),
        HRFlowable(
            width="100%",
            thickness=1.3,
            color=gold
        ),
        Spacer(1, 2.6*mm)
    ]

    # --------------------------------------------------------
    # DADOS DO CLIENTE
    # --------------------------------------------------------

    story.append(
        Paragraph("DADOS DO CLIENTE", styles["SectionPro"])
    )

    cliente_table = Table([
        [
            Paragraph("CLIENTE", styles["LabelPro"]),
            Paragraph("WHATSAPP", styles["LabelPro"])
        ],
        [
            Paragraph(
                pdf_text(data.get("cliente")),
                styles["BodyPro"]
            ),
            Paragraph(
                pdf_text(data.get("whatsapp")) or "Não informado",
                styles["BodyPro"]
            )
        ],
        [
            Paragraph("ENDEREÇO", styles["LabelPro"]),
            ""
        ],
        [
            Paragraph(
                pdf_text(data.get("endereco"))
                or "Não informado",
                styles["BodyPro"]
            ),
            ""
        ]
    ], colWidths=[111*mm, 63*mm])

    cliente_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), soft),
        ("SPAN", (0,2), (-1,2)),
        ("SPAN", (0,3), (-1,3)),
        ("BOX", (0,0), (-1,-1), 0.55, border),
        ("INNERGRID", (0,0), (-1,1), 0.35, colors.HexColor("#E8E3DA")),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))

    story += [
        cliente_table,
        Spacer(1, 2.2*mm)
    ]

    # --------------------------------------------------------
    # SERVIÇO
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "SERVIÇO / ESCOPO DA PROPOSTA",
            styles["SectionPro"]
        )
    )

    service_table = Table([
        [
            Paragraph("SERVIÇO", styles["LabelPro"]),
            Paragraph("PRAZO", styles["LabelPro"]),
            Paragraph("GARANTIA", styles["LabelPro"])
        ],
        [
            Paragraph(
                pdf_text(data.get("servico")),
                styles["BodyPro"]
            ),
            Paragraph(
                pdf_text(data.get("prazo")) or "A combinar",
                styles["BodyPro"]
            ),
            Paragraph(
                pdf_text(data.get("garantia")) or "A combinar",
                styles["BodyPro"]
            )
        ],
        [
            Paragraph("DESCRIÇÃO", styles["LabelPro"]),
            "",
            ""
        ],
        [
            Paragraph(
                pdf_text(short(data.get("descricao"), 700))
                or "Sem descrição adicional.",
                styles["BodyPro"]
            ),
            "",
            ""
        ]
    ], colWidths=[92*mm, 41*mm, 41*mm])

    service_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), soft),
        ("SPAN", (0,2), (-1,2)),
        ("SPAN", (0,3), (-1,3)),
        ("BOX", (0,0), (-1,-1), 0.55, border),
        ("INNERGRID", (0,0), (-1,1), 0.35, colors.HexColor("#E8E3DA")),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))

    story += [
        service_table,
        Spacer(1, 2.2*mm)
    ]

    # --------------------------------------------------------
    # RESUMO FINANCEIRO
    # --------------------------------------------------------

    story.append(
        Paragraph("RESUMO FINANCEIRO", styles["SectionPro"])
    )

    finance = Table([
        [
            Paragraph("VALOR DO SERVIÇO", styles["LabelPro"]),
            Paragraph(money_br(valor), styles["BodyPro"])
        ],
        [
            Paragraph("DESCONTO", styles["LabelPro"]),
            Paragraph(money_br(desconto), styles["BodyPro"])
        ],
        [
            Paragraph(
                "<b>TOTAL DA PROPOSTA</b>",
                styles["LabelPro"]
            ),
            Paragraph(
                money_br(total),
                styles["BigValuePro"]
            )
        ]
    ], colWidths=[105*mm, 69*mm])

    finance.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,1), cream),
        ("BACKGROUND", (0,2), (-1,2), black),
        ("BOX", (0,0), (-1,-1), 1.0, gold),
        ("LINEABOVE", (0,2), (-1,2), 1.2, gold),
        ("TEXTCOLOR", (0,2), (0,2), gold_light),
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))

    story += [
        finance,
        Spacer(1, 2.2*mm)
    ]

    # --------------------------------------------------------
    # CONDIÇÕES COMERCIAIS
    # --------------------------------------------------------

    conditions = [
        ("VALIDADE", data.get("validade") or "Não informada"),
        ("PAGAMENTO", data.get("pagamento") or "A combinar"),
        ("GARANTIA", data.get("garantia") or "A combinar"),
        ("DESCONTO", money_br(desconto) if desconto else "Sem desconto"),
    ]

    cells = []

    for label, value in conditions:
        cells.append([
            Paragraph(label, styles["LabelPro"]),
            Paragraph(pdf_text(value), styles["BodyPro"])
        ])

    cond_table = Table(
        [[cells[0], cells[1], cells[2], cells[3]]],
        colWidths=[43.5*mm] * 4
    )

    cond_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), soft),
        ("BOX", (0,0), (-1,-1), 0.55, border),
        ("INNERGRID", (0,0), (-1,-1), 0.35, colors.HexColor("#E8E3DA")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))

    story += [
        Paragraph(
            "CONDIÇÕES COMERCIAIS",
            styles["SectionPro"]
        ),
        cond_table,
        Spacer(1, 2.2*mm)
    ]

    # --------------------------------------------------------
    # OBSERVAÇÕES
    # --------------------------------------------------------

    obs_text = (
        pdf_text(short(data.get("observacoes"), 560))
        or "Nenhuma observação adicional."
    )

    obs = Table([
        [Paragraph("OBSERVAÇÕES", styles["LabelPro"])],
        [Paragraph(obs_text, styles["BodyPro"])]
    ], colWidths=[174*mm])

    obs.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), black),
        ("BACKGROUND", (0,1), (-1,1), cream),
        ("TEXTCOLOR", (0,0), (-1,0), gold_light),
        ("BOX", (0,0), (-1,-1), 0.65, gold),
        ("LINEBELOW", (0,0), (-1,0), 0.5, gold),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))

    story += [
        obs,
        Spacer(1, 2.4*mm)
    ]

    # --------------------------------------------------------
    # APROVAÇÃO
    # --------------------------------------------------------

    story.append(
        Paragraph("APROVAÇÃO", styles["SectionPro"])
    )

    sign = Table([
        [
            Spacer(1, 8*mm),
            Spacer(1, 8*mm)
        ],
        [
            Paragraph(
                "________________________________",
                styles["CenterPro"]
            ),
            Paragraph(
                "________________________________",
                styles["CenterPro"]
            )
        ],
        [
            Paragraph(
                pdf_text(data.get("empresa")) or "Responsável",
                styles["CenterPro"]
            ),
            Paragraph(
                pdf_text(data.get("cliente")) or "Cliente",
                styles["CenterPro"]
            )
        ],
        [
            Paragraph(
                "Responsável pela proposta",
                styles["GoldCenter"]
            ),
            Paragraph(
                "Cliente / Aprovação",
                styles["GoldCenter"]
            )
        ]
    ], colWidths=[87*mm, 87*mm])

    sign.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "BOTTOM"),
        ("LEFTPADDING", (0,0), (-1,-1), 3),
        ("RIGHTPADDING", (0,0), (-1,-1), 3),
        ("TOPPADDING", (0,0), (-1,-1), 1),
        ("BOTTOMPADDING", (0,0), (-1,-1), 1),
    ]))

    story += [
        sign,
        Spacer(1, 1.2*mm),
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=border
        ),
        Spacer(1, 1.1*mm),
        Paragraph(
            "Obrigado pela oportunidade. Será um prazer realizar este projeto para você.",
            styles["CenterPro"]
        )
    ]

    # --------------------------------------------------------
    # RODAPÉ
    # --------------------------------------------------------

    def footer(canvas, doc):
        canvas.saveState()

        canvas.setStrokeColor(gold)
        canvas.setLineWidth(0.55)
        canvas.line(
            12*mm,
            8.5*mm,
            198*mm,
            8.5*mm
        )

        canvas.setFont("Helvetica", 6.8)
        canvas.setFillColor(gray)

        canvas.drawString(
            12*mm,
            5.5*mm,
            f"Proposta {numero} • {data.get('empresa','')}"
        )

        canvas.drawRightString(
            198*mm,
            5.5*mm,
            f"Página {doc.page}"
        )

        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer
    )

    buffer.seek(0)
    return buffer, numero


# ============================================================
# ROTAS
# ============================================================

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML, data={})


@app.route("/gerar-pdf", methods=["POST"])
def gerar_pdf():
    data = request.form.to_dict()

    try:
        pdf, numero = generate_pdf(data)

    except ValueError as e:
        flash(str(e))
        return render_template_string(
            HTML,
            data=data
        ), 400

    except Exception:
        app.logger.exception(
            "Erro inesperado ao gerar PDF"
        )
        flash(
            "Não foi possível gerar o PDF. "
            "Verifique os valores e tente novamente."
        )
        return render_template_string(
            HTML,
            data=data
        ), 500

    filename = f"proposta_exclusiva_{numero}.pdf"

    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )


@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    data = request.form.to_dict()

    phone = clean_phone(
        data.get("whatsapp", "")
    )

    if not phone:
        return "Informe o WhatsApp do cliente.", 400

    try:
        valor = parse_money(
            data.get("valor"),
            "Valor do serviço"
        )

        desconto = (
            parse_money(
                data.get("desconto"),
                "Desconto"
            )
            if data.get("desconto")
            else 0.0
        )

        if desconto > valor:
            return (
                "O desconto não pode ser maior "
                "que o valor do serviço.",
                400
            )

        total = max(
            0.0,
            valor - desconto
        )

    except ValueError as e:
        return str(e), 400

    text = (
        f"Olá, {data.get('cliente','')}! "
        f"Segue a proposta da "
        f"{data.get('empresa','')} "
        f"para {data.get('servico','')}. "
        f"Valor total: {money_br(total)}. "
        f"Prazo: {data.get('prazo','a combinar')}. "
        f"Validade: {data.get('validade','não informada')}."
    )

    return redirect(
        "https://wa.me/"
        + phone
        + "?text="
        + quote(text)
    )


@app.route("/health")
def health():
    return {"status": "ok"}


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
