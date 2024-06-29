import os
import openai
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Configuração das chaves de API
openai.api_key = os.getenv('OPENAI_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process-form', methods=['POST'])
def process_form():
    situation_description = request.form.get('situation_description')
    feelings = request.form.get('feelings')
    support_reason = request.form.get('support_reason')
    ia_action = request.form.get('ia_action')
    
    if not situation_description or not feelings or not support_reason or not ia_action:
        return "All form fields are required", 400
    
    # Gerar uma resposta inicial com base nas informações fornecidas
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente útil e empático, especializado em Terapia Cognitivo-Comportamental."},
            {"role": "user", "content": f"Descrição: {situation_description}\nEmoções: {feelings}\nRazão do apoio: {support_reason}\nAção da IA: {ia_action}"}
        ],
        max_tokens=150
    )
    initial_response = response['choices'][0]['message']['content']
    
    # Formatar a resposta inicial com parágrafos numerados
    formatted_response = f"""
    <p><strong>1. Primeiramente,</strong> entendo que a situação pode ser desconfortável e causar estresse.</p>
    <p><strong>2. Segundo,</strong> é importante reconhecer seus sentimentos e como eles afetam seu comportamento.</p>
    <p><strong>3. Terceiro,</strong> sugiro estratégias práticas para lidar com a situação:</p>
    <ul>
        <li><strong>Escolha o Momento Certo:</strong> Encontre um momento em que ambos estejam calmos e sem pressa.</li>
        <li><strong>Use um Tom Calmo e Amigável:</strong> Mantenha sua voz calma e amigável.</li>
        <li><strong>Inicie com um Elogio:</strong> Comece com algo positivo.</li>
        <li><strong>Seja Claro e Direto:</strong> Explique como você se sente sem rodeios.</li>
        <li><strong>Ofereça uma Solução:</strong> Sugira uma forma de resolver a situação.</li>
    </ul>
    <p>{initial_response}</p>
    """

    # Verificar se a resposta inicial é suficiente ou se são necessárias mais informações
    additional_info_request = ""
    if "precisamos de mais informações" in initial_response.lower():
        additional_info_request = "Por favor, forneça mais detalhes sobre sua situação para que eu possa ajudar melhor."
    
    # Calcular a porcentagem de tokens usados (ajustar conforme necessário)
    tokens_used = 100 - round((response['usage']['total_tokens'] / 150) * 100, 2)

    return render_template('results.html', description=situation_description, answer=formatted_response, additional_info=additional_info_request, tokens_used=tokens_used)

@app.route('/continue', methods=['POST'])
def continue_conversation():
    previous_answer = request.form.get('previous_answer')
    
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
    professional_type = request.form.get('professional_type')
    location = request.form.get('user_location', '-23.3106665, -51.1899247')  # Simulando a localização do usuário
    
    # Chamada à API do Google Places para buscar profissionais próximos
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius=1500&type={professional_type}&key={google_api_key}"
    response = requests.get(url)
    places = response.json().get('results', [])

    # Criando uma lista de profissionais a partir dos resultados da API
    professionals = []
    for place in places:
        professional = {
            'name': place.get('name'),
            'specialty': professional_type,
            'distance': '1.5 km'  # Simulando a distância
        }
        professionals.append(professional)

    return render_template('professionals.html', professionals=professionals)

if __name__ == '__main__':
    app.run(debug=True)
