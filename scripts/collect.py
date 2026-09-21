import json, re, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DEALS_FILE = DATA / "deals.json"
HISTORY_FILE = DATA / "history.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7",
}

def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()

def won_price(text):
    # 퀘이사존 목록의 ￦12,345 / ₩12,345 형식을 우선 사용
    m = re.search(r"[￦₩]\s*([\d,]+)", text)
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except ValueError:
        return None

def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def normalize_title(title):
    s = re.sub(r"^\[[^\]]+\]\s*", "", title)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s[:160]

def collect_quasarzone():
    url = "https://quasarzone.com/bbs/qb_saleinfo"
    r = requests.get(url, headers=HEADERS, timeout=25)
    print(f"[quasarzone] HTTP {r.status_code}, {len(r.text):,} bytes")
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")
    results, seen = [], set()

    # 현재 퀘이사존 핫딜 글 URL은 /bbs/qb_saleinfo/views/<번호> 형태
    anchors = soup.find_all("a", href=re.compile(r"/bbs/qb_saleinfo/views/\d+"))
    print(f"[quasarzone] deal links found: {len(anchors)}")

    for a in anchors:
        href = a.get("href", "")
        full_url = urljoin("https://quasarzone.com", href)
        if full_url in seen:
            continue

        title = clean(a.get_text(" ", strip=True))
        if not title or "핫딜 게시판 규정" in title:
            continue

        # 링크 주변의 카드/행에서 가격, 카테고리, 조회/시간 텍스트를 찾음.
        block = a
        best_text = ""
        for _ in range(7):
            block = getattr(block, "parent", None)
            if block is None:
                break
            t = clean(block.get_text(" ", strip=True))
            if 20 <= len(t) <= 900:
                best_text = t
            if re.search(r"[￦₩]\s*[\d,]+", t) and ("조회" in t or "배송비" in t):
                best_text = t
                break

        price = won_price(best_text)
        # 가격이 0원인 쿠폰/포인트 글도 목록에는 남김
        shop = ""
        mshop = re.match(r"^\[([^\]]+)\]", title)
        if mshop:
            shop = mshop.group(1)

        category = ""
        for c in ["PC/하드웨어","상품권/쿠폰","게임/SW","노트북/모바일",
                  "가전/TV","생활/식품","패션/의류","포인트/래플","기타"]:
            if c in best_text:
                category = c
                break

        results.append({
            "id": re.search(r"/views/(\d+)", full_url).group(1),
            "source": "quasarzone",
            "source_name": "퀘이사존",
            "title": title,
            "normalized_title": normalize_title(title),
            "price": price,
            "shop": shop,
            "category": category or "기타",
            "url": full_url,
            "meta": best_text[:500],
            "collected_at": datetime.now(timezone.utc).isoformat(),
        })
        seen.add(full_url)

    print(f"[quasarzone] parsed deals: {len(results)}")
    return results

def collect_ppomppu():
    urls = [
        "https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu",
        "https://m.ppomppu.co.kr/new/bbs_list.php?id=ppomppu",
    ]
    results, seen = [], set()
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
            print(f"[ppomppu] HTTP {r.status_code}, {len(r.text):,} bytes")
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")
            for a in soup.find_all("a", href=True):
                href = a.get("href", "")
                if not ("view.php" in href or "bbs_view.php" in href):
                    continue
                title = clean(a.get_text(" ", strip=True))
                if len(title) < 5:
                    continue
                full_url = urljoin(url, href)
                if full_url in seen:
                    continue
                block = a
                text = title
                for _ in range(5):
                    block = getattr(block, "parent", None)
                    if block is None: break
                    t = clean(block.get_text(" ", strip=True))
                    if 10 < len(t) < 700: text = t
                m = re.search(r"([\d,]{2,})\s*원", text)
                price = int(m.group(1).replace(",", "")) if m else None
                ident = re.search(r"(?:no=|num=)(\d+)", full_url)
                results.append({
                    "id": "p" + (ident.group(1) if ident else str(abs(hash(full_url)))),
                    "source": "ppomppu", "source_name": "뽐뿌",
                    "title": title, "normalized_title": normalize_title(title),
                    "price": price, "shop": "", "category": "기타",
                    "url": full_url, "meta": text[:500],
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                })
                seen.add(full_url)
            if results: break
        except Exception as e:
            print(f"[ppomppu] {type(e).__name__}: {e}")
    print(f"[ppomppu] parsed deals: {len(results)}")
    return results[:40]

def update_history(deals):
    old = load_json(HISTORY_FILE, {"items": {}})
    items = old.get("items", {})
    now = datetime.now(timezone.utc).isoformat()

    for d in deals:
        if d.get("price") is None:
            continue
        key = d["normalized_title"]
        rec = items.setdefault(key, {"title": d["title"], "prices": []})
        rec["title"] = d["title"]
        rec["prices"].append({
            "price": d["price"], "at": now, "source": d["source"], "url": d["url"]
        })
        rec["prices"] = rec["prices"][-200:]

        vals = [x["price"] for x in rec["prices"] if isinstance(x.get("price"), int) and x["price"] > 0]
        if vals:
            rec["lowest"] = min(vals)
            rec["average"] = round(sum(vals) / len(vals))

    HISTORY_FILE.write_text(
        json.dumps({"updated_at": now, "items": items}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def main():
    DATA.mkdir(exist_ok=True)
    errors = []
    deals = []

    try:
        deals.extend(collect_quasarzone())
    except Exception as e:
        errors.append(f"quasarzone: {type(e).__name__}: {e}")
        print("[ERROR]", errors[-1])
    try:
        deals.extend(collect_ppomppu())
    except Exception as e:
        errors.append(f"ppomppu: {type(e).__name__}: {e}")
        print("[ERROR]", errors[-1])

    # 중복 URL 제거
    uniq = {d["url"]: d for d in deals}
    deals = list(uniq.values())
    now = datetime.now(timezone.utc).isoformat()

    DEALS_FILE.write_text(
        json.dumps({
            "updated_at": now,
            "count": len(deals),
            "errors": errors,
            "deals": deals
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    update_history(deals)

    print(f"[DealHub] TOTAL: {len(deals)} deals")
    if errors:
        print("[DealHub] WARNINGS:", " | ".join(errors))

    # 0건이면 Action을 성공 처리하지 않음: 문제를 즉시 알 수 있게 함
    if len(deals) == 0:
        print("[DealHub] ERROR: 수집 결과가 0건입니다.", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
