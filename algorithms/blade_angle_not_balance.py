from pandas import DataFrame
from alarms import alarm
import numpy as np
from utils.display_util import DisplayResultXY, DisplayFigures
import pandas as pd
import utils.time_util as time_util
import asyncio
from datetime import datetime as datetime
from configs.config import algConfig
# import pickle
# import zlib


name = algConfig['blade_angle_not_balance']['name']#'叶片角度不平衡'
# 把所需测点定义到每个算法里
ai_points = algConfig['blade_angle_not_balance']['ai_points']
ai_rename = algConfig['blade_angle_not_balance']['ai_rename']
di_points = algConfig['blade_angle_not_balance']['di_points']
general_points = algConfig['blade_angle_not_balance']['general_points']
private_points = algConfig['blade_angle_not_balance']['private_points']
time_duration = algConfig['blade_angle_not_balance']['time_duration']
resample_interval = algConfig['blade_angle_not_balance']['resample_interval']
error_data_time_duration = algConfig['blade_angle_not_balance']['error_data_time_duration']
need_all_turbines = algConfig['blade_angle_not_balance']['need_all_turbines']
store_file = algConfig['blade_angle_not_balance']['store_file']

def wash_data(pn_data: DataFrame, ratedPower):
    temp_data = pn_data[ai_points + di_points+general_points]
    # 清空nan数据
    temp_data = temp_data.dropna(subset=ai_points)
    temp_data = temp_data[temp_data['WGEN.GenActivePW'] > 30]
    return temp_data, ""


def predict_result(pn_data: DataFrame):
    return pn_data[['WROT.Blade1Position', 'WROT.Blade2Position', 'WROT.Blade3Position']]
    
    
async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps, algorithms_config):
    assetId = Turbine_attr['mdmId']
    final_df = predict_result(pn_data)
    threValue = 1
    final_df['result'] = (np.abs(final_df['WROT.Blade1Position'] - final_df['WROT.Blade2Position']) >threValue) | (np.abs(final_df['WROT.Blade1Position'] - final_df['WROT.Blade3Position']) >threValue) | (np.abs(final_df['WROT.Blade3Position'] - final_df['WROT.Blade2Position']) >threValue)

    #数据展示
    x = [str(tick) for tick in list(final_df.index)]
    x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
    x = [int(tick.timestamp()*1000) for tick in x]
    y1 = [str(round(num,4)) for num in list(final_df['WROT.Blade1Position'])]
    y2 = [str(round(num,4)) for num in list(final_df['WROT.Blade2Position'])]
    y3 = [str(round(num,4)) for num in list(final_df['WROT.Blade3Position'])]
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
    data3 = pd.DataFrame({'x': x, 'y': y3}).to_dict('records')
    interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
    interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
    Figs = []
    curves1 = []
    curves1.append(DisplayResultXY('0', '叶片1桨距角', '#FFFF00', 'Solid', data1)) #{'type':'0', 'name': '拟合叶片1桨距角', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data1}
    curves1.append(DisplayResultXY('0', '叶片2桨距角', '#FF0000', 'Solid', data2)) #{'type':'0', 'name': '拟合叶片2桨距角', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data2}
    curves1.append(DisplayResultXY('0', '叶片3桨距角', '#00FF00', 'Solid', data3)) #{'type':'0', 'name': '拟合叶片3桨距角', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data3}

    result1 = DisplayFigures(xUnit=interval_unit, yUnit="度[°]", time=1, multiDimensionDataxy=curves1)
    Figs.append(result1)
    statementException = f'桨距角距离大于等于阈值1'
    statementNormal = f'桨距角距离小于阈值1'
    # 生成告警
    data, statement, alarming =  alarm.generateAlarm(name, 'blade_angle_not_balance', 'WROT.Blade1Position', final_df, error_data_time_duration, resample_interval, assetId, threValue, statementException, statementNormal, idMaps)
    return data, statement, Figs, 0,1 #alarming, 0
    

def judge(pn_data: DataFrame):
    """
    叶片角度不平衡
    风机运行状态，功率大于10、20、30
    :param pn_data: dataframe
    :return: 异常数据
    """
    result_value = []

    for index, row in pn_data.iterrows():
        c72 = float(row.get("WROT.Blade1Position"))
        c73 = float(row.get("WROT.Blade2Position"))
        c74 = float(row.get("WROT.Blade3Position"))

        if abs(c72 - c73) >= 1 or abs(c72 - c74) >= 1 or abs(c73 - c74) >= 1:
            result_value.append(True)
        else:
            result_value.append(False)

    pn_data['result'] = result_value
    
    return alarm.generateAlarm(pn_data, error_data_time_duration)
