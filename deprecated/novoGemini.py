from google import genai
import pathlib
from config import GEMINI_API_KEY
from google.genai import types

api_key = GEMINI_API_KEY
if not api_key:
    raise ValueError("A chave GOOGLE_API_KEY não está definida.")

client = genai.Client(api_key=api_key)


files = [
    pathlib.Path('Ato.pdf'),
    pathlib.Path('Portaria.pdf')
]

prompt = "Qual o nome da servidora? Qual seu enquadramento? Qual o tempo de contribuição? Qual o número da portaria?"

contents = [types.Part.from_bytes(data=fp.read_bytes(), mime_type="application/pdf") for fp in files]
contents.append(prompt)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=contents)
print(response.text)

#EXEMPLO DE CONVERSA EM CHAT COM HISTÓRICO DE PERGUNTAS E RESPOSTAS (CONHECIMENTO ACUMULADO)
#chat = client.chats.create(model="gemini-2.5-flash")

#response = chat.send_message("I have 2 dogs in my house.")
#print(response.text)

#response = chat.send_message("How many paws are in my house?")
#print(response.text)

#for message in chat.get_history():
#    print(f'role - {message.role}',end=": ")
#    print(message.parts[0].text)
