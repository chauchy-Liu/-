# -*- coding: utf-8 -*-
"""
Created on Fri Jun  2 11:00:00 2023

@author: sunyan
"""

from poseidon import poseidon  # 打包时注意
import pandas as pd
from functools import partial  # 偏函数，用于map传递多个参数
from multiprocessing import Pool  # 计算密集型采用该并行
import numpy as np
from sklearn.neighbors import LocalOutlierFactor
from itertools import product
import utils.time_util as time_util
from datetime import timedelta
from configs import config
import logging
from configs.config import AccessKey, SecretKey, GW_Url, OrgId, algConfig
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import traceback
from datetime import datetime
import importlib
import os
from logging.handlers import RotatingFileHandler

data_logger = logging.getLogger('get_data')
if not data_logger.handlers:
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(process)d - %(threadName)s - %(message)s')
    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(formatter)
    # alarm_file_handler = TimedRotatingFileHandler('logs/alarm.log', when='midnight', interval=1, backupCount=30)
    data_file_handler = RotatingFileHandler(filename=os.path.join("logs","data"+".log"), mode='a', maxBytes=5*1024**2, backupCount=3)
    data_file_handler.setFormatter(formatter)
    data_logger.setLevel(logging.INFO)
    # data_logger.addHandler(console_handler)
    data_logger.addHandler(data_file_handler)


Url_asset = GW_Url + '/cds-asset-service/v1.0/hierarchy?orgId=' + OrgId  # 这个api哪里来的？
Url_ai_normalized = GW_Url + '/tsdb-service/v2.1/ai-normalized?orgId=' + OrgId
Url_ai = GW_Url + '/tsdb-service/v2.1/ai?orgId=' + OrgId
Url_raw = GW_Url + '/tsdb-service/v2.1/raw?orgId=' + OrgId
Url_di = GW_Url + '/tsdb-service/v2.1/di?orgId=' + OrgId
Url_node = GW_Url + '/asset-tree-service/v2.1/asset-nodes?action=searchRelatedAsset&orgId=' + OrgId

pd.options.mode.use_inf_as_na = True
lock = asyncio.Lock()

async def run_in_threadpool(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(ThreadPoolExecutor(), lambda: func(*args))


async def getWindTurbines(wind_farm):
    '''
    获取风场下的风机
    '''
    url_asset = Url_asset + '&mdmIds=' + wind_farm + \
        '&mdmTypes=EnOS_Wind_Turbine&attributes=mdmId,name,ratedPower,rotorDiameter,altitude,hubHeight'
    # with ThreadPoolExecutor(max_workers=3) as executor:
    #获取每一个风机属性
    #python版本>3.8
    # ResponsePoint = await asyncio.to_thread(poseidon.urlopen, AccessKey, SecretKey, url_asset)#poseidon.urlopen(AccessKey, SecretKey, url_asset)#await asyncio.to_thread(poseidon.urlopen, AccessKey, SecretKey, url_asset)
    #python版本=3.8
    ResponsePoint = await asyncio.to_thread(poseidon.urlopen, AccessKey, SecretKey, url_asset)#await run_in_threadpool(poseidon.urlopen, AccessKey, SecretKey, url_asset)#poseidon.urlopen(AccessKey, SecretKey, url_asset)#await asyncio.to_thread(poseidon.urlopen, AccessKey, SecretKey, url_asset)
    if ResponsePoint and ResponsePoint['pagination']['pageSize'] > 0:
        wind_turbine_df = pd.DataFrame(
            ResponsePoint['data'][wind_farm]['mdmObjects']['EnOS_Wind_Turbine'][:])
        wind_turbine_df['name'] = list(
            map(lambda x: x['name'],  wind_turbine_df['attributes']))
        wind_turbine_df['ratedPower'] = list(
            map(lambda x: x['ratedPower'],  wind_turbine_df['attributes']))
        wind_turbine_df['rotorDiameter'] = list(
            map(lambda x: x['rotorDiameter'],  wind_turbine_df['attributes']))
        wind_turbine_df['altitude'] = list(
            map(lambda x: x['altitude'],  wind_turbine_df['attributes']))
        wind_turbine_df['hubHeight'] = list(
            map(lambda x: x['hubHeight'],  wind_turbine_df['attributes']))
        wind_turbine_df.drop('attributes', axis=1, inplace=True)
        return wind_turbine_df 
    else:
        return pd.DataFrame()


async def getWindTurbinesNode(turbineIds, algorithms_configs, nameConstrain=None):
    '''
    获取风机下的模块信息
    '''
    url_node = Url_node + '&treeId=VsKgAT9I' #+ \
        #'&projection=attributes,assetId,name'
    # with ThreadPoolExecutor(max_workers=3) as executor:
    multiAssetIds = [] #[风机1[算法1[模型1(id),模型2(id),...], [算法2],...], [风机2],...]
    for turbineId in turbineIds: #[turbine1:(modelid1, modelid2,...), turbine2:(modelid1, modelid2,..), ...]
        params = {
            "filter": {
                "isChildOfAssetId": turbineId
            },
            "action": "searchRelatedAsset"
        }
        #获取每一个风机属性
        ResponsePoint = await asyncio.to_thread(poseidon.urlopen,AccessKey, SecretKey, url_node, params)
        # ResponsePoint = await run_in_threadpool(poseidon.urlopen,AccessKey, SecretKey, url_node, params)
        if ResponsePoint and len(ResponsePoint['data']) > 0:
            wind_turbine_df = pd.DataFrame(ResponsePoint['data'])
            wind_turbine_df['modelName'] = [value['defaultValue'] for value in wind_turbine_df['name']]
            multiAlgs = {}
            for alKey, alValue in algorithms_configs.items():
                modelAssetIds = []
                for modelKey, modelValue in alValue['privatePoints'].items():
                    modelId = modelKey
                    if nameConstrain == None:
                        wind_turbine_df_filted = wind_turbine_df[wind_turbine_df['modelId']==modelId]
                    else:
                        wind_turbine_df_filted = wind_turbine_df[wind_turbine_df['modelId']==modelId]
                        wind_turbine_df_filted = wind_turbine_df_filted[wind_turbine_df['modelName'].str.contains(nameConstrain)]
                    # turbineIds.loc[index, 'modelAssetId'] = wind_turbine_df_filted['assetId']
                    # turbineAssets.append(wind_turbine_df_filted.iloc[0]['assetId'])
                    try:
                        modelAssetIds.append(wind_turbine_df_filted.iloc[0]['assetId'])
                    except Exception as e:
                        errorInfomation = traceback.format_exc()
                        data_logger.info(f'\033[31m{errorInfomation}\033[0m')
                        data_logger.info(f'\033[33mgetWindTurbinesNode->{e}\033[0m')
                multiAlgs[alKey] = modelAssetIds
        else:
            multiAlgs = {}
            for alKey, alValue in algorithms_configs.items():
                modelAssetIds = []
            multiAlgs[alKey] = modelAssetIds

        multiAssetIds.append(multiAlgs)
        
    return multiAssetIds #[机型1:{算法1:[模型1(id),]}, ...]


async def getRawData(startTime, endTime, points, assetIds):
    DfTemp = pd.DataFrame()
    params = {"assetIds": ','.join(assetIds),
              "pointIds": points,
              "startTime": startTime,
              "endTime": endTime,
              "itemFormat": "1",
              "type": "ai_normalized",  # ai,ai_normalized,di,pi,generic
              "boundaryType": "sample",
              "interval": 600,
              "interpolation": "near",
              "pageSize": "20000"}

    ResponsePoint = await asyncio.to_thread(poseidon.urlopen, AccessKey, SecretKey, Url_raw, params)
    # ResponsePoint = await run_in_threadpool(poseidon.urlopen, AccessKey, SecretKey, Url_raw, params)
    if ResponsePoint and ResponsePoint['data'] and len(ResponsePoint['data']['items']) > 0:
        DfTemp = pd.DataFrame(ResponsePoint['data']['items'])
    return DfTemp

async def getGeneralData(algorithmName: str, startTime, endTime, assetId: str, points, resample_interval, algorithms_configs):
    turbinenames = dict(zip(algorithms_configs[algorithmName]['param_assetIds'],algorithms_configs[algorithmName]['param_turbine_num']))
    ResponsePoint = None
    params = {
                "Access Key":AccessKey,
                "Secret Key":SecretKey,
                "assetIds": assetId,
                "pointIds": ','.join(points),
                "startTime": startTime,
                "endTime": endTime,
                # "interval": "0",
                "itemFormat": "1",
                "pageSize": "20000",
                "type": "generic"}
    # ResponsePoint = poseidon.urlopen(AccessKey, SecretKey, Url_raw, params)
    ResponsePoint = await asyncio.to_thread(poseidon.urlopen,AccessKey, SecretKey, Url_raw, params)
    DfTemp = pd.DataFrame()
    if len(ResponsePoint['data']['items']) > 0:
        DfTemp = pd.DataFrame(ResponsePoint['data']['items'])
        DfTemp.set_index('localtime', inplace=True)
        DfTemp.index = pd.to_datetime(DfTemp.index)
        #填充替换NaN
        DfTemp = DfTemp.ffill()
        DfTemp = DfTemp.bfill()
        DfTemp = DfTemp.fillna(0)
        value, unit = time_util.split_time_delta(resample_interval)
        if pd.Timedelta(str(value)+unit) > pd.Timedelta('1min'):
            resample_interval = time_util.replace_to_resample(
                resample_interval)
            #实际取得的测点和自定义的可能不一致会报错
            common_columns = DfTemp.columns.intersection(points).tolist()
            DfTemp = DfTemp[common_columns].resample(
                resample_interval, closed='left').mean().ffill()#  # FIXME
            DfTemp = DfTemp[common_columns].astype(int)
        #重命名
        #算法名
        DfTemp['algorithm'] = algorithmName
        DfTemp['assetId'] = assetId
        DfTemp['wtid'] = turbinenames[assetId]
    return DfTemp

async def getDiData(algorithmName: str, startTime, endTime, assetId: str, points, resample_interval, algorithms_configs):
    # # print(startTime, endTime, points, assetId)
    # DfTemp = pd.DataFrame()
    # params = {"assetIds": assetId,
    #           "pointIds": points,
    #           "startTime": startTime,
    #           "endTime": endTime,
    #           "autoInterpolate": True,
    #           "itemFormat": "1",
    #           "type":"di"}

    # # ResponsePoint = await asyncio.to_thread(poseidon.urlopen, AccessKey, SecretKey, Url_di, params)
    # ResponsePoint = await run_in_threadpool(poseidon.urlopen, AccessKey, SecretKey, Url_di, params)
    # if ResponsePoint and ResponsePoint['data'] and len(ResponsePoint['data']['items']) > 0:
    #     DfTemp = pd.DataFrame(ResponsePoint['data']['items'])
    # return DfTemp
    turbinenames = dict(zip(algorithms_configs[algorithmName]['param_assetIds'],algorithms_configs[algorithmName]['param_turbine_num']))
    ResponsePoint = None
    params = {
                "Access Key":AccessKey,
                "Secret Key":SecretKey,
                "assetIds": assetId,
                "pointIds": ','.join(points),
                "startTime": startTime,
                "endTime": endTime,
                # "interval": "0",
                "itemFormat": "1",
                "pageSize": "20000",
                "type": "di"}
    # ResponsePoint = poseidon.urlopen(AccessKey, SecretKey, Url_di, params)
    ResponsePoint = await asyncio.to_thread(poseidon.urlopen,AccessKey, SecretKey, Url_di, params)
    DfTemp = pd.DataFrame()
    if len(ResponsePoint['data']['items']) > 0:
        DfTemp = pd.DataFrame(ResponsePoint['data']['items'])
        DfTemp.set_index('localtime', inplace=True)
        DfTemp.index = pd.to_datetime(DfTemp.index)
        #填充替换NaN
        DfTemp = DfTemp.ffill()
        DfTemp = DfTemp.bfill()
        DfTemp = DfTemp.fillna(0)
        value, unit = time_util.split_time_delta(resample_interval)
        if pd.Timedelta(str(value)+unit) > pd.Timedelta('1min'):
            resample_interval = time_util.replace_to_resample(
                resample_interval)
            #实际取得的测点和自定义的可能不一致会报错
            common_columns = DfTemp.columns.intersection(points).tolist()
            DfTemp = DfTemp[common_columns].resample(
                resample_interval, closed='left').mean().ffill()#  # FIXME
            DfTemp = DfTemp[common_columns].astype(int)
        #重命名
        if 'WTUR.TurbineSts' not in DfTemp.columns.tolist():
            DfTemp.rename(columns={'WTUR.TurbineSts_Map':'WTUR.TurbineSts'}, inplace=True)
        #算法名
        DfTemp['algorithm'] = algorithmName
        DfTemp['assetId'] = assetId
        DfTemp['wtid'] = turbinenames[assetId]
    return DfTemp


async def getAiData(algorithmName: str, startTime, endTime, assetId: str, points, resample_interval, algorithms_configs):

    turbinenames = dict(zip(algorithms_configs[algorithmName]['param_assetIds'],algorithms_configs[algorithmName]['param_turbine_num']))
    # print(startTime, endTime, assetId, points, resample_interval)
    ResponsePoint = None
    # time.sleep(5)
    if time_util.use_raw_api(resample_interval):
        params = {"assetIds": assetId,
                  "pointIds": ','.join(points),
                  "startTime": startTime,
                  "endTime": endTime,
                  "itemFormat": "1",
                  "pageSize": "20000",
                  "boundaryType": 'inside'}
        ResponsePoint = await asyncio.to_thread(poseidon.urlopen, AccessKey, SecretKey, Url_ai, params)
        # ResponsePoint = await run_in_threadpool(poseidon.urlopen, AccessKey, SecretKey, Url_ai, params)
    else:
        params = {"assetIds": assetId,
                  "pointIdsWithLogic": ','.join(points),
                  "startTime": startTime,
                  "endTime": endTime,
                  "interval": "0",
                  "itemFormat": "1",
                  "pageSize": "20000"}
        ResponsePoint = await asyncio.to_thread(poseidon.urlopen,AccessKey, SecretKey, Url_ai_normalized, params)
        # ResponsePoint = await run_in_threadpool(poseidon.urlopen,
            # AccessKey, SecretKey, Url_ai_normalized, params)
    # logging.getLogger().info(ResponsePoint)
    data_logger.info(f"#####################当前算法：{algorithmName}=>风机ID/机号:{algorithms_configs[algorithmName]['param_assetIds']}/{algorithms_configs[algorithmName]['param_turbine_num']}=>设备ID:{assetId}=>数据时间范围{startTime}到{endTime}#############################")
    data_logger.info(f"数据接口url：{Url_ai_normalized}")
    data_logger.info(f"数据接口参数：{params}")
    DfTemp = pd.DataFrame()
    if ResponsePoint and ResponsePoint['data'] and len(ResponsePoint['data']['items']) > 0:
        DfTemp = pd.DataFrame(ResponsePoint['data']['items'])
        DfTemp.set_index('localtime', inplace=True)
        DfTemp.index = pd.to_datetime(DfTemp.index)
        algorithm = importlib.import_module('.' + algorithmName, package='algorithms')
        if hasattr(algorithm, 'vane_nan_num'):
            for realName, rename in  algConfig[algorithmName]['ai_rename'].items():
                if rename == 'WNAC.WindVaneDirection':
                    break
            if len(algConfig[algorithmName]['ai_rename']) > 0:
                algorithm.vane_nan_num = algorithm.vane_nan_num + DfTemp[realName].isna().sum()
                data_logger.info(realName+f"缺失值的功率{list(DfTemp[DfTemp[realName].isna()]['WGEN.GenActivePW'])}")
            # print(algorithm.vane_nan_num)
        #填充替换NaN
        DfTemp = DfTemp.ffill()
        DfTemp = DfTemp.bfill()
        DfTemp = DfTemp.fillna(0)
        value, unit = time_util.split_time_delta(resample_interval)
        if pd.Timedelta(str(value)+unit) > pd.Timedelta('1min'):
            resample_interval = time_util.replace_to_resample(
                resample_interval)
            #实际取得的测点和自定义的可能不一致会报错
            common_columns = DfTemp.columns.intersection(points).tolist()
            DfTemp = DfTemp[common_columns].resample(
                resample_interval, closed='left').mean()  # FIXME
       
        DfTemp = DfTemp.round(4)
        #算法名
        DfTemp['algorithm'] = algorithmName
        DfTemp['assetId'] = assetId
        DfTemp['wtid'] = turbinenames[algorithms_configs[algorithmName]['param_assetIds'][-1]]
        data_logger.info(f"提取的测点有：{list(DfTemp.columns)}")
        data_logger.info(f"前10行数据：{DfTemp.iloc[:10]}")
    else:
        data_logger.info(f"没有提取到测点")
    return DfTemp


# async def TimeDeviceSlicePrivate(algorithms_configs, assetIds, privateIds, resample_interval, getData):
#     # 按算法种类、时间和设备分片
#         for key, value in algorithms_configs.items():
#             startTime = value['startTime']
#             endTime = value['endTime']
#             date_range = []
#             if endTime - startTime > timedelta(hours=12):
#                 date_range = pd.date_range(startTime, endTime, freq="12H").strftime(
#                     '%Y-%m-%d %H:%M:%S').to_list()
#             else:
#                 date_range = [startTime.strftime('%Y-%m-%d %H:%M:%S'), endTime.strftime('%Y-%m-%d %H:%M:%S')]
#             time_param = [(key, date_range[i], date_range[i + 1])
#                         for i in range(len(date_range) - 1)]
            
def custom_merge(df_list):
    # 获取所有DataFrame的行索引和列名
    all_index = set()
    all_columns = set()
    for df in df_list:
        all_index.update(df.index)
        all_columns.update(df.columns)
    
    # 创建一个空的DataFrame，包含所有可能的行和列
    result = pd.DataFrame(index=sorted(all_index), columns=sorted(all_columns))
    
    # 填充数据
    for df in df_list:
        for idx in df.index:
            for col in df.columns:
                if pd.notna(df.loc[idx, col]):  # 只更新非空值
                    result.loc[idx, col] = df.loc[idx, col]
    
    return result

async def TimeDeviceSlice(algorithms_configs): #, ai_points, resample_interval, getData

    
    # 按算法种类、时间和设备分片
    time_asset_param = []
    di_time_asset_param = []
    for key, value in algorithms_configs.items():
        # print(key)
        # if algorithms_configs[key]['PrepareTurbines'] == True:
        # 私有设备id扁平化
        privateIds = []
        for ids in value['param_private_assetIds']:
            privateIds += ids
        # privateIds = value['param_private_assetIds'] #[风机1[model1(id),model2(id)], 风机2[model1(id),model2(id)]]
        assetIds = value['param_assetIds']
        startTime = value['startTime']
        endTime = value['endTime']
        #di测点一般7天有一次数据, 小于7天可能获取不到数据
        di_startTime = value['startTime']
        di_endTime = value['endTime']
        if di_endTime - di_startTime < timedelta(days=7):
            di_startTime = di_endTime - timedelta(days=7)
        #时间分片
        date_range = []
        if endTime - startTime > timedelta(hours=12):
            date_range = pd.date_range(startTime, endTime, freq="12h").strftime(
                '%Y-%m-%d %H:%M:%S').to_list()
        else:
            date_range = [startTime.strftime('%Y-%m-%d %H:%M:%S'), endTime.strftime('%Y-%m-%d %H:%M:%S')]
        time_param = [(key, date_range[i], date_range[i + 1])
                    for i in range(len(date_range) - 1)]
        #针对di时间
        di_date_range = []
        if di_endTime - di_startTime > timedelta(hours=12):
            di_date_range = pd.date_range(di_startTime, di_endTime, freq="12h").strftime(
                '%Y-%m-%d %H:%M:%S').to_list()
        else:
            di_date_range = [di_startTime.strftime('%Y-%m-%d %H:%M:%S'), di_endTime.strftime('%Y-%m-%d %H:%M:%S')]
        di_time_param = [(key, di_date_range[i], di_date_range[i + 1])
                    for i in range(len(di_date_range) - 1)]
        # 加上设备（笛卡尔积）
        if len(value["privatePoints"])>0:
            # for modelKey, pointsValue in value["privatePoints"].items():
            time_asset_param += product(time_param, privateIds)
        if len(value["aiPoints"]) > 0 or len(value["generalPoints"])>0:
            time_asset_param += product(time_param, assetIds)
        if len(value["diPoints"]) > 0:
            di_time_asset_param += product(di_time_param, assetIds)
    if len(time_asset_param) == 0 and len(di_time_asset_param) == 0:
        return {}, {}, {}, {}
    final_time_asset_param = [(item[0][0], item[0][1], item[0][2], item[1])
                              for item in time_asset_param]  #(algorithm, startTime,startTime+12,turbineId)
    di_final_time_asset_param = [(item[0][0], item[0][1], item[0][2], item[1])
                              for item in di_time_asset_param]  #(algorithm, startTime,startTime+12,turbineId)
    # getAiDataWithTimeFunc = partial(getAiData, points=ai_points, resample_interval=resample_interval)
    # 获取ai数据
    timeout = 300 #180 #秒
    aiTasks = [getAiData(time_tuple[0], time_tuple[1], time_tuple[2], time_tuple[3], algorithms_configs[time_tuple[0]]["aiPoints"], algorithms_configs[time_tuple[0]]["resampleTime"], algorithms_configs) for time_tuple in final_time_asset_param if len(algorithms_configs[time_tuple[0]]["aiPoints"])>0]
    if len(aiTasks) > 0:
        # aiResults = await asyncio.gather(*aiTasks)#, return_exceptions=True
        # aiResults = [asyncio.ensure_future(task) for task in aiTasks]
        # done, pending = await asyncio.wait(aiResults, timeout=timeout)   
        done, pending = await asyncio.wait(aiTasks, timeout=timeout)   
        aiResults = [task.result() for task in done]
        tmp = [task.cancel() for task in pending]
    else:
        aiResults = []
    # 获取di数据
    diTasks = [getDiData(time_tuple[0], time_tuple[1], time_tuple[2], time_tuple[3], algorithms_configs[time_tuple[0]]["diPoints"], algorithms_configs[time_tuple[0]]["resampleTime"], algorithms_configs) for time_tuple in di_final_time_asset_param if len(algorithms_configs[time_tuple[0]]["diPoints"])>0]
    if len(diTasks) > 0:
        # diResults = await asyncio.gather(*diTasks)#, return_exceptions=True
        # diResults = [asyncio.ensure_future(task) for task in diTasks]
        # done, pending = await asyncio.wait(diResults, timeout=timeout)   
        done, pending = await asyncio.wait(diTasks, timeout=timeout)   
        diResults = [task.result() for task in done]
        tmp = [task.cancel() for task in pending]
    else:
        diResults = []
    # 获取general数据
    generalTasks = [getGeneralData(time_tuple[0], time_tuple[1], time_tuple[2], time_tuple[3], algorithms_configs[time_tuple[0]]["generalPoints"], algorithms_configs[time_tuple[0]]["resampleTime"], algorithms_configs) for time_tuple in final_time_asset_param if len(algorithms_configs[time_tuple[0]]["generalPoints"])>0]
    if len(generalTasks) > 0:
        # generalResults = await asyncio.gather(*generalTasks)#, return_exceptions=True
        # generalResults = [asyncio.ensure_future(task) for task in generalTasks]
        # done, pending = await asyncio.wait(generalResults, timeout=timeout)   
        done, pending = await asyncio.wait(generalTasks, timeout=timeout)   
        generalResults = [task.result() for task in done]
        tmp = [task.cancel() for task in pending]
    else:
        generalResults = []
    # 获取private数据
    privateTasks = []#[getAiData(time_tuple[0], time_tuple[1], time_tuple[2], time_tuple[3], algorithms_configs[time_tuple[0]]["privatePoints"], algorithms_configs[time_tuple[0]]["resampleTime"]) for time_tuple in final_time_asset_param if len(algorithms_configs[time_tuple[0]]["privatePoints"])>0]
    for time_tuple in final_time_asset_param:
        if len(algorithms_configs[time_tuple[0]]["privatePoints"])>0:
            for modelKey, pointValue in algorithms_configs[time_tuple[0]]["privatePoints"].items():
                if len(pointValue) > 5:
                    accumCount = 0
                    while len(pointValue[accumCount:]) >= 5:
                        privateTasks.append(getAiData(time_tuple[0], time_tuple[1], time_tuple[2], time_tuple[3], pointValue[accumCount:accumCount+5], algorithms_configs[time_tuple[0]]["resampleTime"], algorithms_configs))
                        accumCount += 5
                    if len(pointValue[accumCount:]) > 0:
                        privateTasks.append(getAiData(time_tuple[0], time_tuple[1], time_tuple[2], time_tuple[3], pointValue[accumCount:], algorithms_configs[time_tuple[0]]["resampleTime"], algorithms_configs))
                else:
                    privateTasks.append(getAiData(time_tuple[0], time_tuple[1], time_tuple[2], time_tuple[3], pointValue, algorithms_configs[time_tuple[0]]["resampleTime"], algorithms_configs))
    if len(privateTasks) > 0:
        # privateResults = await asyncio.gather(*privateTasks)#, return_exceptions=True
        # privateResults = [asyncio.ensure_future(task) for task in privateTasks]
        # done, pending = await asyncio.wait(privateResults, timeout=timeout)   
        done, pending = await asyncio.wait(privateTasks, timeout=timeout)   
        privateResults = [task.result() for task in done]
        tmp = [task.cancel() for task in pending]
    else:
        privateResults = []

    #存储数据结果
    ai_df = {}
    di_df = {}
    general_df = {}
    private_df = {}
    for key, value in algorithms_configs.items():
        aiResultList = []
        for result in aiResults:
            if result.empty == False:
                aiResultList.append(result.loc[result['algorithm']==key])
            else:
                aiResultList.append(pd.DataFrame())
        if len(aiResults) > 0:
            ai_df[key] = pd.concat(aiResultList)
            ai_df[key] = ai_df[key][~ai_df[key].index.duplicated()]
        else:
            ai_df[key] = pd.DataFrame()
        #重命名
        name = importlib.import_module('.' + key, package='algorithms')
        if len(name.ai_rename) != 0:
            for pointkey, evalue in name.ai_rename.items():
                if pointkey in ai_df[key].columns.tolist():
                    ai_df[key].rename(columns={pointkey:evalue}, inplace=True)
                    if pointkey in name.ai_points:
                        index_key = name.ai_points.index(pointkey)
                        name.ai_points[index_key] = evalue
        elif 'WGEN.GenSpdInstant' in ai_df[key].columns.tolist():
            ai_df[key].rename(columns={'WGEN.GenSpdInstant':'WGEN.GenSpd'}, inplace=True)
        diResultList = []
        for result in diResults:
            if result.empty == False:
                diResultList.append(result.loc[result['algorithm']==key])
            else:
                diResultList.append(pd.DataFrame())
        if len(diResults) > 0:
            di_df[key] = pd.concat(diResultList)
            di_df[key] = di_df[key][~di_df[key].index.duplicated()]#时间重复
            if (endTime - startTime) != (di_endTime - di_startTime):
                resample_interval = algorithms_configs[key]["resampleTime"]
                resample_interval = time_util.replace_to_resample(
                resample_interval)
                if startTime < di_df[key].index.min() or startTime > di_df[key].index.max():
                    di_df[key].loc[startTime] = np.nan
                if endTime < di_df[key].index.min() or endTime > di_df[key].index.max():
                    di_df[key].loc[endTime] = np.nan
                #实际取得的测点和自定义的可能不一致会报错
                # common_columns = DfTemp.columns.intersection(points).tolist()
                di_df[key] = di_df[key].resample(resample_interval, closed='left').ffill()
                di_df[key] = di_df[key].ffill()
                di_df[key] = di_df[key].bfill()
                di_df[key] = di_df[key][(di_df[key].index >= startTime) & (di_df[key].index <= endTime)]
        else:
            di_df[key] = pd.DataFrame()
        generalResultList = []
        for result in generalResults:
            if result.empty == False:
                generalResultList.append(result.loc[result['algorithm']==key])
            else:
                generalResultList.append(pd.DataFrame())
        if len(generalResults) > 0:
            general_df[key] = pd.concat(generalResultList)
            general_df[key] = general_df[key][~general_df[key].index.duplicated()]
        else:
            general_df[key] = pd.DataFrame()
        privateResultList = []
        for result in privateResults:
            if result.empty == False:
                privateResultList.append(result.loc[result['algorithm']==key])
            else:
                privateResultList.append(pd.DataFrame())
        if len(privateResults) > 0:
            private_df[key] = custom_merge(privateResultList)
            private_df[key] = private_df[key][~private_df[key].index.duplicated()]
        else:
            private_df[key] = pd.DataFrame()
        # #合并数据
        # fn_df = pd.DataFrame()
        # if ai_df[key].empty == False:
        
    # df = pd.concat(results)


    return ai_df, di_df, general_df, private_df


async def getDataForMultiAlgorithms(algorithms_configs): #assetIds：风机id ,mainLog, algorithmLogs, 

    df_ai, df_di, df_general, df_private = await TimeDeviceSlice(algorithms_configs)

    final_df = {}
    countsAlg = 0
    for key, value in algorithms_configs.items():
        # if algorithms_configs[key]['PrepareTurbines'] == False:
        #     continue
        assetIds = value['param_assetIds']
        privateIds = value['param_private_assetIds']
        countsAlg += 1
        # mainLog.info(key+":"+str(countsAlg)+'/'+str(len(algorithms_configs)))
        # algorithmLogs[key].info(f'获取{assetIds}风机本算法需要的数据:')
        # algorithmLogs[key].info(key+":"+str(countsAlg)+'/'+str(len(algorithms_configs)))
        final_df[key] = pd.DataFrame()
        #获取ai数据
        if df_ai[key].empty == False:
            for index, assetId in enumerate(assetIds):
                if final_df[key].empty == False:
                    df_current_assetId = final_df[key][final_df[key]['assetId'] == assetId].copy()
                    #final_df中删除筛选到的行
                    final_df[key] = final_df[key].drop(df_current_assetId.index)
                else:
                    df_current_assetId = pd.DataFrame()
                df_add_assetId = df_ai[key][df_ai[key]['assetId'] == assetId].copy()
                #剔除重名字段
                common_columns = df_current_assetId.columns.intersection(df_add_assetId.columns)
                for tag in list(common_columns):
                    del df_add_assetId[tag]
                df_current_assetId = df_current_assetId.join(df_add_assetId, how='outer')
                df_current_assetId = df_current_assetId.ffill()#用前面行/列的值填充空值
                df_current_assetId = df_current_assetId.bfill()#用后面行/列的值填充空值
                # allow_points = list(set(df_current_assetId.columns) & set(algorithms_configs[key]["aiPoints"]))
                # df_current_assetId[allow_points] = df_current_assetId[allow_points].ffill()#用前面行/列的值填充空值
                # df_current_assetId[allow_points] = df_current_assetId[allow_points].bfill()#用后面行/列的值填充空值
                final_df[key] = pd.concat([final_df[key], df_current_assetId])
            
        #general数据
        if df_general[key].empty == False:
            for index, assetId in enumerate(assetIds):
                if final_df[key].empty == False:
                    df_current_assetId = final_df[key][final_df[key]['assetId'] == assetId].copy()
                    #final_df中删除筛选到的行
                    final_df[key] = final_df[key].drop(df_current_assetId.index)
                else:
                    df_current_assetId = pd.DataFrame()
                df_add_assetId = df_general[key][df_general[key]['assetId'] == assetId].copy()
                #剔除重名字段
                common_columns = df_current_assetId.columns.intersection(df_add_assetId.columns)
                for tag in list(common_columns):
                    del df_add_assetId[tag]
                df_current_assetId = df_current_assetId.join(df_add_assetId, how='outer')
                df_current_assetId = df_current_assetId.ffill()#用前面行/列的值填充空值
                df_current_assetId = df_current_assetId.bfill()#用后面行/列的值填充空值
                # allow_points = list(set(df_current_assetId.columns) & set(algorithms_configs[key]["generalPoints"]))
                # df_current_assetId[allow_points] = df_current_assetId[allow_points].ffill()#用前面行/列的值填充空值
                # df_current_assetId[allow_points] = df_current_assetId[allow_points].bfill()#用后面行/列的值填充空值
                final_df[key] = pd.concat([final_df[key], df_current_assetId])
        
        #di数据
        if df_di[key].empty == False:
            for index, assetId in enumerate(assetIds):
                if final_df[key].empty == False:
                    df_current_assetId = final_df[key][final_df[key]['assetId'] == assetId].copy()
                    #final_df中删除筛选到的行
                    final_df[key] = final_df[key].drop(df_current_assetId.index)
                else:
                    df_current_assetId = pd.DataFrame()
                df_add_assetId = df_di[key][df_di[key]['assetId'] == assetId].copy()
                #剔除重名字段
                common_columns = df_current_assetId.columns.intersection(df_add_assetId.columns)
                for tag in list(common_columns):
                    del df_add_assetId[tag]
                df_current_assetId = df_current_assetId.join(df_add_assetId, how='outer')
                df_current_assetId = df_current_assetId.ffill()#用前面行/列的值填充空值
                df_current_assetId = df_current_assetId.bfill()#用后面行/列的值填充空值
                # allow_points = list(set(df_current_assetId.columns) & set(algorithms_configs[key]["diPoints"]))
                # df_current_assetId[allow_points] = df_current_assetId[allow_points].ffill()#用前面行/列的值填充空值
                # df_current_assetId[allow_points] = df_current_assetId[allow_points].bfill()#用后面行/列的值填充空值
                final_df[key] = pd.concat([final_df[key], df_current_assetId])

        # 获取private数据
        if df_private[key].empty == False:
            # 多个模型测点id
            df_models_private = pd.DataFrame()
            multiColumnIndex = [] #记录测点类型id
            transmit_privateIds = list(zip(*privateIds))#[机号1:(测点模型id1,测点模型id2,...),...]->[测点模型id1:(机号1,机号2,...),测点模型id2:(机号1,机号2,...)...]
            for classIndex, assets in enumerate(transmit_privateIds): #遍历测点类型
                #单个模型测点id
                multi_index = pd.MultiIndex.from_tuples([("privateAssetId","class"+str(classIndex))])
                df_private[key].rename(columns={"assetId":multi_index[0]}, inplace=True)
                #删除相同列名
                common_columns_df_private = df_models_private.columns.intersection(df_private[key].columns)
                for tag in list(common_columns_df_private):
                    del df_private[tag]
                if len(list(df_private[key].columns)) > 1:
                    multiColumnIndex.append(('privateAssetId', "class"+str(classIndex)))
                    df_models_private = pd.concat([df_models_private, df_private[key]], axis=1)

            #遍历所有风机id
            for index, assetId in enumerate(assetIds):
                if final_df[key].empty == False:
                    df_current_assetId = final_df[key][final_df[key]['assetId'] == assetId].copy()
                    #final_df中删除筛选到的行
                    final_df[key] = final_df[key].drop(df_current_assetId.index)
                else:
                    df_current_assetId = pd.DataFrame()
                # print(df_models_private.columns)
                # print(multiColumnIndex)
                #此方法提取出的值为NaN
                # df_add_assetId = df_models_private[df_models_private[multiColumnIndex].isin(privateIds[index])].copy()
                #处理本风机的多个类型测点id
                if df_models_private.empty == False:
                    condition = None
                    modelIds = list(set(privateIds[index]))
                    #提取同一风机的所有类型的测点id
                    for modelId in df_models_private[multiColumnIndex].columns.tolist():
                        if type(condition) == type(None):
                            condition = df_models_private[modelId].isin(modelIds) 
                        else:
                            condition = condition & df_models_private[modelId].isin(modelIds)
                    df_add_assetId = df_models_private[condition]
                    #剔除重名字段
                    common_columns = df_current_assetId.columns.intersection(df_add_assetId.columns)
                    for tag in list(common_columns):
                        del df_add_assetId[tag]
                    df_current_assetId = df_current_assetId.join(df_add_assetId, how='outer')
                    df_current_assetId = df_current_assetId.ffill()#用前面行/列的值填充空值
                    df_current_assetId = df_current_assetId.bfill()#用前面行/列的值填充空值
                    # allow_points = list(set(df_current_assetId.columns) & set(algorithms_configs[key]["privatePoints"]))
                    # df_current_assetId[allow_points] = df_current_assetId[allow_points].ffill()#用前面行/列的值填充空值
                    # df_current_assetId[allow_points] = df_current_assetId[allow_points].bfill()#用前面行/列的值填充空值
                final_df[key] = pd.concat([final_df[key], df_current_assetId])

    #算法名：数据
    return final_df
    


async def getDataCommon(startTime, endTime, assetIds, ai_points, di_points, resample_interval, algorithms_configs):
    # 按时间和设备分片
    date_range = []
    if endTime - startTime > timedelta(hours=12):
        date_range = pd.date_range(startTime, endTime, freq="12H").strftime(
            '%Y-%m-%d %H:%M:%S').to_list()
    else:
        date_range = [startTime.strftime('%Y-%m-%d %H:%M:%S'), endTime.strftime('%Y-%m-%d %H:%M:%S')]
    time_param = [(date_range[i], date_range[i + 1])
                  for i in range(len(date_range) - 1)]
    # 加上设备（笛卡尔积）
    time_asset_param = product(time_param, assetIds)
    final_time_asset_param = [(item[0][0], item[0][1], item[1])
                              for item in time_asset_param]
    
    tasks = [getAiData(time_tuple[0], time_tuple[1], time_tuple[2], ai_points, resample_interval, algorithms_configs) for time_tuple in final_time_asset_param]
    results = await asyncio.gather(*tasks)
    df_ai = pd.concat(results)
    
    
    
    if df_ai.shape[0] > 0 and len(di_points) > 0:
        final_df = pd.DataFrame()
        for assetId in assetIds:
            df_current_assetId = df_ai[df_ai['assetId'] == assetId].copy()
            # getDiDataWithTimeFunc = partial(getDiData, assetId=assetId, points=','.join(di_points))
            # df_di = getDiDataWithTimeFunc(startTime=startTime.strftime('%Y-%m-%d %H:%M:%S'), endTime=endTime.strftime('%Y-%m-%d %H:%M:%S'))
            df_di = await getDiData(startTime.strftime('%Y-%m-%d %H:%M:%S'), endTime.strftime('%Y-%m-%d %H:%M:%S'), ','.join(di_points), assetId)
            df_di.set_index('localtime', inplace=True)
            df_di.index = pd.to_datetime(df_di.index)
            df_di.drop('assetId', axis=1, inplace=True)
            df_di.drop('timestamp', axis=1, inplace=True)
            df_current_assetId = df_current_assetId.join(df_di, how='outer')
            allow_points = list(set(df_current_assetId.columns) & set(di_points))
            df_current_assetId[allow_points] = df_current_assetId[allow_points].fillna(method='ffill')
            final_df = pd.concat([final_df, df_current_assetId])
        final_df.dropna(inplace=True)
        return final_df
    else:
        return df_ai


async def getData(startTime, endTime, assetIds, algorithm, algorithms_configs):
    return await getDataCommon(startTime, endTime, assetIds, algorithm.ai_points, algorithm.di_points, algorithm.resample_interval, algorithms_configs)

def thresholdfun_pwrat_out(raw_df,neighbors_num,clear):
    '''
    根据数学统计剔数-功率
    '''
    temp_all = raw_df[raw_df['clear'] != clear ]
    temp_clear = raw_df[raw_df['clear'] == clear ]
    X_train = pd.DataFrame()
    X_train['wspd'] = temp_clear['WNAC.WindSpeed']
    X_train['pwrat'] = temp_clear['WGEN.GenActivePW']    
    clf = LocalOutlierFactor(n_neighbors=neighbors_num,p=1,n_jobs=-1)
    #clf = IsolationForest(n_estimators=50,contamination=0.25,random_state=1)
    y_pred = clf.fit_predict(X_train)
    temp_clear['y_pred'] = y_pred
    temp_clear.loc[temp_clear['y_pred']==1,'clear'] = clear-1
    temp_all = pd.concat([temp_all, temp_clear])
    return temp_all

def thresholdfun_pwrat(df_ai, threshold,clear):
    '''
    根据数学统计剔数-功率
    '''
        # temp_all = pd.DataFrame()
    # wind_bin = np.arange(2.0,np.ceil(np.nanmax(df_ai['WNAC.WindSpeed'])),0.5)
    # for m in range(len(wind_bin)):
    #     temp = df_ai[(df_ai['WNAC.WindSpeed']>=wind_bin[m]-0.25) & (df_ai['WNAC.WindSpeed']<wind_bin[m]+0.25)]
    #     pwrat_mean = np.mean(temp['WGEN.GenActivePW'])
    #     pwrat_std = np.std(temp['WGEN.GenActivePW'])
    #     temp = temp[(np.abs(temp['WGEN.GenActivePW']-pwrat_mean)/pwrat_std < threshold)]
    #     temp_all = pd.concat([temp_all, temp])
    # return temp_all
    temp_all = df_ai[df_ai['clear'] != clear ]    
    wind_bin = np.arange(2.0,np.ceil(np.nanmax(df_ai['WNAC.WindSpeed'])),0.5)
    for m in range(len(wind_bin)):
        temp = df_ai[(df_ai['WNAC.WindSpeed']>=wind_bin[m]-0.25) & (df_ai['WNAC.WindSpeed']<wind_bin[m]+0.25)&(df_ai['clear']==clear)]
        pwrat_mean = np.nanmean(temp['WGEN.GenActivePW'])
        pwrat_std = np.nanstd(temp['WGEN.GenActivePW'])
        temp.loc[((temp['WGEN.GenActivePW']-pwrat_mean)/pwrat_std < threshold) & ((temp['WGEN.GenActivePW']-pwrat_mean)/pwrat_std > -threshold),'clear'] = clear-1
        temp_all = pd.concat([temp_all, temp])
    return temp_all


def thresholdfun_pitch(df_ai, threshold,clear):
    '''
    根据数学统计剔数-桨距角
    '''
    # temp_all = pd.DataFrame()
    # wind_bin = np.arange(2.0,np.ceil(np.nanmax(df_ai['WNAC.WindSpeed'])),0.5)
    # for m in range(len(wind_bin)):
    #     temp = df_ai[(df_ai['WNAC.WindSpeed']>=wind_bin[m]-0.25) & (df_ai['WNAC.WindSpeed']<wind_bin[m]+0.25)]
    #     pitch_mean = np.mean(temp['WROT.Blade1Position'])
    #     pitch_std = np.std(temp['WROT.Blade1Position'])
    #     temp = temp[(np.abs(temp['WROT.Blade1Position']-pitch_mean)/pitch_std < threshold)]
    #     temp_all = pd.concat([temp_all, temp])
    # return temp_all
    temp_all = df_ai[df_ai['clear'] != clear ]    
    wind_bin = np.arange(2.0,np.ceil(np.nanmax(df_ai['WNAC.WindSpeed'])),0.5)
    for m in range(len(wind_bin)):
        temp = df_ai[(df_ai['WNAC.WindSpeed']>=wind_bin[m]-0.25) & (df_ai['WNAC.WindSpeed']<wind_bin[m]+0.25)&(df_ai['clear']==clear)]
        pitch_mean = np.mean(temp['WROT.Blade1Position'])
        pitch_std = np.std(temp['WROT.Blade1Position'])
        temp.loc[((temp['WROT.Blade1Position']-pitch_mean)/pitch_std < threshold) & ((temp['WROT.Blade1Position']-pitch_mean)/pitch_std > -threshold),'clear'] = clear-1
        temp_all = pd.concat([temp_all, temp])
    return temp_all


def thresholdfun_rotspd(df_ai, neighbors_num,clear):
    '''
    根据算法模型剔数 功率-桨距角 剔除数据
    '''
# df_ai.dropna(subset=['WGEN.GenActivePW','WROT.Blade1Position'], inplace=True)
    # X_train = df_ai[[PW','WROT.Blade1Position']]
    # clf = LocalOutlierFactor(n_neighbors=neighbors_num,p=1,n_jobs=-1)
    # y_pred = clf.fit_predict(X_train)
    # df_ai['y_pred'] = y_pred
    # final_df = df_ai[df_ai['y_pred']==1]
    # return final_df
    temp_all = df_ai[(df_ai['clear'] != clear)]
    temp_clear = df_ai[(df_ai['clear'] == clear)]
    #temp_clear = temp_clear.dropna(axis=0,subset=[('pwrat','nanmean')],inplace=True)
    #temp_clear = temp_clear.dropna(axis=0,subset=[('pitch1','nanmean')],inplace=True)
    X_train = pd.DataFrame()
    X_train['pwrat'] = temp_clear['WGEN.GenActivePW']
    X_train['pitch'] = temp_clear['WROT.Blade1Position']    
    clf = LocalOutlierFactor(n_neighbors=neighbors_num,p=1,n_jobs=-1)
    #clf = IsolationForest(n_estimators=50,contamination=0.25,random_state=1)
    y_pred = clf.fit_predict(X_train)
    temp_clear['y_pred'] = y_pred
    temp_clear.loc[temp_clear['y_pred']==1,'clear'] = clear-1
    temp_all = pd.concat([temp_all, temp_clear])
    return temp_all


def wash_data_mechanization_new(df_ai, ratedPower):
    '''
    机理清数
    '''
    # turbine_name = df_ai.iloc[0]["assetId"]
    # fig = plt.figure(figsize=(10,8),dpi=100)  
    # plt.title(str(turbine_name)) 
    # with plt.style.context('ggplot'):  
    #     # plt.scatter(df_ai['WNAC.WindSpeed'],df_ai['WGEN.GenActivePW'],c=df_ai['WTUR.TurbineSts'],cmap='jet',s=15)
    #     plt.scatter(df_ai['WGEN.GenSpd'],df_ai['WGEN.GenActivePW'],s=15)
    #     plt.grid()
    #     #plt.ylim(-3,25)
    #     plt.xlabel('风速(wspd)',fontsize=14)
    #     plt.ylabel('功率(kW)',fontsize=14)
    #     plt.colorbar()
    # fig.savefig(str(turbine_name) + '_torqueerr_风速_功率.png',dpi=100)

    # 根据状态码分组，正常组的数据最多，计算众数
    aiGroupedStates = df_ai.groupby('WTUR.TurbineSts').count()['WNAC.WindSpeed']
    normalCode = aiGroupedStates.idxmax()

    # 最小桨距角
    aiGroupedPitch = df_ai.groupby('WROT.Blade1Position').count()['WNAC.WindSpeed']
    minPitch = aiGroupedPitch.idxmax()

    # 转速（并网、额定）
    #生成bin,bin size 10
    bins = np.arange(df_ai['WGEN.GenSpd'].min(), df_ai['WGEN.GenSpd'].max(),10)
    #分组
    grouped = pd.cut(df_ai['WGEN.GenSpd'], bins)
    df_ai['rateSpeedGroup'] = grouped
    aiGroupedRate = df_ai.groupby('rateSpeedGroup').count()['WGEN.GenActivePW']
    connectRateSpeed = aiGroupedRate.nlargest(5).index[1].left#aiGroupedPitch.iloc[:len(aiGroupedPitch)//4].idxmax()
    RateSpeed = aiGroupedRate.nlargest(5).index[0].left#aiGroupedPitch.iloc[len(aiGroupedPitch)*3//4:].idxmax()


    df_ai = df_ai.dropna(axis=0,thresh=len(df_ai.columns)*0.8)
    df_ai['clear'] = 10
    df_ai['pitchlim'] = (df_ai['WGEN.GenActivePW'] - 0.8*ratedPower)*(5.0-2.5-minPitch) / (ratedPower*(0.95-0.8)) + (minPitch+2.5)

    #风机发电状态
    df_ai.loc[(df_ai['WTUR.TurbineSts']==normalCode),'clear'] = 9

    #风机转速、功率正常阈值内
    df_ai.loc[(df_ai['WGEN.GenSpd']>connectRateSpeed*0.9)&(df_ai['WGEN.GenSpd']<RateSpeed*1.1)&(df_ai['WGEN.GenActivePW']>0)&(df_ai['WGEN.GenActivePW']<ratedPower*1.1)&(df_ai['clear']==9),'clear'] = 8

    #非限功率状态
    df_ai.loc[(df_ai['WTUR.TurbineAIStatus'].isin([90002]))|(df_ai['clear']==8),'clear'] = 7

    Pitch_Min_temp = np.nanmean(df_ai[(df_ai['clear']==7)&(df_ai['WGEN.GenActivePW']>100)&(df_ai['WGEN.GenActivePW']<ratedPower*0.6)]['WROT.Blade1Position'])
    if np.abs(minPitch - Pitch_Min_temp)>1.0:
        minPitch = Pitch_Min_temp
    
    #无超过正常范围的变桨
    df_ai.loc[((df_ai['WGEN.GenActivePW']>=ratedPower*0.95)|
              ((df_ai['WGEN.GenActivePW']<ratedPower*0.8)&(df_ai['WROT.Blade1Position']<minPitch+2.5))|
                  ((df_ai['WGEN.GenActivePW']<ratedPower*0.95)&(df_ai['WGEN.GenActivePW']>ratedPower*0.8)&(df_ai['WROT.Blade1Position']<df_ai['pitchlim'])))&(df_ai['clear']==7),'clear'] = 6
    
    return df_ai


def wash_data_mechanization(df_ai, ratedPower):
    '''
    机理清数
    '''

    # 根据状态码分组，正常组的数据最多，计算众数
    aiGroupedStates = df_ai.groupby('WTUR.TurbineSts').count()['WNAC.WindSpeed']
    normalCode = aiGroupedStates.idxmax()
    # aiGroupedAIStates = df_ai.groupby('WTUR.TurbineAIStatus').count()['WNAC.WindSpeed']
    # limitCode = aiGroupedAIStates.idxmax()

    # 根据风机状态码清洗数据
    df_ai = df_ai[(~df_ai['WTUR.TurbineAIStatus'].isin([90002, 90001])) & (df_ai['WTUR.TurbineSts'] == normalCode)]

    # 根据机理清洗数据
    df_ai['pitchlim'] = (df_ai['WGEN.GenActivePW']-0.72 *
                         ratedPower) * (5.0-2.5) / (ratedPower*(0.98-0.72)) + 2.5
    
    df_ai = df_ai[(df_ai['WGEN.GenSpd'] > config.Rotspd_Connect * 0.9) &
                  (df_ai['WGEN.GenActivePW'] > 0) & 
                  (df_ai['WGEN.GenActivePW'] < ratedPower*1.1)]
    
    # 清洗开始变桨之前的数据
    df_ai = df_ai[(df_ai['WGEN.GenActivePW'] >= ratedPower*0.72) | 
                  ((df_ai['WGEN.GenActivePW'] < ratedPower*0.72) & 
                   (df_ai['WROT.Blade1Position'] < config.Pitch_Min+2.5))]
    
    # 清洗提前变桨阶段的数据
    df_ai = df_ai[(df_ai['WGEN.GenActivePW'] >= ratedPower*0.98) |
                  (df_ai['WGEN.GenActivePW'] <= ratedPower*0.72) | 
                  ((df_ai['WGEN.GenActivePW'] < ratedPower*0.98) & 
                   (df_ai['WGEN.GenActivePW'] > ratedPower*0.72) & 
                   (df_ai['WROT.Blade1Position'] < df_ai['pitchlim']))]
    return df_ai


def wash_data_for_train(df_ai, ratedPower):
    '''
    数据清洗（拟合剔数）
    Parameters
    ----------
    df_ai : TYPE
        DESCRIPTION.
    ratedPower : TYPE
        额定功率.
    Returns
    -------
    None.

    '''
    df_ai = wash_data_mechanization_new(df_ai, ratedPower)
    # 数学统计清洗数据
    # 数学统计清洗数据
    threshold = 3
    neighbors_num = 20
    df_ai = thresholdfun_rotspd(df_ai, neighbors_num,6)
    df_ai = thresholdfun_pitch(df_ai, threshold, 5)    
    df_ai = thresholdfun_pwrat(df_ai, threshold, 4)
    df_ai = thresholdfun_pwrat_out(df_ai,neighbors_num,3)

    # df_ai = df_ai[df_ai['clear'] == 2]#1为干净值

    return df_ai






if __name__ == '__main__':
    # assetIds=['BYA2LVsH', 'xmYFZRiI', 'JGT06pg7', 'TzpeZh7e', '57Fed4kz', 'Unbt3ciP', 'fBzGDVYJ', 'nWsNJAdv', 'cSK9gHFh', '3DLQLrSX', 'vRirwair', '2BJhqqzr', 'CQlCBfh2', 'KGvXjY63', 'OUh7PkSh', 'ZuLQjI3u', 'hgpFittR', 'bXOMyiBc', 'hH5RrDsb', '1uW8O7am', 'ZeKO3BAs', 'i8Zkc5Cq', 'kuO9Oo9U', 'jAL17JML', 'anCgqvv5', 'IZhfhGS3', 'FcP4S2Gg', 'wl10lKQB', 'DgQDh9ay', '187RVbfL', 'x8RkQrZK', 'dUcQbdPf', 'D1uY3w78', 'eU70J6Qt', 'JhiFaiCG', 'UESzBt6l', 'ORFXFmGh', 'Ma4fi1Wa', 'YpyUGZbq', 'BsSUf9so', '8xJVOwOI', 'ADFXvze4', 'zWyJfsaZ', 'gSsqGg1Q', 'iTrYcuok', 'pXVKCt43', 'YMLyUQXH', 'TFKtTIox', 'rZ9tFVkp', '7FBhRoZz', 'OXo5VwP6', 'e29Rp0Vs', 'kXuVsrtX', 'bFc3bAwC', 'BXuLDLb7', 'eDuo2Fcm', 'IvoSmzdq', 'H4YKUKqN', 'sdbFengw', 'YYJpio3S', '50TyNWJ1', 'nElJZtqH', 'PXvtd6yq', 'rfWItMF7', 'AJu9oT46', 'oqPsh0pL', '08VyWN67', '9ITke9Lf', 'usq5e0LN', '7aeH3jeI', 'jZYgirEb', 'LekDIfJC', 'eIPfQedJ', 'heZAM65W', 'ghwm5IeY', 'UeS7Wirh', 'GeGBYtD4', 'G7RgSex2', 'ADueJxBq', 'oqXBQ020']
    # getData('2023-07-10 00:00:00', '2023-07-11 00:00:00', ['WNAC.TemNacelleCab'], assetIds)

    # , 'WROT.Blade1Position', 'WROT.Blade2Position', 'WROT.Blade3Position', 'WROT.CurBlade1Motor', 'WROT.CurBlade2Motor', 'WROT.CurBlade3Motor'
    getAiData('2023-07-23 12:00:00', '2023-07-24 00:00:00', '0ZfTpctM', ['WNAC.WindSpeed', 'WGEN.GenSpd', 'WGEN.GenActivePW', 'WROT.Blade1Position'], '10m')

    # getDiData('2023-06-01 00:00:00', '2023-08-11 14:10:00', 'WTUR.TurbineSts', '08VyWN67')

    '''
    import matplotlib.pyplot as plt
    plt.figure()
    plt.scatter(df_ai['WNAC.WindSpeed'], df_ai['WGEN.GenActivePW'], s=1)
    plt.xlabel('风速(m/s)',fontsize=14)
    plt.ylabel('功率(kW)',fontsize=14)
    plt.show()
    
    plt.figure()
    plt.scatter(df_ai['WGEN.GenSpd'],df_ai['WGEN.GenActivePW'], s=1)
    plt.show()
    
    plt.figure()
    plt.scatter(df_ai['WGEN.GenActivePW'],df_ai['WROT.Blade1Position'], s=1)
    plt.show()
    '''
