from openai import OpenAI
client = OpenAI()
prompt = input("Enter your prompt: ")
response = client.responses.create(
    input=prompt,
    model="gpt-5"
)

print(response.output_text)
