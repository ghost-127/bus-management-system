from app import app

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['_user_id'] = '1' # assume admin has id 1
    
    response = client.post('/api/timings', json={
        'bus_id': '6', # the event bus from earlier
        'days_of_week': ['Tuesday'],
        'departure_time': '12:00',
        'arrival_time': '13:00',
        'notes': 'Test'
    })
    print('Status Code:', response.status_code)
    print('Response:', response.get_json())
