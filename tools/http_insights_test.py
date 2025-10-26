import requests
base = 'http://127.0.0.1:5000'
with requests.Session() as s:
    r1 = s.get(base + '/api/load-data')
    print('load-data status', r1.status_code)
    payload = {'filters': {}, 'encoding': 'utf-8'}
    r2 = s.post(base + '/api/generate-insights', json=payload)
    print('insights status', r2.status_code)
    try:
        print(r2.json())
    except Exception as e:
        print('no json', e)
        print(r2.text)
