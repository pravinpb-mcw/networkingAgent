import os
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(
    model="claude-sonnet-4-5-20250929",
    temperature=0,
    max_tokens=1024,
    timeout=None,
    max_retries=2,
    api_key=os.environ.get("ANTHROPIC_API_KEY", "55f27b9278af4b3a83a735e228ae4fb8.2oREoHAH8PdKM13f"),
    base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic"),
)