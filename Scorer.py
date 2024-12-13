# Scorer負責計算搜尋分數
import difflib


class Scorer:
    @staticmethod
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