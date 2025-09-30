# -*- coding: utf-8 -*-
import logging.handlers
from apscheduler.schedulers.background import BackgroundScheduler,BlockingScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import algorithms
# from data.get_data import getData, getWindTurbines, getDataForMultiAlgorithms
from data.get_data_async import getWindTurbines, getDataForMultiAlgorithms, getWindTurbinesNode
from configs.config import Wind_Farm, EXCEPT_MODLES, extraModelName
from utils import time_util, display_util
import datetime
import importlib
import pandas as pd
import logging
from logging_config import init_loggers
import asyncio
from datetime import datetime
from db.db import UpdateTubineNum, UpdateAlgorithmInfo, UpdateResult, get_connection, InsertAlgorithmHead, InsertAlgorithmDetail, UpdateAlgorithmHead, ResetTubineNum
import os
import traceback
from collections import ChainMap


# 多模型执行，保证执行频次相同、数据范围相同、依赖测点相似
async def execute_multi_algorithms(names: list, startTime, endTime, turbineId):
    # 0. 排除不执行的模型
    final_names = list(set(names) - set(EXCEPT_MODLES))
    # 1. 获取算法信息
    multi_algorithms = []
    multi_algorithms_config = {}
    for name in final_names:
        multi_algorithms.append(importlib.import_module('.' + name, package='algorithms'))
        name_convice = multi_algorithms[-1].__name__.split('.')[-1]
        endTime_ = datetime.strptime(endTime, '%Y-%m-%d %H:%M:%S')
        startTime_ = datetime.strptime(startTime, '%Y-%m-%d %H:%M:%S')
        multi_algorithms_config[name_convice] = {'startTime':startTime_, 'endTime': endTime_, 'resampleTime':multi_algorithms[-1].resample_interval, 'turbineId':turbineId}
    # 获取模型执行数据时间范围
    # endTime = datetime.now()
    # if not time_util.is_lower_than_day(multi_algorithms[0].time_duration):
    #     endTime = datetime.strptime(datetime.now().strftime('%Y-%m-%d 00:00:00'), '%Y-%m-%d %H:%M:%S')
    # else:
    #     endTime = datetime.strptime(datetime.now().strftime('%Y-%m-%d 00:00:00'), '%Y-%m-%d %H:%M:%S')
        
    # endTime = datetime(2024, 3, 11, 12, 30)
    # startTime = endTime - pd.to_timedelta(multi_algorithms[0].time_duration)
    # 多模型执行
    # await _do_execute(multi_algorithms, startTime, endTime)
    await _do_execute(multi_algorithms, multi_algorithms_config)
    
    


async def execute(name):
    logging.getLogger(name).info(f'开始执行模型:{name}')
    # 1. 获取算法信息
    algorithm = importlib.import_module('.' + name, package='algorithms')
    # 开始结束时间 FIXME 拿到外边去
    endTime = datetime.now()
    if not time_util.is_lower_than_day(algorithm.time_duration):
        endTime = datetime.strptime(datetime.now().strftime('%Y-%m-%d 00:00:00'), '%Y-%m-%d %H:%M:%S')
    startTime = endTime - pd.to_timedelta(algorithm.time_duration)
    await _do_execute([algorithm], startTime, endTime)
    logging.getLogger(name).info(f'结束执行模型:{name}')
    


# 每个算法执行函数 算法维度
async def _do_execute(multi_algorithms, algorithms_configs): #startTime, endTime
    #日志设置
    #日志
    # logging.basicConfig(filemode='w')
    #主日志
    mainLog = logging.getLogger("check_main")
    mainLog.setLevel(level=logging.INFO)
    mainsh = logging.StreamHandler()
    mainLog.addHandler(mainsh)
    director = os.path.dirname(os.path.abspath(__file__))
    # mainfh = logging.FileHandler(filename=os.path.join(director, "logs","main"+".log"), mode='w')
    # mainfh.setLevel(level=logging.INFO)
    # mainLog.addHandler(mainfh)
    mainrfh = logging.handlers.RotatingFileHandler(filename=os.path.join(director, "logs","check_main"+".log"), mode='a', maxBytes=5*1024**2, backupCount=3)
    mainrfh.setLevel(level=logging.INFO)
    mainLog.addHandler(mainrfh)
    format = '%(asctime)s - %(levelname)s - %(message)s' 
    log_format = logging.Formatter(fmt=format)
    mainsh.setFormatter(log_format)
    # mainfh.setFormatter(log_format)
    mainrfh.setFormatter(log_format)
    mainLog.info("+++++++++++++++++++++++++++++++++++++++++++新任务++++++++++++++++++++++++++++++++++++++++++")
    #算法日志
    algorithmLogs = {}
    algorithmshs = {} #控制台打印
    algorithmfhs = {} #输出到文件
    algorithmrfhs = {} #输出到文件，且文件可以根据大小分割
    modelIds = []
    for algorithm in multi_algorithms:
        name = algorithm.__name__.split('.')[-1]
        if hasattr(algorithm, 'modelId'):
            modelIds.append(algorithm.modelId)
        algorithmLogs[name] = logging.getLogger('check_'+name)
        algorithmLogs[name].setLevel(level=logging.INFO)
        # algorithmshs[name] = logging.StreamHandler()
        # algorithmLogs[name].addHandler(algorithmshs[name])
        # algorithmfhs[name] = logging.FileHandler(filename=os.path.join(director, "logs",name+".log"), mode='w')
        # algorithmfhs[name].setLevel(level=logging.INFO)
        algorithmrfhs[name] = logging.handlers.RotatingFileHandler(filename=os.path.join(director, "logs",'check_'+name+".log"), mode='a', maxBytes=2*1024**2, backupCount=3)
        algorithmrfhs[name].setLevel(level=logging.INFO)
        # algorithmLogs[name].addHandler(algorithmfhs[name])
        algorithmLogs[name].addHandler(algorithmrfhs[name])
        # algorithmshs[name].setFormatter(log_format)
        # algorithmfhs[name].setFormatter(log_format)
        algorithmrfhs[name].setFormatter(log_format)
        algorithmLogs[name].info("+++++++++++++++++++++++++++++++++++++++++++新任务++++++++++++++++++++++++++++++++++++++++++")
        assetId = algorithms_configs[name]['turbineId']

    # 1. 获取所有风机
    df_wind_turbine = await getWindTurbines(Wind_Farm)
    mainLog.info(f'开始执行算法{multi_algorithms}') #，执行时间范围{startTime}-{endTime}
    mainLog.info(f'获取风场{Wind_Farm}的风机数量为{df_wind_turbine.shape[0]}')
    #筛选风机
    df_wind_turbine = df_wind_turbine.loc[df_wind_turbine['mdmId']==assetId]
    assetIds = df_wind_turbine['mdmId']
    #获取每个风机私有节点id
    try:
        multiModelAssetIds = await getWindTurbinesNode(assetIds, modelIds, nameConstrain=extraModelName) #一个风机可能会有多个模型资产Id
    except Exception as e:
        errorInfomation = traceback.format_exc()
        mainLog.info(f'\033[31m{errorInfomation}\033[0m')
        mainLog.info(f'\033[33m获取私有测点时发生异常：{e}\033[0m')
        endAlgorithmTime = datetime.now()
        multiModelAssetIds = [[]]*df_wind_turbine.shape[0]
    total_no_alarm_models = []    # 所有台正常执行、有数据、无告警模型
    total_alarm_models = []       # 所有台正常执行、有数据、有告警模型
    total_exception_models = []   # 所有台执行发生异常模型
    total_data_empty_models = []  # 所有台正常执行、无数据的模型
    turbineIndex = 0
    idMaps = {}
    # mysqlClient = get_connection()
    # 控制风机数量
    # df_wind_turbine = df_wind_turbine.iloc[0:3]
    # df_wind_turbine = df_wind_turbine.iloc[[4]]
    #将model表里上次和这次执行对应算法的sum_num和current_num置回初始位
    # mainLog.info(f'每次请求时重置algorithm_model表里的对应算法的风机总数和当前执行完算法台数')
    # for algorithm in multi_algorithms:
    #     name = algorithm.__name__.split('.')[-1]
    #     algorithmLogs[name].info(f'每次请求时重置algorithm_model表里的对应算法的风机总数和当前执行完算法台数')
        # ResetTubineNum(mysqlClient,name, df_wind_turbine.shape[0],0)
    #
    # 2. 每台风机执行算法
    for index, row in df_wind_turbine.iterrows():
        turbineIndex += 1
        assetId = row['mdmId'] #风机id
        turbineName = row['name']
        ratedPower = row['ratedPower']
        mainLog.info(f'===================================开始执行风机{assetId}预警模型: {turbineIndex}/{df_wind_turbine.shape[0]}==============================================')
        # 判断是否需要全场数据
        
        for algorithm in multi_algorithms:
            name = algorithm.__name__.split('.')[-1]
            algorithmLogs[name].info(f'===================================开始执行风机{assetId}预警模型: {turbineIndex}/{df_wind_turbine.shape[0]}==============================================')
            if algorithm.need_all_turbines:
            # param_assetIds = assetIds
            # param_private_assetIds = multiModelAssetIds#[index]
                if turbineIndex == df_wind_turbine.shape[0]:
                    algorithms_configs[name]['PrepareTurbines'] = True
                    algorithms_configs[name]['param_private_assetIds'] = multiModelAssetIds#[multiModelAssetIds[index]]
                    algorithms_configs[name]['param_assetIds'] = assetIds.tolist() #[assetId]
                else:
                    algorithms_configs[name]['PrepareTurbines'] = False
                    # param_private_assetIds = [multiModelAssetIds[index]]
                    # param_assetIds = [assetId]
            else:
                algorithms_configs[name]['PrepareTurbines'] = True
                algorithms_configs[name]['param_private_assetIds'] = [multiModelAssetIds[-1]]
                algorithms_configs[name]['param_assetIds'] = [assetId]
        

        algorithmData = {}
        mainLog.info(f'获取{turbineName}风机各算法需要的数据:')
        for index_algorithm, algorithm in enumerate(multi_algorithms):
            # subLoop = asyncio.new_event_loop()
            name = algorithm.__name__.split('.')[-1]
            mainLog.info(name+":"+str(index_algorithm)+'/'+str(len(multi_algorithms)))
            algorithmLogs[name].info(f'获取{turbineName}风机本算法需要的数据:')
            algorithmLogs[name].info(name+":"+str(index_algorithm)+'/'+str(len(multi_algorithms)))
            if algorithms_configs[name]['PrepareTurbines'] == True:
                # data = await getDataForMultiAlgorithms(algorithms_configs[algorithm.__name__.split('.')[-1]]['startTime'], 
                #                            algorithms_configs[algorithm.__name__.split('.')[-1]]['endTime'], algorithms_configs[algorithm.__name__.split('.')[-1]]['param_assetIds'], 
                #                            algorithms_configs[algorithm.__name__.split('.')[-1]]['param_private_assetIds'], 
                #                            algorithm)
                data = getDataForMultiAlgorithms(algorithms_configs[algorithm.__name__.split('.')[-1]]['startTime'], 
                                            algorithms_configs[algorithm.__name__.split('.')[-1]]['endTime'], algorithms_configs[algorithm.__name__.split('.')[-1]]['param_assetIds'], 
                                            algorithms_configs[algorithm.__name__.split('.')[-1]]['param_private_assetIds'], 
                                            algorithm)
                try:
                    element_dict = await data
                    algorithmData = {**algorithmData, **element_dict}
                except Exception as e:
                    errorInfomation = traceback.format_exc()
                    mainLog.info(f'\033[31m{errorInfomation}\033[0m')
                    mainLog.info(f'\033[33m风机{assetId}/{turbineName}时发生异常：{e}\033[0m')
                    endAlgorithmTime = datetime.now()

        # chainData = ChainMap(algorithmData)
        # algorithm_data_df = pd.DataFrame()


        #算法名1, 算法名2, ... 
        #数据1, 数据2, ...
        # for name, data in algorithmData.items():
        #     algorithm_data_df[name] = data
            # data_df =  await getDataForMultiAlgorithms(startTime, endTime, param_assetIds, param_private_assetIds, multi_algorithms)#await
        # except Exception as e:
        #     errorInfomation = traceback.format_exc()
        #     mainLog.info(f'\033[31m{errorInfomation}\033[0m')
        #     mainLog.info(f'\033[33m风机{assetId}/{turbineName}时发生异常：{e}\033[0m')
        #     endAlgorithmTime = datetime.now()
        #     algorithm_data_df = pd.DataFrame()
        # if data_df.empty:
        #     names = [algorithm.__name__.split('.')[-1] for algorithm in multi_algorithms]
        #     mainLog.info(f'风机{assetId}模型{names}获取数据为空')
            # continue
        # 4. 串行执行模型
        no_alarm_models = []    # 正常执行、有数据、无告警模型
        alarm_models = []       # 正常执行、有数据、有告警模型
        exception_models = []   # 执行发生异常模型
        data_empty_models = []  # 正常执行、无数据的模型
        startTurbineTime = datetime.now()
        for algorithm in multi_algorithms:
            startAlgorithmTime = datetime.now()
            name = algorithm.__name__.split('.')[-1]
            mainLog.info(f'{turbineName}台风机执行算法{name}')
            algorithmLogs[name].info(f'{name}开始执行风机{assetId}')
            if name not in idMaps.keys():
                #添加任务
                mainLog.info(f"添加任务algorithm_execute_head：算法名>{name},风机名>{turbineName}")
                algorithmLogs[name].info(f"添加任务algorithm_execute_head：算法名>{name},风机名>{turbineName}")
                # taskId = InsertAlgorithmHead(mysqlClient, name, startAlgorithmTime)
                #任务id映射
                # idMaps[name] = str(taskId)
            #提取算法对应的数据
            if name in algorithmData.keys():
                data_df = algorithmData[name]
            else:
                data_df = pd.DataFrame()
            if data_df.empty:
                data_empty_models.append(name)
                #更新algorithm_model表,部分字段
                mainLog.info(f'模型{name}更新algorithm_model，时间，进度字段{turbineIndex}')
                algorithmLogs[name].info(f'模型{name}更新algorithm_model，时间，进度字段{turbineIndex}')
                endAlgorithmTime = datetime.now()
                # UpdateTubineNum(mysqlClient, name, startAlgorithmTime, endAlgorithmTime, df_wind_turbine.shape[0], turbineIndex)
                #更新AlgorithmDetail
                mainLog.info(f"风机名>{turbineName}, 算法名>{name}, 数据为空")
                algorithmLogs[name].info(f"风机名>{turbineName}, 算法名>{name}, 数据为空")
                # InsertAlgorithmDetail(mysqlClient, idMaps[name], turbineName, startTurbineTime, 2, assetId, "从终台没有提取到数据")
                return None
            try:
                # 清洗数据
                # wash_data 要选取自己模型需要的测点数据返回,测点缺失
                if not set(algorithm.ai_points + algorithm.di_points+algorithm.general_points).issubset(set(data_df.columns)):  
                    data_empty_models.append(name)
                    mainLog.info(f'模型{name}缺少测点，无法继续执行')
                    algorithmLogs[name].info(f'模型{name}缺少测点，无法继续执行')
                    #更新algorithm_model表,部分字段
                    mainLog.info(f'模型{name}更新algorithm_model，时间，进度字段{turbineIndex}')
                    algorithmLogs[name].info(f'模型{name}更新algorithm_model，时间，进度字段{turbineIndex}')
                    endAlgorithmTime = datetime.now()
                    # UpdateTubineNum(mysqlClient, name, startAlgorithmTime, endAlgorithmTime, df_wind_turbine.shape[0], turbineIndex)
                    #更新AlgorithmDetail
                    mainLog.info(f"风机名>{turbineName}, 算法名>{name}, 数据为空")
                    algorithmLogs[name].info(f"风机名>{turbineName}, 算法名>{name}, 数据为空")
                    # InsertAlgorithmDetail(mysqlClient, idMaps[name], turbineName, startTurbineTime, 2, assetId, "终台提取数据时缺少算法需要的字段")
                    return None
                final_data = algorithm.wash_data(data_df, ratedPower)
                if not final_data.empty:
                    # 跑模型
                    abnormal_data, statement, display = algorithm.judge_model(final_data, assetId)
                    mainLog.info(f'##############################################\!\!\!本次查看的所有模型已跑完,注：本次请求的mainlog日志会覆盖上次请求的日志!\!\!################################################')
                    # return display
                    display_util.StoreResult(display, name, assetId, 'run')
                    return None
                else:
                    mainLog.info(f'##############################################\!\!\!本次查看的所有模型已跑完,注：本次请求的mainlog日志会覆盖上次请求的日志!\!\!################################################')
                    return None
            except Exception as e:
                errorInfomation = traceback.format_exc()
                mainLog.info(f'\033[31m{errorInfomation}\033[0m')
                mainLog.info(f'\033[33m风机{assetId}在执行模型{name}时发生异常：{e}\033[0m')
                algorithmLogs[name].info(f'\033[31m{errorInfomation}\033[0m')
                algorithmLogs[name].info(f'\033[33m风机{assetId}在执行模型{name}时发生异常：{e}\033[0m')
                mainLog.info(f'##############################################\!\!\!本次查看的所有模型已跑完,注：本次请求的mainlog日志会覆盖上次请求的日志!\!\!################################################')
                return None
    

    