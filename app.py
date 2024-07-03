import os
import openai
import requests
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from dotenv import load_dotenv
import tiktoken
from cachetools import TTLCache
import asyncio

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Configuração das chaves de API
openai.api_key = os.getenv('OPENAI_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')
places_api_key = os.getenv('PLACES_API_KEY')

# Cache para respostas frequentes
response_cache = TTLCache(maxsize=100, ttl=300)

# Função para acumular histórico de mensagens
def get_message_history():
    return session.get('message_history', [])

def add_message_to_history(role, content):
    message_history = get_message_history()
    message_history.append({"role": role, "content": content})
    session['message_history'] = message_history

async def fetch_openai_response(prompt, history):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}] + history,
        max_tokens=500
    )
    return response['choices'][0]['message']['content']

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

    # Armazenar informações iniciais na sessão
    session['situation_description'] = situation_description
    session['feelings'] = feelings
    session['support_reason'] = support_reason
    session['ia_action'] = ia_action

    # Adicionando mensagens ao histórico
    add_message_to_history("user", f"Descrição: {situation_description}\nEmoções: {feelings}\nRazão do apoio: {support_reason}\nAção da IA: {ia_action}")

    # Gerar uma resposta inicial com base nas informações fornecidas
    prompt = (
        f"Descrição: {situation_description}\n"
        f"Emoções: {feelings}\n"
        f"Razão do apoio: {support_reason}\n"
        f"Ação da IA: {ia_action}\n"
        f"Baseado na Teoria e Técnicas da TCC, forneça decisões práticas, eficazes e suficientes para a situação descrita.\n"
        f"Na primeira interação, priorize segurança, proteção e uma direção clara para a tomada de decisão.\n"
        f"Sempre considere as necessidades do usuário como a maior prioridade.\n"
        f"A IA EMOTION DECISION MAKING possui todo o conhecimento necessário nos pilares de emoções, sentimentos, finanças e jurídico/leis em qualquer região e cultura do planeta Terra."
    )

    # Verificar cache
    if prompt in response_cache:
        initial_response = response_cache[prompt]
    else:
        initial_response = asyncio.run(fetch_openai_response(prompt, get_message_history()))
        response_cache[prompt] = initial_response
    
    # Substituir "Terapia Cognitivo-Comportamental" por "Teoria Cognitivo-Comportamental"
    initial_response = initial_response.replace("Terapia Cognitivo-Comportamental", "Teoria Cognitivo-Comportamental")
    
    # Adicionar a resposta da IA ao histórico
    add_message_to_history("assistant", initial_response)
    
    # Formatar a resposta inicial com a resposta da IA incorporada
    formatted_response = initial_response.replace("**", "<b>").replace("**", "</b>").replace("\n", "<br>")
    formatted_response = f"<p>{formatted_response}</p>"

    # Verificar se a resposta inicial é suficiente ou se são necessárias mais informações
    additional_info_request = ""
    if "precisamos de mais informações" in initial_response.lower():
        additional_info_request = "Por favor, forneça mais detalhes sobre sua situação para que eu possa ajudar melhor."
    
    # Contar tokens usados
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens_used = len(encoding.encode(prompt)) + len(encoding.encode(initial_response))
    
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
    
    return render_template('results.html', 
                           description=situation_description, 
                           answer=formatted_response, 
                           additional_info=additional_info_request, 
                           tokens_used=percentage_remaining,
                           initial_description=session['situation_description'],
                           initial_feelings=session['feelings'],
                           initial_support_reason=session['support_reason'],
                           initial_ia_action=session['ia_action'])

@app.route('/continue', methods=['POST'])
def continue_conversation():
    previous_answer = request.form.get('previous_answer')

    # Adicionando mensagens ao histórico
    add_message_to_history("user", f"Continuar a conversa: {previous_answer}")

    prompt = (
        f"Continuar a conversa: {previous_answer}\n"
        f"Baseado na Teoria e Técnicas da TCC, forneça decisões práticas, eficazes e suficientes para a situação descrita.\n"
        f"Sempre considere as necessidades do usuário como a maior prioridade.\n"
        f"A IA EMOTION DECISION MAKING possui todo o conhecimento necessário nos pilares de emoções, sentimentos, finanças e jurídico/leis em qualquer região e cultura do planeta Terra."
    )

    continuation_response = asyncio.run(fetch_openai_response(prompt, get_message_history()))

    # Substituir "Terapia Cognitivo-Comportamental" por "Teoria e Técnicas Cognitivo-Comportamental"
    continuation_response = continuation_response.replace("Terapia Cognitivo-Comportamental", "Teoria e Técnicas Cognitivo-Comportamental")

    # Adicionar a resposta da IA ao histórico
    add_message_to_history("assistant", continuation_response)

    # Contar tokens usados na continuação
    tokens_used = len(tiktoken.encoding_for_model("gpt-3.5-turbo").encode(f"Continuar a conversa: {previous_answer}")) + len(tiktoken.encoding_for_model("gpt-3.5-turbo").encode(continuation_response))
    session['tokens_used'] += tokens_used

    # Calcular a porcentagem de tokens usados
    total_interactions = 5
    current_interaction = session['tokens_used'] // 250
    tokens_used_percentage = round((current_interaction / total_interactions) * 100, 2)
    percentage_remaining = 100 - tokens_used_percentage

    if current_interaction >= total_interactions:
        return redirect(url_for('final'))

    return render_template('results.html', 
                           answer=continuation_response, 
                           tokens_used=percentage_remaining,
                           initial_description=session['situation_description'],
                           initial_feelings=session['feelings'],
                           initial_support_reason=session['support_reason'],
                           initial_ia_action=session['ia_action'])

@app.route('/search_professionals', methods=['POST'])
def search_professionals():
    professional_type = request.form.get('professional_type')
    location = request.form.get('user_location', '-23.3106665, -51.1899247')  # Simulando a localização do usuário
    
    if not professional_type:
        return "Tipo de profissional é obrigatório", 400

    # Chamada à API do Google Places para buscar profissionais próximos
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius=1500&type={professional_type}&key={places_api_key}"
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

@app.route('/feedback', methods=['POST'])
def feedback():
    feedback = request.form.get('feedback')
    if feedback:
        # Lógica para processar o feedback e ajustar os algoritmos
        pass
    return jsonify(success=True)  # Responder com JSON

@app.route('/final')
def final():
    return render_template('final.html')

@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
