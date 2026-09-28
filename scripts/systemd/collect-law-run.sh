#!/bin/bash
# collect-law.service가 호출하는 실제 작업 순서.
# docs/11_law_update_pipeline.md 의 기존 crontab 설계(3단계)를 그대로 옮긴 것 —
# 1) 법령 재수집(content_hash 비교로 변경분만 처리) 2) 변경분만 재임베딩 3) qa-cache 전체 삭제 후 재생성
# (법령 내용이 바뀌었는데 예전 캐시된 답변이 계속 나가는 걸 막기 위함, docs/09_qa_cache.md 참고)
#
# 2026-07-08 실측: DELETE만 하고 끝내면, 그 다음 아무 요청이나 먼저 qa-cache에 쓰기를 시도할 때
# OpenSearch가 knn_vector 필드를 매핑 없이 동적 추론(float)해버려서 이후 모든 캐시 조회가
# "knn_vector is not knn_vector type" 에러로 계속 실패한다(=사실상 캐시가 영구적으로 고장남).
# 그래서 삭제 직후 ensureCacheIndex()로 올바른 스키마(knn_vector 타입)를 바로 재생성한다.
#
# 수동 테스트: bash scripts/systemd/collect-law-run.sh
set -e

cd /home/smt17/PROJECTS/RAG_Mazelone
source .venv/bin/activate

python scripts/collect/collect_law.py
python scripts/rag/embed_index.py --index law-articles

curl -sk -u "admin:Secure#Open2024!" -X DELETE https://localhost:9200/qa-cache

python3 -c "
import sys
sys.path.insert(0, 'scripts/common')
sys.path.insert(0, 'scripts/rag')
from mazel_common import loadConfig, getOsClient
from qa_cache import ensureCacheIndex
ensureCacheIndex(getOsClient(loadConfig()))
"
