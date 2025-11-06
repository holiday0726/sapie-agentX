#!/usr/bin/env python3
"""
Langfuse 환경변수 로드 테스트
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent / ".env"
print(f"📁 .env 파일 경로: {env_path}")
print(f"📄 .env 파일 존재: {env_path.exists()}")
print()

if env_path.exists():
    load_dotenv(env_path, override=True)
    print("✅ .env 파일 로드 완료")
    print()

# 환경변수 확인
print("🔍 Langfuse 환경변수 확인:")
print(f"  LANGFUSE_SECRET_KEY: {os.getenv('LANGFUSE_SECRET_KEY', 'NOT SET')[:20]}...")
print(f"  LANGFUSE_PUBLIC_KEY: {os.getenv('LANGFUSE_PUBLIC_KEY', 'NOT SET')[:20]}...")
print(f"  LANGFUSE_HOST: {os.getenv('LANGFUSE_HOST', 'NOT SET')}")
print()

# LangFuseTracer 초기화 테스트
print("🧪 LangFuseTracer 초기화 테스트:")
try:
    from langflow.services.tracing.langfuse import LangFuseTracer
    from uuid import uuid4
    
    tracer = LangFuseTracer(
        trace_name="test",
        trace_type="chain",
        project_name="test_project",
        trace_id=uuid4(),
        user_id=None,
        session_id=None,
    )
    
    if tracer.ready:
        print("✅ Langfuse 연결 성공!")
    else:
        print("❌ Langfuse 연결 실패 - tracer.ready = False")
        print("   config가 비어있거나 연결에 실패했습니다.")
        
except Exception as e:
    print(f"❌ 에러 발생: {e}")
    import traceback
    traceback.print_exc()

