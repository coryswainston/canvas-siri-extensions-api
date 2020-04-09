from flask import Flask, request, redirect, jsonify

import canvas_requests
import jellyfish
from datetime import datetime, timedelta

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


@app.route('/courses//grades', methods=['GET'])
def get_grades_for_course():
    token = request.args['access_token']
    query = request.args['course']
    status, response = canvas_requests.get(token, 'courses',
                                           params={'include[]': 'total_scores'})

    if status != 200:
        return response, status

    most_similar_id = 1
    high_score = 0
    for course in response:
        name = course['name']
        code = course['course_code']
        name_sim = jellyfish.levenshtein_distance(name, query)
        code_sim = jellyfish.levenshtein_distance(code, query)
        if max(name_sim, code_sim) > high_score:
            most_similar_id = course['id']

    course = [course for course in response if course['id'] == most_similar_id][0]
    enrollment = course['enrollments'][0]

    return {
        'grade': enrollment['computed_current_grade'],
        'score': enrollment['computed_current_score'],
        'course': course['name']
    }


@app.route('/assignments', methods=['GET'])
def get_assignments():
    token = request.args['access_token']
    # course_id = request.args['course_id'] TODO implement passing a course

    status, response = canvas_requests.get(token, 'courses', {})
    if status != 200:
        return response, status

    course_ids = [item['id'] for item in response]
    context_ids = [f'course_{course_id}' for course_id in course_ids]
    context_ids = ','.join(context_ids)

    date_range = request.args['date_range']
    start_date = datetime.today().strftime('%Y-%m-%d')
    if date_range == 'thisWeek':
        end_date = (datetime.today() + timedelta(days=7)).strftime('%Y-%m-%d')
    else:
        end_date = start_date
    print(start_date)

    status, response = canvas_requests.get(token, f'calendar_events',
                                           params={'per_page': 100, 'start_date': start_date,
                                                   'end_date': end_date, 'type': 'assignment',
                                                   'context_codes[]': context_ids})

    if status != 200:
        return response, status

    response_list = []
    for item in response:
        response_list.append({
            'name': item['title'],
            'description': item['description'],
            'id': item['id'],
            'due_date': item['end_at']
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
