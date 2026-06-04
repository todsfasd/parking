from flask import Flask, render_template, jsonify
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SEOUL_API_KEY = os.getenv("SEOUL_API_KEY", "").strip()

# 서울시 공영주차장 실시간 주차대수 API
SEOUL_REALTIME_URL = "http://openapi.seoul.go.kr:8088/{key}/json/GetParkingInfo/1/1000/"
# 서울시 공영주차장 안내 정보 API (위도 LAT, 경도 LOT)
SEOUL_PARK_INFO_URL = "http://openapi.seoul.go.kr:8088/{key}/json/GetParkInfo/{start}/{end}/"

COORDS_BY_CODE_TTL_SEC = 3600
_coords_by_code_cache = {"fetched_at": 0.0, "data": {}}


def to_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def to_float(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def is_valid_seoul_coord(lat, lng):
    try:
        la = float(lat)
        ln = float(lng)
        return 33.0 < la < 39.0 and 124.0 < ln < 132.0
    except (TypeError, ValueError):
        return False


def fetch_coords_by_code(api_key):
    now = time.time()
    if _coords_by_code_cache["data"] and now - _coords_by_code_cache["fetched_at"] < COORDS_BY_CODE_TTL_SEC:
        return _coords_by_code_cache["data"]

    coords_by_code = {}
    start = 1
    page_size = 1000

    while True:
        end = start + page_size - 1
        url = SEOUL_PARK_INFO_URL.format(key=api_key, start=start, end=end)
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        api_data = response.json().get("GetParkInfo", {})
        rows = api_data.get("row") or []
        if not rows:
            break

        for item in rows:
            code = str(pick(item, "PKLT_CD", "pklt_cd")).strip()
            if not code:
                continue
            lat = pick(item, "LAT", "lat", default=None)
            lng = pick(item, "LOT", "lot", "LNG", "lng", default=None)
            if is_valid_seoul_coord(lat, lng):
                coords_by_code[code] = {"lat": float(lat), "lng": float(lng)}

        total = int(api_data.get("list_total_count") or 0)
        if end >= total:
            break
        start = end + 1

    _coords_by_code_cache["data"] = coords_by_code
    _coords_by_code_cache["fetched_at"] = now
    return coords_by_code


def pick(item, *keys, default=""):
    for key in keys:
        if key in item and item.get(key) not in (None, ""):
            return item.get(key)
        lower = key.lower()
        upper = key.upper()
        if lower in item and item.get(lower) not in (None, ""):
            return item.get(lower)
        if upper in item and item.get(upper) not in (None, ""):
            return item.get(upper)
    return default


def normalize_parking(item, coords_by_code=None):
    name = pick(item, "PKLT_NM", "pklt_nm")
    address = pick(item, "ADDR", "addr")
    code = str(pick(item, "PKLT_CD", "pklt_cd")).strip()

    total = to_int(pick(item, "TPKCT", "tpkct"), 0)
    current = to_int(pick(item, "NOW_PRK_VHCL_CNT", "now_prk_vhcl_cnt"), 0)
    available = max(total - current, 0)

    lat = to_float(pick(item, "LAT", "lat"))
    lng = to_float(pick(item, "LNG", "lng", "LOT", "lot"))

    if (lat is None or lng is None) and coords_by_code and code in coords_by_code:
        lat = coords_by_code[code]["lat"]
        lng = coords_by_code[code]["lng"]

    if total <= 0:
        status = "정보없음"
    else:
        ratio = available / total
        if ratio >= 0.5:
            status = "여유"
        elif ratio >= 0.2:
            status = "보통"
        else:
            status = "혼잡"

    bsc_hr = pick(item, "BSC_PRK_HR", "bsc_prk_hr", default="")
    bsc_fee = pick(item, "BSC_PRK_CRG", "bsc_prk_crg", default="")
    fee = "요금 정보 없음"
    if bsc_hr != "" and bsc_fee != "":
        fee = f"기본 {bsc_hr}분 {bsc_fee}원"

    return {
        "code": code,
        "name": name,
        "address": address,
        "lat": lat,
        "lng": lng,
        "hasCoords": lat is not None and lng is not None,
        "total": total,
        "current": current,
        "available": available,
        "status": status,
        "fee": fee,
        "phone": pick(item, "TELNO", "telno"),
        "updated": pick(item, "NOW_PRK_VHCL_UPDT_TM", "now_prk_vhcl_updt_tm"),
        "type": pick(item, "PRK_TYPE_NM", "prk_type_nm"),
        "pay": pick(item, "PAY_YN_NM", "pay_yn_nm"),
        "weekday": f"{pick(item, 'WD_OPER_BGNG_TM', 'wd_oper_bgng_tm')}~{pick(item, 'WD_OPER_END_TM', 'wd_oper_end_tm')}",
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/parkings")
def api_parkings():
    if not SEOUL_API_KEY:
        return jsonify({
            "success": False,
            "error": ".env 파일에 SEOUL_API_KEY가 없습니다.",
            "totalCount": 0,
            "coordCount": 0,
            "parkings": []
        }), 500

    try:
        coords_by_code = fetch_coords_by_code(SEOUL_API_KEY)

        url = SEOUL_REALTIME_URL.format(key=SEOUL_API_KEY)
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        api_data = data.get("GetParkingInfo", {})
        rows = api_data.get("row", [])

        all_parkings = [normalize_parking(item, coords_by_code) for item in rows]
        coord_count = sum(1 for p in all_parkings if p["hasCoords"])

        return jsonify({
            "success": True,
            "totalCount": len(all_parkings),
            "coordCount": coord_count,
            "apiMessage": api_data.get("RESULT", {}).get("MESSAGE", ""),
            "parkings": all_parkings,
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "totalCount": 0,
            "coordCount": 0,
            "parkings": []
        }), 500


if __name__ == "__main__":
    # host="0.0.0.0": 같은 Wi-Fi의 휴대폰 등 다른 기기에서도 접속 가능
    # use_reloader=False: 구버전 프로세스가 남아 API/화면이 깨지는 것을 방지
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)