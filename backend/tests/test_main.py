import pytest
from httpx import AsyncClient
from asgi_lifespan import LifespanManager

from backend import main

registering_student_data: main.RegisteringUser = {
    'username': 'neffieta',
    'given_name': 'Neffie Etta',
    'family_name': 'Denile',
    'hashed_password': 'password123',
    'account_type': 'student'
}

registering_administrator_data: main.RegisteringFullUser = {
    'username': 'lachlantula',
    'given_name': 'Lachlan Charles',
    'family_name': 'Shoesmith',
    'hashed_password': 'abjjsfdjsd',
    'account_type': 'administrator',
    'email': 'lachie@example.com',
    'phone_number': '123-456-7890'
}

registering_student: main.RegisteringStudentRequest = {
    'user': registering_student_data,
    'administrator_id': 1
}

registering_student_as_full_account: main.RegisteringFullUser = {
    'username': 'neffieta',
    'given_name': 'Neffie Etta',
    'family_name': 'Denile',
    'hashed_password': 'password123',
    'account_type': 'student',
    'email': 'neffie@gmail.com',
    'phone_number': '123-456-7890'
}


@pytest.mark.anyio
async def test_register_student_endpoint_with_nonexistent_administrator():
    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.post('/register/student', json=registering_student)
        assert response.status_code == 400, response.text
        assert response.json()[
            'detail'] == 'Administrator 1 does not exist.'


@pytest.mark.anyio
async def test_register_student_at_incorrect_endpoint():
    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.post('/register', json=registering_student_as_full_account)
        assert response.status_code == 400, response.text
        assert response.json()[
            'detail'] == 'Students cannot register via /register. Use /register/student.'


@pytest.mark.anyio
async def test_register_student_at_incorrect_endpoint_using_incorrect_data_model():
    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.post('/register', json=registering_student)
        assert response.status_code == 422, response.text
