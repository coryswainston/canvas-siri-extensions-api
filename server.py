import os

import requests
from flask import Flask, request, redirect, jsonify

app = Flask(__name__)


@app.route('/auth', methods=['GET'])
def sign_in():
    return redirect(f'http://10.0.0.192/login/oauth2/auth?'
                    'client_id=10000000000001&response_type=code&redirect_uri=http://127.0.0.1:8888/auth/complete')


@app.route('/auth/complete', methods=['GET'])
def complete_auth():
    code = request.args['code']
    response = requests.post(url='http://10.0.0.192/login/oauth2/token',
                             data={
                                 'client_id': os.environ.get('CLIENT_ID'),
                                 'client_secret': os.environ.get('CLIENT_SECRET'),
                                 'grant_type': 'authorization_code',
                                 'code': code
                             })
    print(response.status_code)
    token = response.json()['access_token']
    return {'access_token': token}


@app.route('/courses', methods=['GET'])
def get_courses():
    token = request.args['access_token']
    response = requests.get(url='http://10.0.0.192/api/v1/courses',
                            headers={'Authorization': f'Bearer {token}'})
    response_list = []
    for item in response.json():
        response_list.append({
            'name': item['name'],
            'start_date': item['start_at'],
            'end_date': item['end_at'],
            'id': item['id'],
        })

    return jsonify(response_list)


@app.route('/courses/<course_id>/grades', methods=['GET'])
def get_grades_for_course(course_id):
    # inputs: start/end date
    token = request.args['access_token']
    response = requests.get(url='http://10.0.0.192/api/v1/courses?include[]=total_scores',
                            headers={'Authorization': f'Bearer {token}'})

    course_list = response.json()
    print(course_list)
    course = [course for course in course_list if course['id'] == int(course_id)][0]
    enrollment = course['enrollments'][0]
    print(enrollment)

    return {
        'grade': enrollment['computed_current_grade'],
        'score': enrollment['computed_current_score'],
    }


@app.route('/assignments', methods=['GET'])
def get_assignments():
    # inputs: start/end dates
    token = request.args['access_token']
    course_id = request.args['course_id']
    response = requests.get(url=f'http://10.0.0.192/api/v1/courses/{course_id}/assignments',
                            headers={'Authorization': f'Bearer {token}'},
                            params={'per_page': 100})

    response_list = []
    for item in response.json():
        response_list.append({
            'name': item['name'],
            'description': item['description'],
            'id': item['id'],
        })

    return jsonify(response_list)


@app.route('/assignments/<assignment_id>/grades', methods=['GET'])
def get_grades_for_assignment(assignment_id):
    # change this to take a query for assignment name
    token = request.args['access_token']
    course_id = request.args['course_id']
    response = requests.get(url=f'http://10.0.0.192/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions',
                            headers={'Authorization': f'Bearer {token}'})

    submission = response.json()[0]

    response = requests.get(url=f'http://10.0.0.192/api/v1/courses/{course_id}/assignments/{assignment_id}',
                            headers={'Authorization': f'Bearer {token}'})

    assignment = response.json()
    print(assignment)

    return jsonify({
        'grade': submission['grade'],
        'score': submission['score'],
        'score_possible': assignment['points_possible'],
    })
