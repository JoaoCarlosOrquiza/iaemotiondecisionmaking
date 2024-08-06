import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

def reupload_file(file_path):
    with open(file_path, 'rb') as f:
        response = openai.File.create(
            file=f,
            purpose='batch'
        )
    return response

file_path = "path/to/your/modified/input_prompts.jsonl"
response = reupload_file(file_path)
print(response)
