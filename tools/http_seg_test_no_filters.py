import requests

base = 'http://127.0.0.1:5000'
with requests.Session() as s:
    r1 = s.get(base + '/api/load-data')
    print('load-data status', r1.status_code)
    try:
        print('load-data keys:', list(r1.json().keys()))
    except Exception as e:
        print('load-data no json', e)

    payload = {
        'n_clusters': 3,
        'filters': {},
        'encoding': 'utf-8'
    }

    r2 = s.post(base + '/api/customer-segmentation', json=payload)
    print('segmentation status', r2.status_code)
    try:
        data = r2.json()
        print('seg keys:', list(data.keys()))
        # print clusters summary
        clusters = data.get('clusters')
        print('clusters type:', type(clusters), 'len:', len(clusters) if clusters is not None else 'None')
        if clusters:
            print('first cluster keys:', list(clusters[0].keys()))
    except Exception as e:
        print('seg no json', e)
        print(r2.text)
