from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXTRACTED = ROOT / "01-原始擷取"
OUTPUT_ROOT = ROOT / "03-歷屆試題"


@dataclass(frozen=True)
class Exam:
    subject: str
    title: str
    source_md: str
    source_pdf: str
    output_dir: str


EXAMS = [
    Exam(
        subject="L21",
        title="智慧製造生產與作業管理之實務應用",
        source_md="115年第一次中級智慧生產_第一科_智慧製造生產與作業管理之實務應用_公告試題_20260729142554.md",
        source_pdf="115年第一次中級智慧生產_第一科_智慧製造生產與作業管理之實務應用_公告試題_20260729142554.pdf",
        output_dir="115-第一次-L21",
    ),
    Exam(
        subject="L22",
        title="智慧製造之設備與製程管理之實務應用",
        source_md="115年第一次中級智慧生產_第二科_智慧製造之設備與製程管理之實務應用_公告試題_20260422152024.md",
        source_pdf="115年第一次中級智慧生產_第二科_智慧製造之設備與製程管理之實務應用_公告試題_20260422152024.pdf",
        output_dir="115-第一次-L22",
    ),
]


TOPIC_RULES = {
    "MES": ["MES", "製造執行系統"],
    "精實管理": ["精實", "JIT", "看板", "七大浪費", "豐田生產"],
    "生產排程": ["排程", "TOC", "限制理論", "MRP", "RRP", "APP"],
    "產能與線平衡": ["線平衡", "節拍時間", "Takt", "Cycle Time", "週期時間", "產能", "生產力"],
    "OEE與設備效率": ["OEE", "Overall Equipment", "設備使用率", "稼動率", "可動率"],
    "品質管理": ["FMEA", "RPN", "品質", "管制", "魚骨", "良率"],
    "IoT與CPS": ["物聯網", "IoT", "CPS", "網宇實體", "網絡實體"],
    "資料分析": ["資料探勘", "大數據", "巨量資料", "資料前置", "數據"],
    "設備維護": ["維護", "維修", "保養", "點檢", "故障"],
    "機器視覺": ["相機", "視覺", "光源", "FOV", "焦距", "ToF", "結構光"],
    "感測器": ["感測器", "感應器", "位移計", "測溫"],
    "機器人": ["機器人", "機械手臂", "Robotic"],
    "工業通訊": ["MQTT", "TCP/IP", "RS232", "通訊", "資料交換格式"],
    "智慧控制": ["智慧型控制", "控制系統", "基因演算法", "分散式控制"],
    "雲端與邊緣": ["雲端", "邊緣運算", "IaaS", "PaaS", "SaaS"],
}


QUESTION_START = re.compile(r"(?m)^\s*([A-D])\s*\r?\n\s*(\d{1,2})\.\s*")
PAGE_HEADING = re.compile(r"(?m)^## 第 (\d+) 頁\s*$")
OPTION = re.compile(r"\(([A-D])\)")


def page_at(text: str, position: int) -> int | None:
    pages = list(PAGE_HEADING.finditer(text, 0, position))
    return int(pages[-1].group(1)) if pages else None


def clean_block(block: str) -> str:
    skip_patterns = [
        r"^## 第 \d+ 頁$",
        r"^115 年第一次智慧生產工程師-中級能力鑑定【公告試題】$",
        r"^第 \d+ 頁，共 \d+ 頁$",
        r"^第\s*\d+\s*頁，共\s*\d+\s*頁$",
        r"^第一科：.*$",
        r"^第二科：.*$",
        r"^考試日期：.*$",
        r"^答案$",
        r"^題目$",
        r"^---$",
    ]
    kept = []
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if any(re.match(pattern, line) for pattern in skip_patterns):
            continue
        if line:
            kept.append(line)
    text = " ".join(kept)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_question_content(content: str) -> tuple[str, dict[str, str]]:
    matches = list(OPTION.finditer(content))
    if len(matches) < 4:
        return content, {}
    stem = content[: matches[0].start()].strip()
    options = {}
    for index, match in enumerate(matches[:4]):
        end = matches[index + 1].start() if index < 3 else len(content)
        options[match.group(1)] = content[match.end() : end].strip().rstrip("；;")
    return stem, options


def classify(text: str) -> list[str]:
    topics = [topic for topic, terms in TOPIC_RULES.items() if any(term.lower() in text.lower() for term in terms)]
    return topics or ["其他"]


def yaml_list(values: list[str]) -> str:
    return "\n".join(f"  - {value}" for value in values)


def build_exam(exam: Exam) -> dict:
    source_path = EXTRACTED / exam.source_md
    source = source_path.read_text(encoding="utf-8")
    matches = list(QUESTION_START.finditer(source))
    output_dir = OUTPUT_ROOT / exam.output_dir
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for index, match in enumerate(matches):
        answer, number_text = match.groups()
        number = int(number_text)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        content = clean_block(source[match.end() : end])
        stem, options = parse_question_content(content)
        topics = classify(stem + " " + " ".join(options.values()))
        page = page_at(source, match.start())
        question_id = f"115-1-{exam.subject}-Q{number:02d}"
        option_lines = "\n".join(f"- ({key}) {options.get(key, '[擷取缺漏]')}" for key in "ABCD")
        note = f"""---
id: {question_id}
year: 115
session: 1
level: 中級
subject: {exam.subject}
question_no: {number}
topic:
{yaml_list(topics)}
official_answer: {answer}
answer_source: 官方公告試題
source_page: {page if page is not None else 'null'}
verified: false
status: extracted
---

# {question_id}

## 題目

{stem}

{option_lines}

## 官方答案

**{answer}**

## 解題

> [!todo] 待階段 D 完成逐題解析與人工複核。

## 來源

- PDF：`{exam.source_pdf}`
- 頁碼：第 {page} 頁
- 科目：{exam.title}
"""
        (output_dir / f"Q{number:02d}.md").write_text(note, encoding="utf-8")
        records.append(
            {
                "id": question_id,
                "number": number,
                "answer": answer,
                "page": page,
                "topics": topics,
                "stem": stem,
                "options": options,
                "option_count": len(options),
            }
        )

    index_lines = [
        "---",
        f"title: 115 年第一次 {exam.subject} 題目索引",
        "tags:",
        "  - iPAS",
        f"  - {exam.subject}",
        "  - 歷屆試題",
        "status: extracted",
        "---",
        "",
        f"# 115 年第一次 {exam.subject} 題目索引",
        "",
        f"科目：{exam.title}",
        "",
        "| 題號 | 官方答案 | 主題 | 來源頁 |",
        "|---:|:---:|---|---:|",
    ]
    for record in records:
        topics = "、".join(record["topics"])
        index_lines.append(
            f"| [[Q{record['number']:02d}|Q{record['number']:02d}]] | {record['answer']} | {topics} | {record['page']} |"
        )
    index_lines.extend(
        [
            "",
            "```mermaid",
            "flowchart LR",
            f"    A[{exam.subject} 官方試卷] --> B[50 份單題卡片]",
            "    B --> C[題幹與四選項]",
            "    B --> D[官方答案]",
            "    B --> E[考綱主題標籤]",
            "    C --> F[逐題解析]",
            "    D --> F",
            "    E --> F",
            "```",
            "",
        ]
    )
    (output_dir / "00-題目索引.md").write_text("\n".join(index_lines), encoding="utf-8")
    return {
        "subject": exam.subject,
        "title": exam.title,
        "count": len(records),
        "numbers": [r["number"] for r in records],
        "all_four_options": all(r["option_count"] == 4 for r in records),
        "all_answers_valid": all(r["answer"] in "ABCD" for r in records),
        "all_pages_known": all(r["page"] is not None for r in records),
        "records": records,
    }


def main() -> None:
    results = [build_exam(exam) for exam in EXAMS]
    verification = {
        "subjects": results,
        "total_questions": sum(item["count"] for item in results),
        "pass": all(
            item["count"] == 50
            and item["numbers"] == list(range(1, 51))
            and item["all_four_options"]
            and item["all_answers_valid"]
            and item["all_pages_known"]
            for item in results
        ),
    }
    report_dir = ROOT / "08-來源與勘誤"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "question-bank-verification.json").write_text(
        json.dumps(verification, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "---",
        "title: 階段 C 結構化題庫驗證",
        "tags:",
        "  - iPAS",
        "  - question-bank",
        "  - verification",
        f"status: {'verified' if verification['pass'] else 'review'}",
        "updated: 2026-10-19",
        "---",
        "",
        "# 階段 C：結構化題庫驗證",
        "",
        "| 科目 | 題數 | 題號 1–50 | 四選項完整 | 答案有效 | 頁碼完整 |",
        "|---|---:|:---:|:---:|:---:|:---:|",
    ]
    for item in results:
        lines.append(
            f"| {item['subject']} | {item['count']} | "
            f"{'PASS' if item['numbers'] == list(range(1, 51)) else 'FAIL'} | "
            f"{'PASS' if item['all_four_options'] else 'FAIL'} | "
            f"{'PASS' if item['all_answers_valid'] else 'FAIL'} | "
            f"{'PASS' if item['all_pages_known'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            f"**階段結果：{'PASS' if verification['pass'] else 'REVIEW'}**",
            "",
            "```mermaid",
            "flowchart LR",
            "    A[兩份官方卷] --> B[規則式題號切分]",
            "    B --> C[100 份單題 Markdown]",
            "    C --> D{題號連續?}",
            "    C --> E{四選項完整?}",
            "    C --> F{答案 A-D?}",
            "    C --> G{來源頁存在?}",
            "    D --> H[階段 C 驗證]",
            "    E --> H",
            "    F --> H",
            "    G --> H",
            "```",
            "",
        ]
    )
    (report_dir / "階段C-結構化題庫驗證.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"questions": verification["total_questions"], "pass": verification["pass"]}))


if __name__ == "__main__":
    main()
