import json
import os

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def extract_license_no(record):
    """在 record (list of dict) 中尋找包含 '許可證字號' 的 dict 並取出其值。"""
    if isinstance(record, list):
        for d in record:
            if isinstance(d, dict) and "許可證字號" in d:
                return d["許可證字號"].strip()
    elif isinstance(record, dict):
        # 若 record 是 dict，直接取用
        return record.get("許可證字號", "").strip()
    return ""

def index_data_by_license(data):
    """對資料進行索引，以許可證字號為 key."""
    index = {}
    for record in data:
        # record可能是dict或list，需要先取得許可證字號
        license_no = extract_license_no(record)
        if license_no:
            index.setdefault(license_no, []).append(record)
    return index

def flatten_record(record_list):
    """
    將詳細資料(或成份、外觀)的巢狀 list of dict 攤平為單一dict。
    若有重複欄位，以最後出現的為準。
    """
    flat = {}
    for d in record_list:
        if isinstance(d, dict):
            flat.update(d)
    return flat

def process_components(components_records):
    """
    成份內容有可能是多層的結構(list of list of dict)，需要攤平成 list of dict。
    假設最終想要的結構為一維 list，每個元素是一個整合好的 dict。
    若原本結構就是 list of dict，則直接使用。
    若是 list of list of dict，須進一步處理。
    """
    processed = []
    for rec in components_records:
        # rec可能是dict或list
        if isinstance(rec, list):
            # 將整個list中所有dict合併成一個dict
            comp_dict = flatten_record(rec)
            if comp_dict:
                processed.append(comp_dict)
        elif isinstance(rec, dict):
            # 已經是單層
            processed.append(rec)
    return processed

def process_appearance(appearance_records):
    """
    外觀資料同樣有可能是巢狀的。
    同 process_components 方式處理。
    """
    processed = []
    for rec in appearance_records:
        if isinstance(rec, list):
            appear_dict = flatten_record(rec)
            if appear_dict:
                processed.append(appear_dict)
        elif isinstance(rec, dict):
            processed.append(rec)
    return processed

def process_detailed(detailed_record):
    """
    詳細資料同樣可能是list，需要攤平成單一dict。
    """
    if isinstance(detailed_record, list):
        return flatten_record(detailed_record)
    elif isinstance(detailed_record, dict):
        return detailed_record
    return {}

def combine_all_data(detailed_data, components_index, appearance_index):
    combined = []
    for detail_item in detailed_data:
        # 將詳細資料攤平成一個 dict
        detail_dict = process_detailed(detail_item)
        license_no = detail_dict.get("許可證字號", "").strip()
        if not license_no:
            continue

        # 從索引中取得成份內容與外觀
        comp_records = components_index.get(license_no, [])
        app_records = appearance_index.get(license_no, [])

        # 將成份、外觀資料攤平為預期格式
        comp_list = process_components(comp_records)
        app_list = process_appearance(app_records)

        combined_item = {
            "詳細資料": detail_dict,
            "成份內容": comp_list,
            "外觀": app_list
        }
        combined.append(combined_item)

    return combined

def main():
    # 指定 JSON 文件的路徑
    detailed_file = "37_3.json"    # 詳細資料
    components_file = "43_3.json"  # 成份內容
    appearance_file = "42_3.json"  # 外觀

    print("開始讀取 JSON 文件...")
    # 讀取 JSON 文件
    detailed_data = load_json(detailed_file)
    components_data = load_json(components_file)
    appearance_data = load_json(appearance_file)
    print("JSON 文件讀取完成。")

    print("建立成份內容索引...")
    # 建立成份內容的索引
    components_index = index_data_by_license(components_data)
    print(f"成份內容索引建立完成，共索引 {len(components_index)} 個許可證字號。")

    print("建立外觀資料索引...")
    # 建立外觀資料的索引
    appearance_index = index_data_by_license(appearance_data)
    print(f"外觀資料索引建立完成，共索引 {len(appearance_index)} 個許可證字號。")

    print("開始整合資料...")
    # 整合所有資料
    combined_data_all = combine_all_data(detailed_data, components_index, appearance_index)
    print(f"資料整合完成，共整合 {len(combined_data_all)} 筆資料。")

    # 將整合後的資料寫入新的 JSON 文件
    output_file = "../combined_data_all.json"
    print(f"將整合後的資料寫入 '{output_file}'...")
    with open(output_file, "w", encoding="utf-8") as outfile:
        json.dump(combined_data_all, outfile, ensure_ascii=False, indent=4)
    print(f"資料已成功整合並儲存在 '{output_file}'。")

if __name__ == "__main__":
    main()
