import os
import openai
import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Configuração das chaves de API
openai.api_key = os.getenv('OPENAI_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')
google_translate_key = os.getenv('GOOGLE_TRANSLATE_KEY')

@app.route('/')
def index():
    return render_template('voice_interaction.html')

@app.route('/process', methods=['POST'])
def process():
    description = request.form['description']
    emotions = request.form['emotions']
    support_reason = request.form['support_reason']
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente útil."},
            {"role": "user", "content": f"Descrição: {description}\nEmoções: {emotions}\nRazão do apoio: {support_reason}"}
        ],
        max_tokens=150
    )
    
    return render_template('response.html', response=response['choices'][0]['message']['content'])

@app.route('/continue', methods=['POST'])
def continue_conversation():
    previous_answer = request.form['previous_answer']
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente útil."},
            {"role": "user", "content": f"Continuar a conversa: {previous_answer}"}
        ],
        max_tokens=150
    )
    
    return render_template('response.html', response=response['choices'][0]['message']['content'])

@app.route('/search_professionals', methods=['POST'])
def search_professionals():
    professional_type = request.form['professional_type']
    location = request.form.get('user_location', '-23.3106665, -51.1899247')  # Simulando a localização do usuário
    
    # Chamada à API do Google Places para buscar profissionais próximos
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius=1500&type={professional_type}&key={google_api_key}"
    response = requests.get(url)
    places = response.json().get('results', [])

    return render_template('search_results.html', professional_type=professional_type, location=location, places=places)

@app.route('/translate', methods=['POST'])
def translate():
    try:
        text = request.form['text']
        target_language = request.form['target_language']
        
        url = f"https://translation.googleapis.com/language/translate/v2?key={google_translate_key}"
        data = {
            'q': text,
            'target': target_language
        }
        response = requests.post(url, data=data)
        response.raise_for_status()  # Levanta um erro para códigos de status HTTP 4xx/5xx
        translated_text = response.json()['data']['translations'][0]['translatedText']
        
        return jsonify({'translated_text': translated_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/detect_language', methods=['POST'])
def detect_language():
    try:
        text = request.form['text']
        
        url = f"https://translation.googleapis.com/language/translate/v2/detect?key={google_translate_key}"
        data = {'q': text}
        response = requests.post(url, data=data)
        response.raise_for_status()  # Levanta um erro para códigos de status HTTP 4xx/5xx
        detected_language = response.json()['data']['detections'][0][0]['language']
        
        return jsonify({'detected_language': detected_language})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
