import pytest
from httpx import AsyncClient
from asgi_lifespan import LifespanManager

from backend import main

registering_student_data: main.RegisteringUser = {
    'username': 'neffieta',
    'given_name': 'Neffie Etta',
    'family_name': 'Denile',
    'password': 'password123',
    'account_type': 'student'
}

registering_student: main.RegisteringStudentRequest = {
    'user': registering_student_data,
    'administrator_id': 1
}


@pytest.mark.anyio
async def test_register_student_endpoint():
    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.post('/register/student', json=registering_student)
        assert response.status_code == 200, response.text


@pytest.mark.anyio
async def test_register_student_at_incorrect_endpoint():
    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.post('/register/student', json=registering_student)
        print(response.text)
        assert response.status_code == 400, response.text
        assert response.json()[
            'detail'] == 'Students cannot register via /register. Use /register/student.'
