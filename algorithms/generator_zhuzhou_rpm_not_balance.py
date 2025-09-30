# -*- coding: utf-8 -*-
"""
主轴转速和发电机转速不平衡
Created on Thu Aug 10 09:45:34 2023

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
from configs.config import algConfig, state
from data.get_data import wash_data_for_train

name = algConfig['generator_zhuzhou_rpm_not_balance']['name']#'主轴转速和发电机转速不平衡', 只考虑发电状态
# 把所需测点定义到每个算法里
ai_points = algConfig['generator_zhuzhou_rpm_not_balance']['ai_points']
ai_rename = algConfig['generator_zhuzhou_rpm_not_balance']['ai_rename']
di_points = algConfig['generator_zhuzhou_rpm_not_balance']['di_points']
general_points = algConfig['generator_zhuzhou_rpm_not_balance']['general_points']
private_points = algConfig['generator_zhuzhou_rpm_not_balance']['private_points']
time_duration = algConfig['generator_zhuzhou_rpm_not_balance']['time_duration']
resample_interval = algConfig['generator_zhuzhou_rpm_not_balance']['resample_interval']
error_data_time_duration = algConfig['generator_zhuzhou_rpm_not_balance']['error_data_time_duration']
need_all_turbines = algConfig['generator_zhuzhou_rpm_not_balance']['need_all_turbines']
store_file = algConfig['generator_zhuzhou_rpm_not_balance']['store_file']

def wash_data(pn_data: DataFrame, ratedPower):
    temp_data = pn_data[ai_points + di_points+general_points]
    temp = wash_data_for_train(temp_data, ratedPower)
    return temp, ''


def predict_result(pn_data: DataFrame):
    return pn_data[['WGEN.GenSpd','WTRM.RotorSpd']]


async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    pn_data['ratio'] = pn_data['WGEN.GenSpd']/pn_data['WTRM.RotorSpd']
    pn_data = pn_data[(pn_data['WTUR.TurbineSts']==state) & (pn_data['WTRM.RotorSpd'] >= 1)]
    # value_mask = ~pn_data.isna()
    # value_rows = value_mask.all(axis=1)
    # pn_data = pn_data[value_rows]
    
    # 1%波动报警
    pn_data['result'] = np.abs(pn_data['ratio']-np.mean(pn_data['ratio'])) >= np.mean(pn_data['ratio']) * 0.1

    mean_data = [round(float(np.mean(pn_data['ratio'])),4)]*pn_data['ratio'].shape[0]
    #数据展示
    x = [str(tick) for tick in list(pn_data.index)]
    x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
    x = [int(tick.timestamp()*1000) for tick in x]
    y1 = [str(round(num,4)) for num in list(pn_data['ratio'])]
    y2 = [str(round(num,4)) for num in mean_data]
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
    interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
    interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
    Figs = []
    curves1 = []
    curves1.append(DisplayResultXY('1', '转速比', '#FFFF00', '', data1))#{'type':'0', 'name': '转速比', 'xyData': data1}
    curves1.append(DisplayResultXY('0', '均值', '#00FF00', 'Solid', data2))#{'type':'0', 'name': '均值', 'xyData': data2}
    
    result1 = DisplayFigures(xUnit=interval_unit, yUnit="转速比", time=1, multiDimensionDataxy=curves1)#DisplayResultXY(str(pn_data.index.min()), str(pn_data.index.max()), str(interval_value), '转速比', curves)
    Figs.append(result1)

    statementException = f'发电机转速和主轴转速比波动范围超过均值的10%'
    statementNormal = f'发电机转速和主轴转速比波动范围小于均值的10%'
    data, statement, alarming = alarm.generateAlarm(name,'generator_zhuzhou_rpm_not_balance', 'WGEN.GenSpd', pn_data, error_data_time_duration, resample_interval, assetId, 0.01, statementException, statementNormal, idMaps)
    return data, statement, Figs, 0,1 # alarming, 0

