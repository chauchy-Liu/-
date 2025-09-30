from pandas import DataFrame
import numpy as np
from alarms import alarm
from utils.display_util import DisplayResultXY, DisplayFigures
import pandas as pd
import utils.time_util as time_util
import asyncio
from datetime import datetime as datetime
from configs.config import algConfig

name = algConfig['oar_machine_temperature']['name']#'变桨逆变器温度异常'
# 把所需测点定义到每个算法里
ai_points = algConfig['oar_machine_temperature']['ai_points']
ai_rename = algConfig['oar_machine_temperature']['ai_rename']
di_points = algConfig['oar_machine_temperature']['di_points']
general_points = algConfig['oar_machine_temperature']['general_points']
private_points = algConfig['oar_machine_temperature']['private_points']
time_duration = algConfig['oar_machine_temperature']['time_duration']
resample_interval = algConfig['oar_machine_temperature']['resample_interval']
error_data_time_duration = algConfig['oar_machine_temperature']['error_data_time_duration']
need_all_turbines = algConfig['oar_machine_temperature']['need_all_turbines']
store_file = algConfig['oar_machine_temperature']['store_file']

def wash_data(pn_data: DataFrame, ratedPower):
    temp_data = pn_data[ai_points + di_points+general_points]
    return temp_data, ''


def predict_result(pn_data: DataFrame):
    return pn_data[['WROT.TemBlade1Inver', 'WROT.TemBlade2Inver', 'WROT.TemBlade3Inver']]


async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    # 阈值判断
    threValue = 100
    pn_data['result'] = (np.abs(pn_data['WROT.TemBlade1Inver'] - pn_data['WROT.TemBlade2Inver']) >= threValue) | (np.abs(pn_data['WROT.TemBlade1Inver'] - pn_data['WROT.TemBlade3Inver']) >= threValue) | (np.abs(pn_data['WROT.TemBlade2Inver'] - pn_data['WROT.TemBlade3Inver']) >= threValue)

    #数据展示
    x = [str(tick) for tick in list(pn_data.index)]
    x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
    x = [int(tick.timestamp()*1000) for tick in x]
    y1 = [str(round(num,4)) for num in list(pn_data['WROT.TemBlade1Inver'])]
    y2 = [str(round(num,4)) for num in list(pn_data['WROT.TemBlade2Inver'])]
    y3 = [str(round(num,4)) for num in list(pn_data['WROT.TemBlade3Inver'])]
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
    data3 = pd.DataFrame({'x': x, 'y': y3}).to_dict('records')
    interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
    interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
    Figs = []
    curves1 = []
    curves1.append(DisplayResultXY('0', '逆变器温度1', '#FFFF00', 'Solid', data1))#{'type':'0', 'name': '电机温度1', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'data': data1}
    curves1.append(DisplayResultXY('0', '逆变器温度2', '#FF0000', 'Solid', data2))#{'type':'0', 'name': '电机温度2', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'data': data2}
    curves1.append(DisplayResultXY('0', '逆变器温度3', '#00FF00', 'Solid', data3))#{'type':'0', 'name': '电机温度3', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'data': data3}
    
    # result = DisplayResultXY(str(pn_data.index.min()), str(pn_data.index.max()), str(interval_value), '温度', curves)
    result1 = DisplayFigures(xUnit=interval_unit, yUnit="温度[℃]", time=1, multiDimensionDataxy=curves1)
    Figs.append(result1)

    statementException = f'各变桨逆变器之间温度差异偏大，大于阈值{threValue}'
    statementNormal = f'各变桨逆变器之间温度差异不大，小于阈值{threValue}'
    # 生成告警
    data, statement, alarming =  alarm.generateAlarm(name,'oar_machine_temperature','WROT.TemBlade1Inver', pn_data, error_data_time_duration, resample_interval, assetId, threValue, statementException, statementNormal, idMaps)
    return data, statement, Figs, 0,1 # alarming, 0
    # # 生成告警
    # return alarm.generateAlarm(name, pn_data, error_data_time_duration, resample_interval, assetId)



def judge(pn_data: DataFrame):
    """
    变桨逆变器温度异常
    ？？逆变器==驱动器？？ 缺少测点 变桨控制柜温度
    :param pn_data: dataframe
    :return:
    """
    wind_turbine_codes = pn_data['code']
    print(wind_turbine_codes)
    result_value = []

    for index, row in pn_data.iterrows():
        c246 = float(row.get("C246"))
        c247 = float(row.get("C247"))
        c248 = float(row.get("C248"))
        c92 = float(row.get("C92"))
        c562 = float(row.get("C562"))
        c563 = float(row.get("C563"))

        if c246 >= 50 or c247 >= 50 or c248 >= 50 or abs(c246 - c247) >= 15 or abs(c246 - c248) >= 15 or abs(
                c247 - c248) >= 15 or c248 - c92 >= 25 or c247 - c562 >= 25 or c248 - c563 >= 25:
            result_value.append(True)
        else:
            result_value.append(False)

    pn_data['result'] = result_value
    return pn_data
