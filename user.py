#FOR INTEGRATING CHATGPT WITH JARVIS 
from openai import OpenAI
# pip install openai

user = OpenAI(
    api_key="YOUR_API_KEY"
)

completion = user.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a virtual assistant named Jarvis, skilled in general tasks like Alexa and Google Cloud."},
        {"role": "user", "content": "What is coding?"}
    ]
)

print(completion.choices[0].message.content)

