#!/bin/bash
# V2G 웹 애플리케이션 설정 스크립트

echo "=== V2G 사업 분석 웹 시스템 설정 ==="

# 가상환경 생성
echo "🔧 Python 가상환경 설정 중..."
python -m venv venv

# 가상환경 활성화 (Windows/Linux 자동 감지)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# 패키지 설치
echo "📦 필요한 패키지 설치 중..."
pip install -r requirements.txt

# templates 디렉토리 생성
echo "📁 디렉토리 구조 생성 중..."
mkdir -p templates
mkdir -p static

echo "✅ 설정 완료!"
echo "🚀 다음 명령어로 서버를 시작하세요:"
echo "   python run_server.py"
echo ""
echo "🌐 브라우저에서 http://localhost:5000 접속"