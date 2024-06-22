from flask import Flask, request, jsonify
import openai
import os
import requests

app = Flask(__name__)

# Configurar chaves de API a partir das variáveis de ambiente
openai.api_key = os.getenv('OPENAI_API_KEY')
app.secret_key = os.getenv('FLASK_SECRET_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')

@app.route('/')
def home():
    return "Home - Flask Server is Running"

@app.route('/decide', methods=['POST'])
def decide():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid input"}), 400
        
        context = data.get('context', '')
        feelings = data.get('feelings', '')
        options = data.get('options', [])
        
        if not context or not feelings or not options:
            return jsonify({"error": "Missing fields"}), 400

        response = decision_making_prompt(context, feelings, options)
        return jsonify({"decision": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def decision_making_prompt(context, feelings, options):
    messages = [
        {"role": "system", "content": "Você é um assistente útil."},
        {"role": "user", "content": f"Contexto: {context}\nSentimentos: {feelings}\nOpções: {options}\nDecida:"}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150
    )
    return response.choices[0].message['content'].strip()

@app.route('/geocode', methods=['GET'])
def geocode():
    try:
        location = request.args.get('location')
        if not location:
            return jsonify({"error": "Missing 'location' parameter"}), 400
        
        geocode_response = geocode_location(location)
        if not geocode_response:
            return jsonify({"error": "Failed to geocode location"}), 500

        return jsonify(geocode_response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def geocode_location(location):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={google_api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

if __name__ == '__main__':
    app.run(debug=True, port=5001)
