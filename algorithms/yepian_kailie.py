from pandas import DataFrame
from alarms import alarm
import numpy as np
from utils.display_util import DisplayResultXY, DisplayFigures
import pandas as pd
import utils.time_util as time_util
import asyncio
from datetime import datetime as datetime
from configs.config import algConfig


name = algConfig['yepian_kailie']["name"]#'叶尖开裂、叶片外衣裂开'
# 把所需测点定义到每个算法里
ai_points = algConfig['yepian_kailie']["ai_points"]
ai_rename = algConfig['yepian_kailie']["ai_rename"]
di_points = algConfig['yepian_kailie']["di_points"]
general_points = algConfig['yepian_kailie']["general_points"]
private_points = algConfig['yepian_kailie']["private_points"]
time_duration = algConfig['yepian_kailie']["time_duration"]
resample_interval = algConfig['yepian_kailie']["resample_interval"]
error_data_time_duration = algConfig['yepian_kailie']["error_data_time_duration"]
need_all_turbines = algConfig['yepian_kailie']["need_all_turbines"]
store_file = algConfig['yepian_kailie']["store_file"]
# modelId = "SPIC_ZD_CMS_Blade"




def wash_data(pn_data: DataFrame, ratedPower):
    temp_data = pn_data[pn_data["BLD_DEFECTZ_FACTOR"]!=0]
    if temp_data.shape[0] > 0.1*pn_data["BLD_DEFECTZ_FACTOR"].shape[0]:
        return pn_data, ''
    else:
        return pd.DataFrame(), f'BLD_DEFECTZ_FACTOR的非零数据量小于{int(0.1*pn_data["BLD_DEFECTZ_FACTOR"].shape[0])}'


def predict_result(pn_data: DataFrame):
    # 计算全场平均温度
    mean_temperature = pn_data[pn_data["BLD_DEFECTZ_FACTOR"]!=0]
    return mean_temperature["BLD_DEFECTZ_FACTOR"]
    
    
async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    fn_data = predict_result(pn_data)
    rms = np.sqrt(np.average(fn_data**2))
    thre_value = 0.38

    #数据展示
    x = [str(tick) for tick in list(pn_data.index)]
    x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
    x = [int(tick.timestamp()*1000) for tick in x]
    y1 = [str(round(num,4)) for num in list(pn_data["BLD_DEFECTZ_FACTOR"])]
    y2 = [str(round(num,4)) for num in [rms]*pn_data["BLD_DEFECTZ_FACTOR"].shape[0]]
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
    interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
    interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
    Figs = []
    curves1 = []
    curves1.append(DisplayResultXY('0', '缺陷系数', '#FFFF00', 'Solid', data1))#{'type':'0', 'name': '缺陷系数', "abscissaUnit": interval_unit, "ordinateUnit": "", 'xyData': data1}
    curves1.append(DisplayResultXY('0', '均方根', '#00FF00', 'Solid', data2))#{'type':'0', 'name': '均方根', "abscissaUnit": interval_unit, "ordinateUnit": "", 'xyData': data2}
    
    # result = DisplayResultXY(str(pn_data.index.min()), str(pn_data.index.max()), str(interval_value), '角度', curves)
    result1 = DisplayFigures(xUnit=interval_unit, yUnit="缺陷系数", time=1, multiDimensionDataxy=curves1)
    Figs.append(result1)
    
    # 生成告警
    # if rms == 0:
    #     data, statement =  alarm.generateBaseAlarm(name, '去除0数据点后数据量不足原数据量10%')
    #     data = pd.DataFrame #pd.DataFrame({'error':[1,2,3]})
    # else:
    if rms > thre_value:
        data, statement, alarming =  alarm.generateBaseAlarm(name,'yepian_kailie','BLD_DEFECTZ_FACTOR',fn_data,True,assetId,thre_value, f'均方根大于{thre_value}', idMaps)
        data = fn_data
    else:
        data, statement, alarming =  alarm.generateBaseAlarm(name,'yepian_kailie','BLD_DEFECTZ_FACTOR',fn_data,False,assetId,thre_value, f'均方根小于等于{thre_value}', idMaps)
        data = pd.DataFrame()
        alarming = 0

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