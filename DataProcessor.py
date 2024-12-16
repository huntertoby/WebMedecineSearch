# DataProcessor.py

import json
import os

# DataProcessor負責載入JSON檔案、建立索引和整合資料
class DataProcessor:
    def __init__(self, extract_dir="extracted"):
        self.extract_dir = extract_dir
        self.combined_data_file = "combined_data_all.json"

    def load_json(self, file_path):
        with open(file_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)

    def extract_license_no(self, record):
        if isinstance(record, list):
            for d in record:
                if isinstance(d, dict) and "許可證字號" in d:
                    return d["許可證字號"].strip()
        elif isinstance(record, dict):
            return record.get("許可證字號", "").strip()
        return ""

    def index_data_by_license(self, data):
        index = {}
        for record in data:
            license_no = self.extract_license_no(record)
            if license_no:
                index.setdefault(license_no, []).append(record)
        return index

    def flatten_record(self, record_list):
        flat = {}
        for d in record_list:
            if isinstance(d, dict):
                flat.update(d)
        return flat

    def process_components(self, components_records):
        processed = []
        for rec in components_records:
            if isinstance(rec, list):
                comp_dict = self.flatten_record(rec)
                if comp_dict:
                    processed.append(comp_dict)
            elif isinstance(rec, dict):
                processed.append(rec)
        return processed

    def process_appearance(self, appearance_records):
        processed = []
        for rec in appearance_records:
            if isinstance(rec, list):
                appear_dict = self.flatten_record(rec)
                if appear_dict:
                    processed.append(appear_dict)
            elif isinstance(rec, dict):
                processed.append(rec)
        return processed

    def process_instructions(self, instructions_records):
        """處理藥品介紹資料"""
        processed = []
        for rec in instructions_records:
            if isinstance(rec, list):
                intro_dict = {}
                for item in rec:
                    if isinstance(item, dict):
                        intro_dict.update(item)
                processed.append(intro_dict)
            elif isinstance(rec, dict):
                processed.append(rec)
        return processed

    def process_detailed(self, detailed_record):
        if isinstance(detailed_record, list):
            return self.flatten_record(detailed_record)
        elif isinstance(detailed_record, dict):
            return detailed_record
        return {}

    def combine_all_data(self, detailed_data, components_index, appearance_index, instructions_index):
        combined = []
        for detail_item in detailed_data:
            detail_dict = self.process_detailed(detail_item)
            license_no = detail_dict.get("許可證字號", "").strip()
            if not license_no:
                continue

            comp_records = components_index.get(license_no, [])
            app_records = appearance_index.get(license_no, [])
            instr_records = instructions_index.get(license_no, [])

            comp_list = self.process_components(comp_records)
            app_list = self.process_appearance(app_records)
            instr_list = self.process_instructions(instr_records)

            combined_item = {
                "詳細資料": detail_dict,
                "成份內容": comp_list,
                "外觀": app_list,
                "藥品介紹": instr_list  # 新增藥品介紹
            }
            combined.append(combined_item)

        return combined

    def prepare_data(self, downloader, urls_files):
        # 下載ZIP檔案
        for zip_filename, url in urls_files['zips'].items():
            downloader.download_file(url, zip_filename)

        # 解壓縮檔案
        for zip_filename in urls_files['zips'].keys():
            zip_path = os.path.join(downloader.download_dir, zip_filename)
            if os.path.exists(zip_path):
                downloader.extract_zip(zip_path)

        # 檢查並載入JSON檔案
        json_files = {}
        for key, json_filename in urls_files['jsons'].items():
            json_path = os.path.join(self.extract_dir, json_filename)
            if not os.path.exists(json_path):
                print(f"無法找到 {json_path}，將嘗試使用本地既有的 {self.combined_data_file}")
                if os.path.exists(self.combined_data_file):
                    print("使用既有的 combined_data_all.json。")
                    return
                else:
                    print("無法取得必要檔案，請檢查資料來源。")
                    return
            json_files[key] = self.load_json(json_path)

        # 建立索引
        components_index = self.index_data_by_license(json_files['components'])
        appearance_index = self.index_data_by_license(json_files['appearance'])
        instructions_index = self.index_data_by_license(json_files['Instructions'])  # 新增

        # 整合資料
        combined_data_all = self.combine_all_data(
            json_files['detailed'],
            components_index,
            appearance_index,
            instructions_index  # 新增
        )
        print(f"資料整合完成，共整合 {len(combined_data_all)} 筆資料。")

        # 寫入整合後的資料
        with open(self.combined_data_file, "w", encoding="utf-8") as outfile:
            json.dump(combined_data_all, outfile, ensure_ascii=False, indent=4)
        print(f"資料已成功整合並儲存在 '{self.combined_data_file}'。")
