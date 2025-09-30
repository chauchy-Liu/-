from pandas import DataFrame
from alarms import alarm
import numpy as np
from utils.display_util import DisplayResultXY, DisplayFigures
import pandas as pd
import utils.time_util as time_util
import asyncio
from datetime import datetime as datetime
from configs.config import algConfig

name = algConfig['engine_cabinet_temperature']['name']#'机舱柜温度异常'
# 把所需测点定义到每个算法里
ai_points = algConfig['engine_cabinet_temperature']['ai_points']
ai_rename = algConfig['engine_cabinet_temperature']['ai_rename']
di_points = algConfig['engine_cabinet_temperature']['di_points']
general_points = algConfig['engine_cabinet_temperature']['general_points']
private_points = algConfig['engine_cabinet_temperature']['private_points']
time_duration = algConfig['engine_cabinet_temperature']['time_duration']
resample_interval = algConfig['engine_cabinet_temperature']['resample_interval']
error_data_time_duration = algConfig['engine_cabinet_temperature']['error_data_time_duration']
need_all_turbines = algConfig['engine_cabinet_temperature']['need_all_turbines']
store_file = algConfig['engine_cabinet_temperature']['store_file']

def wash_data(pn_data: DataFrame, ratedPower):
    temp_data = pn_data[ai_points + di_points + ['assetId']+general_points]
    return temp_data, ''


def predict_result(pn_data: DataFrame):
    # 计算全场平均温度
    # mean_temperature = pn_data.groupby(pn_data.index)['WNAC.TemNacelleCab'].mean()
    value, unit = time_util.split_time_delta(resample_interval)
    unit = time_util.__timedelta_resample_unit_dict[unit].lower()
    mean_temperature = pn_data['WNAC.TemNacelleCab'].resample(str(6*value)+unit, closed='left').mean()
    #回填平均值
    mean_temperature = mean_temperature.reindex(pn_data.index, method='ffill')
    return mean_temperature
    
    
async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    # 计算全场平均温度
    mean_temperature = predict_result(pn_data)
    # mean_temperature = np.mean(mean_temperature)
    # 目标风机的温度
    target_temperature_df = pn_data[pn_data['assetId']==assetId]
    # 再与目标风机做对比
    final_df = target_temperature_df
    threValue = 100
    final_df['result'] = np.abs(target_temperature_df['WNAC.TemNacelleCab'] - mean_temperature) > threValue
    pn_data = pn_data[~pn_data.index.duplicated()]
    #数据展示
    x = [str(tick) for tick in list(pn_data.index)]
    x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
    x = [int(tick.timestamp()*1000) for tick in x]
    y1 = [str(round(num,4)) for num in mean_temperature] #[mean_temperature,]*len(x)
    y2 = [str(round(num,4)) for num in list(pn_data['WNAC.TemNacelleCab'])]
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
    interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
    interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
    Figs = []
    curves1 = []
    curves1.append(DisplayResultXY('0', '平均温度', '#FFFF00', 'Solid', data1))#{'type':'0', 'name': '预测温度', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'xyData': data1}
    curves1.append(DisplayResultXY('0', '实际温度', '#00FF00', 'Solid', data2))#{'type':'0', 'name': '实际温度', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'xyData': data2}
    
    result1 = DisplayFigures(xUnit=interval_unit, yUnit="温度[℃]", time=1, multiDimensionDataxy=curves1)#DisplayResultXY(str(pn_data.index.min()), str(pn_data.index.max()), str(interval_value), '温度', curves)
    Figs.append(result1)

    statementException = f'全场平均温度和风机实际温度偏差大于5'
    statementNormal = f'全场平均温度和风机实际温度偏差小于等于5'
    # 生成告警
    data, statement, alarming = alarm.generateAlarm(name, 'engine_cabinet_temperature', 'WNAC.TemNacelleCab', final_df, error_data_time_duration, resample_interval, assetId, threValue, statementException, statementNormal, idMaps)
    return data, statement, Figs, 0,1 # alarming, 0


def judge(pn_data: DataFrame):
    """
    机舱柜温度异常
    :param pn_data: dataframe
    :return:
    """
    result_value = []

    for index, row in pn_data.iterrows():
        c93 = float(row.get("WNAC.TemNacelleCab"))
        c71 = float(row.get("WNAC.TemOut"))
        c81 = float(row.get("WNAC.TemNacelle"))

        if c93 >= 45 or c93-c71 >= 40 or c93-c81 >= 35:
            result_value.append(True)
        else:
            result_value.append(False)

    pn_data['result'] = result_value
    return alarm.generateAlarm(pn_data, error_data_time_duration)





