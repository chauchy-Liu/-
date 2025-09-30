from pandas import DataFrame
from alarms import alarm
import numpy as np
from matplotlib import pyplot as plt
# from commonModel.DartsModel import TFTAnalyse, CreateTFTModel, MeanOverTime
# from darts import TimeSeries
import utils.time_util as time_util
import pandas as pd
from utils.display_util import DisplayResultXY, DisplayFigures
import asyncio
from datetime import datetime as datetime
from configs.config import algConfig
from copy import deepcopy

name = deepcopy(algConfig['luoshuansongdong']['name'])#'风机螺栓松动'
# 把所需测点定义到每个算法里
ai_points = deepcopy(algConfig['luoshuansongdong']['ai_points'])
ai_rename = deepcopy(algConfig['luoshuansongdong']['ai_rename'])
di_points = deepcopy(algConfig['luoshuansongdong']['di_points'])
general_points = deepcopy(algConfig['luoshuansongdong']['general_points'])
private_points = deepcopy(algConfig['luoshuansongdong']['private_points'])
# modelId = algConfig['luoshuansongdong']['name']
time_duration = deepcopy(algConfig['luoshuansongdong']['time_duration'])
resample_interval = deepcopy(algConfig['luoshuansongdong']['resample_interval'])
error_data_time_duration = deepcopy(algConfig['luoshuansongdong']['error_data_time_duration'])
horizonTime = deepcopy(algConfig['luoshuansongdong']['horizonTime'])
need_all_turbines = deepcopy(algConfig['luoshuansongdong']['need_all_turbines'])
input_chunk_length = deepcopy(algConfig['luoshuansongdong']['input_chunk_length'])
out_chunck_length = deepcopy(algConfig['luoshuansongdong']['out_chunck_length'])
futureCovariates = deepcopy(algConfig['luoshuansongdong']['futureCovariates'])
numEpoch = deepcopy(algConfig['luoshuansongdong']['numEpoch'])
trainCutOff = deepcopy(algConfig['luoshuansongdong']['trainCutOff'])
timeSampleNum = deepcopy(algConfig['luoshuansongdong']['timeSampleNum'])
store_file = deepcopy(algConfig['luoshuansongdong']['store_file'])
timeUnit = deepcopy(resample_interval) #'10T' #10minute: 10T,  1day:1D, 1quater:1Q
forcastHorizon = deepcopy(out_chunck_length)

def wash_data(pn_data: DataFrame, ratedPower, algorithm_config):
    private_points_ = []
    for modelKey, pointValue in private_points.items():
        for value_elem in  pointValue:
            if value_elem in pn_data.columns.to_list():
                private_points_.append(value_elem)
    # #剔除不符合条件的测点
    # if time_duration != algConfig['luoshuansongdong']['changeDateRange']:
    #     private_points_ = [i for i in private_points_  if i not in algorithm_config['changeMeasurePointQueue'][algorithm_config['param_turbine_num'][-1]] and i in pn_data.columns.to_list()]
    # elif time_duration == algConfig['luoshuansongdong']['changeDateRange']:
    #     private_points_ = [i for i in private_points_  if i in algorithm_config['changeMeasurePointQueue'][algorithm_config['param_turbine_num'][-1]] and i in pn_data.columns.to_list()]
    temp_data = pn_data[private_points_].abs()
    # 清空nan数据
    temp_data = temp_data.ffill()
    temp_data = temp_data.bfill()
    temp_data = temp_data.dropna(how='all', axis=1)
    if not temp_data.empty:
        return temp_data, ''
    else:
        return pd.DataFrame(), f'{private_points_}数据没有,或者小于10个数据点'


def predict_result(pn_data: DataFrame, algorithm_config):
    private_points_ = []
    for modelKey, pointValue in private_points.items():
        for value_elem in  pointValue:
            if value_elem in pn_data.columns.to_list():
                private_points_.append(value_elem)
    # for modelKey, pointValue in private_points.items():
    #     private_points_ += pointValue
    ## 剔除不符合条件的测点
    # if time_duration != algConfig['luoshuansongdong']['changeDateRange']:
    #     private_points_ = [i for i in private_points_  if i not in algorithm_config['changeMeasurePointQueue'][algorithm_config['param_turbine_num'][-1]] and i in pn_data.columns.to_list()]
    # elif time_duration == algConfig['luoshuansongdong']['changeDateRange']:
    #     private_points_ = [i for i in private_points_  if i in algorithm_config['changeMeasurePointQueue'][algorithm_config['param_turbine_num'][-1]] and i in pn_data.columns.to_list()]
    temp =  pn_data[private_points_].dropna() 
    
    temp = temp.ffill()
    temp = temp.bfill()
    return temp


def ProcessSingleMeasurement(data, final_df, measureName, assetId, threshold, alarming, statement, Figs):
    '''
        data:告警数据
        final_df:输入数据
    '''
    warning = 0 #预警
    if data.empty == False:
        # final_df['result'] = final_df['result'].astype('bool')
        # average_level = final_df[final_df['result']==True].mean()
        # for key, value in threshold["gaojing"]["threshold"].items():
        #     if average_level >= value:
        #         alarming = key
        #     else:
        #         break
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
        curves1.append(DisplayResultXY('0', algConfig['luoshuansongdong']['nameMaps'][measureName], '#FFFF00', 'Solid', data1))#{'type':'0', 'name':'倾角', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data1}
        curves1.append(DisplayResultXY('0', '告警线', '#FF0000', 'Solid', data2))#{'type':'0', 'name': '告警线', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data2}

        result1 = DisplayFigures(xUnit=interval_unit, yUnit="角度[°]", time=1, multiDimensionDataxy=curves1)#DisplayResultXY(str(final_df.index.min()), str(final_df.index.max()), str(interval_value), '角度', curves)
        Figs.append(result1)
        return data, statement, Figs, int(alarming), int(warning)
    elif data.empty == True and ("minute" not in threshold["executeTimeValue"] and  "hour" not in threshold["executeTimeValue"]):
        data1, data2, statement, warning, startTime, endTime = alarm.generateAlarmTrend(name, final_df, measureName, threshold, resample_interval, assetId)
        statement = str.replace(statement, measureName, algConfig['luoshuansongdong']['nameMaps'][measureName])
        # 展示数据
        interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
        interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()

        # Figs = []
        curves1 = []
        curves1.append(DisplayResultXY('0', algConfig['luoshuansongdong']['nameMaps'][measureName], '#FFFF00', 'Solid', data1))#{'type':'0', 'name':'倾角', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data1}
        curves1.append(DisplayResultXY('0', str(algConfig['luoshuansongdong']['nameMaps'][measureName])+'预測趋势', '#FF0000', 'Solid', data2))#{'type':'0', 'name': '告警线', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data2}

        result1 = DisplayFigures(xUnit=interval_unit, yUnit="角度[°]", time=1, multiDimensionDataxy=curves1)#DisplayResultXY(str(final_df.index.min()), str(final_df.index.max()), str(interval_value), '角度', curves)
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
        curves1.append(DisplayResultXY('0', algConfig['luoshuansongdong']['nameMaps'][measureName], '#FFFF00', 'Solid', data1))#{'type':'0', 'name':'倾角', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data1}
        curves1.append(DisplayResultXY('0', '告警线', '#00FF00', 'Solid', data2))#{'type':'0', 'name': '告警线', "abscissaUnit": interval_unit, "ordinateUnit": "°", 'xyData': data2}

        result1 = DisplayFigures(xUnit=interval_unit, yUnit="角度[°]", time=1, multiDimensionDataxy=curves1)#DisplayResultXY(str(final_df.index.min()), str(final_df.index.max()), str(interval_value), '角度', curves)
        Figs.append(result1)
        return pd.DataFrame(), statement, Figs, int(alarming), int(warning)

async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps, algorithm_config):
    assetId = Turbine_attr['mdmId']
    final_df = predict_result(pn_data, algorithm_config)
    
    #预警、告警类型及其等级
    alarming = 0 #告警
    warning = 0 #预警
    measureName = []
    
    for modelKey, pointValue in private_points.items():
        for value_elem in pointValue:
            if value_elem in final_df.columns.to_list():
                measureName.append(value_elem)
    # #剔除不符合条件的测点
    # if time_duration != algConfig['luoshuansongdong']['changeDateRange']:
    #     measureName = [i for i in measureName  if i not in algorithm_config['changeMeasurePointQueue'][algorithm_config['param_turbine_num'][-1]] and i in pn_data.columns.to_list()]
    # elif time_duration == algConfig['luoshuansongdong']['changeDateRange']:
    #     measureName = [i for i in measureName  if i in algorithm_config['changeMeasurePointQueue'][algorithm_config['param_turbine_num'][-1]] and i in pn_data.columns.to_list()]
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
            statementException = str(algConfig['luoshuansongdong']['nameMaps'][keyMeasure])+f'超过阈值{threshold["gaojing"]["threshold"][keyMeasure]["10"]}，'
            statementNormal = str(algConfig['luoshuansongdong']['nameMaps'][keyMeasure])+f'未超过阈值{threshold["gaojing"]["threshold"][keyMeasure]["10"]}, '
            if 'result' in list(final_df.columns):
                final_df = final_df.drop('result', axis=1)
            final_df['result'] = final_df[keyMeasure] > threshold["gaojing"]["threshold"][keyMeasure]["10"]
            data, statement, alarming =  alarm.generateAlarm(name, 'luoshuansongdong', keyMeasure,final_df, error_data_time_duration, resample_interval, assetId, threshold, statementException, statementNormal, idMaps)
            data_tmp, statement_tmp, Figs, alarming_tmp, warning_tmp = ProcessSingleMeasurement(data, final_df, keyMeasure, assetId, threshold, alarming, statement, Figs)
            data_fn = pd.concat([data_fn, data_tmp])
            # statement_fn太长缩减
            if "时间大于等于" in statement_tmp:
                pass
            elif "没有达到阈值" in statement_tmp:
                statement_tmp = ''
            elif "未超过阈值" in statement_tmp:
                statement_tmp = ''
            elif "时间小于" in  statement_tmp:
                statement_tmp = ''
            if len(statement_tmp)>0:
                statement_fn += statement_tmp + '; '
            else:
                statement_fn += statement_tmp
            if alarming_fn < alarming_tmp:
                alarming_fn = alarming_tmp
            if warning_fn < warning_tmp:
                warning_fn = warning_tmp
        if len(statement_fn)==0:
            statement_fn = '所有测点没有告警发生'
        return data_fn, statement_fn, Figs, alarming_fn, warning_fn
    else: #单测点
        #告警
        statementException = f'角度超过阈值{threshold["gaojing"]["threshold"]["10"]}，'
        statementNormal = f'角度未超过阈值{threshold["gaojing"]["threshold"]["10"]}'
        Figs = [] #存放每一张图
        # 生成告警
        final_df['result'] = final_df[measureName] > threshold["gaojing"]["threshold"]["10"]
        data, statement, alarming =  alarm.generateAlarm(name, 'luoshuansongdong','BLADE1_BLOT_ANGLE_1', final_df, error_data_time_duration, resample_interval, assetId, threshold, statementException, statementNormal, idMaps)
        data_fn, statement, Figs, alarming, warning = ProcessSingleMeasurement(data, final_df, measureName, assetId, threshold, alarming, statement, Figs)
        return data_fn, statement, Figs, alarming, warning
  
    
def cleanData(data, algorithm_config):
    measurePoints = ['BLADE1_BLOT_ANGLE_1','BLADE1_BLOT_ANGLE_2','BLADE1_BLOT_ANGLE_3','BLADE1_BLOT_ANGLE_4','BLADE1_BLOT_ANGLE_5','BLADE1_BLOT_ANGLE_6','BLADE1_BLOT_ANGLE_7','BLADE1_BLOT_ANGLE_8',
        'BLADE2_BLOT_ANGLE_1','BLADE2_BLOT_ANGLE_2','BLADE2_BLOT_ANGLE_3','BLADE2_BLOT_ANGLE_4','BLADE2_BLOT_ANGLE_5','BLADE2_BLOT_ANGLE_6','BLADE2_BLOT_ANGLE_7','BLADE2_BLOT_ANGLE_8',
        'BLADE3_BLOT_ANGLE_1','BLADE3_BLOT_ANGLE_2','BLADE3_BLOT_ANGLE_3','BLADE3_BLOT_ANGLE_4','BLADE3_BLOT_ANGLE_5','BLADE3_BLOT_ANGLE_6','BLADE3_BLOT_ANGLE_7','BLADE3_BLOT_ANGLE_8',
        'TOWERL1_BLOT_ANGLE_1','TOWERL1_BLOT_ANGLE_2','TOWERL1_BLOT_ANGLE_3','TOWERL1_BLOT_ANGLE_4','TOWERL1_BLOT_ANGLE_5','TOWERL1_BLOT_ANGLE_6','TOWERL1_BLOT_ANGLE_7','TOWERL1_BLOT_ANGLE_8',
        'TOWERL2_BLOT_ANGLE_1','TOWERL2_BLOT_ANGLE_2','TOWERL2_BLOT_ANGLE_3','TOWERL2_BLOT_ANGLE_4','TOWERL2_BLOT_ANGLE_5','TOWERL2_BLOT_ANGLE_6','TOWERL2_BLOT_ANGLE_7','TOWERL2_BLOT_ANGLE_8',
        'TOWERL3_BLOT_ANGLE_1','TOWERL3_BLOT_ANGLE_2','TOWERL3_BLOT_ANGLE_3','TOWERL3_BLOT_ANGLE_4','TOWERL3_BLOT_ANGLE_5','TOWERL3_BLOT_ANGLE_6','TOWERL3_BLOT_ANGLE_7','TOWERL3_BLOT_ANGLE_8',
        'TOWERL4_BLOT_ANGLE_1','TOWERL4_BLOT_ANGLE_2','TOWERL4_BLOT_ANGLE_3','TOWERL4_BLOT_ANGLE_4','TOWERL4_BLOT_ANGLE_5','TOWERL4_BLOT_ANGLE_6','TOWERL4_BLOT_ANGLE_7','TOWERL4_BLOT_ANGLE_8']
    if algConfig['luoshuansongdong']['changeDateRange'] != time_duration:
        #挑选异常的风机及其测点
        for measure_point in measurePoints:
            if measure_point in data.columns.to_list():
                meanValue = data[measure_point].abs().mean()
                if meanValue > algConfig['luoshuansongdong']['threshold']['yujing']['threshold'][measure_point]:
                    algorithm_config['changeMeasurePointQueue'][algorithm_config['param_turbine_num'][-1]].append(measure_point)
                    data.drop(measure_point, axis=1, inplace=True)
    else:
        #时间排序
        data.sort_index(inplace=True)
        #处理异常的风机及其测点
        for measure_point in algorithm_config['changeMeasurePointQueue'][algorithm_config['param_turbine_num'][-1]]:
            if measure_point in data.columns.to_list():
                data['diff'] = data[measure_point].diff()
                data['diff'] = data['diff'].ffill()
                data['diff'] = data['diff'].bfill()
                bias_index = data.loc[data['diff'].abs() > algConfig['luoshuansongdong']['changeDataThreshold']].index
                if len(bias_index) == 0:
                    data.loc[:, measure_point] = data.loc[:, 'diff']
                    continue
                #遍历初始偏执时间
                pre_bias_v = None
                for bias_i, bias_v in enumerate(bias_index):
                    #原始数据中挨着当前偏移突变的前一个时间
                    pre_time_v = data[data.index < bias_v]
                    if len(pre_time_v) == 0:
                        pre_time_v = bias_v
                    else:
                        pre_time_v = pre_time_v.index[-1]
                    if bias_i == 0:
                        data.loc[:pre_time_v, measure_point] = data.loc[:pre_time_v, measure_point] - data.iloc[0][measure_point]
                        #偏移突变序列中挨着当前偏移突变的前一个时间
                        pre_bias_v = bias_v
                    # elif bias_i == len(bias_index) - 1:
                    else:
                        data.loc[pre_bias_v:pre_time_v, measure_point] = data.loc[pre_bias_v:pre_time_v, measure_point] - data.loc[pre_bias_v,measure_point]
                        pre_bias_v = bias_v
                #处理len(bias_index) - 1之后的原始数据
                data.loc[pre_bias_v:, measure_point] = data.loc[pre_bias_v:, measure_point] - data.loc[pre_bias_v, measure_point]
    return data
    

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
    
    return alarm.generateAlarm(pn_data, error_data_time_duration), None