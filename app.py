from flask import Flask, request, jsonify
from Todo_Class import Todo
from Todo_Class import logger as td_logger
import logging
import datetime as dt
import sys 
import time

app = Flask(__name__)

request_number = 0

def create_logger():
    logger = logging.getLogger('request-logger')
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler('logs/requests.log', 'w')
    formtter = logging.Formatter("%(asctime)s.%(msecs)03d %(levelname)s: %(message)s | request #%(request_number)s", "%d-%m-20%y %H:%M:%S")
    file_handler.setFormatter(formtter)
    logger.addHandler(file_handler)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(logging.Formatter("%(asctime)s.%(msecs)03d: %(levelname)s %(message)s | request #%(request_number)s", "%d-%m-20%y %H:%M:%S"))

    logger.addHandler(stdout_handler)

    return logger

def build_info_message(request_number, resource_name, VERB):
    return f"Incoming request | #{request_number} | resource: {resource_name} | HTTP Verb {VERB}"

def build_debug_message(request_number, ms):
    duration = time.time()-ms
    return f"request #{request_number} duration: {duration:03f}ms"

def log_request(resource_name, VERB, start_time):
    logger.info(build_info_message(request_number, resource_name, VERB), extra={"request_number": request_number})
    logger.debug(build_debug_message(request_number, start_time), extra={"request_number": request_number})

@app.route('/todo/health', methods=['GET'])
def health_check():
    global request_number
    request_number += 1
    start_time = time.time()
    log_request('/todo/health', 'GET', start_time)
    return 'OK', 200


@app.route('/todo', methods=['POST'])
def create_new_todo():
    global request_number
    request_number += 1
    start_time = time.time()
    todo_data = request.get_json()
    title = todo_data.get('title')
    content = todo_data.get('content')
    due_date = todo_data.get('dueDate')

    td_logger.info(f"Creating new TODO with Title [{title}]", extra={"request_number": request_number})
    td_logger.debug(f"Currently there are {len(Todo.todos)} TODOs in the system. New TODO will be assigned with id {Todo.id_counter}", extra={"request_number": request_number})

    for todo in Todo.todos:
        if Todo.todos[todo].title == title:
            log_request('/todo', 'POST', start_time)
            return jsonify({'errorMessage': f'Error: TODO with the title [{title}] already exists in the system'}), 409

    if Todo.is_due_time_valid(due_date):
        log_request('/todo', 'POST', start_time)
        return jsonify({'errorMessage': 'Error: Can’t create new TODO that its due date is in the past'}), 409

    new_todo = Todo(title, content, due_date)
    Todo.todos[new_todo.id] = new_todo

    log_request('/todo', 'POST', start_time)
    return jsonify({'result': new_todo.id}), 200


@app.route('/todo/size', methods=['GET'])
def get_todos_count():
    global request_number
    request_number += 1
    start_time = time.time()
    status = request.args.get('status')

    td_logger.info(f"Total TODOs count for state {status} is {Todo.count_by_status(status)}", extra={"request_number": request_number})

    if status not in ['ALL', 'PENDING', 'LATE', 'DONE']:
        result = jsonify({'result': 400}), 400
    elif status == 'ALL':
        result = jsonify({'result': len(Todo.todos)}), 200
    else:
        result = jsonify({'result': Todo.count_by_status(status)}), 200
    
    log_request('/todo/size', 'GET', start_time)
    return result


@app.route('/todo/content', methods=['GET'])
def get_todos_data():
    global request_number
    request_number += 1
    start_time = time.time()
    status = request.args.get('status')
    sort_by = request.args.get('sortBy')

    if not sort_by:
        sort_by = "ID"
    if status not in ['ALL', 'PENDING', 'LATE', 'DONE'] or sort_by not in ['ID', 'DUE_DATE', 'TITLE']:
        return jsonify({'result': 400}), 400

    td_logger.info(f"Extracting todos content. Filter: {status} | Sorting by: {sort_by}", extra={"request_number": request_number})
    td_logger.debug(f"There are a total of {len(Todo.todos)} todos in the system. The result holds {Todo.count_by_status(status)} todos", extra={"request_number": request_number})

    result = []
    if status == 'ALL':
        result_todos = Todo.todos.values()
    else:
        result_todos = Todo.filter_by_status(status)

    if sort_by == 'DUE_DATE':
        result_todos = sorted(result_todos, key=lambda x: x.due_date)
    elif sort_by == 'TITLE':
        result_todos = sorted(result_todos, key=lambda x: x.title)
    else:
        result_todos = sorted(result_todos, key=lambda x: x.id)

    for todo in result_todos:
        result.append({
            'id': todo.id,
            'title': todo.title,
            'content': todo.content,
            'status': todo.status,
            'dueDate': todo.due_date  # convert to ms
        })
    
    log_request('/todo/content', 'GET', start_time)
    return jsonify({'result': result}), 200


@app.route('/todo', methods=['PUT'])
def update_todos_status_property():
    global request_number
    request_number += 1
    start_time = time.time()
    todo_id = int(request.args.get('id'))
    new_status = request.args.get('status')

    td_logger.info(f"Update TODO id [{todo_id}] state to {new_status}", extra={"request_number": request_number})

    if todo_id > Todo.id_counter:

        log_request('/todo', 'PUT', start_time)
        td_logger.error(f"Error: no such TODO with id {todo_id}", extra={"request_number": request_number})

        return jsonify({'errorMessage': f"Error: no such TODO with id {todo_id}"}), 404
    
    if new_status not in ['PENDING', 'LATE', 'DONE']:
        log_request('/todo', 'PUT', start_time)
        td_logger.error(f"Error: no such status", extra={"request_number": request_number})
        return jsonify({'result': 400, 'errorMessage': 'Error: no such status'}), 400

    try:
        result = jsonify({'result': Todo.todos[todo_id].status}), 200
        old_status = Todo.todos[todo_id].status
        Todo.todos[todo_id].status = new_status
    except KeyError:
        log_request('/todo', 'PUT', start_time)
        td_logger.error(f"Error: no such TODO with id {todo_id}", extra={"request_number": request_number})
        return jsonify({'errorMessage': f"Error: no such TODO with id {todo_id}"}), 404
    
    log_request('/todo', 'PUT', start_time)
    td_logger.debug(f"Todo id [{todo_id}] state change: {old_status} --> {new_status}", extra={"request_number": request_number})

    return result


@app.route('/todo', methods=['DELETE'])
def delete_todo():
    global request_number
    request_number += 1
    start_time = time.time()
    todo_id = int(request.args.get('id'))
    try:
        del Todo.todos[todo_id]
        td_logger.info(f"Removing todo id {todo_id}", extra={"request_number": request_number})
        td_logger.debug(f"After removing todo id [{todo_id}] there are {len(Todo.todos)} TODOs in the system", extra={"request_number": request_number})
    except KeyError:
        log_request('/todo', 'DELETE', start_time)
        td_logger.error(f"Error: no such TODO with id {todo_id}", extra={"request_number": request_number})
        return jsonify({'errorMessage': f"Error: no such TODO with id {todo_id}"}), 404
    
    result = jsonify({'result': len(Todo.todos)}), 200
    log_request('/todo', 'DELETE', start_time)
    return result

@app.route('/logs/level', methods=['GET'])
def get_log_level():
    global request_number
    request_number += 1
    start_time = time.time()
    logger_name = request.args.get('logger-name')
    if logger_name == 'request-logger':
        log_request('/logs/level', 'GET', start_time)
        return logging.getLevelName(logger.level)
    elif logger_name == 'todo-logger':
        log_request('/logs/level', 'GET', start_time)
        return logging.getLevelName(td_logger.level)
    else:
        log_request('/logs/level', 'GET', start_time)
        return f"Error! no such logger: {logger_name}"

@app.route('/logs/level', methods=['PUT'])
def set_log_level():
    global request_number
    request_number += 1
    start_time = time.time()
    logger_name = request.args.get('logger-name')
    logger_level = request.args.get('logger-level')
    try:
        numeric_level = getattr(logging, logger_level.upper())
        if not isinstance(numeric_level, int):
            log_request('/logs/level', 'PUT', start_time)
            return f"Error! no such logger level: {logger_level}"
    except:
        return f"Error! no such logger level: {logger_level}"
    
    if logger_name == 'request-logger':
        logger.setLevel(numeric_level)
    elif logger_name == 'todo-logger':
        td_logger.setLevel(numeric_level)
    else:
        log_request('/logs/level', 'PUT', start_time)
        return f"Error! no such logger: {logger_name}"
        
    log_request('/logs/level', 'PUT', start_time)
    return logger_level.upper()


# if __name__ == '__main__':
logger = create_logger()
#app.run(port=9285)
