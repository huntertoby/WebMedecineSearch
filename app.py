# app.py

import os
import json
import logging
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from math import ceil

from DataDownloader import DataDownloader
from DataProcessor import DataProcessor

# 載入環境變數
load_dotenv()

db = SQLAlchemy()


# 定義資料庫模型
class Drug(db.Model):
    __tablename__ = 'drugs'
    id = db.Column(db.Integer, primary_key=True)
    license_number = db.Column(db.String, nullable=True, index=True)
    chinese_name = db.Column(db.String, nullable=True, index=True)
    english_name = db.Column(db.String, nullable=True, index=True)
    indications = db.Column(db.String, nullable=True, index=True)
    dosage = db.Column(db.String, nullable=True)
    manufacturer_country = db.Column(db.String, nullable=True)
    issue_date = db.Column(db.String, nullable=True)
    expiry_date = db.Column(db.String, nullable=True)

    components = db.relationship('Component', backref='drug', lazy=True)
    appearances = db.relationship('Appearance', backref='drug', lazy=True)
    introductions = db.relationship('DrugIntroduction', backref='drug', lazy=True)


class Component(db.Model):
    __tablename__ = 'components'
    id = db.Column(db.Integer, primary_key=True)
    drug_id = db.Column(db.Integer, db.ForeignKey('drugs.id'), nullable=False)
    component_name = db.Column(db.String, nullable=True)
    content = db.Column(db.String, nullable=True)
    unit = db.Column(db.String, nullable=True)


class Appearance(db.Model):
    __tablename__ = 'appearances'
    id = db.Column(db.Integer, primary_key=True)
    drug_id = db.Column(db.Integer, db.ForeignKey('drugs.id'), nullable=False)
    shape = db.Column(db.String, nullable=True)
    color = db.Column(db.String, nullable=True)
    image_url = db.Column(db.String, nullable=True)


class DrugIntroduction(db.Model):
    __tablename__ = 'drug_introductions'
    id = db.Column(db.Integer, primary_key=True)
    drug_id = db.Column(db.Integer, db.ForeignKey('drugs.id'), nullable=False)
    instruction_url = db.Column(db.String, nullable=True)
    box_image_url = db.Column(db.String, nullable=True)


def prepare_and_load_data():
    """下載並處理多個 ZIP / JSON 檔案的流程."""
    # 定義下載和處理的URL與檔名
    urls_files = {
        'zips': {
            "detailed_zip": "http://data.fda.gov.tw/opendata/exportDataList.do?method=ExportData&InfoId=37&logType=3",
            "components_zip": "http://data.fda.gov.tw/opendata/exportDataList.do?method=ExportData&InfoId=43&logType=3",
            "appearance_zip": "http://data.fda.gov.tw/opendata/exportDataList.do?method=ExportData&InfoId=42&logType=3",
            "instructions_zip": "http://data.fda.gov.tw/opendata/exportDataList.do?method=ExportData&InfoId=39&logType=3"
            # 新增
        },
        'jsons': {
            "detailed": "37_3.json",
            "components": "43_3.json",
            "appearance": "42_3.json",
            "Instructions": "39_3.json"  # 新增
        }
    }

    downloader = DataDownloader()
    processor = DataProcessor()
    processor.prepare_data(downloader, urls_files)


def load_data_from_json(json_file_path, app):
    """載入外部 JSON 檔案到資料庫."""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        app.logger.info(f"成功載入 JSON 檔案：{json_file_path}")
    except FileNotFoundError:
        app.logger.info(f"JSON 檔案未找到：{json_file_path}")
        return
    except json.JSONDecodeError as e:
        app.logger.info(f"JSON 解析錯誤：{e}")
        return

    if isinstance(data, dict):
        top_level_keys = data.keys()
        app.logger.info(f"JSON 頂層鍵：{list(top_level_keys)}")
        if 'results' in data:
            items = data['results']
        else:
            app.logger.info("JSON 檔案中缺少 'results' 欄位")
            return
    elif isinstance(data, list):
        items = data
        app.logger.info("JSON 檔案是頂層列表。")
    else:
        app.logger.info("JSON 檔案格式不正確，無法識別資料結構。")
        return

    if not items:
        app.logger.info("JSON 檔案中沒有任何資料。")
        return

    for item in items:
        detailed = item.get('詳細資料', {})
        drug = Drug(
            license_number=detailed.get('許可證字號', ''),
            chinese_name=detailed.get('中文品名', ''),
            english_name=detailed.get('英文品名', ''),
            indications=detailed.get('適應症', ''),
            dosage=detailed.get('用法用量', ''),
            manufacturer_country=detailed.get('製造廠國別', ''),
            issue_date=detailed.get('發證日期', ''),
            expiry_date=detailed.get('有效日期', '')
        )
        db.session.add(drug)
        db.session.flush()  # 讓 SQLAlchemy 先拿到 drug.id

        # 插入成分內容
        components = item.get('成份內容', [])
        for comp in components:
            component = Component(
                drug_id=drug.id,
                component_name=comp.get('成分名稱', ''),
                content=comp.get('含量', ''),
                unit=comp.get('含量單位', '')
            )
            db.session.add(component)

        # 插入外觀
        appearances = item.get('外觀', [])
        for app_item in appearances:
            appearance = Appearance(
                drug_id=drug.id,
                shape=app_item.get('形狀', ''),
                color=app_item.get('顏色', ''),
                image_url=app_item.get('外觀圖檔連結', '')
            )
            db.session.add(appearance)

        # 插入藥品介紹
        introductions = item.get('藥品介紹', [])
        for intro in introductions:
            instruction_url = intro.get("仿單圖檔連結", "")
            box_image_url = intro.get("外盒圖檔連結", "")
            if instruction_url or box_image_url:
                drug_intro = DrugIntroduction(
                    drug_id=drug.id,
                    instruction_url=instruction_url,
                    box_image_url=box_image_url
                )
                db.session.add(drug_intro)

    try:
        db.session.commit()
        app.logger.info("資料已成功載入到資料庫。")
    except Exception as e:
        db.session.rollback()
        app.logger.info(f"資料載入失敗：{e}")


def create_app():
    """應用程式工廠函式：建立 Flask app、初始化資料庫、載入資料。"""
    app = Flask(__name__)

    # 配置資料庫 URI，預設使用 SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///medicine.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 綁定 SQLAlchemy
    db.init_app(app)

    # 以下區塊在應用程式工廠建立後，立刻建立資料表並載入資料
    with app.app_context():
        app.logger.info("建立資料庫表格（如果尚未存在）...")
        db.create_all()
        app.logger.info("資料庫表格建立完成。")

        # 執行下載與處理資料
        prepare_and_load_data()
        # 載入合併後的 JSON 資料至資料庫
        load_data_from_json('combined_data_all.json', app)

    # 定義路由
    @app.route("/")
    def home():
        return render_template('index.html')

    @app.route("/search", methods=["GET"])
    def search():
        query_value = request.args.get("value", "").strip()
        page = request.args.get("page", 1, type=int)
        per_page = 2  # 每頁顯示的結果數量
        has_image = request.args.get("has_image", "false").lower() == "true"

        if not query_value:
            return jsonify({"error": "Missing query parameters"}), 400

        # 使用 SQLAlchemy 進行查詢，搜索中文品名、英文品名和適應症
        drugs_query = Drug.query.filter(
            (Drug.chinese_name.contains(query_value)) |
            (Drug.english_name.contains(query_value)) |
            (Drug.indications.contains(query_value))
        )

        if has_image:
            # 僅搜尋有外觀圖檔者
            drugs_query = drugs_query.join(Appearance).filter(
                Appearance.image_url.isnot(None),
                Appearance.image_url != ""
            )

        # 總結果數量
        total_results = drugs_query.count()
        # 總頁數
        total_pages = ceil(total_results / per_page) if per_page else 1

        # 計算偏移量
        offset = (page - 1) * per_page

        # 使用 limit 和 offset 來實現分頁
        drugs = drugs_query.limit(per_page).offset(offset).all()

        results = []
        for drug in drugs:
            drug_data = {
                "詳細資料": {
                    "許可證字號": drug.license_number,
                    "中文品名": drug.chinese_name,
                    "英文品名": drug.english_name,
                    "適應症": drug.indications,
                    "用法用量": drug.dosage,
                    "製造廠國別": drug.manufacturer_country,
                    "發證日期": drug.issue_date,
                    "有效日期": drug.expiry_date
                },
                "成份內容": [
                    {
                        "成分名稱": comp.component_name,
                        "含量": comp.content,
                        "含量單位": comp.unit
                    } for comp in drug.components
                ],
                "外觀": [
                    {
                        "形狀": app_item.shape,
                        "顏色": app_item.color,
                        "外觀圖檔連結": app_item.image_url
                    } for app_item in drug.appearances
                ],
                "藥品介紹": [
                    {
                        "仿單圖檔連結": intro.instruction_url,
                        "外盒圖檔連結": intro.box_image_url
                    } for intro in drug.introductions
                ]
            }
            results.append(drug_data)

        response = {
            "results": results,
            "pages": total_pages,
            "page": page
        }

        return jsonify(response), 200

    return app


# 建立全域 Flask 應用（供 gunicorn 或其他 WSGI 伺服器呼叫）
app = create_app()

if __name__ == "__main__":
    # 本地端測試或開發時使用 Python 內建伺服器啟動
    app.run(host="0.0.0.0", port=5000, debug=False)
