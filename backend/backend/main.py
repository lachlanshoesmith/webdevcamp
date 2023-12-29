from enum import Enum
import os
import sys
from psycopg_pool import AsyncConnectionPool
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Annotated, Union
from pydantic import BaseModel
from datetime import datetime, timedelta
from psycopg import IntegrityError, sql

load_dotenv()

# much of the authentication code is borrowed from fastapi's documentation
# https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class StudentOrAdministrator(str, Enum):
    student = 'student'
    administrator = 'administrator'


class User(BaseModel):
    given_name: str
    family_name: str
    username: str


class LoggedInUser(User):
    account_id: int


class RegisteringUser(User):
    password: str
    account_type: StudentOrAdministrator


class RegisteringFullUser(RegisteringUser):
    email: str
    phone_number: str | None = None


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class ProposedWebsite(BaseModel):
    title: str
    owner_type: StudentOrAdministrator
    owner_id: int


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

app = FastAPI()

if not os.getenv("DB_HOST") or not os.getenv("DB_PORT") or not os.getenv("DB_NAME") or not os.getenv("DB_USER") or not os.getenv("DB_PASSWORD"):
    sys.exit("Could not find required database environment variables (ie. DB_HOST, DB_PORT, DB_NAME, DB_USER, or DB_PASSWORD).")

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


async def get_user_from_username(username: str):
    async with db_pool:
        async with db_pool.connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(f'''
                        select  *
                        from    account
                        where   username = {username}
                    ''')
                    user_data = cur.fetchone()
                    return user_data
            except AttributeError as e:
                raise HTTPException(
                    status_code=500, detail=f'Couldn\'t get user via username {username}.')


async def get_user_from_email(email: str):
    async with db_pool:
        async with db_pool.connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(f'''
                        select  *
                        from    account a 
                        join    FullAccount f
                        on      a.id = f.id
                        where   f.email = {email}
                    ''')
                    user_data = cur.fetchone()
                    return user_data
            except AttributeError as e:
                raise HTTPException(
                    status_code=500, detail=f'Couldn\'t get user via email {email}.')


def authenticate_user(username: str, password: str):
    user = get_user_from_username(username)
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
    user = get_user_from_username(username=token_data.username)
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


@app.get('/website/{website_id}')
async def get_website(website_id: int):
    async with db_pool:
        async with db_pool.connection() as conn:
            async with conn.cursor() as cur:
                cur.execute('''
                    select  title
                    from    websites
                    where   id = %s
                ''', (website_id))
                website_data = cur.fetchone()
                return website_data


@app.post('/website')
async def create_website(website: ProposedWebsite):
    async with db_pool, db_pool.connection() as conn, conn.cursor() as cur:
        try:
            await cur.execute('''
                insert into website (title)
                values (%(title)s)
                returning id;
            ''', {'title': website.title})

            response = await cur.fetchone()
            website_id = response[0]
            try:
                await cur.execute(sql.SQL('''
                    insert into {owner_type}OwnsWebsite ({owner_type}ID, websiteID)
                    values ({owner_id}, {website_id})
                ''').format(
                    owner_type=sql.SQL(website.owner_type),
                    owner_id=sql.Literal(website.owner_id),
                    website_id=sql.Literal(website_id)
                ))

                await conn.commit()
            except IntegrityError as e:
                if 'not present' in e.diag.message_detail:
                    raise HTTPException(
                        status_code=400, detail=f'The user does not exist or they are not a {website.owner_type}.')
                else:
                    raise HTTPException(status_code=400, detail=e)

        except IntegrityError:
            raise HTTPException(
                status_code=400, detail='Website already exists')
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


# async def check_if_username_exists(username: str, email: str | None):
#     user = await get_user(username)
#     if not user:
#         return False
#     if not verify_password(password, user.hashed_password):
#         return False
#     return user


@app.post('/register/student')
async def register_student(form_data: RegisteringUser, administrator_id: int):
    student_id = await create_account(form_data)
    async with db_pool, db_pool.connection() as conn, conn.cursor() as cur:
        await cur.execute('''
            insert into Teaches (adminID, studentID)
            values (%(administrator_id)s, %(student_id)s)
        ''', {'adminstrator_id': administrator_id, 'student_id': student_id})
        await conn.commit()
        return {'student_id': student_id}


@app.post('/register/administrator')
async def register_administrator(form_data: RegisteringFullUser):
    administrator_id = await create_account(form_data)


async def create_account(user_data: RegisteringUser):
    async with db_pool, db_pool.connection() as conn, conn.cursor() as cur:
        try:
            await cur.execute('''
                    insert into account (givenname, familyname, username, hashed_password)
                    values (%(givenname)s, %(familyname)s, %(username)s, %(hashed_password)s)
                    returning (id);
                ''', {'givenname': user_data.given_name,
                      'familyname': user_data.family_name,
                      'username': user_data.username,
                      'hashed_password': user_data.hashed_password})
            await cur.commit()
            response = await cur.fetchone()
            account_id = response[0]

            await cur.execute('''
                    insert into %(account_type) (id)
                    values (%(id)s);
                ''', {'account_type': user_data.account_type,
                      'id': account_id})
            await cur.commit()

            return account_id

        except IntegrityError:
            raise HTTPException(
                status_code=400, detail='User already exists.')
        return account_id


@app.post('/register')
async def register_full_user(form_data: RegisteringFullUser):
    if form_data.account_type == 'student':
        raise HTTPException(
            status_code=400, detail='Students cannot register via /register. Use /register/student.')
    # check if user exists
    try:
        await get_user_from_username(form_data.username)
        await get_user_from_email(form_data.email)
        raise HTTPException(
            status_code=400, detail='User already exists.'
        )
    except HTTPException:
        # the user does not exist, proceed to create an account
        user_data: RegisteringUser = {
            'username': form_data.username,
            'password': get_password_hash(form_data.password),
            'account_type': form_data.account_type,
            'given_name': form_data.given_name,
            'family_name': form_data.family_name,
        }
        # add to FulLAccounts table
    # 2. create user
    # 3. log in user
    return {'message': 'Hello World'}


# @app.get('/users/me')
# async def read_users_me(current_user: Annotated[FullAccount, Depends(get_current_user)]):
#     return current_user
