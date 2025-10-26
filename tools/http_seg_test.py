import requests

base = 'http://127.0.0.1:5000'
with requests.Session() as s:
    r1 = s.get(base + '/api/load-data')
    print('load-data status', r1.status_code)
    try:
        print(r1.json())
    except Exception as e:
        print('load-data no json', e)

    payload = {
        'n_clusters': 3,
        'filters': {
            'category': 'All',
            'customer_type': 'All',
            'gender': 'All',
            'date_range': ['2025-01-01', '2025-03-29']
        },
        'encoding': 'utf-8'
    }

    r2 = s.post(base + '/api/customer-segmentation', json=payload)
    print('segmentation status', r2.status_code)
    try:
        print(r2.json())
    except Exception as e:
        print('seg no json', e)
        print(r2.text)
