import pytest
from httpx import AsyncClient
from copy import deepcopy
from backend import main
from .testdata import TestData as d
from .testhelpers import register_administrator, register_student


@pytest.mark.anyio
async def test_register_administrator(test_db):
    res = await register_administrator()
    assert res.status_code == 200, res.text
    assert 'account_id' in res.json()


@pytest.mark.anyio
async def test_register_administrator_with_same_username(test_db):
    res = await register_administrator()
    assert res.status_code == 200

    administrator = deepcopy(d.registering_administrator_data)
    administrator['email'] = 'different_example@gmail.com'
    administrator['family_name'] = 'Example'

    res = await register_administrator(administrator)
    assert res.status_code == 400, res.text
    assert res.json()['detail'] == 'User already exists.'


@pytest.mark.anyio
async def test_register_administrator_with_same_email(test_db):
    res = await register_administrator()
    assert res.status_code == 200

    administrator = deepcopy(d.registering_administrator_data)
    administrator['username'] = 'different_username'
    administrator['family_name'] = 'Example'

    res = await register_administrator(administrator)
    assert res.status_code == 400, res.text
    assert res.json()['detail'] == 'User already exists.'


@pytest.mark.anyio
async def test_register_student(test_db):
    res = await register_administrator()
    assert res.status_code == 200

    student = deepcopy(d.registering_student)
    student['administrator_id'] = res.json()['account_id']

    res = await register_student(student)
    assert res.status_code == 200, res.text
    assert 'student_id' in res.json()


@pytest.mark.anyio
async def test_register_student_with_same_username(test_db):
    res = await register_administrator()
    assert res.status_code == 200

    student = deepcopy(d.registering_student)
    student['administrator_id'] = res.json()['account_id']

    res = await register_student(student)
    assert res.status_code == 200, res.text

    # change some things, but not username
    student['user']['given_name'] = 'Example'
    student['user']['family_name'] = 'Example'

    res = await register_student(student)
    assert res.status_code == 400, res.text
    assert res.json()['detail'] == 'User already exists.'


@pytest.mark.anyio
async def test_register_student_with_nonexistent_administrator(test_db):
    res = register_student(d.registering_student)
    assert res.status_code == 400, res.text
    assert 'does not exist' in res.json()['detail']


@pytest.mark.anyio
async def test_register_student_with_student_as_administrator(test_db):
    # register an administrator for student A (valid)
    res = await register_administrator()
    assert res.status_code == 200

    # register student A using the aforementioned administrator ID
    student = deepcopy(d.registering_student)
    student['administrator_id'] = res.json()['account_id']

    res = await register_student(student)
    assert res.status_code == 200
    student_id = res.json()['student_id']

    # register student B using student A's ID as the administrator ID
    # (this should fail)

    student2 = deepcopy(d.registering_student)
    student2['administrator_id'] = student_id

    res = await register_student(student2)
    assert res.status_code == 400, res.text
    assert 'does not exist' in res.json()['detail']


@pytest.mark.anyio
async def test_register_student_at_incorrect_endpoint(test_db):
    res = await register_administrator(d.registering_student_as_full_account)
    assert res.status_code == 400, res.text
    assert res.json()[
        'detail'] == 'Students cannot register via /register. Use /register/student.'


@pytest.mark.anyio
async def test_register_student_at_incorrect_endpoint_with_incorrect_data_model(test_db):
    res = await register_administrator(d.registering_student)
    assert res.status_code == 422, res.text


@pytest.mark.anyio
async def test_register_student_without_administrator_id(test_db):
    student = deepcopy(d.registering_student)
    del student['administrator_id']

    res = await register_student(student)
    assert res.status_code == 422, res.text


@pytest.mark.anyio
async def test_register_student_without_username(test_db):
    res = await register_administrator()
    assert res.status_code == 200

    student = deepcopy(d.registering_student)
    del student['user']['username']

    res = await register_student(student)
    assert res.status_code == 422, res.text


@pytest.mark.anyio
async def test_register_student_without_password(test_db):
    res = await register_administrator()
    assert res.status_code == 200

    student = deepcopy(d.registering_student)
    del student['user']['hashed_password']

    res = await register_student(student)
    assert res.status_code == 422, res.text


@pytest.mark.anyio
async def test_register_student_without_names(test_db):
    res = await register_administrator()
    assert res.status_code == 200

    student = deepcopy(d.registering_student)
    del student['user']['given_name']
    del student['user']['family_name']

    res = await register_student(student)
    assert res.status_code == 422, res.text


@pytest.mark.anyio
async def test_register_student_without_data(test_db):
    res = register_student({})
    assert res.status_code == 422, res.text


@pytest.mark.anyio
async def test_register_student_with_long_username(test_db):
    res = await register_administrator()
    assert res.status_code == 200

    student = deepcopy(d.registering_student)
    student['administrator_id'] = res.json()['account_id']
    student['user']['username'] = 'abcabcabcabcabcabcabcabc'

    res = register_student(student)
    assert res.status_code == 400, res.text
    assert res.json()['detail'] == 'Username is too long.'


@pytest.mark.anyio
async def test_register_administrator_at_incorrect_endpoint_with_incorrect_data_model(test_db):
    res = register_student(d.registering_administrator_as_student_request)
    assert res.status_code == 400, res.text
    assert res.json()[
        'detail'] == 'Only students may register via /register/student. Use /register.'


@pytest.mark.anyio
async def test_register_administrator_without_data(test_db):
    res = await register_administrator({})
    assert res.status_code == 422, res.text


@pytest.mark.anyio
async def test_register_administrator_with_long_username(test_db):
    administrator = deepcopy(d.registering_administrator_data)
    administrator['username'] = 'abcabcabcabcabcabcabcabc'

    res = await register_administrator(administrator)
    assert res.status_code == 400, res.text
    assert res.json()['detail'] == 'Username is too long.'


@pytest.mark.anyio
async def test_register_adminstrator_without_email(test_db):
    administrator = deepcopy(d.registering_administrator_data)
    del administrator['email']

    res = await register_administrator(administrator)
    assert res.status_code == 422, res.text


@pytest.mark.anyio
async def test_register_adminstrator_without_username(test_db):
    administrator = deepcopy(d.registering_administrator_data)
    del administrator['username']

    res = await register_administrator(administrator)
    assert res.status_code == 422, res.text


@pytest.mark.anyio
async def test_register_adminstrator_without_password(test_db):
    administrator = deepcopy(d.registering_administrator_data)
    del administrator['hashed_password']

    res = await register_administrator(administrator)
    assert res.status_code == 422, res.text


@pytest.mark.anyio
async def test_register_adminstrator_without_names(test_db):
    administrator = deepcopy(d.registering_administrator_data)
    del administrator['given_name']
    del administrator['family_name']

    res = await register_administrator(administrator)
    assert res.status_code == 422, res.text


@pytest.mark.anyio
async def test_register_adminstrator_with_incorrect_types(test_db):
    administrator = deepcopy(d.registering_administrator_data)
    administrator['given_name'] = 4
    administrator['email'] = False

    res = await register_administrator(administrator)
    assert res.status_code == 422, res.text


@pytest.mark.anyio
async def test_register_student_with_incorrect_types(test_db):
    student = deepcopy(d.registering_student)
    student['user']['given_name'] = 4
    student['user']['username'] = [3, 'hello', 2]
    student['administrator_id'] = False

    res = await register_student(student)
    assert res.status_code == 422, res.text
