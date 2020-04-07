import os

import requests


def get_token(code):
    response = requests.post(url='http://10.0.0.192/login/oauth2/token',
                             data={
                                 'client_id': os.environ.get('CLIENT_ID'),
                                 'client_secret': os.environ.get('CLIENT_SECRET'),
                                 'grant_type': 'authorization_code',
                                 'code': code
                             })
    return response.json()


def get(token, endpoint, params):
    response = requests.get(url=f'http://10.0.0.192/api/v1/{endpoint}',
                            headers={'Authorization': f'Bearer {token}'},
                            params=params)

    if response != 200:
        print(response.json())

    try:
        body = response.json()
    except ValueError:
        body = {}

    return response.status_code, body
