import os
import logging
import re
import json
import subprocess
from flask import Flask, render_template, send_from_directory, request, session, jsonify
import openai
from openai.error import OpenAIError
from dotenv import load_dotenv
from prompt_generator import generate_prompt, detect_sensitive_situations
from knowledge import knowledge
from flask_session import Session
from functools import lru_cache

# Adicionar a importação do requests
import requests

# Certifique-se de que langdetect esteja instalado
try:
    from langdetect import detect  # Biblioteca para detecção de linguagem
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "langdetect"])
    from langdetect import detect

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

# Inicializa a sessão
Session(app)

# This is a forced update
# Desabilitar a configuração do Azure Key Vault
# key_vault_name = os.getenv('AZURE_KEY_VAULT_NAME')
# if not key_vault_name:
#     raise ValueError("AZURE_KEY_VAULT_NAME não está definido no arquivo .env")

# key_vault_url = f"https://{key_vault_name}.vault.azure.net"
# credential = DefaultAzureCredential()
# client = SecretClient(vault_url=key_vault_url, credential=credential)

# Recuperar a chave da API do OpenAI do Azure Key Vault
# openai_api_key_secret_name = os.getenv('OPENAI_API_KEY_SECRET_NAME')
# if not openai_api_key_secret_name:
#     raise ValueError("OPENAI_API_KEY_SECRET_NAME não está definido no arquivo .env")

# openai.api_key = client.get_secret(openai_api_key_secret_name).value

# Configurar a chave da API do OpenAI diretamente do .env
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configurar logging básico
logging.basicConfig(level=logging.DEBUG)

# ID do modelo ajustado
fine_tuned_model = 'ft:davinci-002:jo-ocarlosorquizanochatgpt:finoaiaemotion3ot:9q0DemaR'

def get_message_history():
    return json.loads(session.get('message_history', '[]'))

def add_message_to_history(role, content):
    message_history = get_message_history()
    message_history.append({"role": role, "content": content})
    if len(message_history) > 5:
        message_history = message_history[-5:]
    session['message_history'] = json.dumps(message_history)
    logging.debug(f"Updated message history: {message_history}")

def extract_age_from_additional_info(additional_info):
    match = re.search(r'\b(\d{1,2})\b', additional_info)
    if match:
        return match.group(1)
    return None

def infer_user_age(user_input):
    prompt = (
        f"Com base na seguinte entrada, inferir a idade provável do usuário:\n"
        f"{user_input}\n"
        f"Responda apenas com a idade estimada, sem nenhuma explicação adicional."
    )
    try:
        response = openai.Completion.create(
            model='gpt-3.5-turbo',
            prompt=prompt,
            max_tokens=10
        )
        age_estimate = response['choices'][0]['text'].strip()
        try:
            age_estimate = int(age_estimate)
        except ValueError:
            age_estimate = None
    except Exception as e:
        logging.error(f"Erro ao inferir a idade: {e}")
        age_estimate = None
    return age_estimate

def detect_language(text):
    try:
        return detect(text)
    except Exception as e:
        logging.error(f"Erro ao detectar a língua: {e}")
        return 'pt'  # Padrão para português caso a detecção falhe

def contains_satisfaction_terms(user_response):
    satisfaction_terms = ["obrigado", "excelente", "ótima resposta", "agradeço", "muito bom", "parabéns"]
    user_response_lower = user_response.lower()
    return any(term in user_response_lower for term in satisfaction_terms)

def send_feedback_to_ia(feedback_message):
    # Esta função simula o envio de feedback para a IA para treinamento.
    # Dependendo do sistema, isso pode envolver chamar uma API ou registrar em um banco de dados.
    logging.info(f"Enviando feedback para IA: {feedback_message}")
    # Implementação para enviar o feedback para a IA

@app.route('/static/<path:filename>')
def send_static(filename):
    return send_from_directory('static', filename)

@app.route('/')
def index():
    logging.debug("Rendering index page")
    return render_template('index.html')

@app.route('/sobre.html')
def sobre():
    return render_template('sobre.html')

@app.route('/contato.html')
def contato():
    return render_template('contato.html')

@app.route('/privacidade.html')
def privacidade():
    return render_template('privacidade.html')    

@app.route('/process-form', methods=['POST'])
def process_form():
    increment_interaction_counter()

    if 'template_sequence' not in session:
        session['template_sequence'] = ['results', 'results_pos_results', 'results_apos_pos_results', 'results_pre_final', 'results_final']

    template_sequence = session.get('template_sequence', [])

    additional_info = request.form.get('additional_info')
    situation_description = request.form.get('situation_description')
    feelings = request.form.get('feelings')
    support_reason = request.form.get('support_reason')
    ia_action = request.form.get('ia_action')

    logging.debug(f"Received form data: {situation_description}, {feelings}, {support_reason}, {ia_action}, {additional_info}")

    if not all([situation_description, feelings, support_reason, ia_action, additional_info]):
        logging.warning("Form submission missing required fields")
        return "Todos os campos do formulário são obrigatórios.", 400

    user_language = detect(situation_description)

    user_age = extract_age_from_additional_info(additional_info)
    if not user_age:
        user_age = infer_user_age(situation_description)
        if not user_age:
            logging.warning("Form submission missing required age information")
            return "A idade é um campo obrigatório.", 400

    session['situation_description'] = situation_description
    session['feelings'] = feelings
    session['support_reason'] = support_reason
    session['ia_action'] = ia_action
    session['additional_info'] = additional_info
    session['user_age'] = user_age
    session['user_language'] = user_language

    add_message_to_history("user", f"Descrição: {situation_description}\nEmoções: {feelings}\nRazão do apoio: {support_reason}\nAção da IA: {ia_action}\nInformações adicionais: {additional_info}\nIdade fornecida: {user_age}")

    prompt = generate_prompt(
        situation_description,
        feelings,
        support_reason,
        ia_action,
        user_age=user_age,
        gender_identity=request.form.get('gender_identity', ''),
        user_region=request.form.get('user_region', ''),
        user_language=user_language,
        interaction_number=session.get('interaction_counter', 1)
    )

    try:
        logging.debug("Generating response with gpt-4")
        message_history_tuple = tuple(tuple(item.items()) for item in get_message_history())
        initial_response_content = generate_response(prompt, message_history_tuple, ia_action, use_fine_tuned_model=False)
    except ValueError as ve:
        logging.error(f"ValueError: {ve}")
        return "Erro ao gerar a resposta da IA.", 500
    except OpenAIError as e:
        logging.error(f"OpenAIError: {e}")
        return "Erro ao gerar a resposta da IA.", 500

    formatted_response = format_response(initial_response_content, ia_action)

    add_message_to_history("assistant", formatted_response)

    logging.debug(f"Template sequence before pop: {session['template_sequence']}")

    if template_sequence:
        next_template = template_sequence.pop(0)
        session['template_sequence'] = template_sequence
        return render_template(next_template + '.html',
                               initial_description=session['situation_description'],
                               initial_feelings=session['feelings'],
                               initial_support_reason=session['support_reason'],
                               initial_ia_action=session['ia_action'],
                               additional_info=session['additional_info'],
                               user_age=session['user_age'],
                               inferred_age='',  # Adicionar a variável inferida, se necessário
                               answer=formatted_response)
    else:
        logging.error("Template sequence is empty. Unable to proceed.")
        return "Erro interno: Sequência de templates está vazia.", 500

def increment_interaction_counter():
    if 'interaction_counter' not in session:
        session['interaction_counter'] = 0
    session['interaction_counter'] += 1
    logging.debug(f"Interaction counter incremented: {session['interaction_counter']}")

@lru_cache(maxsize=100)

def generate_response(prompt, message_history_tuple, ia_action, use_fine_tuned_model=False):
    try:
        if use_fine_tuned_model:
            response = openai.Completion.create(
                engine="davinci-codex",
                prompt=prompt,
                max_tokens=100
            )
        else:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
        return response['choices'][0]['message']['content']
    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")

def generate_final_response(initial_response_content, relevant_knowledge, message_history):
    """
    Gera a resposta final combinando a resposta inicial com o conhecimento relevante,
    garantindo que a resposta não ultrapasse o limite máximo de tokens e que a frase final não seja cortada.

    Args:
        initial_response_content (str): Resposta inicial gerada pelo gpt-4o-mini.
        relevant_knowledge (str): Conhecimento relevante do knowledge.py.
        message_history (list): Histórico de mensagens.

    Returns:
        str: A resposta final.
    """
    model = fine_tuned_model

    logging.debug(f"Generating final response with model: {model}")

    max_length = 4096  # Limite máximo de tokens para GPT-4o-mini

    if len(initial_response_content) + len(relevant_knowledge) > max_length:
        logging.warning(f"Resposta muito longa detectada: {len(initial_response_content) + len(relevant_knowledge)} tokens")
        raise ValueError("Resposta muito longa gerada pela IA")

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "system", "content": initial_response_content + relevant_knowledge}] + list(message_history) + [{"role": "user", "content": initial_response_content}],
            max_tokens=max_length - len(initial_response_content + relevant_knowledge)  # Garantir que a resposta não ultrapasse o limite máximo
        )
        final_response_content = response['choices'][0]['message']['content']

        return final_response_content

    except ValueError as ve:
        logging.error(f"ValueError: {ve}")
        raise
    except openai.error.InvalidRequestError as e:
        logging.error(f"Erro ao gerar a resposta da IA: {e}")
        raise
    except (OpenAIError, openai.error.APIError, openai.error.APIConnectionError, openai.error.AuthenticationError, openai.error.PermissionError, openai.error.RateLimitError) as e:
        logging.error(f"Erro ao gerar a resposta da IA: {e}")
        raise

def format_response(response, ia_action):
    """
    Formata a resposta final, substituindo termos e adicionando conhecimento relevante.
    
    Args:
        response (str): A resposta gerada pela IA.
        ia_action (str): Ação da IA solicitada pelo usuário.
    
    Returns:
        str: A resposta formatada.
    """
    relevant_knowledge = knowledge.get(ia_action, "")
    response = f"{response}\n\n{relevant_knowledge}"
    
    substitutions = {
        "Terapia Cognitivo-Comportamental": "TCC",
        "Identificação e Racionalização dos Pensamentos Automáticos": "<b>Identificação e Racionalização dos Pensamentos Automáticos</b>",
        "(TCC)": "(Teoria Cognitivo-Comportamental)",
        "ACT": "Terapia de Aceitação e Compromisso (ACT)",
        "Psicanálise": "<b>Psicanálise</b>",
        "Terapia Comportamental": "<b>Terapia Comportamental</b>"
    }

    response = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', response)
    response = response.replace("\n", "<br>")
    for key, value in substitutions.items():
        response = response.replace(key, value)

    if "def __init__" in response or "Sequential" in response:
        logging.error("Resposta incoerente detectada, gerando nova resposta")
        raise ValueError("Resposta incoerente gerada pela IA")

    return response

def post_process_response(response, ia_action):
    """
    Processa a resposta após ser gerada pela IA, adicionando formatação e verificando inconsistências.
    
    Args:
        response (str): A resposta gerada pela IA.
        ia_action (str): Ação da IA solicitada pelo usuário.
    
    Returns:
        str: A resposta processada.
    """
    if "def __init__" in response or "Sequential" in response:
        logging.error("Resposta incoerente detectada, gerando nova resposta")
        raise ValueError("Resposta incoerente gerada pela IA")

    # Verificar o comprimento da resposta
    max_length = 4096  # Limite máximo de tokens para GPT-4o-mini
    if len(response) > max_length:
        logging.error(f"Resposta muito longa detectada: {len(response)} tokens")
        raise ValueError("Resposta muito longa gerada pela IA")

    relevant_knowledge = knowledge.get(ia_action, "")
    response = f"{response}\n\n{relevant_knowledge}"
    
    substitutions = {
        "Terapia Cognitivo-Comportamental": "TCC",
        "Identificação e Racionalização dos Pensamentos Automáticos": "<b>Identificação e Racionalização dos Pensamentos Automáticos</b>",
        "(TCC)": "(Teoria Cognitivo-Comportamental)",
        "ACT": "Terapia de Aceitação e Compromisso (ACT)",
        "Psicanálise": "<b>Psicanálise</b>",
        "Terapia Comportamental": "<b>Terapia Comportamental</b>"
    }

    response = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', response)
    response = response.replace("\n", "<br>")
    for key, value in substitutions.items():
        response = response.replace(key, value)
    
    if any(term in response for term in ["def __init__", "Sequential", "Dropout"]):
        logging.error("Resposta incoerente detectada após formatação")
        raise ValueError("Resposta incoerente gerada pela IA")

    return response

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    try:
        feedback = request.json.get('feedback')
        logging.debug(f"Recebido feedback: {feedback}")

        valid_feedback = ['positive', 'negative']
        if feedback not in valid_feedback:
            raise ValueError("Tipo de feedback inválido")
        
        logging.debug(f"Feedback válido recebido: {feedback}")

        return jsonify({"success": True})
    except Exception as e:
        logging.error(f"Erro ao processar feedback: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/continue', methods=['POST'])
def continue_conversation():
    increment_interaction_counter()

    if 'template_sequence' not in session:
        session['template_sequence'] = ['results', 'results_pos_results', 'results_apos_pos_results', 'results_pre_final', 'results_final']

    previous_answer = request.form.get('previous_answer')
    logging.debug(f"Continuing conversation with: {previous_answer}")
    add_message_to_history("user", f"Continuar a conversa: {previous_answer}")

    if contains_satisfaction_terms(previous_answer):
        gratitude_response = "Muito obrigado pelo seu feedback positivo! Fico feliz em saber que pude ajudar. Se precisar de mais alguma coisa, estou aqui para ajudar."
        add_message_to_history("assistant", gratitude_response)
        
        # Enviar feedback positivo para a IA
        send_feedback_to_ia(previous_answer)

        return render_template(session['template_sequence'].pop(0) + '.html', **session, answer=gratitude_response)

    situation_description = session.get('situation_description', '')
    feelings = session.get('feelings', '')
    support_reason = session.get('support_reason', '')
    ia_action = session.get('ia_action', '')
    user_age = session.get('user_age', '')
    additional_info = session.get('additional_info', '')
    user_language = session.get('user_language', '')
    interaction_number = session.get('interaction_counter', 1)

    prompt = generate_prompt(situation_description, feelings, support_reason, ia_action, user_age, user_language=user_language)

    try:
        message_history_tuple = tuple(tuple(item.items()) for item in get_message_history())
        response = generate_response(prompt, message_history_tuple, ia_action, use_fine_tuned_model=False)
        formatted_response = format_response(post_process_response(response, ia_action), ia_action)
        add_message_to_history("assistant", formatted_response)

        template_sequence = session['template_sequence']

        if template_sequence:
            next_template = template_sequence.pop(0)
            session['template_sequence'] = template_sequence
            return render_template(next_template + '.html',
                                   initial_description=session['situation_description'],
                                   initial_feelings=session['feelings'],
                                   initial_support_reason=session['support_reason'],
                                   initial_ia_action=session['ia_action'],
                                   additional_info=session['additional_info'],
                                   user_age=session['user_age'],
                                   inferred_age='',  # Adicionar a variável inferida, se necessário
                                   user_language=session['user_language'],
                                   answer=formatted_response)
        else:
            logging.error("Template sequence is empty.")
            return "A conversa chegou ao fim.", 400

    except ValueError as ve:
        logging.error(f"Erro ao processar a resposta: {ve}")
        return "Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.", 500

    except OpenAIError as e:
        logging.error(f"Erro na OpenAI: {e}")
        return "Ocorreu um erro ao processar sua solicitação.", 500

@app.route('/search_professionals', methods=['POST'])
def search_professionals():
    user_location = request.form.get('user_location')
    professional_type = request.form.get('professional_type')

    # Configuração para chamar a API do Bing Search
    bing_api_key = "SUA_CHAVE_DE_API_DO_BING"  # Substitua pela sua chave de API do Bing
    search_url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": bing_api_key}
    params = {
        "q": f"{professional_type} near {user_location}",
        "mkt": "pt-BR",  # Ajuste o mercado para o Brasil
        "safesearch": "Moderate"
    }

    response = requests.get(search_url, headers=headers, params=params)
    search_results = response.json()

    # Log da resposta para verificar a estrutura
    app.logger.debug(f"Search results: {search_results}")

    # Processar os resultados conforme necessário e renderizar um template com os resultados
    return render_template('search_results.html', results=search_results)

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8000)
