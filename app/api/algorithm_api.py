import flask
from flask import Blueprint, request, jsonify, json, make_response, g
import app.utils.data_util as data_util
import pandas as pd

import importlib
import time
import numpy as np

from app.utils.rest_response import success, error
import logging
import asyncio
import threading
from app.api.analyse import analyseData
from configs.config import Wind_Farm, EXCEPT_MODLES, extraModelName, Path
import utils.display_util as display_util
import os
from checkout import execute_multi_algorithms
# from concurrent.futures import ThreadPoolExecutor

# executor = ThreadPoolExecutor()
# from multiprocessing import Process
# from app.utils import globalVariable
# import sys
# import os
# # 获取当前脚本所在的目录
# current_dir = os.path.dirname(os.path.abspath(__file__))

# # 获取项目根目录
# project_root = os.path.abspath(os.path.join(current_dir, "../../"))

# # 将项目根目录添加到Python路径中
# sys.path.append(project_root)

api = Blueprint('api', __name__, url_prefix='/wind-algorithm-model')


data_cache = {}



# @api.before_request
# def before_request():
#     # 在这里可以检查请求的路径，然后设置一个标记
#     # if 'execute' in request.endpoint :
#     #     g.executeFlag = 'execute'
#     # else:
#     #     g.executeFlage = None
#     asyncio.run(execute())

# @api.after_request
# async def after_request(response):
#     if getattr(g, 'executeFlag', 'execute'):
#         return response





@api.route('/')
def index():
    return {
        "msg": "success",
        "data": "welcome to use flask."
    }


# @api.post('/model/execute')
@api.route('/model/execute', methods=['POST'])
def execute():
    
    response = make_response('ok2')
    # modelCode = request.args.getlist('modelCode')#.decode('utf-8')
    modelCode = request.json
    # modelCode = [item["modelCode"] for item in models]
    # configs = {}
    # for item in models:
    #     configs[item["modelCode"]] = item["threshold"]
    response.data = response.data.decode('utf-8')
    response.status_code = 200

    thread = threading.Thread(target=analyseData, args=(modelCode,))
    thread.start()
    return response

    
@api.route('/model/checkout', methods=['POST'])
def checkout():
    
    # response = make_response('ok2')
    # modelCode = request.args.getlist('modelCode')#.decode('utf-8')
    param = request.json
    detailId = param['detailId']
    modelCode = [param['modelCode']]
    startTime = param['dataStartTime']
    endTime = param['dataEndTime']
    turbineId = param['enosId']
    # 0. 排除不执行的模型
    final_names = list(set(modelCode) - set(EXCEPT_MODLES))
    # 1. 获取算法信息
    algorithm = importlib.import_module('.' + modelCode[-1], package='algorithms')
    if algorithm.store_file == True:
        filename = os.path.join(Path, modelCode[-1], turbineId, str(detailId)+'.pklz')
        try:
            result = display_util.ReadFile(filename)
            return success(result)
        except Exception as e:
            return error()
    else:
        try:
            asyncio.run(execute_multi_algorithms(modelCode, startTime, endTime, turbineId))
            filename = os.path.join(Path, modelCode[-1], turbineId, 'run'+'.pklz')
            if os.path.exists(filename):
                try:
                    result = display_util.ReadFile(filename)
                    os.remove(filename)
                    return success(result)
                except Exception as e:
                    os.remove(filename)
                    return error()
            else:
                return error()
        except Exception as e:
            return error()


  


@api.get('/model/pushAlarm')
def pushAlarm():
    from alarms.alarm import push_alarm_v2
    assetId = request.args.get('assetId')
    alarmName = request.args.get('alarmName')
    alarmTime = request.args.get('alarmTime')
    error_start_time = request.args.get('error_start_time')
    error_end_time = request.args.get('error_end_time')

    push_alarm_v2(assetId, alarmName, alarmTime, error_start_time, error_end_time)


@api.get("/analyse")
def analyse():
    """
    算法执行
    :param algorithm_name:
    :return:
    """
    try:
        print('--------------------------------------------')
        modelCode = request.args.get('modelCode')
        print(modelCode)
        assetId = 'BYA2LVsH'
        data_df = pd.read_csv(f'sample/{modelCode}.csv')
        data_df.set_index('localtime',inplace=True)
        if modelCode == 'blade_angle_not_balance':
            curves = []
            curves.append({'name': '叶片1桨距角', 'data': list(data_df['WROT.Blade1Position'])})
            curves.append({'name': '叶片2桨距角', 'data': list(data_df['WROT.Blade2Position'])})
            curves.append({'name': '叶片3桨距角', 'data': list(data_df['WROT.Blade3Position'])})
            result = {
                'startTime': data_df.index.min(),
                'endTime': data_df.index.max(),
                'timeInterval': 'm',
                'timeIntervalValue': 10,
                'measurement': '角度',
                'multiDimensionData': curves
            }
            return success(result)
        elif modelCode == 'generator_temperature':
            curves = []
            curves.append({'name': '发电机定子U相线圈温度', 'data': list(data_df['WGEN.TemGenStaU'])})
            curves.append({'name': '发电机定子V相线圈温度', 'data': list(data_df['WGEN.TemGenStaV'])})
            curves.append({'name': '发电机定子W相线圈温度', 'data': list(data_df['WGEN.TemGenStaW'])})
            
            algorithm = importlib.import_module('algorithms.' + modelCode)
            predict_function = getattr(algorithm, 'predict_result')
            # FIXME
            if not modelCode in data_cache:
                predict_data = predict_function(data_df[['WGEN.GenActivePW','WNAC.TemOut','WNAC.TemNacelle','WGEN.LHDLGENAI31','WGEN.GenSpd','WNAC.WindSpeed','WGEN.LHDLGENAI103']].copy())
                data_cache[modelCode] = predict_data
                curves.append({'name': '健康温度', 'data': list(np.round(predict_data,2))})
            else:
                predict_data = data_cache[modelCode]
                curves.append({'name': '健康温度', 'data': list(np.round(predict_data,2))})
            result = {
                'startTime': data_df.index.min(),
                'endTime': data_df.index.max(),
                'timeInterval': 'm',
                'timeIntervalValue': 10,
                'measurement': '温度',
                'multiDimensionData': curves
            }
            return success(result)
        else:
            # 实际数据
            algorithm = importlib.import_module('algorithms.' + modelCode)
            target_column_name = algorithm.ai_points[len(algorithm.ai_points)-1]
            real_data = data_df[[target_column_name,'assetId']]
            print(real_data)
            real_data = real_data[real_data['assetId']==assetId]
            real_data.drop('assetId', inplace=True, axis=1)
            real_data = real_data[target_column_name]
            
            # 预测数据
            # TODO 需不需要清洗数据
            predict_function = getattr(algorithm, 'predict_result')
            # predict_data = predict_function(data_df)
            # print(type(predict_data))
            
            curves = []
            curves.append({'name': '实际温度', 'data': real_data.to_list()})
            if not modelCode in data_cache:
                predict_data = predict_function(data_df)
                data_cache[modelCode] = predict_data
                curves.append({'name': '健康温度', 'data': list(np.round(predict_data,2))})
            else:
                predict_data = data_cache[modelCode]
                curves.append({'name': '健康温度', 'data': list(np.round(predict_data,2))})
            result = {
                'startTime': data_df.index.min(),
                'endTime': data_df.index.max(),
                'timeInterval': 'm',
                'timeIntervalValue': 10,
                'measurement': '温度',
                'multiDimensionData': curves
            }
            return success(result)
    except Exception as e:
        print(e)
        return error(str(e))
