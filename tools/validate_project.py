from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cards = sorted((ROOT / "03-歷屆試題").glob("115-第一次-L*/Q??.md"))
    reports = [
        "階段A-PDF稽核清冊.md",
        "階段B-歷屆試題蒐集與驗證.md",
        "階段C-結構化題庫驗證.md",
        "階段D-逐題解析驗證.md",
        "階段E-主題筆記與圖解驗證.md",
        "階段F-備考系統驗證.md",
    ]
    report_dir = ROOT / "08-來源與勘誤"
    markdown_files = list(ROOT.rglob("*.md"))

    checks = {
        "cards": len(cards),
        "reviewed_cards": sum("status: reviewed" in p.read_text(encoding="utf-8") for p in cards),
        "cards_with_solution": sum("### 判斷關鍵" in p.read_text(encoding="utf-8") for p in cards),
        "stage_reports": {name: (report_dir / name).exists() for name in reports},
        "mock_questions": {},
        "markdown_files": len(markdown_files),
        "unbalanced_code_fences": [],
        "unbalanced_display_math": [],
    }
    for subject in ("L21", "L22"):
        mock = (ROOT / "07-模擬考" / f"115-{subject}-模擬考-A.md").read_text(encoding="utf-8")
        checks["mock_questions"][subject] = len(re.findall(r"(?m)^## \d+\. `115-1-", mock))

    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        if len(re.findall(r"(?m)^```", text)) % 2:
            checks["unbalanced_code_fences"].append(str(path.relative_to(ROOT)))
        if len(re.findall(r"\$\$", text)) % 2:
            checks["unbalanced_display_math"].append(str(path.relative_to(ROOT)))

    checks["pass"] = (
        checks["cards"] == 100
        and checks["reviewed_cards"] == 100
        and checks["cards_with_solution"] == 100
        and all(checks["stage_reports"].values())
        and all(value == 50 for value in checks["mock_questions"].values())
        and not checks["unbalanced_code_fences"]
        and not checks["unbalanced_display_math"]
    )
    (report_dir / "project-validation.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "---",
        "title: 專案總驗證報告",
        "tags:",
        "  - iPAS",
        "  - verification",
        "  - complete",
        f"status: {'verified' if checks['pass'] else 'review'}",
        "updated: 2026-10-19",
        "---",
        "",
        "# 專案總驗證報告",
        "",
        f"- 題卡總數：{checks['cards']}（預期 100）",
        f"- 已複核題卡：{checks['reviewed_cards']}（預期 100）",
        f"- 含解析題卡：{checks['cards_with_solution']}（預期 100）",
        f"- L21 模擬考：{checks['mock_questions']['L21']} 題",
        f"- L22 模擬考：{checks['mock_questions']['L22']} 題",
        f"- Markdown 文件：{checks['markdown_files']} 份",
        f"- 未成對程式碼／Mermaid fence：{len(checks['unbalanced_code_fences'])}",
        f"- 未成對 LaTeX 顯示公式界定符：{len(checks['unbalanced_display_math'])}",
        f"- 六階段報告齊全：{'PASS' if all(checks['stage_reports'].values()) else 'FAIL'}",
        "",
        f"## 總結果：{'PASS' if checks['pass'] else 'REVIEW'}",
        "",
        "```mermaid",
        "flowchart LR",
        "    A[階段 A 原始資料] --> B[階段 B 官方來源]",
        "    B --> C[階段 C 100 題題庫]",
        "    C --> D[階段 D 逐題解析]",
        "    D --> E[階段 E 主題與公式]",
        "    E --> F[階段 F 模擬考與錯題本]",
        "    F --> G{總驗證}",
        "    G -->|PASS| H[開始備考循環]",
        "```",
        "",
        "## 已知限制",
        "",
        "1. 官方目前沒有在學習資源頁公開 108～114 年中級試題，因此不能宣稱已取得不存在或不可驗證的官方 PDF。",
        "2. 115 L21 Q28 的公告答案與標準 OEE 推導不一致，已保留為疑義題。",
        "3. 100 題概念題解析為第一版考點解析；後續可再依個人錯題加深每個干擾選項的專項說明。",
        "",
    ]
    (report_dir / "專案總驗證報告.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(checks, ensure_ascii=False))


if __name__ == "__main__":
    main()
