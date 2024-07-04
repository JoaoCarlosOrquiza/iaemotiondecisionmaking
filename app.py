from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import openai
import os
from dotenv import load_dotenv
import tiktoken
import logging

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Configuração das chaves de API
openai.api_key = os.getenv('OPENAI_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')
places_api_key = os.getenv('PLACES_API_KEY')

# Configurar logging básico
logging.basicConfig(level=logging.DEBUG)

# Função para acumular histórico de mensagens
def get_message_history():
    return session.get('message_history', [])

def add_message_to_history(role, content):
    message_history = get_message_history()
    message_history.append({"role": role, "content": content})
    session['message_history'] = message_history
    logging.debug(f"Updated message history: {message_history}")

def format_response(response):
    return response.replace("**", "<b>").replace("**", "</b>").replace("\n", "<br>").replace("Terapia Cognitivo-Comportamental", "Teoria Cognitivo-Comportamental")

def generate_prompt(situation_description, feelings, support_reason, ia_action):
    prompt = (
        f"Descrição: {situation_description}\n"
        f"Emoções: {feelings}\n"
        f"Razão do apoio: {support_reason}\n"
        f"Ação da IA: {ia_action}\n"
        f"Baseado na Teoria e Técnicas da TCC, forneça decisões práticas, eficazes e suficientes para a situação descrita.\n"
        f"Na primeira interação, priorize segurança, proteção e uma direção clara para a tomada de decisão.\n"
        f"Sempre considere as necessidades do usuário como a maior prioridade.\n"
        f"Importante: Evite fornecer informações que não sejam baseadas em fatos ou que não tenham sido solicitadas diretamente. "
        f"Não invente detalhes ou forneça orientações específicas não solicitadas. Mantenha suas respostas dentro dos tópicos de emoções, "
        f"sentimentos, finanças e jurídico/leis conforme descrito. Isso é para evitar 'alucinações', que são informações factualmente incorretas "
        f"ou irrelevantes. Você deve se comportar de maneira humilde e empática, reconhecendo que os humanos, com quem interage, estão buscando ajuda "
        f"porque enfrentam dificuldades na tomada de decisão. Evite fornecer informações ou orientações não solicitadas e, em vez disso, concentre-se "
        f"em pedir esclarecimentos ou mais detalhes sobre a situação do usuário quando necessário. Desta forma, você favorece a tomada de decisão do usuário, "
        f"comportando-se de maneira semelhante a um humano, com sensibilidade e compreensão das limitações humanas.\n"
    )
    logging.debug(f"Generated prompt: {prompt}")
    return prompt

def post_process_response(response):
    unwanted_phrases = [
        "suporte emocional adicional",
        "orientações específicas não solicitadas"
    ]
    for phrase in unwanted_phrases:
        response = response.replace(phrase, "")
    logging.debug(f"Post-processed response: {response}")
    return response

@app.route('/')
def index():
    logging.debug("Rendering index page")
    return render_template('index.html')

@app.route('/process-form', methods=['POST'])
def process_form():
    situation_description = request.form.get('situation_description')
    feelings = request.form.get('feelings')
    support_reason = request.form.get('support_reason')
    ia_action = request.form.get('ia_action')
    
    logging.debug(f"Received form data: {situation_description}, {feelings}, {support_reason}, {ia_action}")
    
    if not situation_description or not feelings or not support_reason or not ia_action:
        logging.warning("Form submission missing required fields")
        return "All form fields are required", 400

    session['situation_description'] = situation_description
    session['feelings'] = feelings
    session['support_reason'] = support_reason
    session['ia_action'] = ia_action

    add_message_to_history("user", f"Descrição: {situation_description}\nEmoções: {feelings}\nRazão do apoio: {support_reason}\nAção da IA: {ia_action}")

    prompt = generate_prompt(situation_description, feelings, support_reason, ia_action)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}] + get_message_history(),
        max_tokens=750  # Aumentar os tokens de saída
    )
    initial_response = response['choices'][0]['message']['content']
    
    initial_response = post_process_response(initial_response)
    add_message_to_history("assistant", initial_response)
    
    formatted_response = format_response(initial_response)

    additional_info_request = ""
    if "precisamos de mais informações" in initial_response.lower():
        additional_info_request = "Por favor, forneça mais detalhes sobre sua situação para que eu possa ajudar melhor."
    
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens_used = len(encoding.encode(prompt)) + len(encoding.encode(initial_response))
    
    if 'tokens_used' not in session:
        session['tokens_used'] = 0
    session['tokens_used'] += tokens_used
    
    total_interactions = 4
    current_interaction = session['tokens_used'] // 250
    tokens_used_percentage = round((current_interaction / total_interactions) * 100, 2)
    percentage_remaining = 100 - tokens_used_percentage
    
    logging.debug(f"Session tokens used: {session['tokens_used']}")
    logging.debug(f"Current interaction: {current_interaction}")
    logging.debug(f"Tokens used percentage: {tokens_used_percentage}")
    
    if current_interaction >= total_interactions:
        logging.debug("Redirecting to pre_final because current_interaction >= total_interactions")
        return redirect(url_for('pre_final'))
    
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
    
    logging.debug(f"Continuing conversation with: {previous_answer}")

    add_message_to_history("user", f"Continuar a conversa: {previous_answer}")

    prompt = (
        f"Continuar a conversa: {previous_answer}\n"
        f"Baseado na Teoria e Técnicas da TCC, forneça decisões práticas, eficazes e suficientes para a situação descrita.\n"
        f"Sempre considere as necessidades do usuário como a maior prioridade.\n"
        f"Importante: NÃO forneça suporte emocional adicional ou orientações específicas não solicitadas. Restrinja suas respostas aos tópicos de emoções, sentimentos, finanças e jurídico/leis conforme descrito.\n"
    )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=get_message_history() + [{"role": "user", "content": prompt}],
        max_tokens=750  # Aumentar os tokens de saída
    )

    continuation_response = response['choices'][0]['message']['content']

    continuation_response = post_process_response(continuation_response)
    add_message_to_history("assistant", continuation_response)

    tokens_used = len(tiktoken.encoding_for_model("gpt-3.5-turbo").encode(f"Continuar a conversa: {previous_answer}")) + len(tiktoken.encoding_for_model("gpt-3.5-turbo").encode(continuation_response))
    session['tokens_used'] += tokens_used

    total_interactions = 4
    current_interaction = session['tokens_used'] // 250
    tokens_used_percentage = round((current_interaction / total_interactions) * 100, 2)
    percentage_remaining = 100 - tokens_used_percentage

    logging.debug(f"Session tokens used: {session['tokens_used']}")
    logging.debug(f"Current interaction: {current_interaction}")
    logging.debug(f"Tokens used percentage: {tokens_used_percentage}")

    if current_interaction >= total_interactions:
        logging.debug("Redirecting to pre_final because current_interaction >= total_interactions")
        return redirect(url_for('pre_final'))

    return render_template('results.html', 
                           answer=format_response(continuation_response), 
                           tokens_used=percentage_remaining,
                           initial_description=session['situation_description'],
                           initial_feelings=session['feelings'],
                           initial_support_reason=session['support_reason'],
                           initial_ia_action=session['ia_action'])

@app.route('/pre_final')
def pre_final():
    logging.debug("Rendering pre_final page")
    return render_template('pre_final.html')

@app.route('/final')
def final():
    logging.debug("Rendering final page")
    return render_template('final.html')

@app.route('/reset')
def reset():
    logging.debug("Resetting session")
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
