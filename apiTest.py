from flask import Flask, jsonify
import asyncio

app = Flask(__name__)

# async def asynchronous_task(a):
#     # 模拟一个耗时的异步任务
#     await asyncio.sleep(100)
#     a = 1
#     return "Task completed"

# # 使用 async def 定义异步视图函数
# @app.route('/async_example')
# async def async_example():
#     # 在异步视图函数中，可以直接调用异步函数或异步任务
#     # task_result = await asynchronous_task()
#     a = 2
#     asyncio.create_task(asynchronous_task(a))

#     # 视图函数立即返回响应
#     return jsonify({'status': 'Task started6', })



# from flask import Flask, render_template
# from flask_socketio import SocketIO
# import asyncio

# # app = Flask(__name__)
# socketio = SocketIO(app)

# async def asynchronous_task():
#     await asyncio.sleep(2)
#     return "Task completed"

# @app.route('/')
# def index():
#     return jsonify({'status': 'Task started6', })

# @socketio.on('connect')
# def handle_connect():
#     print('Client connected')

# @socketio.on('disconnect')
# def handle_disconnect():
#     print('Client disconnected')

# @socketio.on('start_task')
# def start_task():
#     task_result = asyncio.run(asynchronous_task())
#     socketio.emit('task_result', {'result': task_result})

# # if __name__ == '__main__':


# if __name__ == '__main__':
#     # app.run(debug=True)
#     socketio.run(app, debug=True)


@app.route('/')
def my_func():
    yield "Hello"
    print('next line')
    print('next line1')
    print('next line2')
    print('next line3')
    print('next line4')
    print('next line5')
    print('next line6')
    yield "world"
    print('next line7')

if __name__ == '__main__':
    app.run(debug=True)