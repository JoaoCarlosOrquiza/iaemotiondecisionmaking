import openai
import logging
import tiktoken  # type: ignore
import requests
import os

# Configuração do logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Função para gerar decisão com base no contexto, sentimentos e opções fornecidos
def decision_making_prompt(context, feelings, options):
    try:
        openai.api_key = os.getenv('OPENAI_API_KEY')
        logging.debug(f'API Key usada: {openai.api_key}')
        messages = [
            {"role": "system", "content": "Você é um assistente útil."},
            {"role": "user", "content": f"Contexto: {context}\nSentimentos: {feelings}\nOpções: {options}\nDecida:"}
        ]
        logging.debug(f'Mensagens enviadas para OpenAI: {messages}')
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150
        )
        logging.debug(f'Resposta recebida do OpenAI: {response}')
        return response.choices[0].message['content'].strip()
    except Exception as e:
        logging.error(f'Erro ao chamar OpenAI API: {e}')
        return {"error": "Internal server error"}

# Função para contar tokens nas mensagens
def count_tokens(messages):
    try:
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        combined_messages = "\n".join([msg['content'] for msg in messages])
        token_count = len(encoding.encode(combined_messages))
        logging.debug(f'Token count: {token_count}')
        return token_count
    except Exception as e:
        logging.error(f'Erro ao contar tokens: {e}')
        return 0

# Função para geocodificar localização
def geocode_location(location):
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={os.getenv('GOOGLE_API_KEY')}"
        logging.debug(f'URL de geocodificação: {url}')
        response = requests.get(url)
        if response.status_code == 200:
            logging.debug(f'Resposta da geocodificação: {response.json()}')
            return response.json()
        else:
            logging.error(f'Erro na geocodificação: Status Code {response.status_code}')
            return None
    except Exception as e:
        logging.error(f'Erro na geocodificação: {e}')
        return None

# Função para buscar locais de suporte em um raio ao redor de uma localização
def search_support_locations(location, radius):
    try:
        geocoded_location = geocode_location(location)
        if geocoded_location:
            lat_lng = geocoded_location['results'][0]['geometry']['location']
            lat, lng = lat_lng['lat'], lat_lng['lng']
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&key={os.getenv('GOOGLE_API_KEY')}"
            logging.debug(f'URL de busca de locais de suporte: {url}')
            response = requests.get(url)
            if response.status_code == 200:
                logging.debug(f'Resposta da busca de locais de suporte: {response.json()}')
                return response.json()
            else:
                logging.error(f'Erro na busca de locais de suporte: Status Code {response.status_code}')
                return None
        else:
            logging.error('Erro na geocodificação: Localização não encontrada')
            return None
    except Exception as e:
        logging.error(f'Erro na busca de locais de suporte: {e}')
        return None
