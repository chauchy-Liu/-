from pandas import DataFrame
from alarms import alarm
import numpy as np
from utils.display_util import DisplayResultXY, DisplayFigures
import pandas as pd
import utils.time_util as time_util
import asyncio
from datetime import datetime as datetime
from configs.config import algConfig

name = algConfig['hongwai_sanxiang']['name']#'红外测温不平衡'
# 把所需测点定义到每个算法里
ai_points = algConfig['hongwai_sanxiang']['ai_points']
ai_rename = algConfig['hongwai_sanxiang']['ai_rename']
di_points = algConfig['hongwai_sanxiang']['di_points']
general_points = algConfig['hongwai_sanxiang']['general_points']
private_points = algConfig['hongwai_sanxiang']['private_points']
time_duration = algConfig['hongwai_sanxiang']['time_duration']
resample_interval = algConfig['hongwai_sanxiang']['resample_interval']
error_data_time_duration = algConfig['hongwai_sanxiang']['error_data_time_duration']
need_all_turbines = algConfig['hongwai_sanxiang']['need_all_turbines']
store_file = algConfig['hongwai_sanxiang']['store_file']

def wash_data(pn_data: DataFrame, ratedPower):
    private_points_ = []
    for modelKey, pointValue in private_points.items():
        private_points_ += pointValue
    temp_data = pn_data[private_points_]
    # 清空nan数据
    temp_data = temp_data.dropna(how='all', subset=private_points_)
    value_mask = temp_data[['LOW_A_TMP','LOW_B_TMP','LOW_C_TMP']] > 40
    value_rows = value_mask.all(axis=1)
    temp_data = temp_data[value_rows]
    return temp_data, ''


def predict_result(pn_data: DataFrame):
    return pn_data[['LOW_A_TMP','LOW_B_TMP','LOW_C_TMP']]


async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    # 阈值判断
    threValue = 15
    pn_data['result'] = (np.abs(pn_data['LOW_A_TMP'] - pn_data['LOW_B_TMP']) >= threValue) | (np.abs(pn_data['LOW_A_TMP'] - pn_data['LOW_C_TMP']) >= threValue) | (np.abs(pn_data['LOW_B_TMP'] - pn_data['LOW_C_TMP']) >= threValue)

    #数据展示
    x = [str(tick) for tick in list(pn_data.index)]
    x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
    x = [int(tick.timestamp()*1000) for tick in x]
    y1 = [str(round(num,4)) for num in list(pn_data['LOW_A_TMP'])]
    y2 = [str(round(num,4)) for num in list(pn_data['LOW_B_TMP'])]
    y3 = [str(round(num,4)) for num in list(pn_data['LOW_C_TMP'])]
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
    data3 = pd.DataFrame({'x': x, 'y': y3}).to_dict('records')
    interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
    interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
    Figs = []
    curves1 = []
    curves1.append(DisplayResultXY('0', '箱变接线端子温度1', '#FFFF00', 'Solid', data1))#{'type':'0', 'name': '电机温度1', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'data': data1}
    curves1.append(DisplayResultXY('0', '箱变接线端子温度2', '#FF0000', 'Solid', data2))#{'type':'0', 'name': '电机温度2', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'data': data2}
    curves1.append(DisplayResultXY('0', '箱变接线端子温度3', '#00FF00', 'Solid', data3))#{'type':'0', 'name': '电机温度3', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'data': data3}
    
    # result = DisplayResultXY(str(pn_data.index.min()), str(pn_data.index.max()), str(interval_value), '温度', curves)
    result1 = DisplayFigures(xUnit=interval_unit, yUnit="温度[℃]", time=1, multiDimensionDataxy=curves1)
    Figs.append(result1)

    statementException = f'各箱变接线端子之间温度差异偏大，大于阈值{threValue}'
    statementNormal = f'各箱变接线端子之间温度差异不大，小于阈值{threValue}'
    # 生成告警
    data, statement, alarming =  alarm.generateAlarm(name,'oar_engine_temperature', 'LOW_A_TMP', pn_data, error_data_time_duration, resample_interval, assetId, threValue, statementException, statementNormal, idMaps)
    return data, statement, Figs, 0,1 # alarming, 0
    # # 生成告警
    # return alarm.generateAlarm(name, pn_data, error_data_time_duration, resample_interval, assetId)



