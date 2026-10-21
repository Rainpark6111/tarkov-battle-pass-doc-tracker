#!/usr/bin/env python3
"""Fandom BattlePass 문서를 받아 data.json 으로 저장한다.

- 브라우저가 아닌 서버(GitHub Actions)에서 실행하므로 CORS 제약이 없다.
- 응답이 비정상(표 없음, 시즌 정보 없음)이면 기존 data.json 을 건드리지 않고 실패 처리한다.
"""
import json
import sys
import time
import urllib.parse
import urllib.request

PAGE = "BattlePass"
OUT = "data.json"
UA = "Mozilla/5.0 (compatible; TarkovBattlePassTracker/1.0; +https://github.com/)"


def fetch_html() -> str:
    params = urllib.parse.urlencode({
        "action": "parse",
        "page": PAGE,
        "prop": "text",
        "format": "json",
        "formatversion": "1",
    })
    url = f"https://escapefromtarkov.fandom.com/api.php?{params}"

    last_err = None
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as res:
                data = json.loads(res.read().decode("utf-8"))
            html = data.get("parse", {}).get("text", {}).get("*", "")
            if html:
                return html
            last_err = f"응답에 parse.text 없음: {str(data)[:200]}"
        except Exception as e:  # noqa: BLE001
            last_err = repr(e)
        print(f"[시도 {attempt}/3 실패] {last_err}", file=sys.stderr)
        time.sleep(3 * attempt)

    raise SystemExit(f"위키 데이터를 가져오지 못했습니다: {last_err}")


def main() -> None:
    html = fetch_html()

    if "<table" not in html or "Season" not in html:
        raise SystemExit("응답이 비정상입니다 (표 또는 시즌 정보 없음). data.json 을 갱신하지 않습니다.")

    payload = {"page": PAGE, "html": html}

    # 내용이 같으면 파일을 다시 쓰지 않는다 (불필요한 커밋 방지)
    try:
        with open(OUT, encoding="utf-8") as f:
            if json.load(f).get("html") == html:
                print("변경 없음")
                return
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    payload["fetchedAt"] = int(time.time() * 1000)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    print(f"저장 완료: {OUT} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
