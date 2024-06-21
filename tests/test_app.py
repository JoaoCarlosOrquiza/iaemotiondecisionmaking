import sys
import os

# Adiciona o diretório principal ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

def test_example():
    assert True

def test_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Home - Flask Server is Running' in response.data

def test_decide(client):
    response = client.post('/decide', json={
        'context': 'Contexto de teste',
        'feelings': 'Sentimentos de teste',
        'options': ['Opção 1', 'Opção 2']
    })
    assert response.status_code == 200
    assert 'decision' in response.json
