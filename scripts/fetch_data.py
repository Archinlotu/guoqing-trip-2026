# -*- coding: utf-8 -*-
# 云端定时抓取: 百度交通实时拥堵榜 + open-meteo 天气 -> data.json
import json
import urllib.request
from datetime import datetime, timezone, timedelta

WATCH = ["武汉", "黄冈", "黄石", "鄂州"]
PLACES = [("三里畈(罗田)", 30.79, 115.32), ("武穴", 29.85, 115.56)]
TRIP_DATES = ("2026-10-02", "2026-10-05")
WMO = {0: "晴", 1: "多云间晴", 2: "多云", 3: "阴", 45: "雾", 48: "雾",
       51: "毛毛雨", 53: "毛毛雨", 55: "毛毛雨", 61: "小雨", 63: "中雨", 65: "大雨",
       66: "冻雨", 67: "冻雨", 71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒",
       80: "阵雨", 81: "强阵雨", 82: "暴雨", 85: "阵雪", 86: "阵雪",
       95: "雷雨", 96: "雷雨冰雹", 99: "雷雨冰雹"}
CST = timezone(timedelta(hours=8))


def fetch(url, referer=None):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    data = {
        "updatedAt": datetime.now(CST).strftime("%Y-%m-%d %H:%M"),
        "watch": [], "top": [], "weather": [],
    }
    try:
        d = fetch("https://jiaotong.baidu.com/trafficindex/city/list",
                  referer="https://jiaotong.baidu.com/")
        lst = d.get("data", {}).get("list", [])
        for c in lst:
            if c["cityname"] in WATCH:
                data["watch"].append({
                    "name": c["cityname"], "index": float(c["index"]),
                    "speed": float(c["speed"]), "level": int(c["index_level"]),
                    "weekRate": float(c.get("weekRate", 0))})
        data["top"] = [{
            "name": c["cityname"], "index": float(c["index"]),
            "speed": float(c["speed"]), "level": int(c["index_level"])
        } for c in lst[:8]]
        if lst:
            data["updatedAt"] = datetime.strptime(
                lst[0]["time"], "%Y%m%d%H%M").strftime("%Y-%m-%d %H:%M")
    except Exception as e:
        print("traffic fetch failed:", e)

    for name, lat, lon in PLACES:
        place = {"name": name, "lat": lat, "lon": lon, "days": []}
        try:
            url = ("https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s"
                   "&daily=temperature_2m_max,temperature_2m_min,"
                   "precipitation_probability_max,weathercode"
                   "&timezone=Asia%%2FShanghai&forecast_days=7") % (lat, lon)
            w = fetch(url)
            dd = w["daily"]
            for i, date in enumerate(dd["time"]):
                if TRIP_DATES[0] <= date <= TRIP_DATES[1]:
                    place["days"].append({
                        "date": date,
                        "tmax": dd["temperature_2m_max"][i],
                        "tmin": dd["temperature_2m_min"][i],
                        "precip": dd["precipitation_probability_max"][i] or 0,
                        "text": WMO.get(dd["weathercode"][i], "—")})
        except Exception as e:
            print("weather fetch failed:", name, e)
        data["weather"].append(place)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("data.json updated:", data["updatedAt"],
          "| watch:", len(data["watch"]), "| top:", len(data["top"]))


if __name__ == "__main__":
    main()
