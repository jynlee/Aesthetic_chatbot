# -*- coding: utf-8 -*-
"""
bench_compare_answers.py
bench_latency.py 결과 JSON 두 개를 받아 질문별 답변과 LLM 소요시간을 나란히 놓은
마크다운 리포트를 만든다. 설정 변경(예: LLM thinking on/off)이 속도 대신 답변 품질을
얼마나 희생했는지 사람이 직접 판정하기 위한 용도.

사용법:
  python bench_compare_answers.py bench/think_on.json bench/think_off.json --out bench/think_compare.md
"""

# ============================================================
# 라이브러리 임포트
# ============================================================

import argparse
import io
import json


# ============================================================
# 답변 → 텍스트 변환
# ============================================================

def formatAnswer(answer):
    """레코드의 answer dict를 사람이 읽기 좋은 마크다운 줄 리스트로 변환."""
    if not answer:
        return ["(답변 없음)"]
    lines = []
    if answer.get("list_items"):
        for i, item in enumerate(answer["list_items"]):
            lines.append(f"{i+1}. **{item['name']}** — {item['desc']}")
    elif answer.get("summary"):
        lines.append(f"**요약** {answer['summary']}")
        for i, p in enumerate(answer.get("points") or []):
            lines.append(f"{i+1}. **{p['title']}** — {p['body']}")
    else:
        lines.append(f"(형식 파싱 실패) {answer.get('raw_fallback', '')}")
    for s in answer.get("suggestions") or []:
        lines.append(f"- 추천질문: {s}")
    return lines


def loadResult(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def label(result, path):
    cfg = result.get("config") or {}
    if "llm_think" in cfg:
        return f"think={'on' if cfg['llm_think'] else 'off'}"
    return path


# ============================================================
# 리포트 생성
# ============================================================

def buildReport(a, b, labelA, labelB):
    byQueryB = {r["query"]: r for r in b["records"]}
    out = [f"# 답변 비교: {labelA} vs {labelB}", ""]

    out.append("## 속도 요약 (ms)")
    out.append("")
    out.append(f"| stage | {labelA} p50 | {labelB} p50 | {labelA} p95 | {labelB} p95 |")
    out.append("|---|---:|---:|---:|---:|")
    for stage, row in a["summary"].items():
        rb = b["summary"].get(stage, {})
        out.append(f"| {stage} | {row['p50']} | {rb.get('p50', '-')} | {row['p95']} | {rb.get('p95', '-')} |")
    out.append("")

    out.append("## 질문별 답변")
    out.append("")
    for i, ra in enumerate(a["records"]):
        rb = byQueryB.get(ra["query"])
        out.append(f"### {i+1}. {ra['query']}")
        out.append("")
        out.append(f"**{labelA}** · llm {ra['timings'].get('llm', '-')}ms")
        out.append("")
        out.extend(formatAnswer(ra.get("answer")))
        out.append("")
        if rb:
            out.append(f"**{labelB}** · llm {rb['timings'].get('llm', '-')}ms")
            out.append("")
            out.extend(formatAnswer(rb.get("answer")))
        else:
            out.append(f"**{labelB}** · (이 질문 결과 없음)")
        out.append("")
        out.append("판정: [ ] A가 낫다  [ ] 비슷하다  [ ] B가 낫다  메모:")
        out.append("")
        out.append("---")
        out.append("")
    return "\n".join(out)


# ============================================================
# 메인
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="벤치마크 결과 두 개의 답변을 질문별로 비교")
    parser.add_argument("a",     help="기준 결과 JSON (예: think_on.json)")
    parser.add_argument("b",     help="비교 결과 JSON (예: think_off.json)")
    parser.add_argument("--out", required=True, help="저장할 마크다운 경로")
    args = parser.parse_args()

    a, b   = loadResult(args.a), loadResult(args.b)
    report = buildReport(a, b, label(a, args.a), label(b, args.b))
    with io.open(args.out, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[저장] {args.out}")


if __name__ == "__main__":
    main()
