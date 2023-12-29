from fastapi.testclient import TestClient

from backend import main

client = TestClient(main.app)

registering_student: main.RegisteringUser = {
    'username': 'neffieta',
    'given_name': 'Neffie Etta',
    'family_name': 'Denile',
    'password': 'password123',
    'account_type': 'student'
}


def test_register_student_endpoint():
    response = client.post('/register/student', json=registering_student)
    assert response.status_code == 200


def test_register_student_at_incorrect_endpoint():
    response = client.post('/register', json=registering_student)
    assert response.status_code == 400
    assert response.json()[
        'detail'] == 'Students cannot register via /register. Use /register/student.'
