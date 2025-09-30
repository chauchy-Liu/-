from pandas import DataFrame
from alarms import alarm
import numpy as np
from utils.display_util import DisplayResultXY, DisplayFigures
import pandas as pd
import utils.time_util as time_util
import asyncio
from datetime import datetime as datetime
from configs.config import algConfig

name = algConfig['oar_engine_temperature']['name']#'变桨电机温度异常'
# 把所需测点定义到每个算法里
ai_points = algConfig['oar_engine_temperature']['ai_points']
ai_rename = algConfig['oar_engine_temperature']['ai_rename']
di_points = algConfig['oar_engine_temperature']['di_points']
general_points = algConfig['oar_engine_temperature']['general_points']
private_points = algConfig['oar_engine_temperature']['private_points']
time_duration = algConfig['oar_engine_temperature']['time_duration']
resample_interval = algConfig['oar_engine_temperature']['resample_interval']
error_data_time_duration = algConfig['oar_engine_temperature']['error_data_time_duration']
need_all_turbines = algConfig['oar_engine_temperature']['need_all_turbines']
store_file = algConfig['oar_engine_temperature']['store_file']

def wash_data(pn_data: DataFrame, ratedPower):
    temp_data = pn_data[ai_points + di_points+general_points]
    return temp_data, ''


def predict_result(pn_data: DataFrame):
    return pn_data[['WROT.TemB1Mot','WROT.TemB2Mot','WROT.TemB3Mot']]


async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    # 阈值判断
    threValue = 10
    pn_data['result'] = (np.abs(pn_data['WROT.TemB1Mot'] - pn_data['WROT.TemB2Mot']) >= threValue) | (np.abs(pn_data['WROT.TemB1Mot'] - pn_data['WROT.TemB3Mot']) >= threValue) | (np.abs(pn_data['WROT.TemB2Mot'] - pn_data['WROT.TemB3Mot']) >= threValue)

    #数据展示
    x = [str(tick) for tick in list(pn_data.index)]
    x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
    x = [int(tick.timestamp()*1000) for tick in x]
    y1 = [str(round(num,4)) for num in list(pn_data['WROT.TemB1Mot'])]
    y2 = [str(round(num,4)) for num in list(pn_data['WROT.TemB2Mot'])]
    y3 = [str(round(num,4)) for num in list(pn_data['WROT.TemB3Mot'])]
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
    data3 = pd.DataFrame({'x': x, 'y': y3}).to_dict('records')
    interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
    interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
    Figs = []
    curves1 = []
    curves1.append(DisplayResultXY('0', '电机温度1', '#FFFF00', 'Solid', data1))#{'type':'0', 'name': '电机温度1', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'data': data1}
    curves1.append(DisplayResultXY('0', '电机温度2', '#FF0000', 'Solid', data2))#{'type':'0', 'name': '电机温度2', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'data': data2}
    curves1.append(DisplayResultXY('0', '电机温度3', '#00FF00', 'Solid', data3))#{'type':'0', 'name': '电机温度3', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'data': data3}
    
    # result = DisplayResultXY(str(pn_data.index.min()), str(pn_data.index.max()), str(interval_value), '温度', curves)
    result1 = DisplayFigures(xUnit=interval_unit, yUnit="温度[℃]", time=1, multiDimensionDataxy=curves1)
    Figs.append(result1)

    statementException = f'各变桨电机之间温度差异偏大，大于阈值{threValue}'
    statementNormal = f'各变桨电机之间温度差异不大，小于阈值{threValue}'
    # 生成告警
    data, statement, alarming =  alarm.generateAlarm(name,'oar_engine_temperature', 'WROT.TemB1Mot', pn_data, error_data_time_duration, resample_interval, assetId, threValue, statementException, statementNormal, idMaps)
    return data, statement, Figs, 0,1 # alarming, 0
    # # 生成告警
    # return alarm.generateAlarm(name, pn_data, error_data_time_duration, resample_interval, assetId)


def judge(pn_data: DataFrame):
    """
    变桨电机温度异常
    :param pn_data: dataframe
    :return:
    """
    result_value = []

    for index, row in pn_data.iterrows():
        c78 = float(row.get("WROT.TemB1Mot"))
        c79 = float(row.get("WROT.TemB2Mot"))
        c80 = float(row.get("WROT.TemB3Mot"))

        if c78 >= 90 or c79 >= 90 or c80 >= 90 or abs(c78 - c79) >= 15 or abs(c78 - c80) >= 15 or abs(
                c79 - c80) >= 15:
            result_value.append(True)
        else:
            result_value.append(False)

    pn_data['result'] = result_value
    return alarm.generateAlarm(pn_data, error_data_time_duration)
