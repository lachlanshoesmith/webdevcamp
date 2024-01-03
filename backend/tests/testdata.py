from backend import main


class TestData:
    registering_student_data: main.RegisteringUser = {
        'username': 'neffieta',
        'given_name': 'Neffie Etta',
        'family_name': 'Denile',
        'hashed_password': 'password123',
        'account_type': 'student'
    }

    registering_administrator_data: main.RegisteringFullUser = {
        'username': 'lachlantula',
        'given_name': 'Lachlan Charles',
        'family_name': 'Shoesmith',
        'hashed_password': 'abjjsfdjsd',
        'account_type': 'administrator',
        'email': 'lachie@example.com',
        'phone_number': '123-456-7890'
    }

    registering_student: main.RegisteringStudentRequest = {
        'user': registering_student_data,
        'administrator_id': 1
    }

    registering_student_as_full_account: main.RegisteringFullUser = {
        'username': 'neffieta',
        'given_name': 'Neffie Etta',
        'family_name': 'Denile',
        'hashed_password': 'password123',
        'account_type': 'student',
        'email': 'neffie@gmail.com',
        'phone_number': '123-456-7890'
    }

    registering_administrator_as_student: main.RegisteringUser = {
        'username': 'lachlantula',
        'given_name': 'Lachlan Charles',
        'family_name': 'Shoesmith',
        'hashed_password': 'abjjsfdjsd',
        'account_type': 'administrator'
    }

    registering_administrator_as_student_request: main.RegisteringStudentRequest = {
        'user': registering_administrator_as_student,
        'administrator_id': 1
    }
