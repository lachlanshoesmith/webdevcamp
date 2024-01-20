from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from typing import Union


class StudentOrAdministrator(str, Enum):
    student = 'student'
    administrator = 'administrator'


class User(BaseModel):
    given_name: str
    family_name: str
    username: str


class LoggedInUser(User):
    account_id: int
    access_token: str
    # following fields depend on account_type
    email: str | None = None
    phone_number: str | None = None


class RegisteringUser(User):
    hashed_password: str
    account_type: StudentOrAdministrator


class LoggingInUser(BaseModel):
    username: str
    password: str


class RegisteringFullUser(RegisteringUser):
    email: str
    phone_number: str | None = None


class RegisteringFullUserRequest(BaseModel):
    user: RegisteringFullUser
    id: int


class RegisteringStudentRequest(BaseModel):
    user: RegisteringUser
    administrator_id: int


class UserInDB(User):
    account_id: int
    hashed_password: str
    registration_time: datetime
    # following fields depend on account_type
    email: str | None = None
    phone_number: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class ProposedWebsite(BaseModel):
    title: str = Field(..., min_length=1)
