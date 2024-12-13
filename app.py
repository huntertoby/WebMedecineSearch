import json
import requests
import os
import zipfile
import difflib
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def index_data_by_license(data):
    index = {}
    for item in data:
        license_no = item.get("許可證字號", "").strip()
        if license_no:
            index.setdefault(license_no, []).append(item)
    return index

def combine_all_data(detailed_data, components_index, appearance_index):
    combined = []
    for detail_item in detailed_data:
        license_no = detail_item.get("許可證字號", "").strip()
        comp = components_index.get(license_no, [])
        app = appearance_index.get(license_no, [])

        combined_item = {
            "詳細資料": detail_item,
            "成份內容": comp,
            "外觀": app
        }
        combined.append(combined_item)
    return combined

def download_file(url, file_path):
    print(f"從 {url} 嘗試下載資料中...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"下載完成並儲存至 {file_path}")
    except requests.exceptions.RequestException as e:
        print(f"下載失敗：{e}")
        # 若下載失敗，若有舊檔案就使用舊檔案
        if os.path.exists(file_path):
            print(f"使用本地檔案 {file_path}。")
        else:
            print(f"無法取得 {file_path} 的資料，請檢查網路或檔案是否存在。")

def extract_zip(file_path, extract_dir="."):
    print(f"解壓縮 {file_path} 中...")
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    print(f"解壓縮完成，檔案已展開至 {extract_dir}")

def prepare_data():
    # 指定解壓後預期產生的JSON檔名
    detailed_json = "37_5.json"
    components_json = "43_5.json"
    appearance_json = "42_5.json"

    # 暫存下載的 ZIP 檔名
    detailed_zip = "37_data.zip"
    components_zip = "43_data.zip"
    appearance_zip = "42_data.zip"

    # 對應開放資料 API URL
    detailed_url = "http://data.fda.gov.tw/opendata/exportDataList.do?method=ExportData&InfoId=37&logType=3"
    components_url = "http://data.fda.gov.tw/opendata/exportDataList.do?method=ExportData&InfoId=43&logType=3"
    appearance_url = "http://data.fda.gov.tw/opendata/exportDataList.do?method=ExportData&InfoId=42&logType=3"

    # 嘗試更新資料(下載ZIP檔)
    download_file(detailed_url, detailed_zip)
    download_file(components_url, components_zip)
    download_file(appearance_url, appearance_zip)

    # 建立存放解壓後檔案的資料夾
    extract_dir = "extracted"
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)

    # 如果存在下載的 zip 檔則解壓縮 (若下載失敗時，zip檔可能不完整，需檢查)
    if os.path.exists(detailed_zip):
        extract_zip(detailed_zip, extract_dir)
    if os.path.exists(components_zip):
        extract_zip(components_zip, extract_dir)
    if os.path.exists(appearance_zip):
        extract_zip(appearance_zip, extract_dir)

    detailed_file = os.path.join(extract_dir, detailed_json)
    components_file = os.path.join(extract_dir, components_json)
    appearance_file = os.path.join(extract_dir, appearance_json)

    # 確認檔案存在
    for f in [detailed_file, components_file, appearance_file]:
        if not os.path.exists(f):
            print(f"無法找到 {f}，將嘗試使用本地既有的 combined_data_all.json")
            # 若無法取得新檔案，但本地已存在 combined_data_all.json，則放棄更新
            if os.path.exists("combined_data_all.json"):
                print("使用既有的 combined_data_all.json。")
                return
            else:
                print("無法取得必要檔案，請檢查資料來源。")
                return

    print("開始讀取 JSON 文件...")
    detailed_data = load_json(detailed_file)
    components_data = load_json(components_file)
    appearance_data = load_json(appearance_file)
    print("JSON 文件讀取完成。")

    print("建立成份內容索引...")
    components_index = index_data_by_license(components_data)
    print(f"成份內容索引建立完成，共索引 {len(components_index)} 個許可證字號。")

    print("建立外觀資料索引...")
    appearance_index = index_data_by_license(appearance_data)
    print(f"外觀資料索引建立完成，共索引 {len(appearance_index)} 個許可證字號。")

    print("開始整合資料...")
    combined_data_all = combine_all_data(detailed_data, components_index, appearance_index)
    print(f"資料整合完成，共整合 {len(combined_data_all)} 筆資料。")

    output_file = "combined_data_all.json"
    print(f"將整合後的資料寫入 '{output_file}'...")
    with open(output_file, "w", encoding="utf-8") as outfile:
        json.dump(combined_data_all, outfile, ensure_ascii=False, indent=4)
    print(f"資料已成功整合並儲存在 '{output_file}'。")

def compute_score(query, item):
    detailed = item.get("詳細資料", {})
    license_no = detailed.get("許可證字號", "")
    en_name = detailed.get("英文品名", "")
    ch_name = detailed.get("中文品名", "")
    indication = detailed.get("適應症", "")

    fields = [license_no, en_name, ch_name, indication]
    score = 0.0
    for field in fields:
        ratio = difflib.SequenceMatcher(None, query.lower(), field.lower()).ratio()
        score += ratio
    return score

@app.route("/")
def home():
    return send_from_directory('static', 'index.html')

@app.route("/search", methods=["GET"])
def search():
    query_value = request.args.get("value", "").strip()
    page = int(request.args.get("page", 1))
    page_size = 2

    if not query_value:
        return jsonify({"error": "Missing query parameters"}), 400

    if not os.path.exists("combined_data_all.json"):
        return jsonify({"error": "No combined data available"}), 500

    with open("combined_data_all.json", "r", encoding="utf-8-sig") as f:
        combined_data = json.load(f)

    scored_items = []
    for item in combined_data:
        score = compute_score(query_value, item)
        if score > 0:
            scored_items.append((score, item))

    scored_items.sort(key=lambda x: x[0], reverse=True)
    if not scored_items:
        return jsonify({"message": "No results found"}), 404

    total = len(scored_items)
    start = (page - 1) * page_size
    end = start + page_size
    paged_results = [x[1] for x in scored_items[start:end]]

    response = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "results": paged_results
    }
    return jsonify(response), 200

prepare_data()

if __name__ == "__main__":
    # 啟動前嘗試更新資料並合併
    prepare_data()
    app.run(debug=True, host="0.0.0.0", port=5000)
