#!/usr/bin/env python3
"""
Backend 실행 스크립트 - .env 파일을 로드한 후 uvicorn을 실행합니다.
"""
import os
import sys
from pathlib import Path

# .env 파일 로드
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"✓ .env 파일 로드됨: {env_path}")
    print(f"  LANGFUSE_HOST: {os.getenv('LANGFUSE_HOST', 'NOT SET')}")
else:
    print(f"⚠ .env 파일을 찾을 수 없음: {env_path}")

# uvicorn 실행
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "langflow.main:create_app",
        factory=True,
        host="0.0.0.0",
        port=9000,
        reload=True
    )

