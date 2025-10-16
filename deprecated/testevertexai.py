from google import genai

project="studied-brand-475214-e3"
location="us-central1"
model_name="gemini-2.5-flash"

client = genai.Client(vertexai=True, project=project, location=location)

response = client.models.generate_content(
            model=model_name,
            contents="QUEM É VOCÊ?",
            config=genai.types.GenerateContentConfig(temperature=0.1)
        )
print(response.text)
