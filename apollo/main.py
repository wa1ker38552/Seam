import requests
import json

payload = {
   "sort_ascending": False,
   "sort_by_field":"recommendations_score",
   "organization_locations":["United States"],
   "page":1,
   "organization_num_employees_ranges":[
      "201,500",
      "501,1000",
      "1001,2000"
   ],
   "organization_industry_tag_ids":[
      "5567cdd973696453d93f0000"
   ],
   "display_mode":"explorer_mode",
   "per_page":25,
   "open_factor_names":[
      
   ],
   "num_fetch_result":1,
   "context":"companies-index-page",
   "show_suggestions": False,
   "include_account_engagement_stats": False,
   "finder_version":2,
   "ui_finder_random_seed":"dupg4qyo7ok",
   "typed_custom_fields":[],
   "cacheKey":1734206914687
}

headers = {
    'Content-Type': 'application/json',
    'Origin': 'https://app.apollo.io',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'X-Csrf-Token': 'flNAikQSwicdjORfQiaDnXu20ktldSdqZy4YrTgS661DCaRO3SB4u9V_ZXxP6FPl8Flx4Uwr6u1vO25-y5-BAw'
}

cookies = {
    'Cookie': 'zp__utm_medium=(none); zp__initial_utm_medium=(none); zp__initial_utm_source=(direct); __cf_bm=JlRF.DUFx5HXgA_2b.CFy.g.QEGAjD6B3E7xVQIoRgE-1734206485-1.0.1.1-.UYwgBIiL55g32lhlNUv21GAim8CpvvwLFP2VSdkbORBg0XARhv9PkFaQmdcrxLXpUopAhzG7AGkd0Mm7lr_mA; GCLB=CLjn9PDqsfzAtQEQAw; remember_token_leadgenie_v2=eyJfcmFpbHMiOnsibWVzc2FnZSI6IklqWTNOV1JsTkRNd1lUUmhNMkZoTURGaU1ESTFPVGd3WlY5c1pXRmtaMlZ1YVdWamIyOXJhV1ZvWVhOb0lnPT0iLCJleHAiOiIyMDI1LTAxLTE0VDIwOjAxOjUyLjc2N1oiLCJwdXIiOiJjb29raWUucmVtZW1iZXJfdG9rZW5fbGVhZGdlbmllX3YyIn19--521c7b3348ddc4d19dfc8c3d1fab4c1cac868ad1; zp__initial_referrer=https://accounts.google.com/; zp__utm_source=accounts.google.com; ZP_LATEST_LOGIN_PRICING_VARIANT=24Q3_UC_AA59; ZP_Pricing_Split_Test_Variant=24Q3_UC_AA59; intercom-device-id-dyws6i9m=abad775b-e1f0-409e-aa05-a4a4e1c64bc5; amplitude_id_122a93c7d9753d2fe678deffe8fac4cfapollo.io=eyJkZXZpY2VJZCI6Ijc2OTEyOGY3LTA2YjQtNDAxOS04OWQxLTI1MTM2MzVlNjQ4MlIiLCJ1c2VySWQiOiI2NzVkZTQzMGE0YTNhYTAxYjAyNTk4MGUiLCJvcHRPdXQiOnRydWUsInNlc3Npb25JZCI6MTczNDIwNjUxODY5MywibGFzdEV2ZW50VGltZSI6MTczNDIwNjkxMzM4NywiZXZlbnRJZCI6MCwiaWRlbnRpZnlJZCI6MCwic2VxdWVuY2VOdW1iZXIiOjB9; _dd_s=rum=0&expire=1734207813247; intercom-session-dyws6i9m=UlZ3a2trY1M1YVZTekxwSFZSUDNEMWdiUlRJOE1kanlleDlzWFRjWTRpbDBPQnQ1dEJIaGRIbDdKbDBGcEdnQS0tQnlHc2V1MjBMV09tTXQ1U291VUc2QT09--e619fcfdbc1bdf94789f0e2a8353d0e29cdf50a7; X-CSRF-TOKEN=flNAikQSwicdjORfQiaDnXu20ktldSdqZy4YrTgS661DCaRO3SB4u9V_ZXxP6FPl8Flx4Uwr6u1vO25-y5-BAw; _leadgenie_session=DgDpHWCPNNwDIUZpKwkU9Fw5QXnmSOBOQdbuIOgQ0D0aAtXLfm%2FKR6G5YSrLdyOVtlqulfz457BjLi5NuhZ7FOEpBxmCmIWPbZ0di95HiZPF1d7Y8p3XFMou%2BxddILlP6C%2BTw4v0eyyDzBVkrW0Inwza5G6vsPzXnYao8%2FgNcjspn8bfjtOXvSz87BTgi7sI%2BXkBX40ca01CHoznG2L9NqQhIq3drS5YmoB4DkteQy6PA8Ty1B3K%2FxUrSM8d48Fp2R2XYyMRGx9cvHlga4r%2B2pok%2BPaF8p2uGG0%3D--%2Bs%2FarTObVZnPa3xf--fQBPqqnkRLHbm54vdQwv0g%3D%3D'
}

TOTAL_COMPANIES = 1200
offset = 6
parsed_organizations = []


for i in range(int(TOTAL_COMPANIES/25)):
    print(f'Fetching page: {i+1}')
    payload['page'] = i+1+offset
    r = requests.post('https://app.apollo.io/api/v1/mixed_companies/search', json=payload, headers=headers, cookies=cookies)
    r = r.json()
    try:
        organizations = r['organizations']
        for o in organizations:
            parsed_organizations.append({
                'name': o['name'],
                'linkedin': o['linkedin_url'],
                'website': o['website_url']
            })
    except KeyError:
        print(r)
        break
    
    with open('organizations.json', 'w') as file:
        file.write(json.dumps(parsed_organizations, indent=2))