import numpy as np
from pandas import DataFrame
from alarms import alarm
from utils.display_util import DisplayResultXY, DisplayFigures
import pandas as pd
import utils.time_util as time_util
import asyncio
from datetime import datetime as datetime
from configs.config import algConfig

name = algConfig['generator_raozu_not_balance']['name']#'发电机定子线圈温度三相不平衡'
# 把所需测点定义到每个算法里
ai_points = algConfig['generator_raozu_not_balance']['ai_points']
ai_rename = algConfig['generator_raozu_not_balance']['ai_rename']
di_points = algConfig['generator_raozu_not_balance']['di_points']
general_points = algConfig['generator_raozu_not_balance']['general_points']
private_points = algConfig['generator_raozu_not_balance']['private_points']
time_duration = algConfig['generator_raozu_not_balance']['time_duration']
resample_interval = algConfig['generator_raozu_not_balance']['resample_interval']
error_data_time_duration = algConfig['generator_raozu_not_balance']['error_data_time_duration']
need_all_turbines = algConfig['generator_raozu_not_balance']['need_all_turbines']
store_file = algConfig['generator_raozu_not_balance']['store_file']

def wash_data(pn_data: DataFrame, ratedPower):
    temp_data = pn_data[ai_points + di_points+general_points]
    return temp_data, ''


def predict_result(pn_data: DataFrame):
    return pn_data[['WGEN.TemGenStaU','WGEN.TemGenStaV','WGEN.TemGenStaW']]


async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    '''
    发电机定子线圈温度三相不平衡
    '''
    final_df = predict_result(pn_data)
    threValue = 5
    final_df['result'] = (np.abs(final_df['WGEN.TemGenStaU']-final_df['WGEN.TemGenStaV'])>threValue) | (np.abs(final_df['WGEN.TemGenStaU'] - final_df['WGEN.TemGenStaW'])>threValue) | (np.abs(final_df['WGEN.TemGenStaV'] - final_df['WGEN.TemGenStaW'])>threValue)

    #数据展示
    x = [str(tick) for tick in list(pn_data.index)]
    x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
    x = [int(tick.timestamp()*1000) for tick in x]
    y1 = [str(round(num,4)) for num in list(final_df['WGEN.TemGenStaU'])]
    y2 = [str(round(num,4)) for num in list(final_df['WGEN.TemGenStaV'])]
    y3 = [str(round(num,4)) for num in list(final_df['WGEN.TemGenStaW'])]
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
    data3 = pd.DataFrame({'x': x, 'y': y3}).to_dict('records')
    interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
    interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
    Figs = []
    curves1 = []
    curves1.append(DisplayResultXY('0', 'U相温度', '#FFFF00', 'Solid', data1))#{'type':'0', 'name': '拟合U相温度', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'xyData': data1}
    curves1.append(DisplayResultXY('0', 'V相温度', '#FF0000', 'Solid', data2))#{'type':'0', 'name': '拟合V相温度', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'xyData': data2}
    curves1.append(DisplayResultXY('0', 'W相温度', '#00FF00', 'Solid', data3))#{'type':'0', 'name': '拟合W相温度', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'xyData': data3}
    
    result1 = DisplayFigures(xUnit=interval_unit, yUnit="温度[℃]", time=1, multiDimensionDataxy=curves1)#DisplayResultXY(str(pn_data.index.min()), str(pn_data.index.max()), str(interval_value), '温度', curves)
    Figs.append(result1)

    statementException = f'线圈温度三相不平衡,温差大于{threValue}'
    statementNormal = f'线圈温度三相的差异不大,温差小于等于{threValue}'
    # 生成告警
    data, statement, alarming = alarm.generateAlarm(name,'generator_raozu_not_balance','WGEN.TemGenStaU', final_df, error_data_time_duration, resample_interval, assetId, threValue, statementException, statementNormal, idMaps)
    return data, statement, Figs, 0,1 # alarming, 0




