elif use_glm:
            try:
                from langchain_anthropic import ChatAnthropic
                ANTHROPIC_AVAILABLE = True
            except ImportError:
                ANTHROPIC_AVAILABLE = False
                print("⚠️ Anthropic not available. Install with: pip install langchain-anthropic")
            if not ANTHROPIC_AVAILABLE:
                print("GLM requires Anthropic client. Install with: pip install langchain-anthropic")
                return None
            
            # GLM through z.ai using Anthropic-compatible API
            glm_api_key = os.getenv("ANTHROPIC_API_KEY", "44910560602c44a0abb2607d908e7798.sSjyekht0ZkjJWwz")
            glm_base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic")
            
            if not glm_api_key or glm_api_key == "YOUR_ZAI_API_KEY":
                print("ANTHROPIC_API_KEY not found for GLM model")
                return None
            
            print("Initializing GLM-4.5 LLM as Latency Monitoring Agent...")
            llm= ChatAnthropic(
                model="glm-4.5",  # GLM model
                anthropic_api_key=glm_api_key,
                base_url=glm_base_url,  # z.ai endpoint
                temperature=0.1,
                max_tokens=1024,
                timeout=30,
                max_retries=3
            )