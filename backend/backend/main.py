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

oauth2Scheme = OAuth2PasswordBearer(tokenUrl='token')


# def createAccessToken(data: dict, expiresDelta: timedelta | None = None):
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
#     toEncode = data.copy()
#     if expiresDelta:
#         expire = datetime.utcnow() + expiresDelta
#     else:
#         expire = datetime.utcnow() + timedelta(minutes=15)
#     toEncode.update({'exp': expire})
#     encodedJWT = jwt.encode(toEncode, SECRET_KEY, algorithm=ALGORITHM)
#     return encodedJWT

# user management routes


@app.get('/items/')
async def readItems(token: Annotated[str, Depends(oauth2Scheme)]):
    return {'token': token}


@app.post('/register')
async def register():
    return {'message': 'Hello World'}


@app.post('/login')
async def login():
    return {'message': 'hello'}
