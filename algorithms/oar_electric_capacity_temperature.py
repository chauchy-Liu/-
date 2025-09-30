from pandas import DataFrame
from alarms import alarm
import numpy as np
from utils.display_util import DisplayResultXY, DisplayFigures
import pandas as pd
import utils.time_util as time_util
import asyncio
from datetime import datetime as datetime
from configs.config import algConfig

name = algConfig['oar_electric_capacity_temperature']['name']#'变桨电容温度异常'
# 把所需测点定义到每个算法里
ai_points = algConfig['oar_electric_capacity_temperature']['ai_points']
ai_rename = algConfig['oar_electric_capacity_temperature']['ai_rename']
di_points = algConfig['oar_electric_capacity_temperature']['di_points']
general_points = algConfig['oar_electric_capacity_temperature']['general_points']
private_points = algConfig['oar_electric_capacity_temperature']['private_points']
time_duration = algConfig['oar_electric_capacity_temperature']['time_duration']
resample_interval = algConfig['oar_electric_capacity_temperature']['resample_interval']
error_data_time_duration = algConfig['oar_electric_capacity_temperature']['error_data_time_duration']
need_all_turbines = algConfig['oar_electric_capacity_temperature']['need_all_turbines']
store_file = algConfig['oar_electric_capacity_temperature']['store_file']

def wash_data(pn_data: DataFrame, ratedPower):
    temp_data = pn_data[ai_points + di_points+general_points]
    return temp_data, ''


def predict_result(pn_data: DataFrame):
    return pn_data[['WROT.PtCapTemBl1','WROT.PtCapTemBl2','WROT.PtCapTemBl3', 'WROT.VolB1Cap', 'WROT.VolB2Cap', 'WROT.VolB3Cap']]


async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    # 阈值判断
    threValue = 100
    pn_data['result'] = ((np.abs(pn_data['WROT.PtCapTemBl1'] - pn_data['WROT.PtCapTemBl2']) >= threValue) & (np.abs(pn_data['WROT.VolB1Cap'] - pn_data['WROT.VolB2Cap'])/pn_data['WROT.VolB1Cap']) > 0.2) | ((np.abs(pn_data['WROT.PtCapTemBl1'] - pn_data['WROT.PtCapTemBl3']) >= threValue) & (np.abs(pn_data['WROT.VolB1Cap'] - pn_data['WROT.VolB3Cap'])/pn_data['WROT.VolB1Cap']) > 0.2) | ((np.abs(pn_data['WROT.PtCapTemBl3'] - pn_data['WROT.PtCapTemBl2']) >= threValue) & (np.abs(pn_data['WROT.VolB3Cap'] - pn_data['WROT.VolB2Cap'])/pn_data['WROT.VolB3Cap']) > 0.2)


    #数据展示
    x = [str(tick) for tick in list(pn_data.index)]
    x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
    x = [int(tick.timestamp()*1000) for tick in x]
    y1 = [str(round(num,4)) for num in list(pn_data['WROT.PtCapTemBl1'])]
    y2 = [str(round(num,4)) for num in list(pn_data['WROT.PtCapTemBl2'])]
    y3 = [str(round(num,4)) for num in list(pn_data['WROT.PtCapTemBl3'])]
    y4 = [str(round(num,4)) for num in list(pn_data['WROT.VolB1Cap'])]
    y5 = [str(round(num,4)) for num in list(pn_data['WROT.VolB2Cap'])]
    y6 = [str(round(num,4)) for num in list(pn_data['WROT.VolB3Cap'])]
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
    curves1.append(DisplayResultXY('0', '电容温度1', '#FFFF00', 'Solid', data1))#{'type':'0', 'name': '电容温度1', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'xyData': data1}
    curves1.append(DisplayResultXY('0', '电容温度2', '#FF0000', 'Solid', data2))#{'type':'0', 'name': '电容温度2', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'xyData': data2}
    curves1.append(DisplayResultXY('0', '电容温度3', '#00FF00', 'Solid', data3))#{'type':'0', 'name': '电容温度3', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'xyData': data3}
    curves2.append(DisplayResultXY('0', '电容电压1', '#FFFF00', 'Solid', data4))#{'type':'0', 'name': '电机1电流', "abscissaUnit": interval_unit, "ordinateUnit": "A", 'xyData': data4}
    curves2.append(DisplayResultXY('0', '电容电压2', '#00FF00', 'Solid', data5))#{'type':'0', 'name': '电机2电流', "abscissaUnit": interval_unit, "ordinateUnit": "A", 'xyData': data5}
    curves2.append(DisplayResultXY('0', '电容电压3', '#FF0000', 'Solid', data6))#{'type':'0', 'name': '电机3电流', "abscissaUnit": interval_unit, "ordinateUnit": "A", 'xyData': data6}
    
    result1 = DisplayFigures(xUnit=interval_unit, yUnit="温度[℃]", time=1, multiDimensionDataxy=curves1)#DisplayResultXY(str(pn_data.index.min()), str(pn_data.index.max()), str(interval_value), '温度', curves)
    Figs.append(result1)
    result2 = DisplayFigures(xUnit=interval_unit, yUnit="电压[V]", time=1, multiDimensionDataxy=curves2)
    Figs.append(result2)

    statementException = f'各变浆电容之间温度差异偏大，大于阈值{threValue}, 且电容电压差值变化幅度偏大，大于自身20%'
    statementNormal = f'各变浆电容之间温度差异不大，小于阈值{threValue}, 或者电容电压差值变化幅度偏小，小于自身20%'
    # 生成告警
    data, statement, alarming =  alarm.generateAlarm(name,'oar_electric_capacity_temperature', 'WROT.PtCapTemBl1',pn_data, error_data_time_duration, resample_interval, assetId, threValue, statementException, statementNormal, idMaps)
    return data, statement, Figs, 0,1 # alarming, 0


def judge(pn_data: DataFrame):
    """
    变桨电容温度异常
    ？？测点没有 只有叶片超级电容柜温度  逻辑？
    :param pn_data: dataframe
    :return:
    """
    wind_turbine_codes = pn_data['code']
    print(wind_turbine_codes)
    result_value = []

    for index, row in pn_data.iterrows():
        c258 = float(row.get("C258"))
        c259 = float(row.get("C259"))
        c260 = float(row.get("C260"))
        c246 = float(row.get("C246"))
        c247 = float(row.get("C247"))
        c248 = float(row.get("C248"))

        if c258 >= 45 or c259 >= 45 or c260 >= 45 or abs(c258 - c259) >= 10 or abs(c258 - c260) >= 10 or abs(
                c259 - c260) >= 10 or c258 - c246 >= 10 or c259 - c247 >= 10 or c260 - c248 >= 10:
            result_value.append(True)
        else:
            result_value.append(False)

    pn_data['result'] = result_value
    return pn_data
