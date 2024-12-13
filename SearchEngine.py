# SearchEngine負責執行搜尋邏輯
import json
import os

from Scorer import Scorer


class SearchEngine:
    def __init__(self, data_file="combined_data_all.json", page_size=2):
        self.data_file = data_file
        self.page_size = page_size
        self.combined_data = self.load_data()

    def load_data(self):
        if not os.path.exists(self.data_file):
            print(f"無法找到 {self.data_file}。")
            return []
        with open(self.data_file, "r", encoding="utf-8-sig") as f:
            return json.load(f)

    def search(self, query, page=1):
        scorer = Scorer()
        scored_items = []
        for item in self.combined_data:
            score = scorer.compute_score(query, item)
            if score > 0:
                scored_items.append((score, item))

        scored_items.sort(key=lambda x: x[0], reverse=True)
        if not scored_items:
            return {"message": "No results found"}, 404

        total = len(scored_items)
        start = (page - 1) * self.page_size
        end = start + self.page_size
        paged_results = [x[1] for x in scored_items[start:end]]

        response = {
            "total": total,
            "page": page,
            "page_size": self.page_size,
            "pages": (total + self.page_size - 1) // self.page_size,
            "results": paged_results
        }
        return response, 200
