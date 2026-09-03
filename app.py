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
app.secret_key = os.environ.get("SECRET_KEY", "proposta-exclusiva-secret-2026")

# ============================================================
# 🎨 INTERFACE WEB — PREMIUM / LUXO
# ============================================================

HTML = """
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#111111">
<title>Proposta Exclusiva — Soluções Profissionais</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --black:#0b0b0b;
  --black2:#1c1c1c;
  --gold:#b08d57;
  --gold2:#d6b77a;
  --gold-light:#f7f1e5;
  --ink:#171717;
  --muted:#737373;
  --line:#e5e0d7;
  --bg:#f4f2ee;
  --card:#fff;
  --success:#00703c;
  --urgency:#c53030;
}
html{scroll-behavior:smooth}
body{
  background:
    radial-gradient(circle at 8% 0%,rgba(176,141,87,.13),transparent 30%),
    radial-gradient(circle at 95% 10%,rgba(17,17,17,.07),transparent 28%),
    var(--bg);
  color:var(--ink);
  font-family:'Segoe UI',Inter,ui-sans-serif,system-ui,sans-serif;
  line-height:1.5;
}
.container{max-width:1060px;margin:0 auto;padding:20px 16px 60px}
.card{
  background:var(--card);
  border:1px solid rgba(17,17,17,.06);
  border-radius:32px;
  overflow:hidden;
  box-shadow:0 30px 100px rgba(17,17,17,.15);
}
.hero{
  position:relative;overflow:hidden;padding:40px 34px 38px;
  color:#fff;
  background:
    radial-gradient(circle at 92% -10%,rgba(214,183,122,.35),transparent 35%),
    radial-gradient(circle at 0% 100%,rgba(176,141,87,.15),transparent 38%),
    linear-gradient(145deg,#050505,#141414 50%,#1f1c16);
  border-bottom:1px solid rgba(214,183,122,.4);
}
.hero:before,.hero:after{
  content:"";position:absolute;border-radius:50%;border:1px solid rgba(214,183,122,.1)
}
.hero:before{width:320px;height:320px;right:-160px;top:-200px}
.hero:after{width:190px;height:190px;right:-80px;bottom:-120px}
.brand{display:flex;align-items:center;gap:16px;position:relative;z-index:1}
.logo{
  width:64px;height:64px;border-radius:20px;
  display:flex;align-items:center;justify-content:center;
  font-weight:900;font-size:22px;letter-spacing:.5px;
  color:var(--gold-light);
  background:linear-gradient(145deg,#2a2a2a,#101010);
  border:1px solid rgba(214,183,122,.6);
  box-shadow:0 15px 35px rgba(0,0,0,.35),inset 0 0 0 1px rgba(255,255,255,.05);
}
.hero h1{margin:0;font-size:32px;letter-spacing:-.5px}
.hero p{margin:8px 0 0;color:#c8c4b9;font-size:15px;max-width:520px}
.hero-badges{display:flex;gap:10px;flex-wrap:wrap;margin-top:24px}
.badge{
  font-size:12px;font-weight:800;color:#f5ead8;
  padding:8px 14px;border-radius:999px;
  background:rgba(176,141,87,.15);
  border:1px solid rgba(214,183,122,.3);
  display:inline-flex;align-items:center;gap:6px
}
.urgency{
  margin-top:18px;padding:12px 16px;border-radius:14px;
  background:rgba(197,48,48,.08);border:1px solid rgba(197,48,48,.25);
  color:#9b2c2c;font-size:13px;font-weight:600;
  display:flex;align-items:center;gap:8px
}
.body{padding:34px}
.section{
  padding:0 0 32px;margin-bottom:32px;
  border-bottom:1px solid var(--line);
}
.section:last-of-type{border-bottom:0;margin-bottom:0}
.section-title{
  display:flex;align-items:center;gap:12px;margin:0 0 20px;
  font-size:19px;letter-spacing:-.3px;color:var(--black);
}
.num{
  width:36px;height:36px;border-radius:12px;
  background:linear-gradient(135deg,#f8f2e7,#eee5d6);
  color:#8b6a38;display:flex;align-items:center;justify-content:center;
  font-size:12px;font-weight:900;box-shadow:inset 0 0 0 1px #e1d2b9;
}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.full{grid-column:1/-1}
label{display:block;font-size:13px;font-weight:800;color:#2d2d2d;margin:0 0 8px}
input,textarea,select{
  width:100%;padding:15px 16px;border:1px solid #d9d5ce;border-radius:14px;
  background:#fff;color:#171717;font-size:15px;outline:none;transition:.2s;
  box-shadow:0 1px 3px rgba(16,24,40,.03);
}
input:hover,textarea:hover{border-color:#b9aa90}
input:focus,textarea:focus,select:focus{
  border-color:#b08d57;box-shadow:0 0 0 4px rgba(176,141,87,.12);
}
textarea{min-height:110px;resize:vertical;line-height:1.6}
.helper{font-size:12px;color:#928c83;margin-top:6px;line-height:1.5}
.value-wrap{position:relative}
.value-wrap span{
  position:absolute;left:16px;top:50%;transform:translateY(-50%);
  font-size:14px;font-weight:700;color:#756f67;
}
.value-wrap input{padding-left:44px}
.included{
  background:#faf8f3;border:1px solid #e8dfcf;border-radius:14px;padding:18px;
  margin:12px 0 24px
}
.included h3{font-size:15px;color:#6d5028;margin:0 0 12px}
.included ul{list-style:none;margin:0;padding:0}
.included li{padding:6px 0;color:#4a453c;font-size:14px;display:flex;align-items:center;gap:8px}
.included li:before{content:"✓";color:#8b6a38;font-weight:900}
.diferenciais{
  display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:24px 0
}
.diferencial{
  padding:16px;border-radius:14px;background:#faf8f3;border:1px solid #f0e9da;
}
.diferencial strong{display:block;color:#6d5028;font-size:14px;margin-bottom:4px}
.diferencial span{font-size:13px;color:#5a554c;line-height:1.4}
.actions{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:8px}
button{
  border:0;border-radius:16px;padding:16px 20px;
  font-size:15px;font-weight:850;cursor:pointer;transition:.2s;
  letter-spacing:.3px
}
.primary{
  background:linear-gradient(135deg,#b08d57,#947547);
  color:#fff;border:1px solid #947547;
  box-shadow:0 15px 30px rgba(176,141,87,.35);
}
.primary:hover{transform:translateY(-2px);box-shadow:0 20px 40px rgba(176,141,87,.4)}
.secondary{
  background:#fff;color:#3b3833;border:1px solid #d8d0c2;
  box-shadow:0 4px 12px rgba(0,0,0,.04);
}
.secondary:hover{border-color:#b08d57;transform:translateY(-1px)}
.flash{
  background:#fff1f0;border:1px solid #f0c9c4;color:#8d2f25;
  padding:16px;border-radius:14px;margin-bottom:20px;font-size:14px;line-height:1.5;
}
.social-proof{
  display:flex;gap:24px;flex-wrap:wrap;justify-content:center;
  padding:20px 0;border-top:1px solid var(--line);margin-top:30px;
  text-align:center;
}
.social-proof div{font-size:13px;color:#5a554c}
.social-proof strong{display:block;font-size:18px;color:var(--gold);font-weight:900}
.footer-note{text-align:center;color:#7a756c;font-size:12px;margin-top:24px;line-height:1.6}
.terms{font-size:11px;color:#928c83;line-height:1.5;margin-top:20px;text-align:center}
@media(max-width:768px){
  .container{padding:12px 10px 36px}
  .card{border-radius:24px}
  .hero{padding:28px 20px 30px}
  .hero h1{font-size:24px}
  .body{padding:22px 16px}
  .grid,.diferenciais{grid-template-columns:1fr}
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
        <p>Soluções profissionais com excelência, transparência e compromisso com o resultado.</p>
      </div>
    </div>
    <div class="hero-badges">
      <span class="badge">✦ PDF Premium</span>
      <span class="badge">◉ Envio WhatsApp</span>
      <span class="badge">✓ Garantia de Qualidade</span>
      <span class="badge">⚡ Atendimento Ágil</span>
    </div>
    <div class="urgency">
      ⏳ Proposta válida por 7 dias — condições especiais para aprovação antecipada!
    </div>
  </div>

  <div class="body">
  {% with messages = get_flashed_messages() %}
    {% if messages %}<div class="flash">⚠ {{ messages[0] }}</div>{% endif %}
  {% endwith %}

  <form method="post" action="/gerar-pdf" id="orcamentoForm">

    <div class="section">
      <h2 class="section-title"><span class="num">01</span> Sua Empresa</h2>
      <div class="grid">
        <div class="field">
          <label>Nome da Empresa *</label>
          <input name="empresa" required value="{{ data.get('empresa','') }}" placeholder="Ex.: Soluções & Serviços">
        </div>
        <div class="field">
          <label>WhatsApp / Telefone</label>
          <input name="empresa_whatsapp" value="{{ data.get('empresa_whatsapp','') }}" placeholder="(77) 99999-9999">
        </div>
        <div class="field">
          <label>E-mail</label>
          <input type="email" name="empresa_email" value="{{ data.get('empresa_email','') }}" placeholder="contato@empresa.com.br">
        </div>
        <div class="field">
          <label>Cidade / Estado</label>
          <input name="empresa_local" value="{{ data.get('empresa_local','') }}" placeholder="Vitória da Conquista - BA">
        </div>
        <div class="field full">
          <label>CPF / CNPJ <span style="font-weight:500;color:#888">(opcional)</span></label>
          <input name="empresa_doc" value="{{ data.get('empresa_doc','') }}" placeholder="00.000.000/0001-00">
        </div>
      </div>
    </div>

    <div class="section">
      <h2 class="section-title"><span class="num">02</span> Cliente</h2>
      <div class="grid">
        <div class="field">
          <label>Nome Completo *</label>
          <input name="cliente" required value="{{ data.get('cliente','') }}" placeholder="Nome do cliente">
        </div>
        <div class="field">
          <label>WhatsApp do Cliente</label>
          <input name="whatsapp" value="{{ data.get('whatsapp','') }}" placeholder="(77) 98888-8888">
        </div>
        <div class="field full">
          <label>Endereço Completo</label>
          <input name="endereco" value="{{ data.get('endereco','') }}" placeholder="Rua, número, bairro, cidade/UF">
        </div>
      </div>
    </div>

    <div class="section">
      <h2 class="section-title"><span class="num">03</span> Serviço e Valores</h2>
      <div class="grid">
        <div class="field full">
          <label>Serviço / Proposta *</label>
          <input name="servico" required value="{{ data.get('servico','') }}" placeholder="Ex.: Instalação, manutenção, consultoria...">
        </div>
        <div class="field full">
          <label>Descrição Detalhada</label>
          <textarea name="descricao" maxlength="900" placeholder="Detalhe o escopo, etapas e o que será realizado...">{{ data.get('descricao','') }}</textarea>
        </div>
        <div class="field">
          <label>Valor Total do Serviço *</label>
          <div class="value-wrap"><span>R$</span><input id="valor" name="valor" required inputmode="decimal" value="{{ data.get('valor','') }}" placeholder="0,00"></div>
        </div>
        <div class="field">
          <label>Desconto (opcional)</label>
          <div class="value-wrap"><span>R$</span><input id="desconto" name="desconto" inputmode="decimal" value="{{ data.get('desconto','') }}" placeholder="0,00"></div>
        </div>
        <div class="field">
          <label>Prazo de Execução</label>
          <input name="prazo" value="{{ data.get('prazo','') }}" placeholder="Ex.: 3 dias úteis">
        </div>
        <div class="field">
          <label>Validade da Proposta</label>
          <input name="validade" value="{{ data.get('validade','7 dias') }}" placeholder="Ex.: 7 dias">
        </div>
        <div class="field">
          <label>Forma de Pagamento</label>
          <input name="pagamento" value="{{ data.get('pagamento','') }}" placeholder="Ex.: 50% entrada + 50% entrega">
        </div>
        <div class="field">
          <label>Garantia Oferecida</label>
          <input name="garantia" value="{{ data.get('garantia','') }}" placeholder="Ex.: 90 dias">
        </div>
      </div>

      <div class="included">
        <h3>✅ O que está incluído nesta proposta:</h3>
        <ul>
          <li>Execução completa do serviço conforme descrito</li>
          <li>Material e mão de obra qualificada</li>
          <li>Garantia de satisfação e qualidade</li>
          <li>Assistência e suporte pós-serviço</li>
          <li>Transparência total em cada etapa</li>
        </ul>
      </div>

      <div class="diferenciais">
        <div class="diferencial">
          <strong>🚀 Agilidade</strong>
          <span>Compromisso com os prazos acordados</span>
        </div>
        <div class="diferencial">
          <strong>🛡️ Garantia Real</strong>
          <span>Segurança e tranquilidade para você</span>
        </div>
        <div class="diferencial">
          <strong>💎 Qualidade Premium</strong>
          <span>Excelência em cada detalhe do serviço</span>
        </div>
        <div class="diferencial">
          <strong>🤝 Parceria Verdadeira</strong>
          <span>Atendimento personalizado e próximo</span>
        </div>
      </div>
    </div>

    <div class="section">
      <h2 class="section-title"><span class="num">04</span> Observações e Condições</h2>
      <textarea name="observacoes" maxlength="700" placeholder="Materiais, horários, condições especiais ou informações importantes...">{{ data.get('observacoes','') }}</textarea>
    </div>

    <div class="actions">
      <button class="primary" type="submit">✦ Gerar Proposta em PDF</button>
      <button class="secondary" type="button" onclick="enviarWhatsApp()">◉ Enviar pelo WhatsApp</button>
    </div>

    <div class="social-proof">
      <div><strong>+200</strong>Propostas entregues</div>
      <div><strong>⭐ 5.0</strong>Avaliação média</div>
      <div><strong>✅ Garantia</strong>Satisfação ou devolução</div>
      <div><strong>🔒 Sigilo</strong>Total e absoluto</div>
    </div>

    <div class="terms">
      Ao gerar esta proposta, você concorda com os termos de prestação de serviços. Os valores e condições são válidos conforme a validade informada. Esta proposta não gera vínculo trabalhista. Todos os direitos reservados © 2026.
    </div>
  </form>
  </div>
</div>
<div class="footer-note">
  💬 "Ficarei imensamente feliz em realizar este projeto para você. Vamos transformar sua ideia em realidade?" — Agradeço pela confiança!
</div>
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
# 🛠️ FUNÇÕES AUXILIARES
# ============================================================

def clean_phone(phone):
    return re.sub(r"\D", "", phone or "")


def parse_money(value, field_name="Valor"):
    raw = str(value or "").strip()
    if not raw:
        return 0.0
    raw = raw.replace("R$", "").replace("r$", "").replace(" ", "")
    if not re.fullmatch(r"[0-9.,]+", raw):
        raise ValueError(f"O campo '{field_name}' deve conter apenas números. Exemplo: 230,00.")
    try:
        if "," in raw and "." in raw:
            if raw.rfind(",") > raw.rfind("."):
                normalized = raw.replace(".", "").replace(",", ".")
            else:
                normalized = raw.replace(",", "")
        elif "," in raw:
            normalized = raw.replace(".", "").replace(",", ".")
        else:
            normalized = raw if raw.count(".") == 1 else raw.replace(".", "")
        number = float(normalized)
        if number < 0:
            raise ValueError(f"O campo '{field_name}' não pode ser negativo.")
        return number
    except (ValueError, TypeError):
        raise ValueError(f"Valor inválido em '{field_name}'. Use, por exemplo: 230,00.")


def money_br(value):
    return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pdf_text(value):
    return html.escape(str(value or ""), quote=False).replace("\n", "<br/>")


def short(value, max_chars=900):
    value = str(value or "").strip()
    return value[:max_chars-3].rstrip() + "..." if len(value) > max_chars else value


# ============================================================
# 📄 PDF — VERSÃO PREMIUM COMPLETA
# ============================================================

def generate_pdf(data):
    buffer = BytesIO()
    numero = datetime.now().strftime("%Y%m%d-%H%M%S")
    data_emissao = datetime.now().strftime("%d/%m/%Y")

    valor = parse_money(data.get("valor"), "Valor do serviço")
    desconto = parse_money(data.get("desconto"), "Desconto") if data.get("desconto") else 0.0
    if desconto > valor:
        raise ValueError("O desconto não pode ser maior que o valor do serviço.")
    total = max(0.0, valor - desconto)

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=12*mm, bottomMargin=15*mm,
        title=f"Proposta {numero} — {data.get('empresa','')}"
    )

    styles = getSampleStyleSheet()

    # Estilos
    styles.add(ParagraphStyle("BrandPro", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=24, leading=26, textColor=colors.white, alignment=TA_LEFT, spaceAfter=2))
    styles.add(ParagraphStyle("TinyPro", parent=styles["Normal"],
        fontName="Helvetica", fontSize=7.5, leading=10, textColor=colors.HexColor("#D6D1C8")))
    styles.add(ParagraphStyle("LabelPro", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=7.5, leading=9, textColor=colors.HexColor("#6D665C")))
    styles.add(ParagraphStyle("BodyPro", parent=styles["Normal"],
        fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#34312D")))
    styles.add(ParagraphStyle("SectionPro", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=10, leading=12, textColor=colors.HexColor("#171717"), spaceBefore=4, spaceAfter=6))
    styles.add(ParagraphStyle("BigValuePro", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=24, leading=26, textColor=colors.white, alignment=TA_RIGHT))
    styles.add(ParagraphStyle("CenterPro", parent=styles["Normal"],
        fontName="Helvetica", fontSize=7.5, leading=9.5, textColor=colors.HexColor("#737373"), alignment=TA_CENTER))
    styles.add(ParagraphStyle("CenterBoldPro", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.HexColor("#171717"), alignment=TA_CENTER))
    styles.add(ParagraphStyle("GoldCenter", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.HexColor("#8A6837"), alignment=TA_CENTER))
    styles.add(ParagraphStyle("UrgencyPro", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.HexColor("#b53c3c"), alignment=TA_CENTER))

    # Cores
    black = colors.HexColor("#0b0b0b")
    gold = colors.HexColor("#B08D57")
    gold_light = colors.HexColor("#D6B77A")
    cream = colors.HexColor("#FAF8F3")
    light_gold = colors.HexColor("#F7F1E5")
    border = colors.HexColor("#D8D0C2")
    soft = colors.HexColor("#F8F7F4")
    gray = colors.HexColor("#737373")

    story = []

    # CABEÇALHO PREMIUM
    company = pdf_text(data.get("empresa") or "EMPRESA")
    contact_parts = [data.get("empresa_whatsapp"), data.get("empresa_email"), data.get("empresa_local"), data.get("empresa_doc")]
    contact = "<br/>".join(pdf_text(x) for x in contact_parts if str(x or "").strip())

    badge = Table([[Paragraph("<b>PROPOSTA<br/>EXCLUSIVA</b>", styles["CenterBoldPro"])]], colWidths=[36*mm], rowHeights=[18*mm])
    badge.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), light_gold), ("BOX", (0,0), (-1,-1), 1, gold), ("VALIGN", (0,0), (-1,-1), "MIDDLE")]))

    header_left = [
        Paragraph(company, styles["BrandPro"]),
        Paragraph(f"Proposta nº <b>{numero}</b> &nbsp;•&nbsp; Emitida em {data_emissao}", styles["TinyPro"])
    ]

    header = Table([[header_left, Paragraph(contact or " ", styles["TinyPro"]), badge]],
        colWidths=[90*mm, 50*mm, 36*mm])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), black),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (1,0), (1,0), "RIGHT"),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("BOX", (0,0), (-1,-1), 1, gold),
    ]))

    story += [header, Spacer(1, 2*mm), HRFlowable(width="100%", thickness=1.5, color=gold), Spacer(1, 3*mm)]

    # URGÊNCIA
    validade = pdf_text(data.get("validade") or "7 dias")
    urgency_table = Table([[Paragraph(f"⏳ VALIDADE: {validade} — Condições especiais para aprovação antecipada!", styles["UrgencyPro"])]], colWidths=[174*mm])
    urgency_table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#fff2f2")), ("BOX", (0,0), (-1,-1), 0.8, colors.HexColor("#e5b0b0")), ("LEFTPADDING", (0,0), (-1,-1), 8), ("RIGHTPADDING", (0,0), (-1,-1), 8), ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
    story += [urgency_table, Spacer(1, 4*mm)]

    # CLIENTE
    story.append(Paragraph("DADOS DO CLIENTE", styles["SectionPro"]))
    cliente_table = Table([
        [Paragraph("CLIENTE", styles["LabelPro"]), Paragraph("WHATSAPP", styles["LabelPro"])],
        [Paragraph(pdf_text(data.get("cliente")), styles["BodyPro"]), Paragraph(pdf_text(data.get("whatsapp")) or "Não informado", styles["BodyPro"])],
        [Paragraph("ENDEREÇO", styles["LabelPro"]), ""],
        [Paragraph(pdf_text(data.get("endereco")) or "Não informado", styles["BodyPro"]), ""]
    ], colWidths=[111*mm, 63*mm])
    cliente_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), soft), ("SPAN", (0,2), (-1,2)), ("SPAN", (0,3), (-1,3)),
        ("BOX", (0,0), (-1,-1), 0.6, border), ("INNERGRID", (0,0), (-1,1), 0.4, colors.HexColor("#E8E3DA")),
        ("LEFTPADDING", (0,0), (-1,-1), 8), ("RIGHTPADDING", (0,0), (-1,-1), 8), ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story += [cliente_table, Spacer(1, 3*mm)]

    # O QUE ESTÁ INCLUÍDO
    story.append(Paragraph("✅ O QUE ESTÁ INCLUÍDO", styles["SectionPro"]))
    included_items = [
        "Execução completa conforme escopo",
        "Materiais e mão de obra qualificada",
        "Garantia de satisfação e qualidade",
        "Suporte e assistência pós-serviço",
        "Transparência total em cada etapa"
    ]
    included_table = Table([[Paragraph("• " + item, styles["BodyPro"])] for item in included_items], colWidths=[174*mm])
    included_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), cream),
        ("BOX", (0,0), (-1,-1), 0.6, gold),
        ("LEFTPADDING", (0,0), (-1,-1), 8), ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story += [included_table, Spacer(1, 3*mm)]

    # SERVIÇO
    story.append(Paragraph("SERVIÇO / ESCOPO", styles["SectionPro"]))
    service_table = Table([
        [Paragraph("SERVIÇO", styles["LabelPro"]), Paragraph("PRAZO", styles["LabelPro"]), Paragraph("GARANTIA", styles["LabelPro"])],
        [Paragraph(pdf_text(data.get("servico")), styles["BodyPro"]),
         Paragraph(pdf_text(data.get("prazo")) or "A combinar", styles["BodyPro"]),
         Paragraph(pdf_text(data.get("garantia")) or "A combinar", styles["BodyPro"])],
        [Paragraph("DESCRIÇÃO DETALHADA", styles["LabelPro"]), "", ""],
        [Paragraph(pdf_text(short(data.get("descricao"), 700)) or "Sem descrição adicional.", styles["BodyPro"]), "", ""]
    ], colWidths=[92*mm, 41*mm, 41*mm])
    service_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), soft), ("SPAN", (0,2), (-1,2)), ("SPAN", (0,3), (-1,3)),
        ("BOX", (0,0), (-1,-1), 0.6, border), ("INNERGRID", (0,0), (-1,1), 0.4, colors.HexColor("#E8E3DA")),
        ("LEFTPADDING", (0,0), (-1,-1), 8), ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story += [service_table, Spacer(1, 3*mm)]

    # RESUMO FINANCEIRO
    story.append(Paragraph("RESUMO FINANCEIRO", styles["SectionPro"]))
    finance = Table([
        [Paragraph("VALOR DO SERVIÇO", styles["LabelPro"]), Paragraph(money_br(valor), styles["BodyPro"])],
        [Paragraph("DESCONTO", styles["LabelPro"]), Paragraph(money_br(desconto), styles["BodyPro"])],
        [Paragraph("<b>VALOR TOTAL</b>", styles["LabelPro"]), Paragraph(money_br(total), styles["BigValuePro"])]
    ], colWidths=[105*mm, 69*mm])
    finance.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,1), cream), ("BACKGROUND", (0,2), (-1,2), black),
        ("BOX", (0,0), (-1,-1), 1.2, gold), ("LINEABOVE", (0,2), (-1,2), 1.5, gold),
        ("TEXTCOLOR", (0,2), (0,2), gold_light), ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 10), ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story += [finance, Spacer(1, 3*mm)]

    # CONDIÇÕES COMERCIAIS
    conditions = [
        ("VALIDADE", validade),
        ("PAGAMENTO", pdf_text(data.get("pagamento") or "A combinar")),
        ("GARANTIA", pdf_text(data.get("garantia") or "A combinar")),
        ("DESCONTO", money_br(desconto) if desconto else "Sem desconto"),
    ]
    story.append(Paragraph("CONDIÇÕES COMERCIAIS", styles["SectionPro"]))
    cells = []
    for label, value in conditions:
        cells.append([Paragraph(label, styles["LabelPro"]), Paragraph(pdf_text(value), styles["BodyPro"])])
    cond_table = Table([[cells[0], cells[1], cells[2], cells[3]]], colWidths=[43.5*mm]*4)
    cond_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), soft), ("BOX", (0,0), (-1,-1), 0.6, border),
        ("INNERGRID", (0,0), (-1,-1), 0.4, colors.HexColor("#E8E3DA")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 7), ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story += [cond_table, Spacer(1, 3*mm)]

    # OBSERVAÇÕES
    obs_text = pdf_text(short(data.get("observacoes"), 560)) or "Nenhuma observação adicional."
    obs = Table([
        [Paragraph("OBSERVAÇÕES", styles["LabelPro"])],
        [Paragraph(obs_text, styles["BodyPro"])]
    ], colWidths=[174*mm])
    obs.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), black), ("BACKGROUND", (0,1), (-1,1), cream),
        ("TEXTCOLOR", (0,0), (-1,0), gold_light), ("BOX", (0,0), (-1,-1), 0.7, gold),
        ("LEFTPADDING", (0,0), (-1,-1), 9), ("RIGHTPADDING", (0,0), (-1,-1), 9),
        ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    story += [obs, Spacer(1, 4*mm)]

    # APROVAÇÃO
    story.append(Paragraph("APROVAÇÃO", styles["SectionPro"]))
    sign = Table([
        [Spacer(1, 10*mm), Spacer(1, 10*mm)],
        [Paragraph("________________________________", styles["CenterPro"]), Paragraph("________________________________", styles["CenterPro"])],
        [Paragraph(pdf_text(data.get("empresa")) or "Responsável", styles["CenterPro"]), Paragraph(pdf_text(data.get("cliente")) or "Cliente", styles["CenterPro"])],
        [Paragraph("Responsável pela Proposta", styles["GoldCenter"]), Paragraph("Cliente / Aprovação", styles["GoldCenter"])],
        [Paragraph(f"\nData: {data_emissao}", styles["CenterPro"]), Paragraph(f"\nData: {data_emissao}", styles["CenterPro"])]
    ], colWidths=[87*mm, 87*mm])
    sign.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "BOTTOM")]))
    story += [sign, Spacer(1, 3*mm)]

    # FECHAMENTO
    closing = Paragraph(
        "\"Ficarei imensamente feliz em realizar este projeto para você. Vamos transformar sua ideia em realidade?\" — Agradeço pela confiança!",
        styles["CenterPro"]
    )
    story += [closing, Spacer(1, 2*mm), HRFlowable(width="100%", thickness=0.5, color=border)]

    # RODAPÉ
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(gold)
        canvas.setLineWidth(0.6)
        canvas.line(15*mm, 10*mm, 195*mm, 10*mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(gray)
        canvas.drawString(15*mm, 7*mm, f"Proposta nº {numero} • {data.get('empresa','')}")
        canvas.drawRightString(195*mm, 7*mm, f"Página {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    return buffer, numero


# ============================================================
# 🚀 ROTAS
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
        return render_template_string(HTML, data=data), 400
    except Exception:
        flash("Não foi possível gerar o PDF. Verifique os dados e tente novamente.")
        return render_template_string(HTML, data=data), 500
    filename = f"proposta_exclusiva_{numero}.pdf"
    return send_file(pdf, mimetype="application/pdf", as_attachment=True, download_name=filename)


@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    data = request.form.to_dict()
    phone = clean_phone(data.get("whatsapp", ""))
    if not phone:
        flash("Informe o WhatsApp do cliente.")
        return render_template_string(HTML, data=data), 400
    try:
        valor = parse_money(data.get("valor"), "Valor do serviço")
        desconto = parse_money(data.get("desconto"), "Desconto") if data.get("desconto") else 0.0
        total = max(0.0, valor - desconto)
    except ValueError as e:
        flash(str(e))
        return render_template_string(HTML, data=data), 400

    text = (
        f"Olá, {data.get('cliente','')}! 👋\n"
        f"Segue a proposta da {data.get('empresa','')} para: {data.get('servico','')}.\n\n"
        f"💰 Valor total: {money_br(total)}\n"
        f"📅 Prazo: {data.get('prazo','a combinar')}\n"
        f"⏳ Validade: {data.get('validade','não informada')}\n"
        f"🛡️ Garantia: {data.get('garantia','a combinar')}\n\n"
        f"Agradeço pela confiança! Fico à disposição. 🤝"
    )
    return redirect("https://wa.me/" + phone + "?text=" + quote(text))


@app.route("/health")
def health():
    return {"status": "ok"}


# ============================================================
# ▶️ EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
