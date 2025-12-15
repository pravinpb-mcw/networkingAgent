import os
from langfuse.openai import OpenAI

# Langfuse (replace with your real keys)
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-0e3ab579-b733-4eb2-806c-ec8992b533a0"
# LANGFUSE_SECRET_KEY = "sk-lf-3b7e7816-d943-4f19-94d7-036de2857a8a"
# LANGFUSE_PUBLIC_KEY = "pk-lf-0e3ab579-b733-4eb2-806c-ec8992b533a0"
# LANGFUSE_BASE_URL = "http://localhost:3000"
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-3b7e7816-d943-4f19-94d7-036de2857a8a"
os.environ["LANGFUSE_BASE_URL"] = "http://localhost:3000"

# OpenAI client to LiteLLM Proxy
client = OpenAI(
    api_key="44910560602c44a0abb2607d908e7798.sSjyekht0ZkjJWwz",  # LiteLLM does not validate this
    base_url="https://api.z.ai/api/paas/v4/"  # **Your local proxy**
)

response = client.chat.completions.create(
    model="glm-4.5",    # GLM model through Anthropic route
    messages=[
        {"role": "user", "content": "Explain quantum physics like I'm 10."}
    ],
    max_tokens=200
)

print(response.choices[0].message.content)