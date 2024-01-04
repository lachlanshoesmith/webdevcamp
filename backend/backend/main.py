from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from psycopg import DataError, IntegrityError, AsyncConnection, sql
from psycopg_pool import AsyncConnectionPool

from .models import (TokenData, ProposedWebsite, RegisteringStudentRequest,
                     RegisteringUser, RegisteringFullUser, RegisteringFullUserRequest)

import os
import sys

load_dotenv()

# much of the authentication code is borrowed from fastapi's documentation
# https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

db_pool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    # runs on server startup, before the application takes requests
    if not os.getenv("DB_HOST") or not os.getenv("DB_PORT") or not os.getenv("DB_NAME") or not os.getenv("DB_USER") or not os.getenv("DB_PASSWORD"):
        sys.exit("Could not find required database environment variables (ie. DB_HOST, DB_PORT, DB_NAME, DB_USER, or DB_PASSWORD).")

    conninfo = f'host={os.getenv("DB_HOST")} port={os.getenv("DB_PORT")} dbname={os.getenv("DB_NAME")} user={os.getenv("DB_USER")} password={os.getenv("DB_PASSWORD")}'

    db_pool = AsyncConnectionPool(
        min_size=1,
        max_size=10,
        open=False,
        conninfo=conninfo
    )

    await db_pool.open()
    yield
    # runs on server shutdown
    await db_pool.close()

app = FastAPI(lifespan=lifespan)


async def get_connection() -> AsyncConnection:
    async with db_pool.connection() as conn:
        try:
            yield conn
        finally:
            await conn.close()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password, registration_time):
    return pwd_context.hash(password + str(registration_time))


async def get_user_from_username(username: str, conn: AsyncConnection):
    async with conn.cursor() as cur:
        await cur.execute('''
                        select get_user_from_username(%(username)s)
                    ''', {'username': username})
        user_data = await cur.fetchone()
        if not user_data:
            return None
        else:
            return user_data


async def get_user_from_email(email: str, conn: AsyncConnection):
    async with conn.cursor() as cur:
        await cur.execute('''
                        select get_user_from_email(%(email)s)
                    ''', {'email': email})
        user_data = await cur.fetchone()
        if not user_data:
            return None
        else:
            return user_data


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
async def get_website(website_id: int, conn: AsyncConnection = Depends(get_connection)):
    async with conn.cursor() as cur:
        cur.execute('''
                    select  title
                    from    websites
                    where   id = %s
                ''', (website_id))
        website_data = cur.fetchone()
        return website_data


@app.post('/website')
async def create_website(website: ProposedWebsite, conn: AsyncConnection = Depends(get_connection)):
    async with conn.cursor() as cur:
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
async def login_endpoint(user_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(user_data.username, user_data.password)
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


@app.post('/register/student')
async def register_student_endpoint(user_data: RegisteringStudentRequest, conn: AsyncConnection = Depends(get_connection)):
    if user_data.user.account_type != 'student':
        raise HTTPException(
            status_code=400, detail='Only students may register via /register/student. Use /register.')
    # check that administrator exists
    async with conn.cursor() as cur:
        await cur.execute('''
            select *
            from   administrator
            where  id = %(administrator_id)s
        ''', {'administrator_id': user_data.administrator_id})
        administrator = await cur.fetchone()
        if not administrator:
            raise HTTPException(
                status_code=400, detail=f'Administrator {user_data.administrator_id} does not exist.')

    student_id = await create_account(user_data.user, conn)
    try:
        async with conn.cursor() as cur:
            await cur.execute('''
                insert into Teaches (administrator_id, student_id)
                values (%(administrator_id)s, %(student_id)s)
            ''', {'administrator_id': user_data.administrator_id, 'student_id': student_id})
            await conn.commit()
            return {'student_id': student_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=str(e)
        )


async def create_account(user_data: RegisteringUser, conn: AsyncConnection):
    async with conn.cursor() as cur:
        try:
            await cur.execute('''
                    insert into account (given_name, family_name, hashed_password, username)
                    values (%(given_name)s, %(family_name)s, 'temp', %(username)s)
                    returning id, registration_time;
                ''', {'given_name': user_data.given_name,
                      'family_name': user_data.family_name,
                      'username': user_data.username})

            response = await cur.fetchall()
            account_id = response[0][0]
            registration_time = response[0][1]

            # insert hashed password now that registration time is known
            user_data.hashed_password = get_password_hash(
                user_data.hashed_password,
                registration_time
            )

            await conn.commit()

            await cur.execute('''
                    update account
                    set hashed_password = %(hashed_password)s
                    where id = %(account_id)s
                ''', {'account_id': account_id, 'hashed_password': user_data.hashed_password})

            await conn.commit()

            async with conn.cursor() as cur2:
                await cur2.execute(
                    sql.SQL('''
                        insert into {} (id)
                        values (%s)
                    ''').format(sql.Identifier(user_data.account_type)), [account_id])
                await conn.commit()

                return account_id

        except IntegrityError as e:
            print(e.diag.message_detail)
            raise HTTPException(
                status_code=400, detail='User already exists.')
        except DataError:
            raise HTTPException(
                status_code=400, detail='Username is too long.')


async def register_full_account(user_data: RegisteringFullUserRequest, conn: AsyncConnection):
    async with conn.cursor() as cur:
        await cur.execute('''
                insert into Full_Account (id, email, phone_number)
                values (%(id)s, %(email)s, %(phone_number)s)
            ''', {'id': user_data['id'], 'email': user_data['user'].email, 'phone_number': user_data['user'].phone_number})
        await conn.commit()


@app.post('/register')
async def register_full_account_endpoint(user_data: RegisteringFullUser, conn: AsyncConnection = Depends(get_connection)):
    if user_data.account_type == 'student':
        raise HTTPException(
            status_code=400, detail='Students cannot register via /register. Use /register/student.')

    # if either function returns a value other than None, the user exists
    if (await get_user_from_username(user_data.username, conn) or await get_user_from_email(user_data.email, conn)):
        raise HTTPException(
            status_code=400, detail='User already exists.'
        )
    else:
        account_id = await create_account(user_data, conn)
        request: RegisteringFullUserRequest = {
            'user': user_data,
            'id': account_id
        }
        await register_full_account(request, conn)
        return {'account_id': account_id}
