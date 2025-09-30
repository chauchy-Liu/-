# -*- coding: utf-8 -*-
"""
变桨电机性能异常 新做
Created on Mon Aug  7 14:50:02 2023

@author: sunyan
"""

from pandas import DataFrame
from alarms import alarm
import numpy as np
from utils.display_util import DisplayResultXY, DisplayFigures
import pandas as pd
import utils.time_util as time_util
import asyncio
from datetime import datetime as datetime
from configs.config import algConfig

name = algConfig['oar_engine_performance']['name']#'变桨电机性能异常'
# 把所需测点定义到每个算法里
ai_points = algConfig['oar_engine_performance']['ai_points']
ai_rename = algConfig['oar_engine_performance']['ai_rename']
di_points = algConfig['oar_engine_performance']['di_points']
general_points = algConfig['oar_engine_performance']['general_points']
private_points = algConfig['oar_engine_performance']['private_points']
time_duration = algConfig['oar_engine_performance']['time_duration']
resample_interval = algConfig['oar_engine_performance']['resample_interval']
error_data_time_duration = algConfig['oar_engine_performance']['error_data_time_duration']
need_all_turbines = algConfig['oar_engine_performance']['need_all_turbines']
store_file = algConfig['oar_engine_performance']['store_file']

def wash_data(pn_data: DataFrame, ratedPower):
    temp_data = pn_data[ai_points + di_points+general_points]
    return temp_data, ''


def predict_result(pn_data: DataFrame):
    return pn_data[['WROT.TemB1Mot', 'WROT.TemB2Mot', 'WROT.TemB3Mot', 'WROT.CurBlade1Motor', 'WROT.CurBlade2Motor', 'WROT.CurBlade3Motor']]


async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    # 阈值判断
    threValue = 10
    pn_data['result'] = ((np.abs(pn_data['WROT.TemB1Mot'] - pn_data['WROT.TemB2Mot']) >= 10) & (np.abs(pn_data['WROT.CurBlade1Motor'] - pn_data['WROT.CurBlade2Motor']) >= 5)) | ((np.abs(pn_data['WROT.TemB1Mot'] - pn_data['WROT.TemB3Mot']) >= 10) & (np.abs(pn_data['WROT.CurBlade1Motor'] - pn_data['WROT.CurBlade3Motor']) >= 5)) | ((np.abs(pn_data['WROT.TemB2Mot'] - pn_data['WROT.TemB3Mot']) >= 10) & (np.abs(pn_data['WROT.CurBlade2Motor'] - pn_data['WROT.CurBlade3Motor']) >= 5))
    #数据展示
    x = [str(tick) for tick in list(pn_data.index)]
    x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
    x = [int(tick.timestamp()*1000) for tick in x]
    y1 = [str(round(num,4)) for num in list(pn_data['WROT.TemB1Mot'])]
    y2 = [str(round(num,4)) for num in list(pn_data['WROT.TemB2Mot'])]
    y3 = [str(round(num,4)) for num in list(pn_data['WROT.TemB3Mot'])]
    y4 = [str(round(num,4)) for num in list(pn_data['WROT.CurBlade1Motor'])]
    y5 = [str(round(num,4)) for num in list(pn_data['WROT.CurBlade2Motor'])]
    y6 = [str(round(num,4)) for num in list(pn_data['WROT.CurBlade3Motor'])]
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
    data3 = pd.DataFrame({'x': x, 'y': y3}).to_dict('records')
    data4 = pd.DataFrame({'x': x, 'y': y4}).to_dict('records')
    data5 = pd.DataFrame({'x': x, 'y': y5}).to_dict('records')
    data6 = pd.DataFrame({'x': x, 'y': y6}).to_dict('records')
    interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
    interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
    Figs = []
    curves1 = []
    curves2 = []
    curves1.append(DisplayResultXY('0', '电机1温度', '#FFFF00', 'Solid', data1))#{'type':'0', 'name': '电机1温度', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'xyData': data1}
    curves1.append(DisplayResultXY('0', '电机2温度', '#00FF00', 'Solid', data2))#{'type':'0', 'name': '电机2温度', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'xyData': data2}
    curves1.append(DisplayResultXY('0', '电机3温度', '#FF0000', 'Solid', data3))#{'type':'0', 'name': '电机3温度', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'xyData': data3}
    curves2.append(DisplayResultXY('0', '电机1电流', '#FFFF00', 'Solid', data4))#{'type':'0', 'name': '电机1电流', "abscissaUnit": interval_unit, "ordinateUnit": "A", 'xyData': data4}
    curves2.append(DisplayResultXY('0', '电机2电流', '#00FF00', 'Solid', data5))#{'type':'0', 'name': '电机2电流', "abscissaUnit": interval_unit, "ordinateUnit": "A", 'xyData': data5}
    curves2.append(DisplayResultXY('0', '电机3电流', '#FF0000', 'Solid', data6))#{'type':'0', 'name': '电机3电流', "abscissaUnit": interval_unit, "ordinateUnit": "A", 'xyData': data6}
    
    # result1 = DisplayResultXY(str(pn_data.index.min()), str(pn_data.index.max()), str(interval_value), '性能', curves) 
    result1 = DisplayFigures(xUnit=interval_unit, yUnit="温度[℃]", time=1, multiDimensionDataxy=curves1)
    Figs.append(result1)
    result2 = DisplayFigures(xUnit=interval_unit, yUnit="电流[A]", time=1, multiDimensionDataxy=curves2)
    Figs.append(result2)

    statementException = f'各变桨电机之间性能差异偏大，温度大于阈值10,电流大于5'
    statementNormal = f'各变桨电机之间性能差异不大，温度小于阈值10, 电流小于5'
    # 生成告警
    data, statement, alarming =  alarm.generateAlarm(name, "oar_engine_performance",'WROT.TemB1Mot', pn_data, error_data_time_duration, resample_interval, assetId, threValue, statementException, statementNormal, idMaps)
    return data, statement, Figs, 0,1 # alarming, 0
    # # 生成告警
    # return alarm.generateAlarm(name, pn_data, error_data_time_duration, resample_interval, assetId)
