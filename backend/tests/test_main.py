import pytest
from httpx import AsyncClient
from asgi_lifespan import LifespanManager
from copy import deepcopy

from backend import main
from .testdata import TestData as d

async def register_administrator(administrator_data = d.registering_administrator_data):
    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.post('/register', json=administrator_data)
            return response 

@pytest.mark.anyio
async def test_register_administrator(test_db):
    response = await register_administrator()
    assert response.status_code == 200, response.text
    assert 'account_id' in response.json()

@pytest.mark.anyio
async def test_register_student(test_db):
    res = await register_administrator()
    assert res.status_code == 200
    
    student = deepcopy(d.registering_student)
    student['administrator_id'] = res.json()['account_id']

    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.post('/register/student', json=student)
        assert response.status_code == 200, response.text
        assert 'student_id' in response.json() 

@pytest.mark.anyio
async def test_register_student_with_nonexistent_administrator(test_db):
    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.post('/register/student', json=d.registering_student)
        assert response.status_code == 400, response.text
        assert 'does not exist' in response.json()['detail']


@pytest.mark.anyio
async def test_register_student_at_incorrect_endpoint(test_db):
    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.post('/register', json=d.registering_student_as_full_account)
        assert response.status_code == 400, response.text
        assert response.json()[
            'detail'] == 'Students cannot register via /register. Use /register/student.'


@pytest.mark.anyio
async def test_register_student_at_incorrect_endpoint_with_incorrect_data_model(test_db):
    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.post('/register', json=d.registering_student)
        assert response.status_code == 422, response.text

@pytest.mark.anyio
async def test_register_student_without_administrator_id(test_db):
    student = deepcopy(d.registering_student)
    del student['administrator_id']

    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.post('/register/student', json=student)
        assert response.status_code == 422, response.text

@pytest.mark.anyio
async def test_register_student_without_username(test_db):
    res = await register_administrator()
    assert res.status_code == 200
    
    student = deepcopy(d.registering_student)
    del student['user']['username']

    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.post('/register/student', json=student)
        assert response.status_code == 422, response.text

@pytest.mark.anyio
async def test_register_student_without_password(test_db):
    res = await register_administrator()
    assert res.status_code == 200
    
    student = deepcopy(d.registering_student)
    del student['user']['hashed_password']

    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.post('/register/student', json=student)
        assert response.status_code == 422, response.text

@pytest.mark.anyio
async def test_register_student_without_names(test_db):
    res = await register_administrator()
    assert res.status_code == 200
    
    student = deepcopy(d.registering_student)
    del student['user']['given_name']
    del student['user']['family_name']

    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.post('/register/student', json=student)
        assert response.status_code == 422, response.text

@pytest.mark.anyio
async def test_register_student_without_data(test_db):
    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.post('/register/student', json={})
        assert response.status_code == 422, response.text

@pytest.mark.anyio
async def test_register_student_with_long_username(test_db):
    res = await register_administrator()
    assert res.status_code == 200
    
    student = deepcopy(d.registering_student)
    student['administrator_id'] = res.json()['account_id']
    student['user']['username'] = 'abcabcabcabcabcabcabcabc'

    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.post('/register/student', json=student)
        assert response.status_code == 400, response.text
        assert response.json()['detail'] == 'Username is too long.'


@pytest.mark.anyio
async def test_register_administrator_at_incorrect_endpoint_with_incorrect_data_model(test_db):
    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.post('/register/student', json=d.registering_administrator_as_student_request)
        assert response.status_code == 400, response.text
        assert response.json()[
            'detail'] == 'Only students may register via /register/student. Use /register.'
