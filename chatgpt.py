from dotenv import load_dotenv
import openai
import os
import pandas as pd
import time

# Load .env file
load_dotenv()

# Get the API key
openai.api_key = os.getenv("CHATGPT_API_KEY")

def get_completion(prompt, model="gpt-4o-mini"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message["content"]

# create prompt
prompt = """
sing daisy daisy from 2001 a space odyssey, but slow it down like hal does, 
add like a bunch of letters not a -
"""

response = get_completion(prompt)
print(response)
