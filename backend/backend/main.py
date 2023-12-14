import os, psycopg3
from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
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

class User(BaseModel):
    account_id: int,
    given_name: str,
    family_name: str,
    username: str

class FullAccount(User):
    email: str,
    phone_number: str

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str


app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

db_pool = psycopg3.pool.SimpleConnectionPool(
    minconn = 1,
    maxconn = 10,
    host = os.getenv('DB_HOST'),
    port = os.getenv('DB_PORT'),
    user = os.getenv('DB_USERNAME'),
    password = os.getEnv('DB_PASSWORD'),
    database = os.getenv('DB_NAME')
)

def fake_decode_token(token):
    return FullAccount(
        account_id = -1
        given_name = 'Lachlan Charles',
        family_name = 'Shoesmith',
        username = token + 'fakedecoded',
        email = 'fake@gmail.com',
        phone_number = '+61491161258'
    )

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = 'Invalid authentication credentials',
            headers = {'WWW-Authenticate': 'Bearer'},
        )
    return user

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
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(f'''
                select  *
                from    account
                where   username = {form_data.username}
            ''')
            user_data = cur.fetchone()

            if not user_data:
                raise HTTPException(status_code = 400, detail = 'Incorrect username or password')

            # ** is like spread in js
            user = UserInDB(**user_data)

            hashed_password = hash_password(form_data.password)
            if not hashed_password == user['hashed_password']:
                raise HTTPException(status_code = 400, detail = 'Incorrect username or password')
            
            return { 'access_token': get_token(user.account_id), 'token_type': 'bearer' }
    except Error as e:
        raise HTTPException(status_code = 500, detail = f'Database error. {error}')
    finally:
        db_pool.putconn(conn)

@app.get('/users/me')
async def read_users_me(current_user: Annotated[FullAccount, Depends(get_current_user)]):
    return current_user