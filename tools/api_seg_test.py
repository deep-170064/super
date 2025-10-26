from app import app
import json

with app.test_client() as c:
    # Trigger load-data to ensure sample file is created and stored in session
    r = c.get('/api/load-data')
    print('load-data status:', r.status_code)

    # Call segmentation with empty filters so sample data is used
    payload = {
        'n_clusters': 3,
        'filters': {},
        'encoding': 'utf-8'
    }
    r2 = c.post('/api/customer-segmentation', json=payload)
    print('segmentation status:', r2.status_code)
    try:
        data = r2.get_json()
        import pprint
        pprint.pprint(data)
    except Exception as e:
        print('Failed to parse JSON:', e)
        print(r2.get_data(as_text=True))
