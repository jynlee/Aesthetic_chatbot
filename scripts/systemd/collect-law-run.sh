#!/bin/bash
# collect-law.service가 호출하는 실제 작업 순서.
# docs/11_law_update_pipeline.md 의 기존 crontab 설계(3단계)를 그대로 옮긴 것 —
# 1) 법령 재수집(content_hash 비교로 변경분만 처리) 2) 변경분만 재임베딩 3) qa-cache 전체 삭제
# (법령 내용이 바뀌었는데 예전 캐시된 답변이 계속 나가는 걸 막기 위함, docs/09_qa_cache.md 참고)
#
# 수동 테스트: bash scripts/systemd/collect-law-run.sh
set -e

cd /home/smt17/PROJECTS/RAG_Mazelone
source .venv/bin/activate

python scripts/collect/collect_law.py
python scripts/rag/embed_index.py --index law-articles

curl -sk -u "admin:Secure#Open2024!" -X DELETE https://localhost:9200/qa-cache
