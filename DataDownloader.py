import os
import zipfile

import requests

# DataDownloader負責下載和解壓縮資料
class DataDownloader:
    def __init__(self, download_dir="downloads", extract_dir="extracted"):
        self.download_dir = download_dir
        self.extract_dir = extract_dir
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.extract_dir, exist_ok=True)

    def download_file(self, url, filename):
        file_path = os.path.join(self.download_dir, filename)
        print(f"從 {url} 嘗試下載資料中...")
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"下載完成並儲存至 {file_path}")
        except requests.exceptions.RequestException as e:
            print(f"下載失敗：{e}")
            if os.path.exists(file_path):
                print(f"使用本地檔案 {file_path}。")
            else:
                print(f"無法取得 {file_path} 的資料，請檢查網路或檔案是否存在。")
        return file_path

    def extract_zip(self, file_path):
        print(f"解壓縮 {file_path} 中...")
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(self.extract_dir)
            print(f"解壓縮完成，檔案已展開至 {self.extract_dir}")
        except zipfile.BadZipFile as e:
            print(f"解壓縮失敗：{e}")