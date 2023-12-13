import os
from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Annotated
from pydantic import BaseModel

load_dotenv()

# much of the authentication code is borrowed from fastapi's documentation
# https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    accessToken: str
    tokenType: str


app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


# def create_access_token(data: dict, expires_delta: timedelta | None = None):
#     '''
#     Creates an access token by encoding the given data using JWT.

#     Args:
#         data (dict): The data to be encoded into the access token.
#         expiresDelta (timedelta | None, optional): The time delta representing the expiration time of the access token. Defaults to None.

#     Returns:
#         str: The encoded access token.

#     Raises:
#         <ExceptionType>: <Description of the exception raised, if any.>
#     '''
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(minutes=15)
#     to_encode.update({'exp': expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt

# user management routes


@app.get('/items/')
async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
    return {'token': token}


@app.post('/register')
async def register():
    return {'message': 'Hello World'}


@app.post('/login')
async def login():
    return {'message': 'hello'}
