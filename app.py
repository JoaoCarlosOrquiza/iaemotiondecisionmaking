import os
import openai
import requests
from flask import Flask, render_template, request, session, redirect, url_for
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Configuração das chaves de API
openai.api_key = os.getenv('OPENAI_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')

# Definir o roteiro
script = """
1. Primeiramente, entendo que a situação pode ser desconfortável e causar estresse.
2. Segundo, é importante reconhecer seus sentimentos e como eles afetam seu comportamento.
3. Terceiro, sugiro estratégias práticas para lidar com a situação:
    - Escolha o Momento Certo: Encontre um momento em que ambos estejam calmos e sem pressa.
    - Use um Tom Calmo e Amigável: Mantenha sua voz calma e amigável.
    - Inicie com um Elogio: Comece com algo positivo.
    - Seja Claro e Direto: Explique como você se sente sem rodeios.
    - Ofereça uma Solução: Sugira uma forma de resolver a situação.
"""

@app.route('/')
def index():
    session.clear()  # Limpar a sessão ao iniciar uma nova interação
    return render_template('index.html')

@app.route('/process-form', methods=['POST'])
def process_form():
    situation_description = request.form.get('situation_description')
    feelings = request.form.get('feelings')
    support_reason = request.form.get('support_reason')
    ia_action = request.form.get('ia_action')
    
    if not situation_description or not feelings or not support_reason or not ia_action:
        return "All form fields are required", 400
    
    # Armazenar dados na sessão
    session['situation_description'] = situation_description
    session['feelings'] = feelings
    session['support_reason'] = support_reason
    session['ia_action'] = ia_action
    session['history'] = []  # Inicializar histórico da conversa
    session['tokens_used'] = 0  # Inicializar contagem de tokens usados
    
    # Gerar uma resposta inicial com base nas informações fornecidas e no roteiro
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente útil e empático, especializado em Terapia Cognitivo-Comportamental."},
            {"role": "user", "content": f"Descrição: {situation_description}\nEmoções: {feelings}\nRazão do apoio: {support_reason}\nAção da IA: {ia_action}\n\nRoteiro:\n{script}"}
        ],
        max_tokens=150
    )
    initial_response = response['choices'][0]['message']['content']
    
    # Armazenar a resposta no histórico da sessão
    session['history'].append(initial_response)
    session['tokens_used'] += response['usage']['total_tokens']

    # Formatar a resposta inicial com a resposta da IA incorporada
    formatted_response = f"""
    <p>{initial_response}</p>
    """

    # Verificar se a resposta inicial é suficiente ou se são necessárias mais informações
    additional_info_request = ""
    if "precisamos de mais informações" in initial_response.lower():
        additional_info_request = "Por favor, forneça mais detalhes sobre sua situação para que eu possa ajudar melhor."
    
    # Calcular a porcentagem de tokens usados
    tokens_used = 100 - round((session['tokens_used'] / 150) * 100, 2)

    return render_template('results.html', description=situation_description, answer=formatted_response, additional_info=additional_info_request, tokens_used=tokens_used)

@app.route('/continue', methods=['POST'])
def continue_conversation():
    previous_answer = request.form.get('previous_answer')
    
    # Atualizar histórico da sessão com a resposta anterior do usuário
    session['history'].append(previous_answer)
    
    # Gerar uma resposta de continuação com base no histórico atualizado
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente útil e empático, especializado em Terapia Cognitivo-Comportamental."},
            {"role": "user", "content": "\n\n".join(session['history'])}
        ],
        max_tokens=150
    )
    
    continuation_response = response['choices'][0]['message']['content']
    
    # Armazenar a resposta no histórico da sessão
    session['history'].append(continuation_response)
    session['tokens_used'] += response['usage']['total_tokens']
    
    # Calcular a porcentagem de tokens usados
    tokens_used = 100 - round((session['tokens_used'] / 150) * 100, 2)
    
    # Verificar se os tokens usados atingiram o limite e redirecionar para a página final se necessário
    if session['tokens_used'] >= 150:
        return redirect(url_for('final'))
    
    return render_template('results.html', answer=continuation_response, tokens_used=tokens_used)

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

@app.route('/final')
def final():
    return render_template('final.html')

if __name__ == '__main__':
    app.run(debug=True)
