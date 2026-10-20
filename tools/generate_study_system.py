from __future__ import annotations

import json
import random
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "03-歷屆試題"
MOCK = ROOT / "07-模擬考"
WRONG = ROOT / "06-錯題本"
REPORT = ROOT / "08-來源與勘誤"


def frontmatter(text: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+)$", text)
    if not match:
        raise ValueError(f"Missing {key}")
    return match.group(1).strip()


def topics(text: str) -> list[str]:
    block = re.search(r"(?ms)^topic:\s*\n(.*?)(?=^[A-Za-z_]+:)", text)
    return re.findall(r"(?m)^\s*-\s*(.+)$", block.group(1)) if block else []


def question_block(text: str) -> str:
    match = re.search(r"(?ms)^## 題目\s*\n(.*?)(?=^## 官方答案)", text)
    if not match:
        raise ValueError("Missing question block")
    return match.group(1).strip()


def load_subject(subject: str) -> list[dict]:
    records = []
    for path in sorted((BANK / f"115-第一次-{subject}").glob("Q??.md")):
        text = path.read_text(encoding="utf-8")
        records.append(
            {
                "id": frontmatter(text, "id"),
                "number": int(frontmatter(text, "question_no")),
                "answer": frontmatter(text, "official_answer"),
                "topics": topics(text),
                "block": question_block(text),
                "path": path,
            }
        )
    return records


def build_mock(subject: str, records: list[dict], version: str, seed: int) -> dict:
    ordered = list(records)
    random.Random(seed).shuffle(ordered)
    title = f"115 中級 {subject} 模擬考 {version}"
    lines = [
        "---",
        f"title: {title}",
        "tags:",
        "  - iPAS",
        f"  - {subject}",
        "  - 模擬考",
        "time_limit: 90 minutes",
        "questions: 50",
        "---",
        "",
        f"# {title}",
        "",
        "> [!important] 作答規則",
        "> 90 分鐘內完成 50 題。每題 2 分。不要先開答案卷；完成後記錄總分、主題弱點與粗心原因。",
        "",
        "姓名：＿＿＿＿＿＿　日期：＿＿＿＿＿＿　開始：＿＿＿＿　結束：＿＿＿＿",
        "",
    ]
    answer_lines = [
        "---",
        f"title: {title} 答案卷",
        "tags:",
        "  - iPAS",
        f"  - {subject}",
        "  - 模擬考答案",
        "---",
        "",
        f"# {title} 答案卷",
        "",
        "| 模擬題號 | 原題 ID | 答案 | 題卡 |",
        "|---:|---|:---:|---|",
    ]
    for display_number, record in enumerate(ordered, 1):
        lines.extend(
            [
                f"## {display_number}. `{record['id']}`",
                "",
                record["block"],
                "",
                "作答：□ A　□ B　□ C　□ D",
                "",
            ]
        )
        rel = record["path"].relative_to(ROOT).with_suffix("")
        answer_lines.append(
            f"| {display_number} | {record['id']} | {record['answer']} | [[{rel.as_posix()}|解析]] |"
        )

    MOCK.mkdir(parents=True, exist_ok=True)
    exam_path = MOCK / f"115-{subject}-模擬考-{version}.md"
    answer_path = MOCK / f"115-{subject}-模擬考-{version}-答案.md"
    exam_path.write_text("\n".join(lines), encoding="utf-8")
    answer_path.write_text("\n".join(answer_lines) + "\n", encoding="utf-8")
    return {"exam": exam_path, "answers": answer_path, "count": len(ordered)}


def build_wrong_book(subject: str) -> None:
    text = f"""---
title: {subject} 錯題本
tags:
  - iPAS
  - {subject}
  - 錯題
---

# {subject} 錯題本

## 錯題紀錄

| 日期 | 題目 ID | 我的答案 | 正解 | 錯因 | 主題 | 重做日期 | 已通過 |
|---|---|:---:|:---:|---|---|---|:---:|
|  |  |  |  | 觀念／公式／看錯題意／單位／計算 |  |  |  |

## 單題檢討模板

### 題目 ID

- 我的思路：
- 錯誤發生點：
- 正確判斷關鍵：
- 必背公式／定義：
- 24 小時後重做：
- 7 天後重做：

```mermaid
flowchart LR
    A[答錯] --> B[分類錯因]
    B --> C[回讀主題筆記]
    C --> D[不看答案重做]
    D --> E{{24 小時後正確?}}
    E -- 否 --> C
    E -- 是 --> F[7 天後再測]
```
"""
    WRONG.mkdir(parents=True, exist_ok=True)
    (WRONG / f"{subject}-錯題.md").write_text(text, encoding="utf-8")


def main() -> None:
    MOCK.mkdir(parents=True, exist_ok=True)
    results = []
    frequency = {}
    for subject, seed in [("L21", 11521), ("L22", 11522)]:
        records = load_subject(subject)
        results.append(build_mock(subject, records, "A", seed))
        build_wrong_book(subject)
        frequency[subject] = Counter(topic for record in records for topic in record["topics"])

    dashboard = [
        "---",
        "title: 備考儀表板",
        "tags:",
        "  - iPAS",
        "  - dashboard",
        "  - mock-exam",
        "---",
        "",
        "# 備考儀表板",
        "",
        "## 模擬考紀錄",
        "",
        "| 日期 | 科目 | 版本 | 分數 | 用時 | 概念錯 | 計算錯 | 粗心錯 |",
        "|---|---|---|---:|---:|---:|---:|---:|",
        "|  | L21 | A |  |  |  |  |  |",
        "|  | L22 | A |  |  |  |  |  |",
        "",
        "## 達標標準",
        "",
        "- 每科 90 分鐘內完成。",
        "- 每科至少 80 分。",
        "- 兩科各連續三回達 80 分以上。",
        "- 計算題須能寫出公式與單位，不只記答案。",
        "- 疑義題須知道「官方答案」與「標準推導」的差異。",
        "",
        "## 115 年題目主題標籤頻率",
        "",
        "| 科目 | 主題 | 題數（可複選） |",
        "|---|---|---:|",
    ]
    for subject, counter in frequency.items():
        for topic, count in counter.most_common():
            dashboard.append(f"| {subject} | {topic} | {count} |")
    dashboard.extend(
        [
            "",
            "## 建議四週節奏",
            "",
            "```mermaid",
            "flowchart LR",
            "    W1[第 1 週：考綱與公式] --> W2[第 2 週：100 題逐題理解]",
            "    W2 --> W3[第 3 週：限時模擬與錯題]",
            "    W3 --> W4[第 4 週：弱點回補與二刷]",
            "    W4 --> R{連續三回 80+?}",
            "    R -- 否 --> W3",
            "    R -- 是 --> E[應試準備完成]",
            "```",
            "",
        ]
    )
    (MOCK / "備考儀表板.md").write_text("\n".join(dashboard), encoding="utf-8")

    checks = {
        "mock_files": len(results),
        "all_50_questions": all(item["count"] == 50 for item in results),
        "answer_rows": {},
        "wrong_books": all((WRONG / f"{subject}-錯題.md").exists() for subject in ("L21", "L22")),
    }
    for subject in ("L21", "L22"):
        answer_text = (MOCK / f"115-{subject}-模擬考-A-答案.md").read_text(encoding="utf-8")
        checks["answer_rows"][subject] = len(re.findall(r"(?m)^\| \d+ \|", answer_text))
    checks["pass"] = (
        checks["all_50_questions"]
        and checks["wrong_books"]
        and all(count == 50 for count in checks["answer_rows"].values())
    )
    (REPORT / "study-system-verification.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")

    report = f"""---
title: 階段 F 備考系統驗證
tags:
  - iPAS
  - mock-exam
  - verification
status: {'verified' if checks['pass'] else 'review'}
updated: 2026-10-19
---

# 階段 F：備考系統驗證

| 檢核 | L21 | L22 |
|---|:---:|:---:|
| 模擬考題數 | {'50' if results[0]['count'] == 50 else 'FAIL'} | {'50' if results[1]['count'] == 50 else 'FAIL'} |
| 答案卷題數 | {checks['answer_rows']['L21']} | {checks['answer_rows']['L22']} |
| 錯題本 | {'PASS' if (WRONG / 'L21-錯題.md').exists() else 'FAIL'} | {'PASS' if (WRONG / 'L22-錯題.md').exists() else 'FAIL'} |

**階段結果：{'PASS' if checks['pass'] else 'REVIEW'}**

```mermaid
flowchart LR
    A[50 題模擬考] --> B[答案卷核對]
    B --> C[錯題分類]
    C --> D[24 小時重做]
    D --> E[7 天重做]
    E --> F{{連續三回 80+}}
```
"""
    (REPORT / "階段F-備考系統驗證.md").write_text(report, encoding="utf-8")
    print(json.dumps(checks, ensure_ascii=False))


if __name__ == "__main__":
    main()
