import openai
import tiktoken  # type: ignore
import requests
import os

def decision_making_prompt(context, feelings, options):
    messages = [
        {"role": "system", "content": "Você é um assistente útil."},
        {"role": "user", "content": f"Contexto: {context}\nSentimentos: {feelings}\nOpções: {options}\nDecida:"}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150
    )
    return response.choices[0].message['content'].strip()

def count_tokens(messages):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    combined_messages = "\n".join([msg['content'] for msg in messages])
    return len(encoding.encode(combined_messages))

def geocode_location(location):
    google_api_key = os.getenv('GOOGLE_API_KEY')
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={google_api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def search_support_locations(location, radius):
    geocoded_location = geocode_location(location)
    if geocoded_location:
        lat_lng = geocoded_location['results'][0]['geometry']['location']
        lat, lng = lat_lng['lat'], lat_lng['lng']
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&key={google_api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    else:
        return None
