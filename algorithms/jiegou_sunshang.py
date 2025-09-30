from pandas import DataFrame
from alarms import alarm
import numpy as np
from utils.display_util import DisplayResultXY, DisplayFigures
import utils.time_util as time_util
import pandas as pd
from utils import model_util
from data.get_data import wash_data_for_train
from configs import config
import asyncio
from datetime import datetime as datetime
from configs.config import algConfig

name = algConfig['jiegou_sunshang']['name']#'塔筒结构损伤'
# 把所需测点定义到每个算法里
ai_points = algConfig['jiegou_sunshang']['ai_points']
ai_rename = algConfig['jiegou_sunshang']['ai_rename']
di_points = algConfig['jiegou_sunshang']['di_points']
general_points = algConfig['jiegou_sunshang']['general_points']
private_points = algConfig['jiegou_sunshang']['private_points']
time_duration = algConfig['jiegou_sunshang']['time_duration']
resample_interval = algConfig['jiegou_sunshang']['resample_interval']
error_data_time_duration = algConfig['jiegou_sunshang']['error_data_time_duration']
need_all_turbines = algConfig['jiegou_sunshang']['need_all_turbines']
store_file = algConfig['jiegou_sunshang']['store_file']

def wash_data(pn_data: DataFrame, ratedPower):
    private_points_ = []
    for modelKey, pointValue in private_points.items():
        private_points_ += pointValue
    temp_data = pn_data[ai_points + di_points+general_points + private_points_]
    # final_df = wash_data_for_train(temp_data, ratedPower)
    # final_df = final_df[final_df['clear'] == 2]
    final_df = temp_data[temp_data['WGEN.GenActivePW'] > 30]
    if final_df.shape[0] > 0:
        return final_df, ''   
    else:
        return pd.DataFrame(), '清洗数据后干净数据量为0'   


def predict_result(pn_data: DataFrame, assetId):
    # 处理空数据
    pn_data.fillna(method='ffill', axis=0, inplace=True)
    pn_data.fillna(method='bfill', axis=0, inplace=True)
    # 加载模型
    model = model_util.load_model(config.Wind_Farm, 'jiegou_sunshang', assetId,'jiegou_sunshang')
    # 预测健康数据 并判断是否告警
    y_predict = model.predict(pn_data[ai_points])
    error = model_util.load_model(config.Wind_Farm, 'jiegou_sunshang', assetId,'error')
    return y_predict, error


async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    #预警、告警类型及其等级
    alarming = 0 #告警
    warning = 0 #预警
    measureName = 'Vibration_Strength'
    #告警
    statementException = f'振动强度超过阈值{threshold["gaojing"]["threshold"]["10"]}，'
    statementNormal = f'振动强度未超过阈值{threshold["gaojing"]["threshold"]["10"]}'
    # 生成告警
    pn_data['result'] = pn_data[measureName] > threshold["gaojing"]["threshold"]["10"]
    pn_data = pn_data.sort_index()
    data, statement, alarming =  alarm.generateAlarm(name,'jiegou_sunshang',measureName, pn_data, error_data_time_duration, resample_interval, assetId, threshold, statementException, statementNormal, idMaps)
    if data.empty == False:
        # 展示数据
        x = [str(tick) for tick in list(pn_data.index)]
        x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
        x = [int(tick.timestamp()*1000) for tick in x]
        y1 = [str(round(num,4)) for num in list(pn_data[measureName])]
        data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
        data2 = pd.DataFrame({'x': [x[0], x[-1]], 'y': [str(threshold["gaojing"]["threshold"]["10"]), str(threshold["gaojing"]["threshold"]["10"])]}).to_dict('records')

        interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
        interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()

        Figs = []
        curves1 = []
        curves1.append(DisplayResultXY('0', '振动强度', '#FFFF00', 'Solid', data1))#{'type':'0', 'name':'倾角', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data1}
        curves1.append(DisplayResultXY('0', '告警线', '#FF0000', 'Solid', data2))#{'type':'0', 'name': '告警线', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data2}

        result1 = DisplayFigures(xUnit=interval_unit, yUnit="强度", time=1, multiDimensionDataxy=curves1)#DisplayResultXY(str(final_df.index.min()), str(final_df.index.max()), str(interval_value), '角度', curves)
        Figs.append(result1)
        return data, statement, Figs, int(alarming), int(warning)
    elif data.empty == True and ("minute" not in threshold["executeTimeValue"] and  "hour" not in threshold["executeTimeValue"]):
        # 模型推理
        pn_data['predict'], error = predict_result(pn_data, assetId)
        # 阈值判断
        # pn_data['result'] = np.abs(pn_data[measureName] - pn_data['predict']) > 2*error # | (np.abs(pn_data[measureName] - pn_data['predict']) < -3*error)
        pn_data['result'] = pn_data[measureName] - pn_data['predict'] > 2*error # | (np.abs(pn_data[measureName] - pn_data['predict']) < -3*error)
        #数据展示
        x = [str(tick) for tick in list(pn_data.index)]
        x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
        x = [int(tick.timestamp()*1000) for tick in x]
        y1 = [str(round(num,4)) for num in list(pn_data['predict'])]
        y2 = [str(round(num,4)) for num in list(pn_data[measureName])]
        y3 = [str(round(num,4)) for num in list(pn_data['predict']+2*error)]
        # y4 = [str(round(num,4)) for num in list(pn_data['predict']-2*error)]
        data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
        data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
        data3 = pd.DataFrame({'x': x, 'y': y3}).to_dict('records')
        # data4 = pd.DataFrame({'x': x, 'y': y4}).to_dict('records')
        interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
        interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
        Figs = []
        curves1 = []
        curves1.append(DisplayResultXY('0', '预测晃度', '#FFFF00', 'Solid', data1))#{'type':'0', 'name': '预测温度', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'xyData': data1}
        curves1.append(DisplayResultXY('0', '实际晃度', '#00FF00', 'Solid', data2))#{'type':'0', 'name': '实际温度', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'xyData': data2}
        curves1.append(DisplayResultXY('0', '误差上限', '#888888', 'Dash', data3))#{'type':'0', 'name': '实际温度', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'xyData': data2}
        # curves1.append(DisplayResultXY('0', '误差下限', '#888888', 'Dash', data4))#{'type':'0', 'name': '实际温度', "abscissaUnit": interval_unit, "ordinateUnit": "°C", 'xyData': data2}
        
        result1 = DisplayFigures(xUnit=interval_unit, yUnit="强度", time=1, multiDimensionDataxy=curves1)#DisplayResultXY(str(pn_data.index.min()), str(pn_data.index.max()), str(interval_value), '温度', curves)
        Figs.append(result1)

        statementException = f'实际晃度大于历史拟合晃度2倍标准差上限'
        statementNormal = f'实际晃度小于等于历史拟合晃度2倍标准差上限'
        # 生成告警
        data, statement, alarming = alarm.generateAlarm(name,'jiegou_sunshang',measureName, pn_data, error_data_time_duration, resample_interval, assetId, 2*error, statementException, statementNormal, idMaps)
        return data, statement, Figs, 0,1 # alarming, 0
    else:
        # 展示数据
        x = [str(tick) for tick in list(pn_data.index)]
        x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
        x = [int(tick.timestamp()*1000) for tick in x]
        y1 = [str(round(num,4)) for num in list(pn_data[measureName])]
        data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
        data2 = pd.DataFrame({'x': [x[0], x[-1]], 'y': [str(threshold["gaojing"]["threshold"]["10"]), str(threshold["gaojing"]["threshold"]["10"])]}).to_dict('records')

        interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
        interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()

        Figs = []
        curves1 = []
        curves1.append(DisplayResultXY('0', '振动强度', '#FFFF00', 'Solid', data1))#{'type':'0', 'name':'倾角', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data1}
        curves1.append(DisplayResultXY('0', '告警线', '#FF0000', 'Solid', data2))#{'type':'0', 'name': '告警线', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data2}

        result1 = DisplayFigures(xUnit=interval_unit, yUnit="强度", time=1, multiDimensionDataxy=curves1)#DisplayResultXY(str(final_df.index.min()), str(final_df.index.max()), str(interval_value), '角度', curves)
        Figs.append(result1)
        return data, statement, Figs, int(alarming), int(warning)

   

 
# # 生成告警
# data, statement =  alarm.generateBaseAlarm(name, '正常运行')
# return data, statement, None, 1, 0


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