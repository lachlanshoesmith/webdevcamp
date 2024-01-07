from httpx import AsyncClient
from asgi_lifespan import LifespanManager
from .testdata import TestData as d
from backend import main, models


async def register_administrator(administrator_data=d.registering_administrator_data):
    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            res = await ac.post('/register', json=administrator_data)
            return res


async def register_student(student_data=d.registering_student):
    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            res = await ac.post('/register/student', json=student_data)
            return res


async def login(user_data: models.LoggingInUser):
    async with LifespanManager(main.app):
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            res = await ac.post('/login', json=user_data)
            return res
