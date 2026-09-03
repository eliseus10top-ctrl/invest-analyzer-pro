from flask import Flask, request, render_template_string, send_file, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable
)
from io import BytesIO
from datetime import datetime, timedelta
from urllib.parse import quote
import re
import os
import html
import uuid

# ============================================================
# 🚀 CONFIGURAÇÕES — JÁ PREENCHIDAS PARA VOCÊ!
# ============================================================

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "proposta-exclusiva-secret-2026")

# ✅ BANCO — FUNCIONA 100% NO RENDER!
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

PLANO_VALOR = 10.00
LIMITE_GRATIS = 1

# ✅ SEUS LINKS — JÁ CONFIGURADOS!
LINK_PAGAMENTO = "https://wa.me/5577999999999?text=Ol%C3%A1!%20Quero%20assinar%20o%20plano%20de%20R%2410%2C00%2Fm%C3%AAs.%20Minha%20chave%20Pix%3A%20eliseusud3%40gmail.com.%20Pode%20confirmar%3F"
LINK_WHATSAPP_SUPORTE = "https://wa.me/5577999999999?text=Ol%C3%A1!%20Preciso%20de%20ajuda!"

# ============================================================
# 📊 BANCO DE DADOS
# ============================================================

class UserUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))
    free_used = db.Column(db.Integer, default=0)
    is_subscribed = db.Column(db.Boolean, default=False)
    subscription_expires = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UserUsage {self.session_id}>"

# ============================================================
# 🎨 TEMPLATE HTML
# ============================================================

HTML = """
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Proposta Exclusiva — PDF Profissional</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--black:#0b0b0b;--gold:#b08d57;--gold-light:#f7f1e5;--ink:#171717;--muted:#737373;--line:#e5e0d7;--bg:#f4f2ee;--card:#fff}
body{background:radial-gradient(circle at 8% 0%,rgba(176,141,87,.13),transparent 30%),radial-gradient(circle at 95% 10%,rgba(17,17,17,.07),transparent 28%),var(--bg);color:var(--ink);font-family:'Segoe UI',Inter,sans-serif;line-height:1.5;}
.container{max-width:1060px;margin:0 auto;padding:20px 16px 60px}
.card{background:var(--card);border:1px solid rgba(17,17,17,.06);border-radius:32px;overflow:hidden;box-shadow:0 30px 100px rgba(17,17,17,.15);position:relative;}
.hero{padding:40px 34px 38px;color:#fff;background:radial-gradient(circle at 92% -10%,rgba(214,183,122,.35),transparent 35%),radial-gradient(circle at 0% 100%,rgba(176,141,87,.15),transparent 38%),linear-gradient(145deg,#050505,#141414 50%,#1f1c16);border-bottom:1px solid rgba(214,183,122,.4);}
.brand{display:flex;align-items:center;gap:16px}
.logo{width:64px;height:64px;border-radius:20px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:22px;color:var(--gold-light);background:linear-gradient(145deg,#2a2a2a,#101010);border:1px solid rgba(214,183,122,.6);}
.hero h1{margin:0;font-size:32px}
.hero p{margin:8px 0 0;color:#c8c4b9;font-size:15px}
.hero-badges{display:flex;gap:10px;flex-wrap:wrap;margin-top:24px}
.badge{font-size:12px;font-weight:800;color:#f5ead8;padding:8px 14px;border-radius:999px;background:rgba(176,141,87,.15);border:1px solid rgba(214,183,122,.3);}
.usage-bar{margin-top:18px;padding:12px 16px;border-radius:14px;background:rgba(22,163,74,.08);border:1px solid rgba(22,163,74,.25);color:#15803d;font-size:13px;font-weight:600;}
.locked{background:rgba(220,38,38,.08);border-color:rgba(220,38,38,.25);color:#b91c1c}
.body{padding:34px}
.section{padding:0 0 32px;margin-bottom:32px;border-bottom:1px solid var(--line);}
.section-title{display:flex;align-items:center;gap:12px;margin:0 0 20px;font-size:19px;}
.num{width:36px;height:36px;border-radius:12px;background:linear-gradient(135deg,#f8f2e7,#eee5d6);color:#8b6a38;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:900;}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.full{grid-column:1/-1}
label{display:block;font-size:13px;font-weight:800;color:#2d2d2d;margin:0 0 8px}
input,textarea{width:100%;padding:15px 16px;border:1px solid #d9d5ce;border-radius:14px;background:#fff;color:#171717;font-size:15px;outline:none;transition:.2s;}
input:focus,textarea:focus{border-color:#b08d57;box-shadow:0 0 0 4px rgba(176,141,87,.12);}
.value-wrap{position:relative}
.value-wrap span{position:absolute;left:16px;top:50%;transform:translateY(-50%);font-size:14px;font-weight:700;color:#756f67;}
.value-wrap input{padding-left:44px}
.included{background:#faf8f3;border:1px solid #e8dfcf;border-radius:14px;padding:18px;margin:12px 0 24px}
.included h3{font-size:15px;color:#6d5028;margin:0 0 12px}
.included ul{list-style:none;margin:0;padding:0}
.included li{padding:6px 0;color:#4a453c;font-size:14px;display:flex;align-items:center;gap:8px}
.included li:before{content:"✓";color:#8b6a38;font-weight:900}
.diferenciais{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:24px 0}
.diferencial{padding:16px;border-radius:14px;background:#faf8f3;border:1px solid #f0e9da;}
.diferencial strong{display:block;color:#6d5028;font-size:14px;margin-bottom:4px}
.diferencial span{font-size:13px;color:#5a554c;line-height:1.4}
.actions{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:8px}
button{border:0;border-radius:16px;padding:16px 20px;font-size:15px;font-weight:850;cursor:pointer;transition:.2s;}
.primary{background:linear-gradient(135deg,#b08d57,#947547);color:#fff;border:1px solid #947547;box-shadow:0 15px 30px rgba(176,141,87,.35);}
.primary:hover{transform:translateY(-2px)}
.primary:disabled{opacity:.6;cursor:not-allowed}
.secondary{background:#fff;color:#3b3833;border:1px solid #d8d0c2;}
.secondary:hover{border-color:#b08d57}
.flash{background:#fff1f0;border:1px solid #f0c9c4;color:#8d2f25;padding:16px;border-radius:14px;margin-bottom:20px;font-size:14px;}
.plan-lock{position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(255,255,255,.97);z-index:100;display:flex;align-items:center;justify-content:center;border-radius:32px;padding:30px;text-align:center;}
.plan-card{background:linear-gradient(145deg,#fff,#faf8f3);border:2px solid var(--gold);border-radius:24px;padding:36px 28px;max-width:400px;width:100%;box-shadow:0 20px 60px rgba(176,141,87,.2);}
.plan-card h2{font-size:28px;color:var(--black);margin:0 0 8px}
.plan-price{font-size:48px;font-weight:900;color:var(--gold);margin:12px 0}
.plan-price span{font-size:18px;color:var(--muted);font-weight:500}
.plan-features{list-style:none;padding:0;margin:24px 0;text-align:left}
.plan-features li{padding:10px 0;border-bottom:1px solid #f0e9da;display:flex;align-items:center;gap:10px}
.plan-features li:before{content:"✓";color:var(--gold);font-weight:900;font-size:18px}
.plan-btn{width:100%;padding:18px;background:linear-gradient(135deg,#b08d57,#947547);color:#fff;border:none;border-radius:14px;font-size:18px;font-weight:800;cursor:pointer;margin-top:10px;}
.unlock-form{margin-top:20px;padding:16px;background:#f8f6f0;border-radius:12px}
.unlock-form input{margin-bottom:10px}
.pix-key{background:#fff8e6;border:1px solid #f0c94f;border-radius:12px;padding:12px;margin:12px 0;font-family:monospace;font-size:13px;color:#856404;word-break:break-all;}
.social-proof{display:flex;gap:24px;flex-wrap:wrap;justify-content:center;padding:20px 0;border-top:1px solid var(--line);margin-top:30px;text-align:center;}
.social-proof div{font-size:13px;color:#5a554c}
.social-proof strong{display:block;font-size:18px;color:var(--gold);font-weight:900}
.terms{font-size:11px;color:#928c83;line-height:1.5;margin-top:20px;text-align:center}
@media(max-width:768px){.container{padding:12px 10px 36px}.card{border-radius:24px}.hero{padding:28px 20px 30px}.hero h1{font-size:24px}.body{padding:22px 16px}.grid,.diferenciais{grid-template-columns:1fr}.actions{grid-template-columns:1fr}.plan-lock{padding:15px}.plan-card{padding:24px 18px}}
</style>
</head>
<body>
<div class="container">
<div class="card">
  {% if bloquear %}
  <div class="plan-lock">
    <div class="plan-card">
      <h2>🔒 Limite Atingido</h2>
      <p style="color:var(--muted);font-size:15px">Você usou sua proposta grátis!</p>
      <div class="plan-price">R$ 10,00<span>/mês</span></div>
      <p style="font-size:14px;color:#666;margin:-8px 0 16px">Ilimitado • Sem fidelidade</p>
      <div style="background:#fff8e6;border:1px solid #f0c94f;border-radius:12px;padding:14px;margin:16px 0;">
        <p style="font-size:14px;font-weight:700;color:#856404;margin:0 0 8px">💳 Pague via Pix:</p>
        <div class="pix-key">eliseusud3@gmail.com</div>
        <p style="font-size:12px;color:#856404;margin:8px 0 0">Valor: R$ 10,00 — Após pagar, volte e ative!</p>
      </div>
      <ul class="plan-features">
        <li>Propostas ILIMITADAS</li><li>PDF Premium</li><li>Sem marca d'água</li><li>Envio WhatsApp</li><li>Suporte prioritário</li>
      </ul>
      <a href="{{ link_pagamento }}" target="_blank" style="text-decoration:none">
        <button class="plan-btn">💳 Falar para Pagar</button>
      </a>
      <div class="unlock-form">
        <p style="font-size:14px;margin:0 0 10px;color:#555">✅ Já pagou? Informe seu e-mail:</p>
        <form method="post" action="/ativar-assinatura">
          <input type="text" name="codigo" placeholder="Seu e-mail ou comprovante" required>
          <button type="submit" class="secondary" style="width:100%;margin-top:8px">✅ Ativar Conta</button>
        </form>
      </div>
      <p style="font-size:12px;color:#888;margin-top:16px">Dúvidas? <a href="{{ link_whatsapp_suporte }}" target="_blank" style="color:var(--gold);font-weight:600">Falar com suporte</a></p>
    </div>
  </div>
  {% endif %}

  <div class="hero">
    <div class="brand">
      <div class="logo">PE</div>
      <div><h1>Proposta Exclusiva</h1><p>Propostas profissionais em PDF — feche mais e valorize seu serviço.</p></div>
    </div>
    <div class="hero-badges"><span class="badge">✦ PDF Premium</span><span class="badge">◉ Envio WhatsApp</span><span class="badge">✓ Qualidade</span><span class="badge">⚡ 1 grátis</span></div>
    <div class="usage-bar {% if bloquear %}locked{% endif %}">
      {% if not bloquear %}✅ {{ usos_restantes }} de {{ limite_gratis }} grátis restantes
      {% else %}❌ Limite atingido — Assine R$10,00/mês e gere ilimitado!{% endif %}
    </div>
  </div>

  <div class="body" style="{{ 'filter:blur(3px);pointer-events:none;user-select:none;' if bloquear else '' }}">
  {% with messages = get_flashed_messages() %}{% if messages %}<div class="flash">⚠ {{ messages[0] }}</div>{% endif %}{% endwith %}

  <form method="post" action="/gerar-pdf" id="orcamentoForm">
    <div class="section"><h2 class="section-title"><span class="num">01</span>Sua Empresa</h2>
      <div class="grid">
        <div><label>Nome da Empresa *</label><input name="empresa" required value="{{ data.get('empresa','') }}" placeholder="Ex.: Soluções & Serviços"></div>
        <div><label>WhatsApp</label><input name="empresa_whatsapp" value="{{ data.get('empresa_whatsapp','') }}" placeholder="(77) 99999-9999"></div>
        <div><label>E-mail</label><input type="email" name="empresa_email" value="{{ data.get('empresa_email','') }}" placeholder="contato@email.com"></div>
        <div><label>Cidade/UF</label><input name="empresa_local" value="{{ data.get('empresa_local','') }}" placeholder="Vitória da Conquista - BA"></div>
        <div class="full"><label>CNPJ/CPF (opcional)</label><input name="empresa_doc" value="{{ data.get('empresa_doc','') }}" placeholder="00.000.000/0001-00"></div>
      </div>
    </div>
    <div class="section"><h2 class="section-title"><span class="num">02</span>Cliente</h2>
      <div class="grid">
        <div><label>Nome Completo *</label><input name="cliente" required value="{{ data.get('cliente','') }}" placeholder="Nome do cliente"></div>
        <div><label>WhatsApp do Cliente</label><input name="whatsapp" value="{{ data.get('whatsapp','') }}" placeholder="(77) 98888-8888"></div>
        <div class="full"><label>Endereço Completo</label><input name="endereco" value="{{ data.get('endereco','') }}" placeholder="Rua, número, bairro, cidade/UF"></div>
      </div>
    </div>
    <div class="section"><h2 class="section-title"><span class="num">03</span>Serviço e Valores</h2>
      <div class="grid">
        <div class="full"><label>Serviço/Proposta *</label><input name="servico" required value="{{ data.get('servico','') }}" placeholder="Ex.: Instalação, manutenção..."></div>
        <div class="full"><label>Descrição Detalhada</label><textarea name="descricao" maxlength="900" placeholder="Detalhe...">{{ data.get('descricao','') }}</textarea></div>
        <div><label>Valor Total *</label><div class="value-wrap"><span>R$</span><input name="valor" required inputmode="decimal" value="{{ data.get('valor','') }}" placeholder="0,00"></div></div>
        <div><label>Desconto (opcional)</label><div class="value-wrap"><span>R$</span><input name="desconto" inputmode="decimal" value="{{ data.get('desconto','') }}" placeholder="0,00"></div></div>
        <div><label>Prazo de Execução</label><input name="prazo" value="{{ data.get('prazo','') }}" placeholder="Ex.: 3 dias úteis"></div>
        <div><label>Validade da Proposta</label><input name="validade" value="{{ data.get('validade','7 dias') }}" placeholder="Ex.: 7 dias"></div>
        <div><label>Forma de Pagamento</label><input name="pagamento" value="{{ data.get('pagamento','') }}" placeholder="Ex.: 50% entrada + 50% entrega"></div>
        <div><label>Garantia Oferecida</label><input name="garantia" value="{{ data.get('garantia','') }}" placeholder="Ex.: 90 dias"></div>
      </div>
      <div class="included"><h3>✅ O que está incluído:</h3><ul><li>Execução completa conforme escopo</li><li>Material e mão de obra qualificada</li><li>Garantia de satisfação e qualidade</li><li>Suporte pós-serviço</li><li>Transparência total</li></ul></div>
      <div class="diferenciais">
        <div class="diferencial"><strong>🚀 Agilidade</strong><span>Prazos cumpridos</span></div>
        <div class="diferencial"><strong>🛡️ Garantia</strong><span>Segurança total</span></div>
        <div class="diferencial"><strong>💎 Qualidade</strong><span>PDF profissional</span></div>
        <div class="diferencial"><strong>🤝 Atendimento</strong><span>Sempre disponível</span></div>
      </div>
    </div>
    <div class="section"><h2 class="section-title"><span class="num">04</span>Observações</h2>
      <textarea name="observacoes" maxlength="700" placeholder="Informações adicionais...">{{ data.get('observacoes','') }}</textarea>
    </div>
    <div class="actions">
      <button class="primary" type="submit" {% if bloquear %}disabled{% endif %}>✦ Gerar PDF</button>
      <button class="secondary" type="button" onclick="enviarWhatsApp()" {% if bloquear %}disabled{% endif %}>◉ Enviar WhatsApp</button>
    </div>
  </form>
    <div class="social-proof"><div><strong>+5.000</strong>Propostas</div><div><strong>⭐ 5.0</strong>Avaliação</div><div><strong>✅ Sem fidelidade</strong>Cancele</div><div><strong>🔒 Pagamento seguro</strong>Protegido</div></div>
    <div class="terms">Plano R$10,00/mês — ilimitado. Pix: eliseusud3@gmail.com © 2026</div>
  </div>
</div>
</div>
<script>
function enviarWhatsApp(){const f=document.getElementById('orcamentoForm');if(!f.reportValidity())return;const old=f.action;f.action='/whatsapp';f.submit();f.action=old;}
</script>
</body>
</html>
"""

# ============================================================
# 🛠️ FUNÇÕES AUXILIARES
# ============================================================

def get_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def get_or_create_user():
    sess_id = get_session_id()
    ip = request.remote_addr
    user = UserUsage.query.filter_by(session_id=sess_id).first()
    if not user:
        user = UserUsage(session_id=sess_id, ip_address=ip)
        db.session.add(user)
        db.session.commit()
    return user

def can_use_free():
    user = get_or_create_user()
    if user.is_subscribed:
        return True
    return user.free_used < LIMITE_GRATIS

def register_use():
    user = get_or_create_user()
    if not user.is_subscribed:
        user.free_used += 1
        db.session.commit()
    return user

def clean_phone(phone):
    return re.sub(r"\D", "", phone or "")

def parse_money(value, field_name="Valor"):
    raw = str(value or "").strip()
    if not raw: return 0.0
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
        if number < 0: raise ValueError(f"'{field_name}' não pode ser negativo.")
        return number
    except (ValueError, TypeError):
        raise ValueError(f"Valor inválido em '{field_name}'. Exemplo: 230,00.")

def money_br(value):
    return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def pdf_text(value):
    return html.escape(str(value or ""), quote=False).replace("\n", "<br/>")

def short(value, max_chars=900):
    value = str(value or "").strip()
    return value[:max_chars-3].rstrip() + "..." if len(value) > max_chars else value

# ============================================================
# 📄 GERAR PDF — CORRIGIDO! <br/> FECHADO ✅
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
        buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm,
        topMargin=12*mm, bottomMargin=15*mm,
        title=f"Proposta {numero} — {data.get('empresa','')}"
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("BrandPro", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=24, leading=26, textColor=colors.black, alignment=TA_LEFT, spaceAfter=2))
    styles.add(ParagraphStyle("TinyPro", parent=styles["Normal"],
        fontName="Helvetica", fontSize=8, leading=10, textColor=colors.grey))
    styles.add(ParagraphStyle("LabelPro", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=colors.black))
    styles.add(ParagraphStyle("BodyPro", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10, leading=13, textColor=colors.black))
    styles.add(ParagraphStyle("SectionPro", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=12, leading=14, textColor=colors.black, spaceBefore=6, spaceAfter=8))
    styles.add(ParagraphStyle("CenterBoldPro", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=10, leading=12, alignment=TA_CENTER))

    gold = colors.HexColor("#B08D57")
    black = colors.HexColor("#0b0b0b")
    light_gold = colors.HexColor("#F7F1E5")
    cream = colors.HexColor("#FAF8F3")
    border = colors.HexColor("#D8D0C2")

    story = []

    company = pdf_text(data.get("empresa") or "EMPRESA")

    # ✅ CORRIGIDO: Usar <br/> FECHADO — sem conteúdo dentro!
    header_left = Paragraph(f"<b>{company}</b>", styles["BrandPro"])
    header_right = Paragraph(f"Proposta nº {numero}<br/>Emitida em: {data_emissao}", styles["TinyPro"])

    header = Table([
        [header_left, header_right]
    ], colWidths=[130*mm, 44*mm])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), light_gold),
        ("ALIGN", (0,0), (0,0), "LEFT"),
        ("ALIGN", (1,0), (1,0), "RIGHT"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("PADDING", (0,0), (-1,-1), 12),
        ("BOX", (0,0), (-1,-1), 0.5, gold),
    ]))
    story.extend([header, Spacer(1, 10*mm)])

    story.append(Paragraph("DADOS DO CLIENTE", styles["SectionPro"]))
    cliente_info = f"Nome: {pdf_text(data.get('cliente',''))}<br/>WhatsApp: {pdf_text(data.get('whatsapp',''))}<br/>Endereço: {pdf_text(data.get('endereco',''))}"
    story.append(Paragraph(cliente_info, styles["BodyPro"]))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("SERVIÇO / DESCRIÇÃO", styles["SectionPro"]))
    story.append(Paragraph(pdf_text(data.get("servico","")), styles["BodyPro"]))
    if data.get("descricao"):
        story.append(Paragraph(pdf_text(data.get("descricao","")), styles["BodyPro"]))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("RESUMO FINANCEIRO", styles["SectionPro"]))
    valor_table = [
        [Paragraph("Valor:", styles["LabelPro"]), Paragraph(money_br(valor), styles["BodyPro"])],
    ]
    if desconto > 0:
        valor_table.append([Paragraph("Desconto:", styles["LabelPro"]), Paragraph(f"- {money_br(desconto)}", styles["BodyPro"])])
    valor_table.append([Paragraph("<b>TOTAL:</b>", styles["LabelPro"]), Paragraph(f"<b>{money_br(total)}</b>", styles["BodyPro"])])

    fin_table = Table(valor_table, colWidths=[120*mm, 54*mm])
    fin_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, border),
        ("BACKGROUND", (0,-1), (-1,-1), light_gold),
        ("FONTWEIGHT", (0,-1), (-1,-1), "bold"),
        ("PADDING", (0,0), (-1,-1), 8),
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
    ]))
    story.append(fin_table)
    story.append(Spacer(1, 8*mm))

    story.append(Paragraph("CONDIÇÕES COMERCIAIS", styles["SectionPro"]))
    cond_text = f"Validade: {pdf_text(data.get('validade','7 dias'))}<br/>Prazo de execução: {pdf_text(data.get('prazo','A combinar'))}<br/>Forma de pagamento: {pdf_text(data.get('pagamento','A combinar'))}<br/>Garantia: {pdf_text(data.get('garantia','A combinar'))}"
    story.append(Paragraph(cond_text, styles["BodyPro"]))
    story.append(Spacer(1, 15*mm))

    assinatura_table = Table([
        [Paragraph("_" * 30, styles["CenterBoldPro"]), Paragraph("_" * 30, styles["CenterBoldPro"])],
        [Paragraph(f"{company}", styles["CenterBoldPro"]), Paragraph(f"{pdf_text(data.get('cliente','Cliente'))}", styles["CenterBoldPro"])],
        [Paragraph("Responsável", styles["TinyPro"]), Paragraph("Cliente", styles["TinyPro"])],
    ], colWidths=[85*mm, 85*mm])
    assinatura_table.setStyle(TableStyle([("ALIGN", (0,0), (-1,-1), "CENTER"), ("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
    story.append(assinatura_table)

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(195*mm, 15*mm, f"Proposta nº {numero} — Página {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    return buffer, numero

# ============================================================
# 🚀 ROTAS
# ============================================================

@app.route("/", methods=["GET"])
def index():
    user = get_or_create_user()
    bloquear = not can_use_free()
    usos_restantes = LIMITE_GRATIS - user.free_used
    return render_template_string(HTML, 
        data={}, bloquear=bloquear, usos_restantes=max(0, usos_restantes),
        limite_gratis=LIMITE_GRATIS, link_pagamento=LINK_PAGAMENTO,
        link_whatsapp_suporte=LINK_WHATSAPP_SUPORTE)

@app.route("/gerar-pdf", methods=["POST"])
def gerar_pdf():
    if not can_use_free():
        flash("Você atingiu o limite! Assine por R$ 10,00/mês e gere ilimitado.")
        return redirect("/")
    
    data = request.form.to_dict()
    try:
        pdf, numero = generate_pdf(data)
        register_use()
    except ValueError as e:
        flash(str(e))
        return render_template_string(HTML, data=data, bloquear=False, usos_restantes=1,
            limite_gratis=LIMITE_GRATIS, link_pagamento=LINK_PAGAMENTO,
            link_whatsapp_suporte=LINK_WHATSAPP_SUPORTE), 400
    
    filename = f"proposta_{numero}.pdf"
    return send_file(pdf, mimetype="application/pdf", as_attachment=True, download_name=filename)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    if not can_use_free():
        flash("Assine o plano para enviar pelo WhatsApp! R$ 10,00/mês.")
        return redirect("/")
    
    data = request.form.to_dict()
    phone = clean_phone(data.get("whatsapp", ""))
    if not phone:
        flash("Informe o WhatsApp do cliente.")
        return render_template_string(HTML, data=data, bloquear=False, usos_restantes=1,
            limite_gratis=LIMITE_GRATIS, link_pagamento=LINK_PAGAMENTO,
            link_whatsapp_suporte=LINK_WHATSAPP_SUPORTE), 400
    
    try:
        valor = parse_money(data.get("valor"), "Valor do serviço")
        desconto = parse_money(data.get("desconto"), "Desconto") if data.get("desconto") else 0.0
        total = max(0.0, valor - desconto)
    except ValueError as e:
        flash(str(e))
        return render_template_string(HTML, data=data, bloquear=False, usos_restantes=1,
            limite_gratis=LIMITE_GRATIS, link_pagamento=LINK_PAGAMENTO,
            link_whatsapp_suporte=LINK_WHATSAPP_SUPORTE), 400

    # ✅ F-string FECHADA corretamente!
    texto = f"Olá, {data.get('cliente','')}! 👋\nSegue sua proposta de {data.get('servico','')} no valor de {money_br(total)}.\nValidade: {data.get('validade','7 dias')}\nAgradeço pela confiança! 😊"
    
    url = f"https://wa.me/{phone}?text={quote(texto)}"
    return redirect(url)

@app.route("/ativar-assinatura", methods=["POST"])
def ativar_assinatura():
    user = get_or_create_user()
    user.is_subscribed = True
    user.subscription_expires = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    flash("✅ Assinatura ativada com sucesso! Você tem 30 dias de acesso ilimitado.")
    return redirect("/")

# ============================================================
# 📊 INICIALIZAR BANCO
# ============================================================

with app.app_context():
    db.create_all()
    print("✅ Banco de dados criado!")

# ============================================================
# ▶️ EXECUTAR — FECHADO CORRETAMENTE!
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
