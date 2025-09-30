# -*- coding: utf-8 -*-
"""
叶片结冰
Created on Tue Aug 15 10:48:49 2023

@author: sunyan
"""
from pandas import DataFrame
from alarms import alarm
import numpy as np
from configs import config
import joblib
from utils import model_util
from sklearn import preprocessing
import pandas as pd
import utils.time_util as time_util
from utils.display_util import DisplayResultXY, DisplayFigures
import asyncio
from data.get_data import wash_data_for_train
from datetime import datetime as datetime
from configs.config import algConfig

name = algConfig['blade_freeze']['name']#'叶片结冰'
# 把所需测点定义到每个算法里
ai_points = algConfig['blade_freeze']['ai_points']
ai_rename = algConfig['blade_freeze']['ai_rename']
di_points = algConfig['blade_freeze']['di_points']
general_points = algConfig['blade_freeze']['general_points']
private_points = algConfig['blade_freeze']['private_points']
time_duration = algConfig['blade_freeze']['time_duration']
resample_interval = algConfig['blade_freeze']['resample_interval']
error_data_time_duration = algConfig['blade_freeze']['error_data_time_duration']
need_all_turbines = algConfig['blade_freeze']['need_all_turbines']
store_file = algConfig['blade_freeze']['store_file']
# modelId = "SPIC_ZD_CMS_Blade"



private_points_ = []
for modelKey, pointValue in private_points.items():
    private_points_ += pointValue

def wash_data(pn_data: DataFrame, ratedPower):    
    # temp_data = pn_data[ai_points + di_points+general_points]

    '''
    剔除限功率、环境温度+-5、风速低于10、桨距角<最小桨距角+2
    '''
    # pn_data = pn_data[(pn_data['WTUR.TurbineSts'] != 90001) 
    #         & (np.abs(pn_data['WNAC.TemOut']) < 5) 
    #         & (pn_data['WNAC.WindSpeed'] < 10) 
    #         & (pn_data['WROT.Blade1Position'] < config.Pitch_Min + 2)]
    # return pn_data, ''
    #pn_data[private_points]是序列时
    # temp_data = pn_data.loc[pn_data[private_points] != 0]
    #pn_data[private_points]是dataframe时
    
    # condition = pn_data[private_points_] != 0
    # #dataframe->series
    # condition = condition.squeeze('columns')
    # temp_data = pn_data[condition]
    # if temp_data.shape[0] > pn_data.shape[0]*0.1:
    #     return temp_data, ''
    # else:
    #     return pd.DataFrame(), f'{private_points_}的非0数据量小于{int(pn_data.shape[0]*0.1)}'

    temp_data = pn_data[ai_points + di_points+general_points]
    temp_data = wash_data_for_train(temp_data, ratedPower)
    if temp_data.empty == False:
        return temp_data, '' #temp_data[temp_data['clear'] == 2], ''
    else:
        return pd.DataFrame(), '无数据'

    

def predict_result(pn_data: DataFrame):
    # temp_data = pn_data.loc[np.mean(pn_data[ai_points])<0]
    pass
    
async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    # meanTemp = np.mean(pn_data[ai_points])
    # rmsFactor = np.sqrt(np.average(pn_data[private_points_]**2))

    pn_data['result'] = False
    
    pn_data_error = pn_data[(pn_data['WTUR.TurbineSts'] != 90001) 
            & (np.abs(pn_data['WNAC.TemOut']) < 5) 
            & (pn_data['WNAC.WindSpeed'] < 10) 
            & (pn_data['WROT.Blade1Position'] < config.Pitch_Min + 2)]
    
    pn_data.loc[pn_data_error.index, 'result'] = True

    function = model_util.load_model(config.Wind_Farm, 'speed_power',assetId, 'speed_power')
    #风速排序
    pn_data_sorted = pn_data.sort_values(by='WNAC.WindSpeed', ascending=True)    

    if True in list(pn_data['result']):

        
        pn_data_error_sorted = pn_data_error.sort_values(by='WNAC.WindSpeed', ascending=True)
        # pn_data_sorted['theory_power'] = function(pn_data_sorted['WNAC.WindSpeed'])
        #归一化数据
        # scalorWS = preprocessing.MinMaxScaler()
        # pn_data_sorted['wsTransformed'] = scalorWS.fit_transform(pn_data_sorted[['WNAC.WindSpeed']])
        # scalorPW = preprocessing.MinMaxScaler()
        # pn_data_sorted['pwTransformed'] = scalorPW.fit_transform(pn_data_sorted[['WGEN.GenActivePW']])
        # pn_data_sorted['theory_power_transformed'] = function(pn_data_sorted['wsTransformed'])
        #逆变换
        # pn_data_sorted['theory_power'] = scalorPW.inverse_transform(pn_data_sorted[['theory_power_transformed']])
        # pn_data_sorted['result'] = pn_data_sorted['WGEN.GenActivePW'] - pn_data_sorted['theory_power'] * 0.9 < 0

        pn_data_sorted['theory_power'] = function(pn_data_sorted['WNAC.WindSpeed'])
        
        #数据展示
        x = [str(round(tick,4)) for tick in list(pn_data_sorted['WNAC.WindSpeed'])]
        x1 = [str(round(tick,4)) for tick in list(pn_data_error_sorted['WNAC.WindSpeed'])]
        y1 = [str(round(num,4)) for num in list(pn_data_sorted['theory_power'])]
        y2 = [str(round(num,4)) for num in list(pn_data_sorted['WGEN.GenActivePW'])]
        y3 = [str(round(num,4)) for num in list(pn_data_error_sorted['WGEN.GenActivePW'])]
        # y3 = [str(round(num,4)) for num in [meanTemp]*pn_data.shape[0]]
        # y4 = [str(round(num,4)) for num in [rmsFactor]*pn_data.shape[0]]
        data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
        data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
        data3 = pd.DataFrame({'x': x1, 'y': y3}).to_dict('records')
        # data3 = pd.DataFrame({'x': x, 'y': y3}).to_dict('records')
        # data4 = pd.DataFrame({'x': x, 'y': y4}).to_dict('records')
        interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
        interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
        Figs = []
        curves1 = []
        # curves2 = []
        curves1.append(DisplayResultXY('0', '理论风速功率曲线', '#FFFF00', 'Solid', data1))#{'type':'0', 'name': '室外温度', "abscissaUnit": interval_unit, "ordinateUnit": "℃", 'xyData': data1}
        # curves1.append(DisplayResultXY('0', '均方根', data4))#{'type':'0', 'name': '均方根', "abscissaUnit": interval_unit, "ordinateUnit": "℃", 'xyData': data4}
        curves1.append(DisplayResultXY('1', '实际风速功率分布', '#00FF00', '', data2))#{'type':'0', 'name': '覆冰系数', "abscissaUnit": interval_unit, "ordinateUnit": "", 'xyData': data2}
        curves1.append(DisplayResultXY('1', '异常点风速功率分布', '#FF0000', '', data3))#{'type':'0', 'name': '覆冰系数', "abscissaUnit": interval_unit, "ordinateUnit": "", 'xyData': data2}
        # curves2.append(DisplayResultXY('0', '均值', data3))#{'type':'0', 'name': '均值', "abscissaUnit": interval_unit, "ordinateUnit": "", 'xyData': data3}
        
        result1 = DisplayFigures(xUnit='风速[m/s]', yUnit="功率[kw]", time=0, multiDimensionDataxy=curves1)
        Figs.append(result1)
        # result2 = DisplayFigures(xUnit=interval_unit, yUnit="", time=0, multiDimensionDataxy=curves2)
        # Figs.append(result2)

        #警告
        # if meanTemp < 0 and rmsFactor > 0.8:
        #     data, statement, alarming =  alarm.generateBaseAlarm(name,pn_data,True,assetId, '覆冰系数均方根大于0.8且室外温度低于0℃')
        #     data = pn_data
        # else:
        #     data, statement, alarming =  alarm.generateBaseAlarm(name,pn_data,False,assetId, '覆冰系数均方根小于等于0.8或者室外温度高于0℃')
        #     data = pd.DataFrame() 
        #     alarming = 0
        statementException = f'异常点占比超过'
        statementNormal = f'异常点占比低于'
        data, statement, alarming =   alarm.generateAlarmPercentage(name,'blade_freeze','WNAC.TemOut', pn_data_sorted, 0.5, assetId, 5, statementException, statementNormal, idMaps) # 50%的点在功率曲线以下
        return data, statement, Figs, 0,1 # alarming, 0
    else:
        # 生成告警
        data, statement, alarming =  alarm.generateBaseAlarm(name,'blade_freeze','WNAC.TemOut', pn_data, False, assetId, 5, '无可疑数据满足：非限电情况下环境温度小于5、风速低于10、桨距角小于最小桨距角+2', idMaps)
        Figs = []
        return data, statement, Figs, 0,1


    
def new_judge_model(pn_data: DataFrame, assetId):
    # 低于标准功率曲线有多少百分比数据点
    # 加载标准风速功率曲线
    # function = joblib.load('model/speed_power.model')
    function = model_util.load_model(config.Wind_Farm, 'speed_power', assetId, 'speed_power')
    # pn_data['theory_power'] = function(pn_data['WNAC.WindSpeed'])
    #归一化数据
    scalorWS = preprocessing.MinMaxScaler()
    pn_data['wsTransformed'] = scalorWS.fit_transform(pn_data[['WNAC.WindSpeed']])
    scalorPW = preprocessing.MinMaxScaler()
    pn_data['pwTransformed'] = scalorPW.fit_transform(pn_data[['WGEN.GenActivePW']])
    pn_data['theory_power_transformed'] = function(pn_data['wsTransformed'])
    #逆变换
    pn_data['theory_power'] = scalorPW.inverse_transform(pn_data[['theory_power_transformed']])
    pn_data['result'] = pn_data['WGEN.GenActivePW'] - pn_data['theory_power'] * 0.9 < 0

    #数据展示
    x = [str(tick) for tick in list(pn_data.index)]
    y1 = [str(round(num,4)) for num in list(pn_data['theory_power'])]
    y2 = [str(round(num,4)) for num in list(pn_data['WGEN.GenActivePW'])]
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
    interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
    interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
    curves = []
    curves.append({'type':'0', 'name': '理论发电', "abscissaUnit": interval_unit, "ordinateUnit": "kw", 'xyData': data1})#0:线，1:点
    curves.append({'type':'0', 'name': '当前桨距角发电', "abscissaUnit": interval_unit, "ordinateUnit": "kw", 'xyData': data2})
    
    result = DisplayResultXY(str(pn_data.index.min()), str(pn_data.index.max()), str(interval_value), '功率', curves)

    statementException = f'当前功率低于理论发电功率的占比超过'
    statementNormal = f'当前功率低于理论发电功率的占比低于'
    
    data, statement =  alarm.generateAlarmPercentage(name, pn_data, 0.5, assetId, statementException, statementNormal) # 50%的点在功率曲线以下
    return data, statement, result
    