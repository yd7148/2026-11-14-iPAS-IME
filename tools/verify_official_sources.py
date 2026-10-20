from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path


RESOURCE_BASE = (
    "https://www.ipas.org.tw/api/proxy/uploads/certification_resource/"
    "4ee7f4184b654a3495f586fc869054fd/"
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    names = [
        "115-01-初級智慧生產_L11_生產與作業管理基礎_公告試題_20260608113807.pdf",
        "115-01-初級智慧生產_L12_智慧製造生產線管理基礎_公告試題_20260608113824.pdf",
        "115年第一次中級智慧生產_第一科_智慧製造生產與作業管理之實務應用_公告試題_20260729142554.pdf",
        "115年第一次中級智慧生產_第二科_智慧製造之設備與製程管理之實務應用_公告試題_20260422152024.pdf",
    ]
    results = []
    for name in names:
        url = RESOURCE_BASE + urllib.parse.quote(name)
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            remote_data = response.read()
            content_type = response.headers.get("Content-Type")
        local_data = (args.root / name).read_bytes()
        results.append(
            {
                "file": name,
                "url": url,
                "content_type": content_type,
                "remote_bytes": len(remote_data),
                "local_bytes": len(local_data),
                "remote_sha256": digest(remote_data),
                "local_sha256": digest(local_data),
                "match": digest(remote_data) == digest(local_data),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"checked": len(results), "matched": sum(r["match"] for r in results)}))


if __name__ == "__main__":
    main()
