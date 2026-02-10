#!/bin/bash
# GitHub Actions Secrets 설정을 위한 값 출력 스크립트

echo "========================================="
echo "📋 GitHub Secrets 설정 값"
echo "========================================="
echo ""
echo "아래 값들을 GitHub Repository Settings > Secrets and variables > Actions에 추가하세요."
echo ""
echo "========================================="
echo ""

ENV_FILE="/Users/damee/dev/my-first-skill/daily-focus/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env 파일을 찾을 수 없습니다: $ENV_FILE"
    exit 1
fi

# .env 파일에서 주석과 빈 줄 제외하고 환경변수 추출
grep -v '^#' "$ENV_FILE" | grep -v '^$' | while IFS='=' read -r key value; do
    if [ -n "$key" ] && [ -n "$value" ]; then
        echo "Secret 이름: $key"
        echo "값: $value"
        echo ""
        echo "-----------------------------------------"
        echo ""
    fi
done

echo "========================================="
echo "✅ 총 $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | wc -l | tr -d ' ') 개의 Secret을 추가해야 합니다."
echo "========================================="
echo ""
echo "💡 Tip: 각 Secret을 복사하여 GitHub에 하나씩 추가하세요."
echo ""
