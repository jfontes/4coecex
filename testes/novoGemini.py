from google import genai
from config import GEMINI_API_KEY

#EXEMPLO DE CONVERSA EM CHAT COM HISTÓRICO DE PERGUNTAS E RESPOSTAS (CONHECIMENTO ACUMULADO)

api_key = GEMINI_API_KEY
if not api_key:
    raise ValueError("A chave GOOGLE_API_KEY não está definida.")

client = genai.Client(api_key=api_key)

chat = client.chats.create(model="gemini-2.5-flash")

response = chat.send_message("I have 2 dogs in my house.")
print(response.text)

response = chat.send_message("How many paws are in my house?")
print(response.text)

for message in chat.get_history():
    print(f'role - {message.role}',end=": ")
    print(message.parts[0].text)
