from flask import Flask, request, redirect, jsonify

import canvas_requests

app = Flask(__name__)


@app.route('/auth', methods=['GET'])
def sign_in():
    return redirect(f'http://10.0.0.192/login/oauth2/auth?'
                    'client_id=10000000000001&response_type=code&redirect_uri=http://127.0.0.1:8888/auth/complete')


@app.route('/auth/complete', methods=['GET'])
def complete_auth():
    code = request.args['code']
    response = canvas_requests.get_token(code)
    return {'access_token': response['access_token']}


@app.route('/courses', methods=['GET'])
def get_courses():
    token = request.args['access_token']
    status, response = canvas_requests.get(token, 'courses', {})

    if status != 200:
        return response, status

    response_list = []
    for item in response:
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
    status, response = canvas_requests.get(token, 'courses',
                                           params={'include[]': 'total_scores'})

    if status != 200:
        return response, status

    course = [course for course in response if course['id'] == int(course_id)][0]
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
    status, response = canvas_requests.get(token, f'courses/{course_id}/assignments',
                                           params={'per_page': 100})
    if status != 200:
        return response, status

    response_list = []
    for item in response:
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

    status, assignment = canvas_requests.get(token, f'courses/{course_id}/assignments/{assignment_id}',
                                             {'include[]': 'submission'})
    if status != 200:
        return {}, status

    grade = None
    score = None

    if assignment.get('submission') is not None:
        submission = assignment.get('submission')
        grade = submission['grade']
        score = submission['score']

    return jsonify({
        'grade': grade,
        'score': score,
        'score_possible': assignment['points_possible'],
    })
