
from flask import Flask, request, render_template_string, send_file, redirect, url_for, flash
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from io import BytesIO
from datetime import datetime
from urllib.parse import quote
import re
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "orcamento-profissional-secret")

HTML = """
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gerador de Orçamento Profissional</title>
<style>
*{box-sizing:border-box} body{margin:0;background:#f3f5f7;font-family:Arial,sans-serif;color:#17202a}
.container{max-width:900px;margin:30px auto;padding:20px}
.card{background:#fff;border-radius:18px;padding:28px;box-shadow:0 8px 30px rgba(0,0,0,.08)}
h1{margin:0 0 8px;font-size:28px}.sub{color:#68737d;margin-bottom:26px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.full{grid-column:1/-1} label{display:block;font-weight:700;margin-bottom:7px}
input,textarea{width:100%;padding:13px;border:1px solid #ccd3da;border-radius:10px;font-size:16px}
textarea{min-height:100px;resize:vertical}
.section{margin-top:25px;padding-top:20px;border-top:1px solid #e6e9ec}
.section h2{font-size:18px;margin:0 0 16px}
button{border:0;border-radius:11px;padding:14px 20px;background:#111827;color:white;font-size:16px;font-weight:700;cursor:pointer}
button:hover{opacity:.92}.note{font-size:13px;color:#68737d;margin-top:12px}
.flash{background:#fff1f1;color:#a51d2d;padding:12px;border-radius:10px;margin-bottom:16px}
@media(max-width:650px){.grid{grid-template-columns:1fr}.full{grid-column:auto}.container{margin:0 auto;padding:12px}.card{padding:20px}}
</style>
</head>
<body>
<div class="container"><div class="card">
<h1>Orçamento Profissional</h1>
<div class="sub">Preencha os dados e gere um PDF pronto para enviar ao seu cliente pelo WhatsApp.</div>
{% with messages = get_flashed_messages() %}
{% if messages %}<div class="flash">{{ messages[0] }}</div>{% endif %}
{% endwith %}
<form method="post" action="/gerar-pdf">
<div class="section"><h2>1. Sua empresa</h2>
<div class="grid">
<div><label>Nome da empresa *</label><input name="empresa" required value="{{ data.get('empresa','') }}"></div>
<div><label>Telefone / WhatsApp da empresa</label><input name="empresa_whatsapp" value="{{ data.get('empresa_whatsapp','') }}"></div>
<div><label>E-mail</label><input type="email" name="empresa_email" value="{{ data.get('empresa_email','') }}"></div>
<div><label>Cidade / Estado</label><input name="empresa_local" value="{{ data.get('empresa_local','') }}"></div>
</div></div>

<div class="section"><h2>2. Cliente</h2>
<div class="grid">
<div><label>Nome do cliente *</label><input name="cliente" required value="{{ data.get('cliente','') }}"></div>
<div><label>WhatsApp do cliente</label><input name="whatsapp" value="{{ data.get('whatsapp','') }}"></div>
<div class="full"><label>Endereço do cliente</label><input name="endereco" value="{{ data.get('endereco','') }}"></div>
</div></div>

<div class="section"><h2>3. Serviço</h2>
<div class="grid">
<div class="full"><label>Nome do serviço *</label><input name="servico" required value="{{ data.get('servico','') }}"></div>
<div class="full"><label>Descrição detalhada</label><textarea name="descricao">{{ data.get('descricao','') }}</textarea></div>
<div><label>Valor (R$) *</label><input name="valor" required placeholder="620,00" value="{{ data.get('valor','') }}"></div>
<div><label>Prazo de execução</label><input name="prazo" placeholder="3 dias úteis" value="{{ data.get('prazo','') }}"></div>
<div><label>Validade do orçamento</label><input name="validade" placeholder="7 dias" value="{{ data.get('validade','7 dias') }}"></div>
<div><label>Forma de pagamento</label><input name="pagamento" placeholder="50% na aprovação + 50% na entrega" value="{{ data.get('pagamento','') }}"></div>
<div class="full"><label>Observações / condições</label><textarea name="observacoes" placeholder="Materiais, garantia, condições e outras informações...">{{ data.get('observacoes','') }}</textarea></div>
</div></div>

<div class="section">
<button type="submit">Gerar PDF profissional →</button>
<div class="note">O PDF será gerado com número do orçamento, data, resumo do serviço, valor, condições e área de assinatura.</div>
</div>
</form>
</div></div>
</body></html>
"""

def clean_phone(phone):
    return re.sub(r"\D", "", phone or "")

def parse_money(value):
    value = (value or "").strip().replace("R$", "").replace(" ", "")
    if not value:
        return 0.0
    # Aceita 620,00 / 620.00 / 1.620,00
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    else:
        # Se houver vários pontos, assume separadores de milhar
        if value.count(".") > 1:
            value = value.replace(".", "")
    return float(value)

def money_br(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def pdf_text(value):
    return (value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def generate_pdf(data):
    buffer = BytesIO()
    numero = datetime.now().strftime("%Y%m%d-%H%M%S")
    data_emissao = datetime.now().strftime("%d/%m/%Y")
    valor = parse_money(data.get("valor"))

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=18*mm, leftMargin=18*mm,
        topMargin=17*mm, bottomMargin=17*mm,
        title=f"Orçamento {numero}",
        author=data.get("empresa","")
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TitlePro", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=23, leading=27, textColor=colors.HexColor("#111827"),
        alignment=TA_LEFT, spaceAfter=3
    ))
    styles.add(ParagraphStyle(
        name="SmallGray", parent=styles["Normal"], fontName="Helvetica",
        fontSize=8.5, leading=12, textColor=colors.HexColor("#667085")
    ))
    styles.add(ParagraphStyle(
        name="Section", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=11, leading=14, textColor=colors.HexColor("#111827"),
        spaceBefore=8, spaceAfter=7
    ))
    styles.add(ParagraphStyle(
        name="BodyPro", parent=styles["Normal"], fontName="Helvetica",
        fontSize=9.5, leading=14, textColor=colors.HexColor("#344054")
    ))
    styles.add(ParagraphStyle(
        name="ValueBig", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=18, leading=22, textColor=colors.HexColor("#111827"),
        alignment=TA_RIGHT
    ))
    styles.add(ParagraphStyle(
        name="CenterSmall", parent=styles["SmallGray"], alignment=TA_CENTER
    ))

    story = []

    # Cabeçalho
    header_left = [
        Paragraph(pdf_text(data.get("empresa","EMPRESA")), styles["TitlePro"]),
        Paragraph(
            f"Orçamento nº <b>{numero}</b> &nbsp; • &nbsp; Emitido em {data_emissao}",
            styles["SmallGray"]
        )
    ]
    contact = "<br/>".join(filter(None, [
        pdf_text(data.get("empresa_whatsapp","")),
        pdf_text(data.get("empresa_email","")),
        pdf_text(data.get("empresa_local",""))
    ]))
    header = Table([[header_left, Paragraph(contact, styles["SmallGray"])]],
                   colWidths=[112*mm, 62*mm])
    header.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("ALIGN",(1,0),(1,0),"RIGHT"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),0),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    story += [header, Spacer(1,5*mm), HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D0D5DD")), Spacer(1,5*mm)]

    # Cliente
    story.append(Paragraph("DADOS DO CLIENTE", styles["Section"]))
    cliente_data = [
        [Paragraph("<b>Cliente</b>", styles["SmallGray"]), Paragraph("<b>WhatsApp</b>", styles["SmallGray"])],
        [Paragraph(pdf_text(data.get("cliente","")), styles["BodyPro"]),
         Paragraph(pdf_text(data.get("whatsapp","")), styles["BodyPro"])],
        [Paragraph("<b>Endereço</b>", styles["SmallGray"]), ""],
        [Paragraph(pdf_text(data.get("endereco","")) or "Não informado", styles["BodyPro"]), ""]
    ]
    t = Table(cliente_data, colWidths=[105*mm, 69*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#F2F4F7")),
        ("SPAN",(0,2),(-1,2)),
        ("SPAN",(0,3),(-1,3)),
        ("BOX",(0,0),(-1,-1),0.6,colors.HexColor("#D0D5DD")),
        ("INNERGRID",(0,0),(-1,1),0.4,colors.HexColor("#E4E7EC")),
        ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    story += [t, Spacer(1,4*mm)]

    # Serviço
    story.append(Paragraph("SERVIÇO / PROPOSTA", styles["Section"]))
    service_box = Table([
        [Paragraph("<b>Serviço</b>", styles["SmallGray"]),
         Paragraph("<b>Prazo</b>", styles["SmallGray"])],
        [Paragraph(pdf_text(data.get("servico","")), styles["BodyPro"]),
         Paragraph(pdf_text(data.get("prazo","")) or "A combinar", styles["BodyPro"])],
        [Paragraph("<b>Descrição</b>", styles["SmallGray"]), ""],
        [Paragraph(pdf_text(data.get("descricao","")) or "Sem descrição adicional.", styles["BodyPro"]), ""],
    ], colWidths=[125*mm, 49*mm])
    service_box.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#F2F4F7")),
        ("SPAN",(0,2),(-1,2)),("SPAN",(0,3),(-1,3)),
        ("BOX",(0,0),(-1,-1),0.6,colors.HexColor("#D0D5DD")),
        ("INNERGRID",(0,0),(-1,1),0.4,colors.HexColor("#E4E7EC")),
        ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    story += [service_box, Spacer(1,5*mm)]

    # Valor em destaque
    value_table = Table([
        [Paragraph("VALOR TOTAL", styles["SmallGray"]), Paragraph(money_br(valor), styles["ValueBig"])]
    ], colWidths=[90*mm, 84*mm])
    value_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F9FAFB")),
        ("BOX",(0,0),(-1,-1),0.8,colors.HexColor("#D0D5DD")),
        ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10),
        ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story += [value_table, Spacer(1,5*mm)]

    # Condições
    story.append(Paragraph("CONDIÇÕES COMERCIAIS", styles["Section"]))
    conditions = [
        ["Validade do orçamento", data.get("validade","") or "Não informado"],
        ["Forma de pagamento", data.get("pagamento","") or "A combinar"],
    ]
    ct = Table([[Paragraph(f"<b>{pdf_text(k)}</b>", styles["SmallGray"]),
                 Paragraph(pdf_text(v), styles["BodyPro"])] for k,v in conditions],
               colWidths=[58*mm,116*mm])
    ct.setStyle(TableStyle([
        ("BOX",(0,0),(-1,-1),0.6,colors.HexColor("#D0D5DD")),
        ("INNERGRID",(0,0),(-1,-1),0.4,colors.HexColor("#E4E7EC")),
        ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#F2F4F7")),
        ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),
        ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),
    ]))
    story += [ct, Spacer(1,5*mm)]

    if data.get("observacoes","").strip():
        story.append(Paragraph("OBSERVAÇÕES", styles["Section"]))
        obs = Table([[Paragraph(pdf_text(data["observacoes"]), styles["BodyPro"])]],
                    colWidths=[174*mm])
        obs.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#FFFCF5")),
            ("BOX",(0,0),(-1,-1),0.6,colors.HexColor("#D0D5DD")),
            ("LEFTPADDING",(0,0),(-1,-1),9),("RIGHTPADDING",(0,0),(-1,-1),9),
            ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),
        ]))
        story += [obs, Spacer(1,6*mm)]

    # Assinaturas
    story.append(Paragraph("APROVAÇÃO", styles["Section"]))
    sign = Table([
        [Spacer(1,15*mm), Spacer(1,15*mm)],
        [Paragraph("__________________________________", styles["CenterSmall"]),
         Paragraph("__________________________________", styles["CenterSmall"])],
        [Paragraph(pdf_text(data.get("empresa","")), styles["CenterSmall"]),
         Paragraph(pdf_text(data.get("cliente","")), styles["CenterSmall"])],
        [Paragraph("Responsável pela proposta", styles["CenterSmall"]),
         Paragraph("Cliente / Aprovação", styles["CenterSmall"])]
    ], colWidths=[87*mm,87*mm])
    sign.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"BOTTOM"),
        ("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),
    ]))
    story.append(sign)
    story += [Spacer(1,7*mm),
              HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#D0D5DD")),
              Spacer(1,3*mm),
              Paragraph("Obrigado pela oportunidade. Este documento representa a proposta comercial descrita acima.",
                        styles["CenterSmall"])]

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#98A2B3"))
        canvas.drawString(18*mm, 9*mm, f"Orçamento {numero} • {data.get('empresa','')}")
        canvas.drawRightString(192*mm, 9*mm, f"Página {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    return buffer, numero

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
    return send_file(pdf, mimetype="application/pdf", as_attachment=True, download_name=filename)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    data = request.form.to_dict()
    phone = clean_phone(data.get("whatsapp",""))
    if not phone:
        return "Informe o WhatsApp do cliente.", 400
    valor = parse_money(data.get("valor"))
    text = (
        f"Olá, {data.get('cliente','')}! "
        f"Segue o orçamento da {data.get('empresa','')} para {data.get('servico','')}. "
        f"Valor: {money_br(valor)}. "
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
