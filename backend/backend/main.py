from pydantic import BaseModel, ConfigDict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Annotated, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from psycopg import DataError, IntegrityError, AsyncConnection, sql
from psycopg.errors import UniqueViolation
from psycopg_pool import AsyncConnectionPool

from .models import (TokenData, ProposedWebsite, RegisteringStudentRequest,
                     RegisteringUser, RegisteringFullUser, RegisteringFullUserRequest,
                     LoggingInUser, UserInDB, LoggedInUser, StudentOrAdministrator)

import os
import sys

load_dotenv()

# much of the authentication code is borrowed from fastapi's documentation
# https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/

SECRET_KEY = os.getenv('SECRET_KEY')

if SECRET_KEY == None:
    sys.exit("Could not find required environment variable (ie. SECRET_KEY).")

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


async def get_connection():
    async with db_pool.connection() as conn:
        try:
            yield conn
        finally:
            await conn.close()


def verify_password(plain_password: str, hashed_password, registration_time: datetime):
    salted_password = plain_password + str(registration_time)
    return pwd_context.verify(salted_password, hashed_password)


def get_password_hash(password, registration_time: datetime):
    return pwd_context.hash(password + str(registration_time))


async def get_user_from_username(username: str, conn: AsyncConnection) -> Optional[UserInDB]:
    async with conn.cursor() as cur:
        await cur.execute('''
                        select * from get_user_from_username(%(username)s)
                    ''', {'username': username})
        user_data = await cur.fetchone()
        if not user_data:
            return None
        else:
            formatted_user_data: UserInDB = {
                'account_id': user_data[0],
                'given_name': user_data[3],
                'family_name': user_data[4],
                'username': user_data[5],
                'registration_time': user_data[6],
                'hashed_password': user_data[7],
                'email': None,
                'phone_number': None
            }
            if user_data[1]:
                formatted_user_data['email'] = user_data[1]
                formatted_user_data['phone_number'] = user_data[2]
            return formatted_user_data


async def get_user_from_email(email: str, conn: AsyncConnection) -> Optional[UserInDB]:
    async with conn.cursor() as cur:
        await cur.execute('''
                        select get_user_from_email(%(email)s)
                    ''', {'email': email})
        user_data: UserInDB = await cur.fetchone()
        if not user_data:
            return None
        else:
            return user_data


async def get_user_type(id: int, conn: AsyncConnection) -> Optional[StudentOrAdministrator]:
    async with conn.cursor() as cur:
        await cur.execute('''
                        select * from get_user_type(%(id)s)
                    ''', {'id': id})
        res = await cur.fetchone()
        user_type = res[0]
        if not user_type:
            return None
        else:
            return user_type


async def authenticate_user(username: str, password: str, conn: AsyncConnection):
    user: UserInDB = await get_user_from_username(username, conn)
    if not user:
        return None
    if not verify_password(password, user['hashed_password'], user['registration_time']):
        return False
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], conn: AsyncConnection = Depends(get_connection)) -> UserInDB:
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
    user = await get_user_from_username(username=token_data.username, conn=conn)
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


class websiteIDModel(BaseModel):
    website_id: int


@app.post('/website')
async def create_website(website: ProposedWebsite, current_user: UserInDB = Depends(get_current_user), conn: AsyncConnection = Depends(get_connection)):
    owner_type = await get_user_type(current_user['account_id'], conn)
    async with conn.cursor() as cur:
        try:
            res = await cur.execute('''
                insert into website (title)
                values (%(title)s)
                returning id;
            ''', {'title': website.title})

            res = await res.fetchone()
            website_id = res[0]
            try:
                await cur.execute(sql.SQL('''
                    insert into {owner_type}_Owns_Website ({owner_type}_id, website_id)
                    values ({owner_id}, {website_id})
                ''').format(
                    owner_type=sql.SQL(owner_type),
                    owner_id=sql.Literal(current_user['account_id']),
                    website_id=sql.Literal(website_id)
                ))

                await conn.commit()
                return {'website_id': website_id}
            except IntegrityError as e:
                if 'not present' in e.diag.message_detail:
                    raise HTTPException(
                        status_code=400, detail=f'The user does not exist or they are not a {owner_type}.')
                else:
                    raise HTTPException(status_code=400, detail=e)

        except IntegrityError:
            raise HTTPException(
                status_code=400, detail='Website already exists.')


@app.post('/website/{website_id}')
async def upload_webpage(website_id: int, current_user: UserInDB = Depends(get_current_user), conn: AsyncConnection = Depends(get_connection)):
    return {'webpage_id': 5}


@app.post('/login')
async def login_endpoint(user_data: LoggingInUser, conn: AsyncConnection = Depends(get_connection)) -> LoggedInUser:
    """
    Logs in a user - either a student or administrator - and returns an access token.

    Parameters:
        LoggingInUser: The user data containing the username and password.

    Returns:
        LoggedInUser: A dictionary containing the access token and the user's ID.
    """
    user: UserInDB = await authenticate_user(user_data.username, user_data.password, conn)

    if not user:
        raise HTTPException(
            status_code=400,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'}
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token: str = create_access_token(
        data={'sub': user['username']},
        expires_delta=access_token_expires
    )

    return {'account_id': user['account_id'], 'access_token': access_token, 'username': user['username'], 'given_name': user['given_name'], 'family_name': user['family_name'], 'email': user['email'], 'phone_number': user['phone_number']}


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
            registration_time: datetime = response[0][1]

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
            raise HTTPException(
                status_code=400, detail='User already exists.')
        except DataError:
            raise HTTPException(
                status_code=400, detail='Username is too long.')


async def register_full_account(user_data: RegisteringFullUserRequest, conn: AsyncConnection):
    async with conn.cursor() as cur:
        try:
            await cur.execute('''
                    insert into Full_Account (id, email, phone_number)
                    values (%(id)s, %(email)s, %(phone_number)s)
                ''', {'id': user_data['id'], 'email': user_data['user'].email, 'phone_number': user_data['user'].phone_number})
            await conn.commit()
        except UniqueViolation:
            raise HTTPException(
                status_code=400, detail='Phone number taken.')


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
