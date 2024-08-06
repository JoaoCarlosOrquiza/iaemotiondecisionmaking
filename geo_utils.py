import requests
import logging
import os

# Carregar as variáveis de ambiente corretamente
bing_api_key = os.getenv('AZURE_BING_SEARCH_API_KEY')
bing_endpoint = os.getenv('AZURE_BING_SEARCH_ENDPOINT')
bing_maps_key = os.getenv('BING_MAPS_API_KEY')

def get_user_geolocation(address):
    try:
        search_url = f"{bing_endpoint}/v7.0/search"
        params = {
            'q': address,
            'count': 1,
            'offset': 0,
            'mkt': 'en-US',
            'safesearch': 'Moderate'
        }
        headers = {
            'Ocp-Apim-Subscription-Key': bing_api_key
        }
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()
        if search_results.get('resourceSets'):
            location = search_results['resourceSets'][0]['resources'][0]['point']['coordinates']
            return {'latitude': location[0], 'longitude': location[1]}
        else:
            raise ValueError("Nenhum resultado encontrado para o endereço fornecido.")
    except Exception as e:
        logging.error(f"Erro ao converter endereço para coordenadas: {e}")
        raise

def search_nearby_professionals(location, professional_type, radius=5):
    query = f"{professional_type} near {location['latitude']},{location['longitude']}"
    headers = {'Ocp-Apim-Subscription-Key': bing_api_key}
    params = {'q': query, 'count': 10}
    search_url = f"{bing_endpoint}/v7.0/search"
    try:
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()
        return search_results.get('webPages', {}).get('value', [])
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao buscar {query}: {e}")
        raise

def search_nearby_professionals_maps(location, professional_type, radius=5):
    search_url = "http://dev.virtualearth.net/REST/v1/LocalSearch/"
    params = {
        'query': professional_type,
        'userLocation': f"{location['latitude']},{location['longitude']}",
        'key': bing_maps_key,
        'maxResults': 10,
        'radius': radius
    }
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        search_results = response.json()
        if 'resourceSets' in search_results and search_results['resourceSets'][0]['resources']:
            return search_results['resourceSets'][0]['resources']
        else:
            return []
    except Exception as e:
        logging.error(f"Erro ao buscar profissionais com Bing Maps: {e}")
        raise

def format_results(results):
    formatted_results = []
    for result in results:
        formatted_results.append({
            "name": result.get('name', 'Nome não disponível'),
            "url": result.get('url', result.get('Website', '')),
            "snippet": result.get('snippet', result.get('Address', 'Descrição não disponível'))
        })
    return formatted_results
