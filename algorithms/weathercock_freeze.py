from pandas import DataFrame
from alarms import alarm
from utils.display_util import DisplayResultXY, DisplayFigures
import pandas as pd
import utils.time_util as time_util
import asyncio
from data.get_data import wash_data_for_train
import numpy as np
from datetime import datetime as datetime
from configs.config import algConfig

name = algConfig['weathercock_freeze']['name']#'风向标冻结'
# 把所需测点定义到每个算法里
ai_points = algConfig['weathercock_freeze']['ai_points']
ai_rename = algConfig['weathercock_freeze']['ai_rename']
di_points = algConfig['weathercock_freeze']['di_points']
general_points = algConfig['weathercock_freeze']['general_points']
private_points = algConfig['weathercock_freeze']['private_points']
time_duration = algConfig['weathercock_freeze']['time_duration']
resample_interval = algConfig['weathercock_freeze']['resample_interval']
error_data_time_duration = algConfig['weathercock_freeze']['error_data_time_duration']
need_all_turbines = algConfig['weathercock_freeze']['need_all_turbines']
store_file = algConfig['weathercock_freeze']['store_file']

def wash_data(pn_data: DataFrame, ratedPower):    
    temp_data = pn_data[ai_points + di_points+general_points]
    '''
    剔除限功率数据 FIXME ？？？
    '''
    temp_data = wash_data_for_train(temp_data, ratedPower)
    if temp_data[temp_data['clear'] == 2].shape[0] > 0:
        return temp_data[temp_data['clear'] == 2], ''
    else:
        return pd.DataFrame(), '没有干净数据'



def predict_result(pn_data: DataFrame):
    return pn_data[['WNAC.WindVaneDirection']]


async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    meanTemp = np.mean(pn_data['WNAC.TemOut'])
    

    
    # 阈值判断
    thrvalue = 5
    temp = predict_result(pn_data)
    temp['result'] = (temp - temp.shift(1) > thrvalue) & (meanTemp<0) #故障设为True
    temp['shift'] = temp.shift(1)['WNAC.WindVaneDirection']
    temp['shift'] = temp['shift'].ffill()
    temp['shift'] = temp['shift'].bfill()
    temp.sort_index(inplace=True)
    #数据展示
    x = [str(tick) for tick in list(temp.index)]
    x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
    x = [int(tick.timestamp()*1000) for tick in x]
    y1 = [str(round(num,4)) for num in list(temp['WNAC.WindVaneDirection'])]
    y2 = [str(round(num,4)) for num in list(temp['shift'])]
    y3 = [str(round(num,4)) for num in list(pn_data["WNAC.TemOut"])]
    y4 = [str(round(num,4)) for num in [meanTemp]*pn_data.shape[0]]  #
    
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
    data3 = pd.DataFrame({'x': x, 'y': y3}).to_dict('records')
    data4 = pd.DataFrame({'x': x, 'y': y4}).to_dict('records')
    interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
    interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
    Figs = []
    curves1 = []
    curves2 = []
    curves1.append(DisplayResultXY('0', '原始数据', '#FFFF00', 'Solid', data1))#{'type':'0', 'name': '原始数据', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data1}
    curves1.append(DisplayResultXY('0', '错时数据', '#00FF00', 'Solid', data2))#{'type':'0', 'name': '错时数据', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data2}
    # result = DisplayResultXY(str(temp.index.min()), str(temp.index.max()), str(interval_value), '角度', curves)
    result1 = DisplayFigures(xUnit=interval_unit, yUnit="角度[°]", time=1, multiDimensionDataxy=curves1)
    Figs.append(result1)

    curves2.append(DisplayResultXY('0', '实时温度', '#FFFF00', 'Solid', data3))#{'type':'0', 'name': '原始数据', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data1}
    curves2.append(DisplayResultXY('0', '平均温度', '#00FF00', 'Solid', data4))#{'type':'0', 'name': '错时数据', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data2}
    # result = DisplayResultXY(str(temp.index.min()), str(temp.index.max()), str(interval_value), '角度', curves)
    result2 = DisplayFigures(xUnit=interval_unit, yUnit="温度[℃]", time=1, multiDimensionDataxy=curves2)
    Figs.append(result2)

    

    statementException = f'风向标变化幅度偏大，大于阈值{thrvalue}, 平均温度低于0℃'
    statementNormal = f'风向标变化幅度偏小，小于阈值{thrvalue}或者平均温度高于0℃'
    # 生成告警
    data, statement, alarming =  alarm.generateAlarm(name, 'weathercock_freeze', 'WNAC.TemOut', temp, error_data_time_duration, resample_interval, assetId, thrvalue, statementException, statementNormal, idMaps)
    return data, statement, Figs, 0,1 # alarming, 0
    # # 生成告警
    # return alarm.generateAlarm(name, temp, error_data_time_duration, resample_interval, assetId)


def judge(pn_data: DataFrame):
    """
    风向标冻结
    风向1min数据 持续5分钟 变化小于1-2° 环境温度正负10°范围内 
    风速仪：
    实测功率值 高于 理论功率曲线 10%
    
    
    
    
    ？？如何判断是否为非限功率状态？都为None
    ？？逻辑是否需要调整
    ？？过滤非限功率状态数据
    :param pn_data: dataframe
    :return:
    """
    
    result_value = []

    for index, row in pn_data.iterrows():
        pw = float(row.get("WGEN.GenActivePW"))
        direction = abs(float(row.get("WNAC.WindDirection")))
        speed = float(row.get("WNAC.WindSpeed"))

        if speed >= 12 and direction <= 20 and pw <= 1400:
            result_value.append(True)
        else:
            result_value.append(False)

    pn_data['result'] = result_value
    return alarm.generateAlarm(pn_data, error_data_time_duration)