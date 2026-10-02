# -*- coding: utf-8 -*-
"""
bench_latency.py
RAG 파이프라인의 단계별 응답 시간을 측정하는 벤치마크 스크립트.
QA 캐시를 거치지 않고 runCombinedRag()를 직접 호출하므로, "캐시에 없는 질문"이
들어왔을 때의 실제 소요시간을 잰다.

목적: 쿼리 재작성·멀티턴·Neo4j 등 기능을 추가하기 전에 기준값(baseline)을 남겨두고,
변경 후 같은 질문 세트로 다시 돌려 "응답 속도가 느려지지 않았는지"를 숫자로 비교한다.

전제: OpenSearch / Ollama 가 기동되어 있어야 함 (rag_server.py 는 필요 없음).

사용법:
  python bench_latency.py                          # 법령·안전정보 FAQ에서 고르게 20건
  python bench_latency.py --n 30 --out baseline.json
  python bench_latency.py --compare baseline.json  # 이전 결과와 p50/p95 비교
"""

# ============================================================
# 라이브러리 임포트
# ============================================================

import argparse
import io
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))
from mazel_common import loadConfig, getOsClient
from search_hybrid import ensurePipeline
from rag_pipeline  import runCombinedRag
from warm_cache    import LAW_FAQS, HAZARD_FAQS


# ============================================================
# 상수 정의
# ============================================================

STAGES = ["law_search", "hazard_search", "llm", "suggest_check", "total"]


# ============================================================
# 질문 세트 구성
# ============================================================

def pickQuestions(n):
    """
    warm_cache.py의 FAQ 목록에서 sector별로 고르게 n건을 뽑는다.
    매번 같은 질문이 나오도록 무작위가 아닌 고정 간격으로 고른다 (전후 비교용).
    """
    pool = LAW_FAQS + [{"query": h["query"], "sector": None} for h in HAZARD_FAQS]
    step = max(1, len(pool) // n)
    return pool[::step][:n]


# ============================================================
# 측정 / 집계
# ============================================================

def percentile(values, p):
    """정렬된 값에서 p 백분위수 (최근접 순위 방식)."""
    if not values:
        return 0
    ordered = sorted(values)
    idx     = max(0, math.ceil(p / 100 * len(ordered)) - 1)
    return ordered[idx]


def runBench(osClient, cfg, questions):
    """질문마다 runCombinedRag를 호출하고 단계별 소요시간(ms) 레코드 리스트를 반환."""
    records = []
    for i in range(0, len(questions)):
        item    = questions[i]
        timings = {}
        start   = time.perf_counter()
        try:
            runCombinedRag(osClient, cfg, item["query"], sector=item["sector"], timings=timings)
        except Exception as e:
            print(f"  [{i+1}/{len(questions)}] 실패: {item['query']} — {e}")
            continue
        timings["total"] = round((time.perf_counter() - start) * 1000)
        records.append({"query": item["query"], "sector": item["sector"], "timings": timings})
        stages = " ".join(f"{k}={timings.get(k, 0)}" for k in STAGES)
        print(f"  [{i+1}/{len(questions)}] {stages}  {item['query']}")
    return records


def summarize(records):
    """단계별 p50/p95 (ms) 요약 dict."""
    summary = {}
    for stage in STAGES:
        values = [r["timings"][stage] for r in records if stage in r["timings"]]
        summary[stage] = {"p50": percentile(values, 50), "p95": percentile(values, 95)}
    return summary


def printSummary(summary, baseline=None):
    print(f"\n{'stage':<15}{'p50(ms)':>10}{'p95(ms)':>10}" + (f"{'Δp50':>10}{'Δp95':>10}" if baseline else ""))
    for stage in STAGES:
        row = summary[stage]
        line = f"{stage:<15}{row['p50']:>10}{row['p95']:>10}"
        if baseline and stage in baseline:
            line += f"{row['p50'] - baseline[stage]['p50']:>+10}{row['p95'] - baseline[stage]['p95']:>+10}"
        print(line)


# ============================================================
# 메인
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="RAG 파이프라인 단계별 응답시간 벤치마크")
    parser.add_argument("--n",       type=int, default=20, help="측정할 질문 수 (기본 20)")
    parser.add_argument("--out",     default=None, help="결과를 저장할 JSON 경로")
    parser.add_argument("--compare", default=None, help="비교할 이전 결과 JSON 경로")
    args = parser.parse_args()

    cfg      = loadConfig()
    osClient = getOsClient(cfg)
    ensurePipeline(osClient)

    questions = pickQuestions(args.n)
    print(f"[벤치마크] 질문 {len(questions)}건 (QA 캐시 미사용)")

    # 첫 호출은 Ollama 모델 로딩 시간이 섞이므로 워밍업 1회 후 측정
    print("[워밍업] 모델 로딩용 1회 호출")
    runCombinedRag(osClient, cfg, questions[0]["query"], sector=questions[0]["sector"])

    records = runBench(osClient, cfg, questions)
    summary = summarize(records)

    baseline = None
    if args.compare:
        with io.open(args.compare, encoding="utf-8") as f:
            baseline = json.load(f)["summary"]
    printSummary(summary, baseline)

    if args.out:
        with io.open(args.out, "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "records": records}, f, ensure_ascii=False, indent=2)
        print(f"\n[저장] {args.out}")


if __name__ == "__main__":
    main()
