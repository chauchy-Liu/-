from pandas import DataFrame
from alarms import alarm
import numpy as np
from matplotlib import pyplot as plt
# from commonModel.DartsModel import TFTAnalyse, CreateTFTModel, MeanOverTime
# from darts import TimeSeries
import utils.time_util as time_util
import pandas as pd
import os
from utils.display_util import DisplayResultXY, DisplayFigures
from scipy.stats import linregress
import asyncio
from datetime import datetime as datetime
from configs.config import algConfig

name = algConfig['chuandonglian']['name']#'风机基础不均匀沉降'
# 把所需测点定义到每个算法里
ai_points = algConfig['chuandonglian']['ai_points']
ai_rename = algConfig['chuandonglian']['ai_rename']
di_points = algConfig['chuandonglian']['di_points']
general_points = algConfig['chuandonglian']['general_points']
private_points = algConfig['chuandonglian']['private_points']
# modelId = algConfig['tatong_qingjiao']['name']
time_duration = algConfig['chuandonglian']['time_duration']
resample_interval = algConfig['chuandonglian']['resample_interval']
error_data_time_duration = algConfig['chuandonglian']['error_data_time_duration']
need_all_turbines = algConfig['chuandonglian']['need_all_turbines']
store_file = algConfig['tatong_qingjiao']['store_file']
timeUnit = resample_interval #'10T' #10minute: 10T,  1day:1D, 1quater:1Q

def wash_data(pn_data: DataFrame, ratedPower):
    private_points_ = []
    for modelKey, pointValue in private_points.items():
        private_points_ += pointValue
    temp_data = pn_data[private_points_+ai_points]
    # 清空nan数据
    temp_data = temp_data.dropna(how='all', subset=private_points_+ai_points)
    temp_data = temp_data[temp_data["WGEN.GenActivePW"]>=30]
    if not temp_data.empty:
        return temp_data, ''
    else:
        return temp_data, f'{private_points_+ai_points}清洗低于30的功率值后没有数据'


def predict_result(pn_data: DataFrame):

    return pn_data[['TOAT', 'TOTT']].dropna()
def ProcessSingleMeasurement(data, final_df, measureName, assetId, threshold, alarming, statement, Figs):
    '''
        data:告警数据
        final_df:输入数据
    '''
    warning = 0 #预警
    if data.empty == False:
    #     final_df['result'] = final_df['result'].astype('bool')
    #     average_level = final_df[final_df['result']==True].mean()
    #     for key, value in threshold["gaojing"]["threshold"].items():
    #         if average_level >= value:
    #             alarming = key
    #         else:
    #             break
        # 展示数据
        x = [str(tick) for tick in list(final_df.index)]
        x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
        x = [int(tick.timestamp()*1000) for tick in x]
        y1 = [str(round(num,4)) for num in list(final_df[measureName])]
        data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
        if measureName in threshold["gaojing"]["threshold"]:
            data2 = pd.DataFrame({'x': [x[0], x[-1]], 'y': [str(threshold["gaojing"]["threshold"][measureName]["10"]), str(threshold["gaojing"]["threshold"][measureName]["10"])]}).to_dict('records')
        else:
            data2 = pd.DataFrame({'x': [x[0], x[-1]], 'y': [str(threshold["gaojing"]["threshold"]["10"]), str(threshold["gaojing"]["threshold"]["10"])]}).to_dict('records')

        interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
        interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()

        # Figs = []
        curves1 = []
        curves1.append(DisplayResultXY('0', measureName, '#00FF00', 'Solid', data1))#{'type':'0', 'name':'倾角', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data1}
        curves1.append(DisplayResultXY('0', '告警线', '#FF0000', 'Solid', data2))#{'type':'0', 'name': '告警线', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data2}

        result1 = DisplayFigures(xUnit=interval_unit, yUnit="振动有效值", time=1, multiDimensionDataxy=curves1)#DisplayResultXY(str(final_df.index.min()), str(final_df.index.max()), str(interval_value), '角度', curves)
        Figs.append(result1)
        return data, statement, Figs, int(alarming), int(warning)
    elif data.empty == True and ("minute" not in threshold["executeTimeValue"] and  "hour" not in threshold["executeTimeValue"]):
        data1, data2, statement, warning, startTime, endTime = alarm.generateAlarmTrend(name, final_df, measureName, threshold, resample_interval, assetId)
        # 展示数据
        interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
        interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()

        # Figs = []
        curves1 = []
        curves1.append(DisplayResultXY('0', measureName, '#00FF00', 'Solid', data1))#{'type':'0', 'name':'倾角', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data1}
        curves1.append(DisplayResultXY('0', f'{measureName}趋势', '#FFFF00', 'Solid', data2))#{'type':'0', 'name': '告警线', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data2}

        result1 = DisplayFigures(xUnit=interval_unit, yUnit="振动有效值", time=1, multiDimensionDataxy=curves1)#DisplayResultXY(str(final_df.index.min()), str(final_df.index.max()), str(interval_value), '角度', curves)
        Figs.append(result1)
        if warning == 0:
            return pd.DataFrame(), statement, Figs, int(alarming), int(warning)
        else:
            return final_df, statement, Figs, int(alarming), int(warning)
    else:
        # 展示数据
        x = [str(tick) for tick in list(final_df.index)]
        x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
        x = [int(tick.timestamp()*1000) for tick in x]
        y1 = [str(round(num,4)) for num in list(final_df[measureName])]
        data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
        if measureName in threshold["gaojing"]["threshold"]:
            data2 = pd.DataFrame({'x': [x[0], x[-1]], 'y': [str(threshold["gaojing"]["threshold"][measureName]["10"]), str(threshold["gaojing"]["threshold"][measureName]["10"])]}).to_dict('records')
        else:
            data2 = pd.DataFrame({'x': [x[0], x[-1]], 'y': [str(threshold["gaojing"]["threshold"]["10"]), str(threshold["gaojing"]["threshold"]["10"])]}).to_dict('records')

        interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
        interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()

        # Figs = []
        curves1 = []
        curves1.append(DisplayResultXY('0', measureName, '#FFFF00', 'Solid', data1))#{'type':'0', 'name':'倾角', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data1}
        curves1.append(DisplayResultXY('0', '告警线', '#FF0000', 'Solid', data2))#{'type':'0', 'name': '告警线', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data2}

        result1 = DisplayFigures(xUnit=interval_unit, yUnit="振动有效值", time=1, multiDimensionDataxy=curves1)#DisplayResultXY(str(final_df.index.min()), str(final_df.index.max()), str(interval_value), '角度', curves)
        Figs.append(result1)
        return pd.DataFrame(), statement, Figs, int(alarming), int(warning)
    
async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    final_df = pn_data
    
    #预警、告警类型及其等级
    alarming = 0 #告警
    warning = 0 #预警
    measureName = ['GBXHSSA1_RMS','GENDER1_RMS', 'MBA1_RMS']
    # 生成告警
    if set(measureName).issubset(set(threshold["gaojing"]["threshold"].keys())) and not isinstance(measureName, str): #多测点
        data_fn = pd.DataFrame()
        statement_fn = ''
        statementException = ''
        statementNormal = ''
        alarming_fn = 0
        warning_fn = 0
        Figs = []
        for keyMeasure in measureName:
            #告警
            statementException = f'{keyMeasure}超过阈值{threshold["gaojing"]["threshold"][keyMeasure]["10"]}，'
            statementNormal = f'{keyMeasure}未超过阈值{threshold["gaojing"]["threshold"][keyMeasure]["10"]}, '
            if 'result' in list(final_df.columns):
                final_df = final_df.drop('result', axis=1)
            final_df['result'] = final_df[keyMeasure] > threshold["gaojing"]["threshold"][keyMeasure]["10"]
            data, statement, alarming =  alarm.generateAlarm(name, 'chuandonglian', keyMeasure,final_df, error_data_time_duration, resample_interval, assetId, threshold, statementException, statementNormal, idMaps)
            data_tmp, statement_tmp, Figs, alarming_tmp, warning_tmp = ProcessSingleMeasurement(data, final_df, keyMeasure, assetId, threshold, alarming, statement, Figs)
            data_fn = pd.concat([data_fn, data_tmp])
            statement_fn += statement_tmp + '; '
            if alarming_fn < alarming_tmp:
                alarming_fn = alarming_tmp
            if warning_fn < warning_tmp:
                warning_fn = warning_tmp
        return data_fn, statement_fn, Figs, alarming_fn, warning_fn
    else: #单测点
        #告警
        statementException = f'有效振动超过阈值{threshold["gaojing"]["threshold"]["10"]}，'
        statementNormal = f'有效振动未超过阈值{threshold["gaojing"]["threshold"]["10"]}'
        Figs = [] #存放每一张图
        final_df['result'] = final_df[measureName] > threshold["gaojing"]["threshold"]["10"]
        data, statement, alarming =  alarm.generateAlarm(name, 'chuandonglian', 'GBXHSSA1_RMS',final_df, error_data_time_duration, resample_interval, assetId, threshold, statementException, statementNormal, idMaps)
        data_fn, statement, Figs, alarming, warning = ProcessSingleMeasurement(data, final_df, measureName, assetId, threshold, alarming, statement, Figs)
        return data_fn, statement, Figs, alarming, warning

# def judge_model2(pn_data: DataFrame, assetId, threshold):
#     # plt.figure()
#     # plt.plot(pn_data['TOAT'])
#     # plt.savefig('TOAT.pdf')
#     # plt.close()

#     final_df = predict_result(pn_data)

#     #取平均
#     series = MeanOverTime(final_df['TOAT'], timeUnit)
#     # #归一化
#     # trainNormal, valNormal, seriesNormal, seriesTransformer = NormalizeSeries(series, trainCutOff)
#     # #协变量
#     # trainCovariate, valCovariate, seiresCovariate, covariateTransformer = CreateCovariates(seriesNormal, trainCutOff)

#     #创建模型并进行拟合训练
#     tftModel = CreateTFTModel(series, input_chunk_length = input_chunk_length, out_chunck_length = out_chunck_length, futureCovariates=futureCovariates, numEpoch=numEpoch, cutOff=trainCutOff, timeUnit=resample_interval) 
#     interval_value, interval_unit = time_util.split_time_delta(timeUnit)
#     freqValue = (timeSampleNum+timeSampleNum)*int(interval_value)
#     date_rng = pd.date_range(start=series.time_index[input_chunk_length], end=series.time_index[-1], freq=str(freqValue)+interval_unit)

#     #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#     workPath = os.getcwd()
#     #预测
#     # tftModel.Predict(forcastHorizon=forcastHorizon)
#     #评估模型
#     # tftModel.EvaluatePredict()
#     #作图
#     # tftModel.PlotPredict(os.path.join(workPath,'result','predict', assetId))

#     #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#     #历史回溯
#     startTime_ = series.time_index[input_chunk_length] #series.time_index[series.time_index >= startTime][0]
#     # endTime_ = series.time_index[series.time_index <= endTime][-1]
#     tftModel.BackTest(startTime_, forcastHorizon=forcastHorizon, last_points_only=False)
#     #评估模型并作图
#     # tftModel.EvaluateBackTest(forcastHorizon, startTime_, os.path.join(workPath,'result','BackTest', assetId))

#     #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#     #预警
#     frontValueList = []
#     backValueList = []
#     centerDistanceList = []
#     timeRangeList = []
#     meanDeviationList = []
#     iouList = []
#     disRateList = []
#     for countIndex, time_index in enumerate(date_rng):
#         startTime = time_index #+ pd.Timedelta(timeSampleNum//2, unit=timeUnit)
#         endTime = time_index + pd.Timedelta(timeSampleNum*4*int(interval_value), unit=time_util.__timedelta_resample_unit_dict[interval_unit])#+ pd.Timedelta(timeSampleNum//2, unit=timeUnit)
#         # if countIndex == 0:
#         #     timeUnitSize = len(final_df.loc[startTime:endTime])
#         frontValue, backValue, centerDistance, timeRange, meanDeviation, iou, distanceRate = TFTAnalyse(series, tftModel, timeUnit, startTime, endTime, timeSampleNum=timeSampleNum, forcastHorizon=forcastHorizon,highQuantile=0.9, lowQuantile=0.1, iouThreshold=0.5, distanceThreshold=0.5) #startTime和endTime间隔>(timeSampleNum+timeSampleNum)*timeUnit
#         counts = 0
#         if centerDistance != 0:
#             if tftModel.backTestSeries.time_index[-1] > endTime:
#                 final_df.loc[startTime:endTime,'result'] = True
#                 counts = final_df.loc[startTime:endTime,'result'].iloc[:freqValue].shape[0]
#             else:
#                 final_df.loc[startTime:,'result'] = True
#                 counts = final_df.loc[startTime:endTime,'result'].iloc[:freqValue].shape[0]
#         else:
#             if tftModel.backTestSeries.time_index[-1] > endTime:
#                 final_df.loc[startTime:endTime,'result'] = False
#                 counts = final_df.loc[startTime:endTime,'result'].iloc[:freqValue].shape[0]
#             else:
#                 final_df.loc[startTime:,'result'] = False
#                 counts = final_df.loc[startTime:endTime,'result'].iloc[:freqValue].shape[0]
#             # final_df.loc[startTime:endTime,'result'] = False
        
#         frontValueList.append(frontValue)
#         backValueList.append(backValue)
#         iouList += [float(iou)]*counts
#         disRateList += [float(distanceRate)]*counts
#         centerDistanceList.append(centerDistance)
#         timeRangeList.append(timeRange)
#         meanDeviationList.append(meanDeviation)

#     #数据展示
#     # tolist显示float类型，list()显示numpy.float类型
    
#     historyOriginSeries = tftModel.backTestSeries
#     high_curve = historyOriginSeries.quantile(0.9).univariate_values().reshape(-1).tolist() #series.iloc[:input_chunk_length].tolist()+
#     low_curve = historyOriginSeries.quantile(0.1).univariate_values().reshape(-1).tolist() #series.iloc[:input_chunk_length].tolist()+
#     series_new = series.univariate_values().reshape(-1).tolist()[input_chunk_length:]
#     x = list(series.time_index[input_chunk_length:])
#     y1 = [str(round(num,4)) for num in series_new]
#     y2 = [str(round(num,4)) for num in high_curve[:len(series_new)]]
#     y3 = [str(round(num,4)) for num in low_curve[:len(series_new)]]
#     y4 = [str(round(num,4)) for num in iouList[:len(series_new)]]
#     y5 = [str(round(num,4)) for num in disRateList[:len(series_new)]]
#     data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
#     data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
#     data3 = pd.DataFrame({'x': x, 'y': y3}).to_dict('records')
#     data4 = pd.DataFrame({'x': x, 'y': y4}).to_dict('records')
#     data5 = pd.DataFrame({'x': x, 'y': y5}).to_dict('records')
#     interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
#     interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
#     curves = []
#     curves.append({'type':'0', 'name': '角度', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data1})
#     curves.append({'type':'0', 'name': '角度上限', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data2})
#     curves.append({'type':'0', 'name': '角度下限', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data3})
#     curves.append({'type':'0', 'name': 'iou', "abscissaUnit": interval_unit, "ordinateUnit": "", 'xyData': data4})
#     curves.append({'type':'0', 'name': '中心距波动比', "abscissaUnit": interval_unit, "ordinateUnit": "", 'xyData': data5})
    
#     result = DisplayResultXY(series.time_index[input_chunk_length], series.time_index.max(), str(interval_value), '角度', curves)

#     statementException = f'跟据当前角度变化, 存在相邻时间窗口波动中心距占比超高{0.5}倍波动区间且相邻波动区间IOU小于{0.5}'
#     statementNormal = f'跟据当前角度变化, 不存在相邻时间窗口波动中心距占比超高{0.5}倍波动区间且相邻波动区间IOU小于{0.5}'
#     # 生成告警
#     final_df = final_df[series.time_index[input_chunk_length]:]
#     data, statement =  alarm.generateAlarm(name, final_df, error_data_time_duration, resample_interval, assetId, statementException, statementNormal)
#     return data, statement, result
    

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


# if len(threshold) == 0:
    #     threshold = {
    #     "levelline": 10,
    #     "executeTime":{
    #         "minute":{
    #             "duration": "1h",
    #             "kelidu": "1m",
    #             "continue": "3m"
    #         },
    #         "hour":{
    #             "duration": "5D",
    #             "kelidu": "1h",
    #             "continue": "3h"
    #         },
    #         "halfday":{
    #             "duration": "15D",
    #             "kelidu": "4h",
    #             "continue": "3h"
    #         },
    #         "day":{
    #             "duration": "90D",
    #             "kelidu": "1D",
    #             "continue": "3D"
    #         }
    #     },
    #     "yujing":{
    #         "threshold": 0.3
    #     },
    #     "gaojing":{
    #         "threshold": {
    #             "10": 0.3,
    #             "11": 0.4,
    #             "12": 0.5,
    #             "13": 0.6,
    #             "14": 0.7,
    #             "15": 0.8,
    #             "16": 0.9,
    #             "17": 1
    #         }
    #     }
    # }