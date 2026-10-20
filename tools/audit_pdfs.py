from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

import pymupdf


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_pdf(path: Path) -> dict:
    with pymupdf.open(path) as document:
        pages = []
        full_text = []
        total_images = 0
        for index, page in enumerate(document):
            text = page.get_text("text")
            image_count = len(page.get_images(full=True))
            total_images += image_count
            full_text.append(text)
            pages.append(
                {
                    "page": index + 1,
                    "text_chars": len(text.strip()),
                    "images": image_count,
                }
            )

        joined = "\n".join(full_text)
        question_numbers = sorted(
            {
                int(match.group(1))
                for match in re.finditer(r"(?m)^\s*(\d{1,3})\.\s*", joined)
                if 1 <= int(match.group(1)) <= 100
            }
        )
        return {
            "file": path.name,
            "relative_path": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "pages": document.page_count,
            "encrypted": document.needs_pass,
            "metadata": document.metadata,
            "text_chars": len(joined.strip()),
            "pages_with_text": sum(p["text_chars"] > 0 for p in pages),
            "embedded_images": total_images,
            "detected_question_numbers": question_numbers,
            "detected_question_count": len(question_numbers),
            "page_details": pages,
        }


def markdown_report(records: list[dict], generated_at: str) -> str:
    lines = [
        "---",
        "title: 階段 A PDF 稽核清冊",
        "tags:",
        "  - iPAS",
        "  - audit",
        "  - source-inventory",
        "status: verified",
        f"generated: {generated_at}",
        "---",
        "",
        "# 階段 A PDF 稽核清冊",
        "",
        "> [!info] 方法",
        "> 使用 PyMuPDF 1.28.2 重新開啟每份 PDF，獨立檢查頁數、加密狀態、文字層、內嵌圖片、題號與 SHA-256。原始 PDF 未被修改。",
        "",
        "| 檔案 | 頁數 | 文字頁 | 文字字元 | 圖片 | 題號數 | 加密 | SHA-256 |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for item in records:
        lines.append(
            f"| {item['file']} | {item['pages']} | {item['pages_with_text']} | "
            f"{item['text_chars']} | {item['embedded_images']} | "
            f"{item['detected_question_count']} | "
            f"{'是' if item['encrypted'] else '否'} | `{item['sha256']}` |"
        )

    all_open = all(not item["encrypted"] for item in records)
    all_text = all(item["pages_with_text"] == item["pages"] for item in records)
    lines.extend(
        [
            "",
            "## 驗證結果",
            "",
            f"- PDF 可直接開啟且未加密：{'PASS' if all_open else 'REVIEW'}",
            f"- 每頁均具有可擷取文字層：{'PASS' if all_text else 'REVIEW'}",
            f"- 已建立 SHA-256：{'PASS' if all(item['sha256'] for item in records) else 'FAIL'}",
            f"- 檔案總數：{len(records)}",
            f"- 總頁數：{sum(item['pages'] for item in records)}",
            "",
            "```mermaid",
            "flowchart LR",
            "    A[原始 PDF] --> B[PyMuPDF 開啟檢查]",
            "    B --> C[頁數與文字層]",
            "    B --> D[題號與圖片]",
            "    A --> E[SHA-256]",
            "    C --> F{完整性檢核}",
            "    D --> F",
            "    E --> F",
            "    F -->|通過| G[進入歷屆試題蒐集]",
            "    F -->|異常| H[人工複核或 OCR]",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()

    pdfs = sorted(args.root.glob("*.pdf"), key=lambda path: path.name)
    records = [inspect_pdf(path) for path in pdfs]
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    payload = {"generated_at": generated_at, "root": str(args.root), "files": records}

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown.write_text(markdown_report(records, generated_at), encoding="utf-8")

    print(json.dumps({"files": len(records), "pages": sum(r["pages"] for r in records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
