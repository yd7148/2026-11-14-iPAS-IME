from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / "00-首頁.md",
    ROOT / "04-科目筆記" / "L21-生產與作業管理" / "00-L21-MOC.md",
    ROOT / "04-科目筆記" / "L22-設備與製程管理" / "00-L22-MOC.md",
    ROOT / "04-科目筆記" / "共通知識" / "智慧工廠系統架構.md",
    ROOT / "05-公式與圖解" / "公式總表.md",
    ROOT / "05-公式與圖解" / "易混淆比較表.md",
    ROOT / "05-公式與圖解" / "Mermaid-考綱知識圖.md",
]


def resolve_wikilink(source: Path, target: str) -> bool:
    target = target.split("|", 1)[0].split("#", 1)[0]
    if not target:
        return True
    candidate = (source.parent / target).resolve()
    possibilities = [candidate, candidate.with_suffix(".md")]
    if any(path.exists() for path in possibilities):
        return True
    name = Path(target).name + ("" if Path(target).suffix else ".md")
    return any(path.name == name for path in ROOT.rglob("*.md"))


def main() -> None:
    records = []
    for path in TARGETS:
        text = path.read_text(encoding="utf-8")
        links = re.findall(r"\[\[([^\]]+)\]\]", text)
        broken = [link for link in links if not resolve_wikilink(path, link)]
        mermaid_open = len(re.findall(r"```mermaid", text))
        fences = len(re.findall(r"(?m)^```", text))
        display_math = len(re.findall(r"\$\$", text))
        records.append(
            {
                "file": str(path.relative_to(ROOT)),
                "exists": path.exists(),
                "wikilinks": len(links),
                "broken_links": broken,
                "mermaid_blocks": mermaid_open,
                "code_fences_balanced": fences % 2 == 0,
                "display_math_balanced": display_math % 2 == 0,
            }
        )

    passed = all(
        record["exists"]
        and not record["broken_links"]
        and record["code_fences_balanced"]
        and record["display_math_balanced"]
        for record in records
    )
    payload = {"pass": passed, "files": records}
    out_dir = ROOT / "08-來源與勘誤"
    (out_dir / "vault-validation.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "---",
        "title: 階段 E 主題筆記與圖解驗證",
        "tags:",
        "  - iPAS",
        "  - Obsidian",
        "  - verification",
        f"status: {'verified' if passed else 'review'}",
        "updated: 2026-10-19",
        "---",
        "",
        "# 階段 E：主題筆記與圖解驗證",
        "",
        "| 檔案 | Wikilinks | 斷鏈 | Mermaid | Code fence | LaTeX 區塊 |",
        "|---|---:|---:|---:|:---:|:---:|",
    ]
    for record in records:
        lines.append(
            f"| {record['file']} | {record['wikilinks']} | {len(record['broken_links'])} | "
            f"{record['mermaid_blocks']} | {'PASS' if record['code_fences_balanced'] else 'FAIL'} | "
            f"{'PASS' if record['display_math_balanced'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            f"**階段結果：{'PASS' if passed else 'REVIEW'}**",
            "",
            "```mermaid",
            "flowchart LR",
            "    A[首頁] --> B[L21 MOC]",
            "    A --> C[L22 MOC]",
            "    B --> D[公式總表]",
            "    C --> D",
            "    B --> E[共通知識]",
            "    C --> E",
            "    D --> F[歷屆題卡]",
            "    E --> F",
            "```",
            "",
        ]
    )
    (out_dir / "階段E-主題筆記與圖解驗證.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"files": len(records), "pass": passed, "broken": sum(len(r['broken_links']) for r in records)}))


if __name__ == "__main__":
    main()
