import os
import logging
import urllib.parse
import re
import json
import subprocess
import sys
from flask import Flask, render_template, request, session, jsonify, send_from_directory
import openai
from openai import OpenAIError
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from prompt_generator import generate_prompt, detect_sensitive_situations
from difflib import get_close_matches
from knowledge import knowledge
from flask_session import Session
from functools import lru_cache
from cachetools import TTLCache
import requests

# Certifique-se de que langdetect esteja instalado
try:
    from langdetect import detect  # Biblioteca para detecção de linguagem
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "langdetect"])
    from langdetect import detect

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações da aplicação Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

# Inicializa a sessão
Session(app)

# Carregar as credenciais da Twilio do arquivo .env
twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')

# Obter as chaves da API do Google Places e Custom Search API
google_places_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
custom_search_api_key = os.getenv('CUSTOM_SEARCH_API_KEY')
custom_search_engine_id = os.getenv('CUSTOM_SEARCH_ENGINE_ID')

# Função para carregar termos de preenchimento automático do arquivo XML
def load_autocompletion_terms(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    terms = []
    for autocompletion in root.findall('Autocompletion'):
        term = autocompletion.get('term')
        if autocompletion.get('type') == '1':
            terms.append(term)
    return terms

# Exemplo de uso: Carregar termos do arquivo XML e imprimir a lista de termos
autocompletion_terms = load_autocompletion_terms('config/autocompletion_terms.xml')
print(autocompletion_terms)

# Função de busca que utiliza os termos carregados para aprimorar as consultas à API do Google Custom Search
def search_custom(query):
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.googleapis.com/customsearch/v1?q={encoded_query}&cx={custom_search_engine_id}&key={custom_search_api_key}"
    
    try:
        logging.debug(f"URL de pesquisa gerada: {search_url}")
        response = requests.get(search_url)
        response.raise_for_status()
        search_results = response.json()
        
        phone_numbers = []
        urls = []
        
        if 'items' in search_results:
            for item in search_results['items']:
                snippet = item.get('snippet', '')
                phone_match = re.search(r'\+?\d[\d\-\(\)\s]+', snippet)
                if phone_match:
                    phone_numbers.append(phone_match.group())
                
                link = item.get('link', '')
                if link:
                    urls.append(link)
        
        return phone_numbers or ["Número de telefone indisponível."], urls or ["URL não encontrada."]
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro de requisição na Custom Search API: {e}")
        return ["Erro de requisição."], ["Erro de requisição."]
    
    except ValueError as ve:
        logging.error(f"Erro ao interpretar o JSON da resposta: {ve}")
        return ["Erro ao processar resposta."], ["Erro ao processar resposta."]
    
    except Exception as e:
        logging.error(f"Erro inesperado ao realizar busca: {e}")
        return ["Erro desconhecido."], ["Erro desconhecido."]

# Função para converter endereço em latitude e longitude
def convert_address_to_lat_lng(address):
    google_maps_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={google_places_api_key}"
    response = requests.get(google_maps_url)
    response.raise_for_status()
    data = response.json()

    if data['status'] == 'OK':
        lat = data['results'][0]['geometry']['location']['lat']
        lng = data['results'][0]['geometry']['location']['lng']
        return lat, lng
    else:
        logging.error(f"Geocoding API error: {data['status']}")
        return None, None

# Função para converter coordenadas em um endereço usando Google Places (Geocodificação Reversa)
def get_user_geolocation(lat, lng):
    try:
        google_places_url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={google_places_api_key}"
        response = requests.get(google_places_url)
        response.raise_for_status()
        location_data = response.json()

        if location_data['status'] == 'OK' and location_data['results']:
            return location_data['results'][0]['formatted_address']
        elif location_data['status'] == 'ZERO_RESULTS':
            logging.info("Nenhum resultado encontrado para as coordenadas fornecidas.")
            return None
        else:
            logging.error(f"Erro na API: {location_data['status']}")
            return None
    except requests.RequestException as e:
        logging.error(f"Falha na requisição: {e}")
        return None

# Função para buscar detalhes de um lugar específico usando a API do Google Places
def get_place_details(place_id):
    details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_phone_number,website,formatted_address,vicinity&key={google_places_api_key}"
    
    try:
        response = requests.get(details_url)
        response.raise_for_status()
        details_data = response.json()
        if details_data['status'] == 'OK':
            return details_data['result']
        else:
            logging.error(f"Erro na API: {details_data['status']}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao obter detalhes para o place_id {place_id}: {e}")
        return None

# Cache com tempo de vida de 10 minutos e máximo de 1000 entradas
cache = TTLCache(maxsize=1000, ttl=600)

# Função para sugerir termos alternativos caso o termo fornecido pelo usuário não seja reconhecido
def suggest_alternatives(input_term, type_map):
    return get_close_matches(input_term, type_map.keys(), n=3, cutoff=0.6)

# Função para buscar profissionais próximos usando integração do Google Places API com a Google Custom Search API
@lru_cache(maxsize=100)
def search_nearby_professionals(location, professional_type):
    # Dicionário de mapeamento para tipos de profissionais e entidades de apoio
    type_map = {
        "suicídio": "crisis_center",
        "morte": "funeral_home",
        "depressão": "psychologist",
        "abuso": "lawyer",
        "assédio": "lawyer",
        "violência": "lawyer",
        "auto-mutilação": "doctor",
        "abuso sexual": "lawyer",
        "estupro": "lawyer",
        "tristeza extrema": "psychologist",
        "desespero": "psychologist",
        "ansiedade severa": "psychologist",
        "pânico": "psychologist",
        "crise emocional": "psychologist",
        "bullying": "lawyer",
        "transtorno de estresse pós-traumático": "psychologist",
        "PTSD": "psychologist",
        "transtorno alimentar": "doctor",
        "anorexia": "doctor",
        "bulimia": "doctor",
        "autoestima baixa": "psychologist",
        "insônia": "doctor",
        "solidão": "psychologist",
        "perda": "funeral_home",
        "luto": "funeral_home",
        "trauma": "psychologist",
        "isolamento": "psychologist",
        "abandono": "lawyer",
        "culpa": "psychologist",
        "vergonha": "psychologist",
        "autolesão": "doctor",
        "drogas": "rehabilitation_center",
        "alcoolismo": "rehabilitation_center",
        "dependência": "rehabilitation_center",
        "vulnerabilidade": "psychologist",
        "medo extremo": "psychologist",
        "raiva intensa": "psychologist",
        "confusão mental": "psychologist",
        "desconexão": "psychologist",
        "apatia": "psychologist",
        "cansaço extremo": "doctor",
        "dificuldade de concentração": "doctor",
        "irritabilidade extrema": "doctor",
        "insegurança": "psychologist",
        "tristeza prolongada": "psychologist",
        "desmotivação": "psychologist",
        "falta de propósito": "psychologist",
        "conflito interno": "psychologist",
        "problemas familiares": "family_therapist",
        "problemas de relacionamento": "family_therapist",
        "pressão social": "psychologist",
        "exigências acadêmicas": "psychologist",
        "pressão no trabalho": "psychologist",
        "terapeuta de casais": "psychologist",
        "psiquiatra": "psychiatrist",
        "psicólogo": "psychologist",
        "hospital": "hospital",
        "consultoria financeira": "finance",
        "ajuda legal": "lawyer",
        "ong": "ngo",
        "grupo de apoio": "support_group",
        "cvv": "crisis_center",
        "apoio para mulheres": "women_support",
        "violência doméstica e familiar contra a mulher": "domestic_violence_center",
        "violência doméstica e sexual contra a mulher": "sexual_violence_center"
    }

    professional_type = professional_type.lower()

    if professional_type not in type_map:
        logging.error(f"Tipo de profissional '{professional_type}' não reconhecido.")
        suggestions = suggest_alternatives(professional_type, type_map)
        return None, suggestions

    logging.debug(f"Buscando profissionais do tipo '{professional_type}', mapeado para '{type_map[professional_type]}'")

    encoded_location = urllib.parse.quote(location)
    google_places_url = (
        f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        f"?location={encoded_location}"
        f"&radius=5000"
        f"&type={type_map.get(professional_type, 'health')}"
        f"&key={google_places_api_key}"
    )

    logging.debug(f"Requisição à API do Google Places com a URL: {google_places_url}")

    try:
        response = requests.get(google_places_url)
        response.raise_for_status()
        location_data = response.json()
        results = location_data.get('results', [])
        
        # Refinar os resultados para garantir que eles correspondam ao termo de busca
        expected_terms = professional_type.split()
        refined_results = refine_results(results, expected_terms)
        
        detailed_results = []
        for result in refined_results:
            place_id = result.get('place_id')
            if place_id:
                details = get_place_details(place_id)
                if details:
                    query = details.get('name') + " " + details.get('vicinity', '')
                    phone_numbers, urls = search_custom(query)
                    details['phone_number'] = phone_numbers[0] if phone_numbers else "indisponível para nosso sistema"
                    details['profile_url'] = urls[0] if urls else None
                    detailed_results.append(details)
        return detailed_results, None
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao realizar busca com Google Places: {e}")
        return None, ["Erro ao realizar busca. Por favor, tente novamente mais tarde."]

# Função para refinar os resultados com base em termos esperados
def refine_results(results, expected_terms):
    refined_results = []
    for result in results:
        description = result.get('name', '').lower() + ' ' + result.get('vicinity', '').lower()
        if any(term in description for term in expected_terms):
            refined_results.append(result)
    return refined_results
        
# Função principal para buscar detalhes e profissionais próximos usando coordenadas
def search_and_get_details(lat, lng, professional_type):
    logging.debug(f"Iniciando busca por profissionais do tipo: {professional_type} com base nas coordenadas: {lat},{lng}")
    
    location = f"{lat},{lng}"
    
    try:
        google_results, suggestions = search_nearby_professionals(location, professional_type)
        logging.debug(f"Resultados de profissionais encontrados: {google_results}")
        if suggestions:
            return [], suggestions
        return google_results, None
    except Exception as e:
        logging.error(f"Erro ao buscar profissionais: {e}")
        return [], ["Erro ao realizar busca. Por favor, tente novamente mais tarde."]

def search_additional_info(query):
    search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&cx={custom_search_engine_id}&key={custom_search_api_key}"
    
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        search_results = response.json()
        additional_info = {}
        
        if search_results.get('items'):
            for item in search_results['items']:
                link = item.get('link')
                snippet = item.get('snippet')
                if link and snippet:
                    additional_info[link] = snippet
        
        return additional_info
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao realizar busca na Custom Search API: {e}")
        return {}
    
    except Exception as e:
        logging.error(f"Erro inesperado ao buscar informações adicionais: {e}")
        return {}

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
    logging.info(f"Enviando feedback para IA: {feedback_message}")

@app.route('/static/<path:filename>')
def send_static(filename):
    return send_from_directory('static', filename)

@app.route('/')
def index():
    logging.debug("Rendering index page")
    return render_template('index.html')

@app.context_processor
def inject_dynamic_script():
    return dict(dynamic_script="""
    <script>
    document.getElementById('situation_description').addEventListener('input', function() {
        const situation = this.value.toLowerCase();
        
        let emotionalKeywords = ["depressão", "ansiedade", "suicídio", "crise emocional"];
        let financialKeywords = ["dívidas", "problemas financeiros", "perda de emprego"];
        let legalKeywords = ["violência", "assédio", "abuso", "disputa legal"];
        
        let iaActionSelect = document.getElementById('ia_action');
        iaActionSelect.innerHTML = ''; // Limpa as opções atuais

        if (emotionalKeywords.some(keyword => situation.includes(keyword))) {
            iaActionSelect.innerHTML += '<option value="emotional">Emotional Health (Saúde Emocional)</option>';
        }
        if (financialKeywords.some(keyword => situation.includes(keyword))) {
            iaActionSelect.innerHTML += '<option value="financial">Financial Health (Saúde Financeira)</option>';
        }
        if (legalKeywords.some(keyword => situation.includes(keyword))) {
            iaActionSelect.innerHTML += '<option value="legal">Legal Support (Suporte Jurídico)</option>';
        }

        if (iaActionSelect.innerHTML === '') {
            iaActionSelect.innerHTML = `
                <option value="emotional">Emotional Health (Saúde Emocional)</option>
                <option value="financial">Financial Health (Saúde Financeira)</option>
                <option value="legal">Legal Support (Suporte Jurídico)</option>
            `;
        }
    });
    </script>
    """)

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
    
    detected_sensitive_keywords = detect_sensitive_situations(situation_description)
    if detected_sensitive_keywords:
        if any(keyword in situation_description.lower() for keyword in ["depressão", "ansiedade", "suicídio", "crise emocional"]):
            session['ia_action'] = 'emotional'
        elif any(keyword in situation_description.lower() for keyword in ["dívidas", "problemas financeiros", "perda de emprego"]):
            session['ia_action'] = 'financial'
        elif any(keyword in situation_description.lower() for keyword in ["violência", "assédio", "abuso", "disputa legal"]):
            session['ia_action'] = 'legal'

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
        logging.debug("Generating response with GPT-4o-mini")
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
                               inferred_age='',
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
    model = "gpt-4o-mini" if not use_fine_tuned_model else fine_tuned_model

    logging.debug(f"Generating response with model: {model}")

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "system", "content": "You are a helpful assistant."}] + [dict(item) for item in message_history_tuple] + [{"role": "user", "content": prompt}],
            max_tokens=1024  # Aumente para 1024 ou 1500 conforme necessário
        )
        response_content = response['choices'][0]['message']['content']
        
        logging.debug(f"Resposta inicial gerada: {response_content}")

        return response_content

    except (OpenAIError, openai.error.APIError, openai.error.APIConnectionError, openai.error.AuthenticationError, openai.error.PermissionError, openai.error.RateLimitError) as e:
        logging.error(f"Erro ao gerar a resposta da IA: {e}")
        raise

def generate_final_response(initial_response_content, relevant_knowledge, message_history):
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
            max_tokens=max_length - len(initial_response_content + relevant_knowledge)
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
    relevant_knowledge = knowledge.get(ia_action, "")
    response = f"{response}\n\n{relevant_knowledge}"
    
    substitutions = {
        "Terapia Cognitivo-Comportamental": "TCC",
        "Identificação e Racionalização dos Pensamentos Automáticos": "<b>Identificação e Racionalização dos Pensamentos Automáticos</b>",
        "(TCC)": "(Teoria Cognitivo-Comportamental)",
        "(ACT)": "(Terapia de Aceitação e Compromisso)",
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
    if "def __init__" in response or "Sequential" in response:
        logging.error("Resposta incoerente detectada, gerando nova resposta")
        raise ValueError("Resposta incoerente gerada pela IA")

    max_length = 4096  # Limite máximo de tokens para GPT-4o-mini
    if len(response) > max_length:
        logging.error(f"Resposta muito longa detectada: {len(response)} tokens")
        raise ValueError("Resposta muito longa gerada pela IA")

    relevant_knowledge = knowledge.get(ia_action, "")
    response = f"{response}\n\n{relevant_knowledge}"
    
    substitutions = {
        "Terapia Cognitivo-Comportamental": "Teoria Cognitivo-Comportamental (TCC)",  
        "Identificação e Racionalização dos Pensamentos Automáticos": "<b>Teoria da Identificação e Racionalização dos Pensamentos Automáticos</b>",  
        "(TCC)": "(Teoria Cognitivo-Comportamental)",  
        "(ACT)": "(Teoria de Aceitação e Compromisso)",  
        "TCC": "Teoria Cognitivo-Comportamental",  
        "ACT": "Teoria de Aceitação e Compromisso (ACT)",  
        "Psicanálise": "<b>Teoria da Psicanálise</b>",  
        "Terapia Comportamental": "<b>Teoria Comportamental</b>"  
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
                                   inferred_age='',
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

@app.route('/get_address', methods=['GET'])
def get_address():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    if lat is None or lng is None or not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        return jsonify({'error': 'Latitude e longitude inválidas ou ausentes'}), 400

    address = get_user_geolocation(lat, lng)
    if address:
        return jsonify({'address': address}), 200
    else:
        return jsonify({'error': 'Endereço não encontrado'}), 404
           
@app.route('/search_results', methods=['POST'])
def render_search_results():
    user_location = request.form.get('user_location')
    professional_type = request.form.get('professional_type')

    # Nova lógica inserida para construir a query e redirecionar para a página de resultados
    query = f"{professional_type} {user_location}"
    return render_template('search_results.html', query=query)

    # Código antigo comentado para desabilitar
    """
    # Carregar termos de autocompletar
    terms = load_autocompletion_terms('config/autocompletion_terms.xml')

    # Converter o endereço para latitude e longitude
    lat, lng = convert_address_to_lat_lng(user_location)
    if not lat or not lng:
        return render_template('search_results.html', success=False, message="Não foi possível determinar as coordenadas para o endereço fornecido. Por favor, verifique o endereço e tente novamente.", terms=terms)

    # Buscar profissionais ou entidades com base no tipo solicitado e localização
    results, suggestions = search_and_get_details(lat, lng, professional_type)

    # Se houver sugestões, retornar um template com as sugestões
    if suggestions:
        return render_template('search_results.html', success=False, suggestions=suggestions, terms=terms)

    # Se não houver resultados, informar o usuário
    if not results:
        return render_template('search_results.html', success=False, message="Nenhum resultado encontrado. Por favor, tente novamente.", terms=terms)

    # Codificar URLs de perfil para garantir que estão corretamente formatadas
    for result in results:
        if 'profile_url' in result and result['profile_url']:
            result['profile_url'] = urllib.parse.quote(result['profile_url'], safe=':/')

    # Retornar os resultados finais renderizando um template HTML
    return render_template('search_results.html', success=True, results=results, terms=terms)
    """

@app.route('/verify_phone', methods=['POST'])
def verify_phone():
    phone_number = request.form.get('phone_number')
    if phone_number:
        phone_details = lookup_phone_number(phone_number)
        return jsonify(phone_details)
    return jsonify({"error": "Phone number is required"}), 400    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
