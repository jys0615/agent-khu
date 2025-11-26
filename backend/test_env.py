import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

if api_key:
    print(f"✅ API Key 로드됨: {api_key[:20]}...")
else:
    print("❌ API Key 없음!")
    print("현재 환경변수:", dict(os.environ))
