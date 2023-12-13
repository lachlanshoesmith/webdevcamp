import os
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')

app = FastAPI()


# user management


@app.post('/register')
async def register():
    return {'message': 'Hello World'}


@app.post('/login')
async def login():
    return {'message': 'hello'}
