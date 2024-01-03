from pydantic import BaseModel
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


class RegisteringUser(User):
    hashed_password: str
    account_type: StudentOrAdministrator


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