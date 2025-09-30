from pandas import DataFrame
from alarms import alarm
import joblib
from data.get_data import wash_data_mechanization_new
import numpy as np
from utils import model_util
from utils.display_util import DisplayResultXY, DisplayFigures
import pandas as pd
import utils.time_util as time_util
from configs import config
import asyncio
from data.get_data import wash_data_for_train
from datetime import datetime as datetime
from configs.config import algConfig

name = algConfig['chilunxiang_sanre']['name']#'齿轮箱散热异常'
# 把所需测点定义到每个算法里
ai_points = algConfig['chilunxiang_sanre']['ai_points']
ai_rename = algConfig['chilunxiang_sanre']['ai_rename']
di_points = algConfig['chilunxiang_sanre']['di_points']
general_points = algConfig['chilunxiang_sanre']['general_points']
private_points = algConfig['chilunxiang_sanre']['private_points']
time_duration = algConfig['chilunxiang_sanre']['time_duration']
resample_interval = algConfig['chilunxiang_sanre']['resample_interval']
error_data_time_duration = algConfig['chilunxiang_sanre']['error_data_time_duration']
need_all_turbines = algConfig['chilunxiang_sanre']['need_all_turbines']
store_file = algConfig['chilunxiang_sanre']['store_file']

def wash_data(pn_data: DataFrame, ratedPower):
    # temp_data = pn_data[ai_points + di_points+general_points]
    # final_df = wash_data_mechanization_new(temp_data, ratedPower)
    # # 处理空数据
    # final_df.fillna(method='ffill', axis=0, inplace=True)
    # final_df.fillna(method='bfill', axis=0, inplace=True)
    # return final_df, ''    
    temp_data = pn_data[ai_points + di_points+general_points]
    temp_data = wash_data_for_train(temp_data, ratedPower)
    if temp_data[temp_data['clear'] == 2].shape[0] > 0:
        return temp_data[temp_data['clear'] == 2], ''
    else:
        return pd.DataFrame(), '清洗后没有干净数据'


def predict_result(pn_data: DataFrame, assetId):
    # 处理空数据
    pn_data.fillna(method='ffill', axis=0, inplace=True)
    pn_data.fillna(method='bfill', axis=0, inplace=True)
    # 加载模型
    model = model_util.load_model(config.Wind_Farm, 'chilunxiang_sanre', assetId,'chilunxiang_sanre')
    # 预测健康温度 并判断是否告警
    y_predict = model.predict(pn_data[['WNAC.WindSpeed','WGEN.GenActivePW','WNAC.TemNacelle','WGEN.GenSpd']])
    return y_predict


async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    # 模型推理
    pn_data['WTRM.TemGeaOil_predict'] = predict_result(pn_data, assetId)
    threValue = 5
    # 阈值判断
    pn_data['result'] = np.abs(pn_data['WTRM.TemGeaOil'] - pn_data['WTRM.TemGeaOil_predict']) > threValue
    pn_data = pn_data.sort_index()
    #数据展示
    x = [str(tick) for tick in list(pn_data.index)]
    x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
    x = [int(tick.timestamp()*1000) for tick in x]
    y1 = [str(round(num,4)) for num in list(pn_data['WTRM.TemGeaOil_predict'])]
    y2 = [str(round(num,4)) for num in list(pn_data['WTRM.TemGeaOil'])]
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
    interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
    interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
    Figs = []
    curves1 = []
    curves1.append(DisplayResultXY('0', '预测温度', '#FFFF00', 'Solid', data1))#{'type':'0', 'name': '预测温度', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'xyData': data1}
    curves1.append(DisplayResultXY('0', '实际温度', '#00FF00', 'Solid', data2))#{'type':'0', 'name': '实际温度', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'xyData': data2}
    
    result1 = DisplayFigures(xUnit=interval_unit, yUnit="温度[℃]", time=1, multiDimensionDataxy=curves1)#DisplayResultXY(str(pn_data.index.min()), str(pn_data.index.max()), str(interval_value), '温度', curves)
    Figs.append(result1)

    statementException = f'在风机运行正常时采样训练拟合后给出的趋势预测温度和实际温度偏差大于5'
    statementNormal = f'在风机运行正常时采样训练拟合后给出的趋势预测温度和实际温度偏差小于等于5'
    # 生成告警
    data, statement, alarming = alarm.generateAlarm(name,'chilunxiang_sanre', 'WTRM.TemGeaOil',pn_data, error_data_time_duration, resample_interval, assetId, threValue, statementException, statementNormal, idMaps)
    return data, statement, Figs, 0,1 # alarming, 0


def judge(pn_data: DataFrame):
    """
    齿轮箱散热异常
    :param pn_data: dataframe
    :return:
    """
    result_value = []

    for index, row in pn_data.iterrows():
        c81 = float(row.get("WNAC.TemNacelle"))
        c82 = float(row.get("WTRM.TemGeaOil"))

        if c82 - c81 >= 35 and c82 >= 70:
            result_value.append(True)
        else:
            result_value.append(False)

    pn_data['result'] = result_value
    return alarm.generateAlarm(pn_data, error_data_time_duration)