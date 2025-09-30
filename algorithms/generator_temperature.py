import numpy as np
from pandas import DataFrame
from alarms import alarm
import joblib
from data.get_data import wash_data_mechanization_new
from utils import model_util
from utils.display_util import DisplayResultXY, DisplayFigures
import pandas as pd
import utils.time_util as time_util
from configs import config
import asyncio
from data.get_data import wash_data_for_train
from datetime import datetime as datetime
from configs.config import algConfig

name = algConfig['generator_temperature']['name']#'发电机定子绕组温度异常'
# 把所需测点定义到每个算法里
ai_points = algConfig['generator_temperature']['ai_points']
ai_rename = algConfig['generator_temperature']['ai_rename']
di_points = algConfig['generator_temperature']['di_points']
general_points = algConfig['generator_temperature']['general_points']
private_points = algConfig['generator_temperature']['private_points']
time_duration = algConfig['generator_temperature']['time_duration']
resample_interval = algConfig['generator_temperature']['resample_interval']
error_data_time_duration = algConfig['generator_temperature']['error_data_time_duration']
need_all_turbines = algConfig['generator_temperature']['need_all_turbines']
store_file = algConfig['generator_temperature']['store_file']

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
    # 加载模型
    model = model_util.load_model(config.Wind_Farm, 'generator_temperature', assetId,'generator_temperature')
    # 预测健康温度 并判断是否告警
    y_predict = model.predict(pn_data[['WGEN.GenActivePW','WNAC.TemOut','WNAC.TemNacelle','WGEN.GenSpd','WNAC.WindSpeed']]) # 'WGEN.LHDLGENAI31','WGEN.LHDLGENAI103'
    print(y_predict)
    error = model_util.load_model(config.Wind_Farm, 'generator_temperature', assetId,'error')
    return y_predict, error


async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    predict, error = predict_result(pn_data, assetId)
    
    factor = 3
    # 平均温度-拟合温度
    pn_data['result'] = np.mean(pn_data[['WGEN.TemGenStaU','WGEN.TemGenStaV','WGEN.TemGenStaW']], axis=1) - predict > error*factor# | (np.abs(np.mean(pn_data[['WGEN.TemGenStaU','WGEN.TemGenStaV','WGEN.TemGenStaW']], axis=1) - predict) < error*-3)
    pn_data = pn_data.sort_index()
    #数据展示
    x = [str(tick) for tick in list(pn_data.index)]
    x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
    x = [int(tick.timestamp()*1000) for tick in x]
    y1 = [str(round(num,4)) for num in list(np.mean(pn_data[['WGEN.TemGenStaU','WGEN.TemGenStaV','WGEN.TemGenStaW']], axis=1))]
    y2 = [str(round(num,4)) for num in list(predict)]
    y3 = [str(round(num,4)) for num in list(predict+3*error)]
    # y4 = [str(round(num,4)) for num in list(predict-3*error)]
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
    data3 = pd.DataFrame({'x': x, 'y': y3}).to_dict('records')
    # data4 = pd.DataFrame({'x': x, 'y': y4}).to_dict('records')
    interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
    interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
    Figs = []
    curves1 = []
    curves1.append(DisplayResultXY('0', '温度', '#00FF00', 'Solid', data1))#{'type':'0', 'name': '平均温度', 'data': data1}
    curves1.append(DisplayResultXY('0', '预测温度', '#FFFF00', 'Solid', data2))#{'type':'0', 'name': '预测温度', 'data': data2}
    curves1.append(DisplayResultXY('0', '误差上限', '#888888', 'Dash', data3))#{'type':'0', 'name': '预测温度', 'data': data2}
    # curves1.append(DisplayResultXY('0', '误差下限', '#888888', 'Dash', data4))#{'type':'0', 'name': '预测温度', 'data': data2}
    
    result1 = DisplayFigures(xUnit=interval_unit, yUnit="温度[℃]", time=1, multiDimensionDataxy=curves1)#DisplayResultXY(str(pn_data.index.min()), str(pn_data.index.max()), str(interval_value), '温度', curves)
    Figs.append(result1)

    statementException = f'线圈三相平均实际温度高于在正常工况下给出的预测温度的上限阈值'
    statementNormal = f'线圈三相平均实际温度低于在正常工况下给出的预测温度的上限阈值'
    # 生成告警
    data, statement, alarming = alarm.generateAlarm(name,'generator_temperature','WGEN.TemGenStaU', pn_data, error_data_time_duration, resample_interval, assetId, error*2, statementException, statementNormal, idMaps)
    return data, statement, Figs, 0,1 # alarming, 0
    
    

def judge(pn_data: DataFrame):
    """
    发电机温度异常（发电机定子绕组温度异常）
    ？？测点没有 并且算法逻辑有变更 变成三个值的平均值
    :param pn_data: dataframe
    :return:
    """
    result_value = []

    for index, row in pn_data.iterrows():
        temp1 = float(row["WGEN.TemGenStaU"])
        temp2 = float(row["WGEN.TemGenStaV"])
        temp3 = float(row["WGEN.TemGenStaW"])

        env_temp = float(row.get("WNAC.TemOut"))
        mean = np.mean([temp1, temp2, temp3])
        if mean - env_temp >= 80:
            result_value.append(True)
        else:
            result_value.append(False)

    pn_data['result'] = result_value
    return alarm.generateAlarm(pn_data, error_data_time_duration)





