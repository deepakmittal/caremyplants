import os
import requests
import time

def test_get_garden_details_new_design():
    base_url = os.environ['BASE_URL']
    
    # Create a garden
    with open('sample.jpeg', 'rb') as f:
        files = {'photos': ('sample.jpeg', f, 'image/jpeg')}
        response = requests.post(f'{base_url}/gardens/upload', files=files)
    
    assert response.status_code == 200
    garden_id = response.json()['id']
    
    # Poll for processing to complete
    for _ in range(30): # 5 minutes timeout
        response = requests.get(f'{base_url}/gardens/{garden_id}/details')
        if response.status_code == 200 and response.json()['status'] == 'Ready':
            break
        time.sleep(10)
    
    # Get garden details
    response = requests.get(f'{base_url}/gardens/{garden_id}/details')
    assert response.status_code == 200
    details = response.json()
    
    # Assert new fields are present
    assert 'needs_watering' in details
    assert 'needs_sunlight' in details
    assert 'has_pests' in details
    assert 'has_disease' in details
    
    # Assert old fields are not present
    assert 'summary' not in details
    assert 'immediate_changes' not in details
    assert 'disease_overview' not in details
    assert 'growth_trend' not in details
    
    # Assert recommendation is truncated
    if details['recommendation']:
        assert len(details['recommendation'].split()) <= 10
    
    assert 'recommendation_full' in details
