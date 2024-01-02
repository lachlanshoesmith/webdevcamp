import pytest
from httpx import AsyncClient

from backend import main

registering_student: main.RegisteringUser = {
    'username': 'neffieta',
    'given_name': 'Neffie Etta',
    'family_name': 'Denile',
    'password': 'password123',
    'account_type': 'student'
}


@pytest.mark.anyio
async def test_register_student_endpoint():
    async with AsyncClient(app=main.app, base_url='http://test') as nc:
        response = await nc.post('/register/student', json=registering_student)
    assert response.status_code == 200


@pytest.mark.anyio
async def test_register_student_at_incorrect_endpoint():
    async with AsyncClient(app=main.app, base_url='http://test') as nc:
        response = await nc.post('/register/student', json=registering_student)
    assert response.status_code == 400
    assert response.json()[
        'detail'] == 'Students cannot register via /register. Use /register/student.'
