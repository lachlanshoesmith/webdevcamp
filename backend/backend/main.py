from enum import Enum
import os
from psycopg_pool import AsyncConnectionPool
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Annotated, Union
from pydantic import BaseModel
from datetime import datetime, timedelta
from psycopg import IntegrityError

load_dotenv()

# much of the authentication code is borrowed from fastapi's documentation
# https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class User(BaseModel):
    account_id: int
    given_name: str
    family_name: str
    username: str


class FullAccount(User):
    email: str
    phone_number: str


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class StudentOrAdministrator(str, Enum):
    student = 'student'
    administrator = 'administrator'


class ProposedWebsite(BaseModel):
    title: str
    owner: StudentOrAdministrator
    ownerID: int


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

app = FastAPI()

conninfo = f'host={os.getenv("DB_HOST")} port={os.getenv("DB_PORT")} dbname={os.getenv("DB_NAME")} user={os.getenv("DB_USER")} password={os.getenv("DB_PASSWORD")}'

db_pool = AsyncConnectionPool(
    min_size=1,
    max_size=10,
    conninfo=conninfo
)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def fake_decode_token(token):
    return FullAccount(
        account_id=-1,
        given_name='Lachlan Charles',
        family_name='Shoesmith',
        username=token + 'fakedecoded',
        email='fake@gmail.com',
        phone_number='+61491161258'
    )


def get_user(username: str):
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(f'''
                select  *
                from    account
                where   username = {username}
            ''')
            user_data = cur.fetchone()
            return user_data
    except Error as e:
        raise HTTPException(
            status_code=500, detail=f'Couldn\'t get user. {error}')
    finally:
        db_pool.putconn(conn)


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid authentication credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # 'sub' is the subject of the JWT token
        # user identification is typically stored as the subject
        username: str = payload.get('sub')
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    '''
    Creates an access token by encoding the given data using JWT.

    Args:
        data (dict): The data to be encoded into the access token.
        expiresDelta (timedelta | None, optional): The time delta representing the expiration time of the access token. Defaults to None.

    Returns:
        str: The encoded access token.

    Raises:
        <ExceptionType>: <Description of the exception raised, if any.>
    '''

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.get('/items/')
async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
    return {'token': token}


@app.post('/register')
async def register():
    return {'message': 'Hello World'}


@app.get('/website/{website_id}')
async def get_website(website_id: int):
    async with db_pool:
        async with db_pool.connection() as conn:
            async with conn.cursor() as cur:
                cur.execute(f'''
                    select  title
                    from    websites
                    where   id = {website_id}
                ''')
                website_data = cur.fetchone()
                return website_data


@app.post('/website')
async def create_website(website: ProposedWebsite):
    async with db_pool, db_pool.connection() as conn, conn.cursor() as cur:
        try:
            await cur.execute('''
                insert into website (title)
                values (%s)
                returning id;
            ''', (website.title))

            response = await cur.fetchone()
            website_id = response[0]

            try:
                await cur.execute('''
                    insert into %sOwnsWebsite (accountID, websiteID)
                    values(%s, %s)                    
                ''', (website.owner, website.ownerID, website_id))

                await conn.commit()
            except IntegrityError as e:
                if 'not present' in e.diag.message_detail:
                    raise HTTPException(status_code=400, detail=f'The user does not exist or they are not a {website.owner}.')
                else:
                    raise HTTPException(status_code=400, detail=e)
                    
        except IntegrityError:
            raise HTTPException(status_code=400, detail='Website already exists')
        return website_id


@app.post('/login')
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=400,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': user.username},
        expires_delta=access_token_expires
    )
    return {'access_token': access_token, 'token_type': 'bearer'}


@app.get('/users/me')
async def read_users_me(current_user: Annotated[FullAccount, Depends(get_current_user)]):
    return current_user
