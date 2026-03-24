import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    from app.agent import chat_with_claude_async
    from app.database import SessionLocal
    
    print(f"API Key: {os.getenv('ANTHROPIC_API_KEY')[:20] if os.getenv('ANTHROPIC_API_KEY') else 'None'}...")
    
    db = SessionLocal()
    try:
        result = await chat_with_claude_async("안녕", db)
        print("✅ 성공!")
        print(f"응답: {result.get('message', '')}")
    except Exception as e:
        print(f"❌ 에러: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

asyncio.run(test())
