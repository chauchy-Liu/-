from pandas import DataFrame
from alarms import alarm
import joblib
import numpy as np
from utils import model_util
from sklearn import preprocessing
from utils.display_util import DisplayResultXY, DisplayFigures
import pandas as pd
import utils.time_util as time_util
from configs import config
import asyncio
from data.get_data import wash_data_for_train
import data.get_data as get_data
from datetime import datetime as datetime
from configs.config import algConfig

name = algConfig['wind_speed_fault']['name']#'风速仪故障'
# 把所需测点定义到每个算法里
ai_points = algConfig['wind_speed_fault']['ai_points']
ai_rename = algConfig['wind_speed_fault']['ai_rename']
di_points = algConfig['wind_speed_fault']['di_points']
general_points = algConfig['wind_speed_fault']['general_points']
private_points = algConfig['wind_speed_fault']['private_points']
time_duration = algConfig['wind_speed_fault']['time_duration']
resample_interval = algConfig['wind_speed_fault']['resample_interval']
error_data_time_duration = algConfig['wind_speed_fault']['error_data_time_duration']
need_all_turbines = algConfig['wind_speed_fault']['need_all_turbines']
store_file = algConfig['wind_speed_fault']['store_file']

def wash_data(pn_data: DataFrame, ratedPower):    
    temp_data = pn_data[ai_points + di_points + general_points]
    '''
    剔除限功率数据 FIXME ？？？
    '''
    temp_data = wash_data_for_train(temp_data, ratedPower)
    if temp_data[temp_data['clear'] == 2].shape[0] > 0:
        return temp_data, ''
    else:
        return pd.DataFrame(), '没有干净数据'


def predict_result(pn_data: DataFrame):
    return pn_data['WNAC.WindSpeed','WGEN.GenActivePW']


#额定功率异常
def Pwrat_Rate_loss(data,Pwrat_Rate):
    temp = data[data['clear']<=8]
    if ((np.nanmean(temp.loc[(temp['WROT.Blade1Position']>=5),('WGEN.GenActivePW')].nlargest(10))<0.95*Pwrat_Rate)):
        return True
    else:
        False

async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    # FIXME 刨除限功率运行数据
    # 理论功率曲线
    # function = joblib.load('model/speed_power.model')
    function = model_util.load_model(config.Wind_Farm, 'speed_power', assetId, 'speed_power')
    # pn_data['theory_power'] = function(pn_data['WNAC.WindSpeed'])
    Pwrat_Rate =  get_data.Pwrat_Rate
    turbine_err_all = {}
    turbine_err_all['power_rate_err'] = 0


    #额定功率异常
    # if Pwrat_Rate_loss(pn_data,Pwrat_Rate):
    #     turbine_err_all['power_rate_err'] = 1
    pn_data = pn_data[pn_data['WTUR.TurbineUnionSts']!=80]
    if pn_data.shape[0] < 5:
        turbine_err_all['power_rate_err'] = 1
    if turbine_err_all['power_rate_err'] == 0:
        pn_data = pn_data[pn_data["clear"]<=5]
        #风速排序
        pn_data_sorted = pn_data.sort_values(by='WNAC.WindSpeed', ascending=True)
        #归一化数据
        # scalorWS = preprocessing.MinMaxScaler()
        # pn_data_sorted['wsTransformed'] = scalorWS.fit_transform(pn_data_sorted[['WNAC.WindSpeed']])
        # scalorPW = preprocessing.MinMaxScaler()
        # pn_data_sorted['pwTransformed'] = scalorPW.fit_transform(pn_data_sorted[['WGEN.GenActivePW']])
        # pn_data_sorted['theory_power_transformed'] = function(pn_data_sorted['wsTransformed'])
        # #逆变换
        # pn_data_sorted['theory_power'] = scalorPW.inverse_transform(pn_data_sorted[['theory_power_transformed']])

        pn_data_sorted['theory_power'] = function(pn_data_sorted['WNAC.WindSpeed'])

        error = model_util.load_model(config.Wind_Farm, 'speed_power', assetId, 'error')
        
        # 阈值判断
        pn_data_sorted['result'] = pn_data_sorted['WGEN.GenActivePW'] - pn_data_sorted['theory_power'] > 3*error

        #数据展示
        # x = [str(tick) for tick in list(pn_data.index)]
        x = [str(round(tick,4)) for tick in list(pn_data_sorted['WNAC.WindSpeed'])]
        y1 = [str(round(num,4)) for num in list(pn_data_sorted['WGEN.GenActivePW'])]
        y2 = [str(round(num,4)) for num in list(pn_data_sorted['theory_power'])]
        # y3 = [str(round(num,4)) for num in list(np.abs(pn_data['theory_power'] - pn_data['WGEN.GenActivePW']) / pn_data['theory_power'])]
        y3 = [str(round(num,4)) for num in list(pn_data_sorted['theory_power']+3*error)]
        # y4 = [str(round(num,4)) for num in list(pn_data_sorted['theory_power']-1*error)]
        data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
        data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
        data3 = pd.DataFrame({'x': x, 'y': y3}).to_dict('records')
        # data4 = pd.DataFrame({'x': x, 'y': y4}).to_dict('records')
        interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
        interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
        Figs = []
        curves1 = []
        curves2 = []
        curves1.append(DisplayResultXY('1', '数据', '#00FF00', '', data1))#{'type':'0', 'name': '数据', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data1}
        curves1.append(DisplayResultXY('0', '理论', '#FFFF00', 'Solid', data2))#{'type':'0', 'name': '理论', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data2}
        curves1.append(DisplayResultXY('0', '上限', '#888888', 'Dash', data3))#{'type':'0', 'name': '偏差幅度百分比', "abscissaUnit": interval_unit, "ordinateUnit": "", 'xyData': data3}
        # curves1.append(DisplayResultXY('0', '下限', data4))#{'type':'0', 'name': '偏差幅度百分比', "abscissaUnit": interval_unit, "ordinateUnit": "", 'xyData': data3}
        
        # result = DisplayResultXY(str(pn_data.index.min()), str(pn_data.index.max()), str(interval_value), '角度', curves)
        result1 = DisplayFigures(xUnit="风速[m/s]", yUnit="功率[kw]", time=0, multiDimensionDataxy=curves1)
        Figs.append(result1)
        # result2 = DisplayFigures(xUnit=interval_unit, yUnit="m/s", time=0, multiDimensionDataxy=curves2)
        # Figs.append(result2)

        statementException = f'根据风速功率曲线，存在当前功率高于理论值, 超过3倍标准差'
        statementNormal = f'根据风速功率曲线，当前功率未超过理论值的3倍标准差'
        pn_data_sorted.sort_index(inplace=True)
        # 生成告警
        data, statement, alarming =  alarm.generateAlarm(name,'wind_speed_fault','WGEN.GenActivePW', pn_data_sorted, error_data_time_duration, resample_interval, assetId, 3*error, statementException, statementNormal, idMaps)
        return data, statement, Figs, 0,1 # alarming, 0
    # 生成告警
    data, statement, alarming =  alarm.generateBaseAlarm(name,'wind_speed_fault','WGEN.GenActivePW', pn_data, False, assetId, 1, '额定功率异常,可能风机处在限功率发电中,无法判断风速仪故障', idMaps)
    Figs = []
    return data, statement, Figs, 0,1


def judge(pn_data: DataFrame):
    """
    风速仪故障
    :param pn_data: dataframe
    :return:
    """
    result_value = []

    for index, row in pn_data.iterrows():
        c51 = float(row.get("WGEN.GenActivePW"))
        c66 = float(row.get("WNAC.WindSpeed"))

        if c66 <= 7 and c51 >= 1000:
            result_value.append(True)
        else:
            result_value.append(False)

    pn_data['result'] = result_value
    return alarm.generateAlarm(pn_data, error_data_time_duration)
