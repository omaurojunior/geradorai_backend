INGREDIENTES_PROIBIDOS = [
    "lombriga", "bosta", "xixi", "cocô", "coco", "fezes", "urina", "sangue", "esperma", "semen", "vômito", "vomito", "pus", "larva", "verme", "barata", "rato", "ratazana", "carniça", "cadáver", "cadaver", "carne humana", "humano", "pessoa", "gente"
]

def contem_ingrediente_proibido(ingredientes):
    for ingrediente in ingredientes:
        ingrediente_baixo = ingrediente.lower()
        for proibido in INGREDIENTES_PROIBIDOS:
            if proibido in ingrediente_baixo:
                return True, proibido
    return False, None
def contem_conteudo_inapropriado(texto):
    palavras_bloqueadas = [
        "sexo", "pornografia", "pornográfico", "violência", "violento", "ódio", "racismo", "discriminação", "assassinato", "morte", "estupro", "pedofilia", "terrorismo", "droga", "drogas", "arma", "armas", "suicídio", "suicidio", "autolesão", "autolesao", "preconceito", "homofobia", "xenofobia", "nazismo", "fascismo", "genocídio", "genocidio"
    ]
    texto_baixo = texto.lower()
    for palavra in palavras_bloqueadas:
        if palavra in texto_baixo:
            return True
    return False
# app.py (Parte 1)
import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Importando o que criamos no outro arquivo:
from config import RECEITA_SCHEMA, SYSTEM_INSTRUCTION

# Carrega as variáveis de ambiente e inicia o Gemini
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# Inicializa o Flask
app = Flask(__name__)
CORS(app)

# app.py (Parte 2)

def generate_recipe(ingredientes):
    # Junta os ingredientes enviados em uma única linha de texto
    lista_ingredientes = ", ".join(ingredientes)
    conteudo_prompt = f"Crie uma receita utilizando obrigatoriamente estes ingredientes: {lista_ingredientes}."
    
    # Faz a chamada para o modelo pedindo uma resposta estruturada em JSON
    response = client.models.generate_content(
        model="gemini-3-flash-preview", # Modelo otimizado para geração de conteúdo
        contents=conteudo_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json", # Força a saída em formato JSON
            response_schema=RECEITA_SCHEMA,       # Segue o esquema do config.py
        )
    )
    return response.text

# app.py (Parte 3)

@app.route("/")
def root():
    return jsonify({
        "status": "success",
        "message": "API Gerador de Receitas funcionando!",
        "version": "1.0"
    }), 200

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    
    # Validação 1: O JSON foi enviado?
    if not data or "ingredientes" not in data:
        return jsonify({
            "status": "error",
            "message": "Por favor, envie uma lista de ingredientes no formato JSON."
        }), 400
        
    ingredientes = data.get("ingredientes", [])
    
    # Validação 2: É uma lista e possui no mínimo 3 itens?
    if not isinstance(ingredientes, list) or len(ingredientes) < 3:
        return jsonify({
            "status": "error",
            "message": "Você precisa fornecer no mínimo 3 ingredientes."
        }), 400

    # Validação 3: Ingredientes impróprios
    tem_proibido, ingrediente_proibido = contem_ingrediente_proibido(ingredientes)
    if tem_proibido:
        return jsonify({
            "status": "error",
            "message": f"Ingrediente impróprio detectado: '{ingrediente_proibido}'. Por favor, envie apenas ingredientes adequados para alimentação."
        }), 400
    
    try:
        # Pede para o Gemini gerar a receita (retorna como string JSON)
        receita_json_string = generate_recipe(ingredientes)

        # Filtro de conteúdo impróprio (na string bruta)
        if contem_conteudo_inapropriado(receita_json_string):
            return jsonify({
                "status": "error",
                "message": "Conteúdo impróprio detectado na resposta da IA. Solicite novamente com outros ingredientes."
            }), 400

        # Converte a string JSON em Dicionário Python para o Flask organizar a resposta
        receita_estruturada = json.loads(receita_json_string)

        # Filtro de conteúdo impróprio (em cada campo)
        for valor in receita_estruturada.values():
            if isinstance(valor, str) and contem_conteudo_inapropriado(valor):
                return jsonify({
                    "status": "error",
                    "message": "Conteúdo impróprio detectado na resposta da IA. Solicite novamente com outros ingredientes."
                }), 400
            if isinstance(valor, list):
                for item in valor:
                    if isinstance(item, str) and contem_conteudo_inapropriado(item):
                        return jsonify({
                            "status": "error",
                            "message": "Conteúdo impróprio detectado na resposta da IA. Solicite novamente com outros ingredientes."
                        }), 400

        return jsonify({
            "status": "success",
            "ingredientes_enviados": ingredientes,
            "dados_receita": receita_estruturada
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erro ao gerar a receita: {str(e)}"
        }), 500

# Executa o servidor local
if __name__ == "__main__":
    app.run(debug=True)