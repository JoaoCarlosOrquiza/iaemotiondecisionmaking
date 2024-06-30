import os
import openai
import requests
from flask import Flask, render_template, request, session, redirect, url_for
from dotenv import load_dotenv
import tiktoken

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
    return render_template('index.html')

@app.route('/process-form', methods=['POST'])
def process_form():
    situation_description = request.form.get('situation_description')
    feelings = request.form.get('feelings')
    support_reason = request.form.get('support_reason')
    ia_action = request.form.get('ia_action')
    
    if not situation_description or not feelings or not support_reason or not ia_action:
        return "All form fields are required", 400
    
    # Gerar uma resposta inicial com base nas informações fornecidas e no roteiro
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente útil e empático, especializado em Terapia Cognitivo-Comportamental."},
            {"role": "user", "content": f"Descrição: {situation_description}\nEmoções: {feelings}\nRazão do apoio: {support_reason}\nAção da IA: {ia_action}\n\nRoteiro:\n{script}"}
        ],
        max_tokens=250
    )
    initial_response = response['choices'][0]['message']['content']
    
    # Formatar a resposta inicial com a resposta da IA incorporada
    formatted_response = f"""
    <p>{initial_response}</p>
    <!-- Adicione os parágrafos e sugestões aqui -->
    <p>1. [Estratégia 1]</p>
    <p>2. [Estratégia 2]</p>
    <p>- [Subestratégia 1]</p>
    <p>- [Subestratégia 2]</p>
    """

    # Contar tokens usados
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens_used = len(encoding.encode(f"Descrição: {situation_description}\nEmoções: {feelings}\nRazão do apoio: {support_reason}\nAção da IA: {ia_action}\n\nRoteiro:\n{script}")) + len(encoding.encode(initial_response))
    
    # Atualizar a contagem de tokens na sessão
    if 'tokens_used' not in session:
        session['tokens_used'] = 0
    session['tokens_used'] += tokens_used
    
    # Calcular a porcentagem de tokens usados
    total_interactions = 5
    current_interaction = session['tokens_used'] // 250
    tokens_used_percentage = round((current_interaction / total_interactions) * 100, 2)
    percentage_remaining = 100 - tokens_used_percentage
    
    if current_interaction >= total_interactions:
        return redirect(url_for('final'))
    
    return render_template('results.html', description=situation_description, answer=formatted_response, tokens_used=percentage_remaining)

@app.route('/continue', methods=['POST'])
def continue_conversation():
    previous_answer = request.form.get('previous_answer')
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente útil e empático, especializado em Terapia Cognitivo-Comportamental."},
            {"role": "user", "content": f"Continuar a conversa: {previous_answer}"}
        ],
        max_tokens=150
    )
    
    continuation_response = response['choices'][0]['message']['content']
    
    # Contar tokens usados na continuação
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens_used = len(encoding.encode(f"Continuar a conversa: {previous_answer}")) + len(encoding.encode(continuation_response))
    session['tokens_used'] += tokens_used
    
    # Calcular a porcentagem de tokens usados
    current_interaction = session['tokens_used'] // 250
    tokens_used_percentage = round((current_interaction / total_interactions) * 100, 2)
    percentage_remaining = 100 - tokens_used_percentage
    
    if current_interaction >= total_interactions:
        return redirect(url_for('final'))
    
    return render_template('results.html', answer=continuation_response, tokens_used=percentage_remaining)

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
