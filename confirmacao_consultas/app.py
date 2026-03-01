from flask import Flask, request, jsonify, render_template
import pdfplumber
import pandas as pd
import re
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def formatar_telefone(tel):
    numeros = re.sub(r"\D", "", str(tel))
    numeros = numeros[-11:]
    return "55" + numeros


def extrair_dados(pdf_path, nome_medico):

    linhas = []

    with pdfplumber.open(pdf_path) as pdf:

        texto = pdf.pages[0].extract_text()
        local = "LOCAL NÃO ENCONTRADO"

        for linha in texto.split("\n"):
            if "UBS" in linha:
                local = linha.split("-")[0].strip()
                break

        for pagina in pdf.pages:
            tabela = pagina.extract_table()

            if not tabela:
                continue

            tabela = tabela[1:]

            for row in tabela:
                if len(row) < 5:
                    continue

                nome = row[0]
                telefone = formatar_telefone(row[2])
                data = row[3]
                hora = row[4]

                linhas.append({
                    "nome": nome,
                    "telefone": telefone,
                    "data": data,
                    "hora": hora
                })

    return {
        "local": local,
        "medico": f"DR {nome_medico}",
        "pacientes": linhas
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_pdf():

    if "pdf" not in request.files:
        return jsonify({"erro": "PDF não enviado"}), 400

    pdf = request.files["pdf"]
    nome_medico = request.form.get("medico")

    if not nome_medico:
        return jsonify({"erro": "Nome do médico obrigatório"}), 400

    caminho = os.path.join(UPLOAD_FOLDER, pdf.filename)
    pdf.save(caminho)

    dados = extrair_dados(caminho, nome_medico)

    return jsonify(dados)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
