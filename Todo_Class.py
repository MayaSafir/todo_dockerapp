import time
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('logs/todos.log', 'w')
formtter = logging.Formatter("%(asctime)s.%(msecs)03d %(levelname)s: %(message)s | request #%(request_number)s", "%d-%m-20%y %H:%M:%S")
file_handler.setFormatter(formtter)
logger.addHandler(file_handler)


class Todo:
    id_counter = 1  # class variable to keep track of unique id
    todos = {}

    def __init__(self, title, content, due_date):
        self.id = Todo.id_counter  # assign unique id
        self.title = title
        self.content = content
        self.due_date = due_date
        self.status = "PENDING"
        Todo.id_counter += 1

    @staticmethod
    def is_due_time_valid(due_date):
        due_time_sec = due_date
        current_time_sec = time.time()
        return due_time_sec < current_time_sec

    @staticmethod
    def count_by_status(status):
        if status == 'ALL':
            return len(Todo.todos)
        
        todos_with_the_status = 0
        for todo in Todo.todos:
            if Todo.todos[todo].status == status:
                todos_with_the_status = todos_with_the_status + 1
        return todos_with_the_status

    @staticmethod
    def filter_by_status(status):
        todos_with_the_status = []
        for todo in Todo.todos:
            if Todo.todos[todo].status == status:
                todos_with_the_status.append(Todo.todos[todo])
        return todos_with_the_status
    



