from flask import Flask, request, render_template_string, send_file, redirect, flash
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from io import BytesIO
from datetime import datetime
from urllib.parse import quote
import re
import os
import html

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "orcamento-profissional-secret")

# ============================================================
# INTERFACE WEB
# ============================================================

HTML = """
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Orçamento Pro — Gerador de Propostas</title>
<style>
*{box-sizing:border-box}
:root{
  --primary:#4f46e5;--primary2:#4338ca;--ink:#172033;
  --muted:#667085;--line:#e4e7ec;--bg:#f5f7fb;--card:#fff;
}
body{margin:0;background:linear-gradient(135deg,#f7f8fc,#eef1f8);
font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:var(--ink)}
.container{max-width:980px;margin:0 auto;padding:28px 16px 50px}
.card{background:var(--card);border:1px solid #eaecf0;border-radius:24px;
box-shadow:0 18px 50px rgba(16,24,40,.10);overflow:hidden}
.hero{padding:30px 32px;background:linear-gradient(135deg,#111827,#312e81);color:#fff}
.brand{display:flex;align-items:center;gap:14px}
.logo{width:48px;height:48px;border-radius:14px;background:rgba(255,255,255,.14);
display:flex;align-items:center;justify-content:center;font-weight:900;font-size:21px;
border:1px solid rgba(255,255,255,.18)}
.hero h1{margin:0;font-size:28px;letter-spacing:-.6px}
.hero p{margin:7px 0 0;color:#d9ddf5;font-size:14px}
.body{padding:28px 32px}
.section{padding:0 0 26px;margin-bottom:26px;border-bottom:1px solid var(--line)}
.section:last-of-type{border-bottom:0;margin-bottom:0}
.section-title{display:flex;align-items:center;gap:10px;margin:0 0 17px;font-size:17px}
.num{width:29px;height:29px;border-radius:9px;background:#eef2ff;color:var(--primary);
display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:900}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.full{grid-column:1/-1}
label{display:block;font-size:12px;font-weight:800;color:#344054;margin:0 0 7px}
input,textarea,select{width:100%;padding:13px 14px;border:1px solid #d0d5dd;
border-radius:11px;background:#fff;color:#17202a;font-size:15px;outline:none;transition:.15s}
input:focus,textarea:focus,select:focus{border-color:#818cf8;box-shadow:0 0 0 4px #eef2ff}
textarea{min-height:92px;resize:vertical}
.helper{font-size:11px;color:#98a2b3;margin-top:5px}
.actions{display:flex;gap:12px;flex-wrap:wrap;align-items:center}
button{border:0;border-radius:12px;padding:14px 18px;font-size:15px;font-weight:800;
cursor:pointer;transition:.15s}
.primary{background:linear-gradient(135deg,var(--primary),var(--primary2));color:#fff;
box-shadow:0 8px 20px rgba(79,70,229,.22)}
.secondary{background:#fff;color:#344054;border:1px solid #d0d5dd}
button:hover{transform:translateY(-1px)}
.note{margin-top:12px;color:#667085;font-size:12px;line-height:1.5}
.flash{background:#fff1f3;border:1px solid #fecdd3;color:#9f1239;padding:12px 14px;
border-radius:12px;margin-bottom:20px;font-size:13px}
.footer-note{text-align:center;color:#98a2b3;font-size:11px;margin-top:18px}
@media(max-width:680px){
  .container{padding:10px 8px 30px}.hero{padding:24px 20px}.body{padding:22px 18px}
  .grid{grid-template-columns:1fr}.full{grid-column:auto}.actions button{width:100%}
}
</style>
</head>
<body>
<div class="container">
<div class="card">
  <div class="hero">
    <div class="brand">
      <div class="logo">OP</div>
      <div>
        <h1>Orçamento Pro</h1>
        <p>Crie propostas comerciais elegantes, prontas para PDF e WhatsApp.</p>
      </div>
    </div>
  </div>

  <div class="body">
  {% with messages = get_flashed_messages() %}
    {% if messages %}<div class="flash">{{ messages[0] }}</div>{% endif %}
  {% endwith %}

  <form method="post" action="/gerar-pdf" id="orcamentoForm">

    <div class="section">
      <h2 class="section-title"><span class="num">01</span> Sua empresa</h2>
      <div class="grid">
        <div><label>Nome da empresa *</label><input name="empresa" required value="{{ data.get('empresa','') }}" placeholder="Ex.: Luana Serviços"></div>
        <div><label>Telefone / WhatsApp</label><input name="empresa_whatsapp" value="{{ data.get('empresa_whatsapp','') }}" placeholder="(77) 99999-9999"></div>
        <div><label>E-mail</label><input type="email" name="empresa_email" value="{{ data.get('empresa_email','') }}" placeholder="contato@empresa.com"></div>
        <div><label>Cidade / Estado</label><input name="empresa_local" value="{{ data.get('empresa_local','') }}" placeholder="Vitória da Conquista - BA"></div>
        <div class="full"><label>CPF / CNPJ <span style="font-weight:500;color:#98a2b3">(opcional)</span></label><input name="empresa_doc" value="{{ data.get('empresa_doc','') }}" placeholder="00.000.000/0001-00"></div>
      </div>
    </div>

    <div class="section">
      <h2 class="section-title"><span class="num">02</span> Cliente</h2>
      <div class="grid">
        <div><label>Nome do cliente *</label><input name="cliente" required value="{{ data.get('cliente','') }}" placeholder="Nome completo"></div>
        <div><label>WhatsApp do cliente</label><input name="whatsapp" value="{{ data.get('whatsapp','') }}" placeholder="(77) 98888-8888"></div>
        <div class="full"><label>Endereço</label><input name="endereco" value="{{ data.get('endereco','') }}" placeholder="Rua, número, bairro, cidade"></div>
      </div>
    </div>

    <div class="section">
      <h2 class="section-title"><span class="num">03</span> Serviço e valores</h2>
      <div class="grid">
        <div class="full"><label>Serviço / proposta *</label><input name="servico" required value="{{ data.get('servico','') }}" placeholder="Ex.: Instalação e manutenção de porta"></div>
        <div class="full"><label>Descrição detalhada</label><textarea name="descricao" maxlength="900" placeholder="Explique de forma clara o que será realizado...">{{ data.get('descricao','') }}</textarea></div>
        <div><label>Valor total (R$) *</label><input name="valor" required value="{{ data.get('valor','') }}" placeholder="230,00"></div>
        <div><label>Prazo de execução</label><input name="prazo" value="{{ data.get('prazo','') }}" placeholder="2 dias úteis"></div>
        <div><label>Validade do orçamento</label><input name="validade" value="{{ data.get('validade','7 dias') }}" placeholder="7 dias"></div>
        <div><label>Forma de pagamento</label><input name="pagamento" value="{{ data.get('pagamento','') }}" placeholder="50% na aprovação + 50% na entrega"></div>
        <div><label>Garantia</label><input name="garantia" value="{{ data.get('garantia','') }}" placeholder="90 dias"></div>
        <div><label>Desconto (opcional)</label><input name="desconto" value="{{ data.get('desconto','') }}" placeholder="0,00"></div>
      </div>
    </div>

    <div class="section">
      <h2 class="section-title"><span class="num">04</span> Observações</h2>
      <textarea name="observacoes" maxlength="700" placeholder="Materiais, condições, garantia, horários ou informações importantes...">{{ data.get('observacoes','') }}</textarea>
      <div class="helper">Dica: mantenha as observações objetivas para o documento continuar em uma única página.</div>
    </div>

    <div class="actions">
      <button class="primary" type="submit">✦ Gerar PDF profissional</button>
      <button class="secondary" type="button" onclick="enviarWhatsApp()">◉ Enviar pelo WhatsApp</button>
    </div>
    <div class="note">O PDF inclui número do orçamento, data, dados do cliente, serviço, valor em destaque, condições, garantia, observações e espaço para assinatura.</div>
  </form>
  </div>
</div>
<div class="footer-note">Orçamento Pro • simples para você, profissional para o seu cliente.</div>
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

def parse_money(value):
    value = (value or "").strip().replace("R$", "").replace(" ", "")
    if not value:
        return 0.0
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    elif value.count(".") > 1:
        value = value.replace(".", "")
    return float(value)

def money_br(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def pdf_text(value):
    return html.escape(str(value or ""), quote=False).replace("\n", "<br/>")

def short(value, max_chars=900):
    value = str(value or "").strip()
    if len(value) <= max_chars:
        return value
    return value[:max_chars-3].rstrip() + "..."

# ============================================================
# PDF PROFISSIONAL — OTIMIZADO PARA UMA ÚNICA PÁGINA A4
# ============================================================

def generate_pdf(data):
    buffer = BytesIO()
    numero = datetime.now().strftime("%Y%m%d-%H%M%S")
    data_emissao = datetime.now().strftime("%d/%m/%Y")
    valor = parse_money(data.get("valor"))
    desconto = parse_money(data.get("desconto")) if data.get("desconto") else 0.0

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=12*mm,
        leftMargin=12*mm,
        topMargin=11*mm,
        bottomMargin=12*mm,
        title=f"Orçamento {numero}",
        author=data.get("empresa", "")
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="Brand", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=21, leading=23, textColor=colors.HexColor("#111827"),
        alignment=TA_LEFT, spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        name="Tiny", parent=styles["Normal"], fontName="Helvetica",
        fontSize=7.2, leading=9.2, textColor=colors.HexColor("#667085")
    ))
    styles.add(ParagraphStyle(
        name="Label", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=7.2, leading=9, textColor=colors.HexColor("#667085")
    ))
    styles.add(ParagraphStyle(
        name="Body", parent=styles["Normal"], fontName="Helvetica",
        fontSize=8.4, leading=11.2, textColor=colors.HexColor("#344054")
    ))
    styles.add(ParagraphStyle(
        name="Section", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=9.5, leading=11, textColor=colors.HexColor("#111827"),
        spaceBefore=3, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="BigValue", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=19, leading=21, textColor=colors.HexColor("#111827"),
        alignment=TA_RIGHT
    ))
    styles.add(ParagraphStyle(
        name="Center", parent=styles["Normal"], fontName="Helvetica",
        fontSize=7.2, leading=9, textColor=colors.HexColor("#667085"),
        alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        name="CenterBold", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=7.6, leading=9.2, textColor=colors.HexColor("#344054"),
        alignment=TA_CENTER
    ))

    primary = colors.HexColor("#4F46E5")
    light = colors.HexColor("#EEF2FF")
    border = colors.HexColor("#D0D5DD")
    soft = colors.HexColor("#F8FAFC")
    gray = colors.HexColor("#667085")
    dark = colors.HexColor("#111827")

    story = []

    # Cabeçalho premium
    company = pdf_text(data.get("empresa") or "EMPRESA")
    contact_parts = [
        data.get("empresa_whatsapp"),
        data.get("empresa_email"),
        data.get("empresa_local"),
        data.get("empresa_doc")
    ]
    contact = "<br/>".join(pdf_text(x) for x in contact_parts if str(x or "").strip())

    badge = Table([
        [Paragraph("<b>PROPOSTA<br/>COMERCIAL</b>", styles["CenterBold"])]
    ], colWidths=[31*mm], rowHeights=[14*mm])
    badge.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),light),
        ("BOX",(0,0),(-1,-1),0.7,primary),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1),3),
        ("RIGHTPADDING",(0,0),(-1,-1),3),
    ]))

    header_left = [
        Paragraph(company, styles["Brand"]),
        Paragraph(
            f"Orçamento nº <b>{numero}</b> &nbsp; • &nbsp; Emitido em {data_emissao}",
            styles["Tiny"]
        )
    ]
    header = Table(
        [[header_left, Paragraph(contact, styles["Tiny"]), badge]],
        colWidths=[92*mm, 51*mm, 31*mm]
    )
    header.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("ALIGN",(1,0),(1,0),"RIGHT"),
        ("ALIGN",(2,0),(2,0),"RIGHT"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),0),
        ("BOTTOMPADDING",(0,0),(-1,-1),0),
    ]))
    story += [header, Spacer(1,2.5*mm),
              HRFlowable(width="100%", thickness=1.1, color=primary),
              Spacer(1,2.5*mm)]

    # Cliente
    story.append(Paragraph("DADOS DO CLIENTE", styles["Section"]))
    cliente_data = [
        [Paragraph("CLIENTE", styles["Label"]),
         Paragraph("WHATSAPP", styles["Label"])],
        [Paragraph(pdf_text(data.get("cliente")), styles["Body"]),
         Paragraph(pdf_text(data.get("whatsapp")) or "Não informado", styles["Body"])],
        [Paragraph("ENDEREÇO", styles["Label"]), ""],
        [Paragraph(pdf_text(data.get("endereco")) or "Não informado", styles["Body"]), ""]
    ]
    t = Table(cliente_data, colWidths=[111*mm, 63*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),soft),
        ("SPAN",(0,2),(-1,2)), ("SPAN",(0,3),(-1,3)),
        ("BOX",(0,0),(-1,-1),0.55,border),
        ("INNERGRID",(0,0),(-1,1),0.35,colors.HexColor("#E4E7EC")),
        ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
        ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    story += [t, Spacer(1,2.3*mm)]

    # Serviço
    story.append(Paragraph("SERVIÇO / ESCOPO DA PROPOSTA", styles["Section"]))
    service = [
        [Paragraph("SERVIÇO", styles["Label"]),
         Paragraph("PRAZO", styles["Label"]),
         Paragraph("GARANTIA", styles["Label"])],
        [Paragraph(pdf_text(data.get("servico")), styles["Body"]),
         Paragraph(pdf_text(data.get("prazo")) or "A combinar", styles["Body"]),
         Paragraph(pdf_text(data.get("garantia")) or "A combinar", styles["Body"])],
        [Paragraph("DESCRIÇÃO", styles["Label"]), "", ""],
        [Paragraph(pdf_text(short(data.get("descricao"), 700)) or "Sem descrição adicional.", styles["Body"]), "", ""]
    ]
    st = Table(service, colWidths=[92*mm, 41*mm, 41*mm])
    st.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),soft),
        ("SPAN",(0,2),(-1,2)), ("SPAN",(0,3),(-1,3)),
        ("BOX",(0,0),(-1,-1),0.55,border),
        ("INNERGRID",(0,0),(-1,1),0.35,colors.HexColor("#E4E7EC")),
        ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
        ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    story += [st, Spacer(1,2.3*mm)]

    # Valor
    total_text = money_br(valor)
    value_table = Table([
        [Paragraph("INVESTIMENTO TOTAL", styles["Label"]),
         Paragraph(total_text, styles["BigValue"])]
    ], colWidths=[105*mm, 69*mm])
    value_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),light),
        ("BOX",(0,0),(-1,-1),0.9,primary),
        ("LINEBEFORE",(1,0),(1,0),0.5,colors.HexColor("#C7D2FE")),
        ("LEFTPADDING",(0,0),(-1,-1),9),("RIGHTPADDING",(0,0),(-1,-1),9),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story += [value_table, Spacer(1,2.3*mm)]

    # Condições em 4 blocos
    conditions = [
        ("VALIDADE", data.get("validade") or "Não informada"),
        ("PAGAMENTO", data.get("pagamento") or "A combinar"),
        ("GARANTIA", data.get("garantia") or "A combinar"),
        ("DESCONTO", money_br(desconto) if desconto else "Sem desconto"),
    ]
    cells = []
    for label, value in conditions:
        cells.append(
            [Paragraph(label, styles["Label"]),
             Paragraph(pdf_text(value), styles["Body"])]
        )

    cond_table = Table(
        [[cells[0], cells[1], cells[2], cells[3]]],
        colWidths=[43.5*mm]*4
    )
    cond_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),soft),
        ("BOX",(0,0),(-1,-1),0.55,border),
        ("INNERGRID",(0,0),(-1,-1),0.35,colors.HexColor("#E4E7EC")),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]))
    story += [Paragraph("CONDIÇÕES COMERCIAIS", styles["Section"]),
              cond_table, Spacer(1,2.3*mm)]

    # Observações
    obs_text = pdf_text(short(data.get("observacoes"), 560)) or "Nenhuma observação adicional."
    obs = Table([
        [Paragraph("OBSERVAÇÕES", styles["Label"])],
        [Paragraph(obs_text, styles["Body"])]
    ], colWidths=[174*mm])
    obs.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#FFFDF5")),
        ("BACKGROUND",(0,1),(-1,1),colors.HexColor("#FFFEFA")),
        ("BOX",(0,0),(-1,-1),0.55,border),
        ("LINEBELOW",(0,0),(-1,0),0.35,colors.HexColor("#E4E7EC")),
        ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
        ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    story += [obs, Spacer(1,2.8*mm)]

    # Aprovação / assinaturas
    story.append(Paragraph("APROVAÇÃO", styles["Section"]))
    sign = Table([
        [Spacer(1,9*mm), Spacer(1,9*mm)],
        [Paragraph("________________________________", styles["Center"]),
         Paragraph("________________________________", styles["Center"])],
        [Paragraph(pdf_text(data.get("empresa")) or "Responsável", styles["Center"]),
         Paragraph(pdf_text(data.get("cliente")) or "Cliente", styles["Center"])],
        [Paragraph("Responsável pela proposta", styles["Center"]),
         Paragraph("Cliente / Aprovação", styles["Center"])]
    ], colWidths=[87*mm,87*mm])
    sign.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"BOTTOM"),
        ("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),1),("BOTTOMPADDING",(0,0),(-1,-1),1),
    ]))
    story.append(sign)

    story += [
        Spacer(1,1.5*mm),
        HRFlowable(width="100%", thickness=0.5, color=border),
        Spacer(1,1.2*mm),
        Paragraph(
            "Obrigado pela oportunidade. Este documento representa a proposta comercial descrita acima.",
            styles["Center"]
        )
    ]

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#E4E7EC"))
        canvas.setLineWidth(0.4)
        canvas.line(12*mm, 8.5*mm, 198*mm, 8.5*mm)
        canvas.setFont("Helvetica", 6.8)
        canvas.setFillColor(gray)
        canvas.drawString(12*mm, 5.5*mm, f"Orçamento {numero} • {data.get('empresa','')}")
        canvas.drawRightString(198*mm, 5.5*mm, f"Página {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
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
    except Exception as e:
        flash(f"Não foi possível gerar o PDF: {e}")
        return render_template_string(HTML, data=data), 400

    filename = f"orcamento_{numero}.pdf"
    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    data = request.form.to_dict()
    phone = clean_phone(data.get("whatsapp", ""))
    if not phone:
        return "Informe o WhatsApp do cliente.", 400

    try:
        valor = parse_money(data.get("valor"))
    except Exception:
        valor = 0.0

    text = (
        f"Olá, {data.get('cliente','')}! "
        f"Segue a proposta da {data.get('empresa','')} para {data.get('servico','')}. "
        f"Valor total: {money_br(valor)}. "
        f"Prazo: {data.get('prazo','a combinar')}. "
        f"Validade: {data.get('validade','não informada')}."
    )
    return redirect("https://wa.me/" + phone + "?text=" + quote(text))

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
