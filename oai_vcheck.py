from langfuse.openai import openai
from dotenv import load_dotenv
import os
os.environ["LANGFUSE_BASE_URL"] = "http://localhost:3000"
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-0e3ab579-b733-4eb2-806c-ec8992b533a0"
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-3b7e7816-d943-4f19-94d7-036de2857a8a"
load_dotenv()
client = openai.Client(base_url="https://api.z.ai/api/coding/paas/v4", api_key="60b19768f0334766a3e3259590b14460.QTFX9bVQYgALL0Mj")
# client.base_url = "https://api.z.ai/api/coding/paas/v4"
# client.api_key = "60b19768f0334766a3e3259590b14460.QTFX9bVQYgALL0Mj"
response = client.chat.completions.create(
    model="glm-4.5",
    messages=[
        {"role": "user", "content": "Write a Python function that checks if a number is prime."}
    ],
)
print(response.choices[0].message.content)