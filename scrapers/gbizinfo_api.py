# scrapers/gbizinfo_api.py
import requests

def get_company_info_from_gbizinfo(company_name):
    base_url = "https://info.gbiz.go.jp/hojin/swagger-ui.html"  # APIエンドポイントのURLを正確に設定
    params = {"name": company_name}
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        return None
