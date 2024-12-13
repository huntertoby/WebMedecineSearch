import os
from flask import Flask, request, jsonify, render_template

from DataDownloader import DataDownloader
from DataProcessor import DataProcessor
from SearchEngine import SearchEngine


class App:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_routes()
        self.prepare_and_load_data()

    def prepare_and_load_data(self):
        # 定義下載和處理的URL與檔名
        urls_files = {
            'zips': {
                "detailed_zip": "http://data.fda.gov.tw/opendata/exportDataList.do?method=ExportData&InfoId=37&logType=3",
                "components_zip": "http://data.fda.gov.tw/opendata/exportDataList.do?method=ExportData&InfoId=43&logType=3",
                "appearance_zip": "http://data.fda.gov.tw/opendata/exportDataList.do?method=ExportData&InfoId=42&logType=3"
            },
            'jsons': {
                "detailed": "37_3.json",
                "components": "43_3.json",
                "appearance": "42_3.json"
            }
        }

        downloader = DataDownloader()
        processor = DataProcessor()
        processor.prepare_data(downloader, urls_files)

        self.search_engine = SearchEngine()


    def setup_routes(self):
        @self.app.route("/")
        def home():
            return render_template('index.html')

        @self.app.route("/search", methods=["GET"])
        def search():
            query_value = request.args.get("value", "").strip()
            page = int(request.args.get("page", 1))

            if not query_value:
                return jsonify({"error": "Missing query parameters"}), 400

            if not os.path.exists("combined_data_all.json"):
                return jsonify({"error": "No combined data available"}), 500

            if not self.search_engine:
                return jsonify({"error": "Search engine not initialized"}), 500

            response, status = self.search_engine.search(query_value, page)
            return jsonify(response), status

    def run(self, **kwargs):
        self.app.run(**kwargs)

if __name__ == "__main__":
    # 初始化並運行應用程式
    application = App()
    application.run(debug=False, host="0.0.0.0", port=5000)
