from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/calcular", methods=["POST"])
def calcular():
    try:
        dados = request.get_json()

        ingredientes = float(dados.get("ingredientes", 0))
        embalagens = float(dados.get("embalagens", 0))
        outros = float(dados.get("outros", 0))
        mao_obra = float(dados.get("mao_obra", 0))
        quantidade = int(dados.get("quantidade", 0))
        margem = float(dados.get("margem", 0))

        # Validações
        if quantidade <= 0:
            return jsonify({
                "erro": "Informe uma quantidade de doces maior que zero."
            }), 400

        if margem < 0 or margem >= 100:
            return jsonify({
                "erro": "A margem de lucro deve estar entre 0% e 99%."
            }), 400

        if min(
            ingredientes,
            embalagens,
            outros,
            mao_obra
        ) < 0:
            return jsonify({
                "erro": "Os valores não podem ser negativos."
            }), 400

        # Custo total
        custo_total = (
            ingredientes
            + embalagens
            + outros
            + mao_obra
        )

        # Custo por unidade
        custo_por_doce = custo_total / quantidade

        # Preço mínimo = custo por unidade
        preco_minimo = custo_por_doce

        # Preço recomendado considerando a margem sobre o preço final
        if margem == 0:
            preco_recomendado = custo_por_doce
        else:
            preco_recomendado = custo_por_doce / (1 - margem / 100)

        # Lucro por unidade
        lucro_por_doce = preco_recomendado - custo_por_doce

        # Lucro total
        lucro_total = lucro_por_doce * quantidade

        # Faturamento total
        faturamento = preco_recomendado * quantidade

        return jsonify({
            "custo_total": round(custo_total, 2),
            "custo_por_doce": round(custo_por_doce, 2),
            "preco_minimo": round(preco_minimo, 2),
            "preco_recomendado": round(preco_recomendado, 2),
            "lucro_por_doce": round(lucro_por_doce, 2),
            "lucro_total": round(lucro_total, 2),
            "faturamento": round(faturamento, 2),
            "quantidade": quantidade,
            "margem": margem
        })

    except (ValueError, TypeError):
        return jsonify({
            "erro": "Digite valores válidos nos campos."
        }), 400

    except Exception as e:
        return jsonify({
            "erro": "Ocorreu um erro ao realizar o cálculo."
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
