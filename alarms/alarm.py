# -*- coding: utf-8 -*-
"""
Created on Fri Jun  2 10:18:24 2023

@author: sunyan
"""
import numpy as np
import pandas as pd
import utils.time_util as time_util
import requests
from configs.config import Alarm_Push_Url, ALARM_PUSH_MODE, DB_HOST, AL_PUSH_URL_SELF,OV_PUSH_URL_THR, KKS_DEVICE, POSITION_CONFIG
from datetime import datetime
from db.db import save_alarm
# from commonModel.DartsModel import MeanOverTime
from sklearn.linear_model import LinearRegression
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from db.db import CheckModuleCode
import traceback
from configs.config import algConfig

alarm_logger = logging.getLogger('alarm')
if not alarm_logger.handlers:
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(process)d - %(threadName)s - %(message)s')
    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(formatter)
    # alarm_file_handler = TimedRotatingFileHandler('logs/alarm.log', when='midnight', interval=1, backupCount=30)
    alarm_file_handler = logging.handlers.RotatingFileHandler(filename=os.path.join("logs","alarm"+".log"), mode='a', maxBytes=5*1024**2, backupCount=3)
    alarm_file_handler.setFormatter(formatter)
    alarm_logger.setLevel(logging.INFO)
    # alarm_logger.addHandler(console_handler)
    alarm_logger.addHandler(alarm_file_handler)


def generateAlarm(name, modelCode, pnCode, data_df_in, continuous_time, sample_interval, assetId, threshold, statementException, statementNormal, idMaps):
    '''
    连续异常数据告警
    '''
    # 故障设为True, 连续True出现的次数
    interval_value, interval_unit = time_util.split_time_delta(sample_interval)
    interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit]
    continue_interval_value, continue_interval_unit = time_util.split_time_delta(continuous_time)
    continue_interval_unit = time_util.__timedelta_resample_unit_dict[continue_interval_unit]
    continuous_time = str(continue_interval_value) + continue_interval_unit
    data_df_in['result'] = data_df_in['result'].astype('bool')
    data_df = data_df_in.select_dtypes(include=['number', 'bool'])
    data_df_ = pd.DataFrame()
    for column in data_df.columns.values:
        data_df_[column] = data_df[column].resample(str(interval_value)+interval_unit).mean() #.asfreq(timeUnit).fillna(method='ffill')
    #处理数据缺失和采样时间缺失
    date_index = pd.date_range(start=data_df_.index[0], end=data_df_.index[-1], freq=str(interval_value)+interval_unit)
    data_df_ = data_df_.reindex(date_index).ffill()#fillna(method='ffill')
    data_df_ = data_df_.sort_index()
    data_df_['zero_one_seq'] = data_df_['result'].astype(bool).astype(int)#np.bitwise_not(data_df_['result'].astype(bool)).cumsum()
    # data_df_['zero_one_seq'] = data_df_.groupby(['sum'])['result'].rank(method='dense')-1
    data_df_['cumsum'] = data_df_['zero_one_seq'].cumsum()
    data_df_['diff'] = data_df_['cumsum'].diff()
    data_df_['block'] = data_df_['diff'].ne(1).cumsum()
    data_df_['consecutive_ones_extend'] = data_df_.groupby('block')['zero_one_seq'].transform('sum')
    data_df_['consecutive_ones'] = data_df_['consecutive_ones_extend'] * data_df_['zero_one_seq']
    data_df_['continuous']=pd.to_timedelta(data_df_['consecutive_ones'] * interval_value, unit=interval_unit)#time_util.__timedelta_resample_unit_dict[interval_unit]
    # freq = data_df.index[1]-data_df.index[0]
    # timeUnitSize = freq/np.timedelta64(1,time_util.__timedelta_resample_unit_dict[continue_interval_unit])
    # data_df['continuous'] = data_df['continuous'] * timeUnitSize
    # continuous_time_ = str(continue_interval_value*timeUnitSize)+time_util.__timedelta_resample_unit_dict[continue_interval_unit]
    # continuous_time_ = pd.Timedelta(continuous_time_)
    # error_data = data_df_[data_df_['continuous']>=continuous_time] # 连续三十分钟出现
    # if True in data_df_['continuous']>=continuous_time:
    #     statementException = statementException + f', 且持续时间大于等于{continuous_time}'
    # else:
    #     statementNormal = statementException + f', 但持续时间小于{continuous_time}'
    # if error_data.empty:
    if True in list(data_df_['continuous']>=pd.to_timedelta(continue_interval_value, unit=continue_interval_unit)):
        max_error_data = data_df_['continuous'].nlargest(1)
        error_data = data_df_[data_df_['continuous'] == max_error_data.iloc[0]]
        error_end_time = error_data.index[-1]
        error_start_time = error_data.index[0]#error_end_time - max_error_data.iloc[0]
        abnomal_data = data_df[(data_df.index>=error_start_time) & (data_df.index<=error_end_time)]#.loc[error_start_time:error_end_time]
        if pd.to_timedelta(abnomal_data.shape[0] * interval_value, unit=interval_unit) < pd.to_timedelta(continue_interval_value, unit=continue_interval_unit):
            statementNormal = statementException + f' 但持续时间小于{continuous_time}'
            alarming = 0
            return (pd.DataFrame(), statementNormal, alarming)
        statementException = statementException + f' 且持续时间大于等于{continuous_time}'
        abnomal_data['result'] = abnomal_data['result'].astype('bool')
        if isinstance(threshold, int) or isinstance(threshold, float):
            push_alarm_self(assetId, pnCode, statementException, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), threshold,modelCode)
            alarming = 11
            # push_alarm(assetId, name, datetime.now(), error_start_time, error_end_time, alarming//7+1)
            push_alarm(assetId, pnCode, statementException, (alarming-10)//3+1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), threshold,modelCode, idMaps)
        else:
            if len(threshold) > 0:
                average_level = abnomal_data[abnomal_data['result']==True][pnCode].mean()
                if pnCode in threshold["gaojing"]["threshold"]:
                    for key, value in threshold["gaojing"]["threshold"][pnCode].items():
                        if average_level >= value:
                            alarming = int(key)
                            alarmingValue = value
                        else:
                            break
                else:
                    for key, value in threshold["gaojing"]["threshold"].items():
                        if average_level >= value:
                            alarming = int(key)
                            alarmingValue = value
                        else:
                            break
                # push_alarm(assetId, name, datetime.now(), error_start_time, error_end_time, alarming//7+1)
                push_alarm(assetId, pnCode, statementException, (alarming-10)//3+1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), alarmingValue,modelCode, idMaps)
                push_alarm_self(assetId, pnCode, statementException, (alarming-10)//3+1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), alarmingValue,modelCode) #alarming//7+1
            else:
                alarming = 11
                # push_alarm(assetId, name, datetime.now(), error_start_time, error_end_time, alarming//7+1)
                push_alarm(assetId, pnCode, statementException, (alarming-10)//3+1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), threshold,modelCode, idMaps)
        return (abnomal_data, statementException, alarming)
    else:    
        alarm_logger.info('没有异常数据')
        if True in list(data_df_in['result']):
            statementNormal = statementException + f' 但持续时间小于{continuous_time}'
            if isinstance(threshold, int) or isinstance(threshold, float):
                # push_alarm_self(assetId, pnCode, statementException, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), threshold,modelCode)
                push_over_threshold(assetId, pnCode, 1)
                alarming = 11
            else:
                if len(threshold) > 0:
                    average_level = data_df_in[data_df_in['result']==True][pnCode].mean()
                    if pnCode in threshold["gaojing"]["threshold"]:
                        for key, value in threshold["gaojing"]["threshold"][pnCode].items():
                            if average_level >= value:
                                alarming = int(key)
                                alarmingValue = value
                            else:
                                break
                    else:
                        for key, value in threshold["gaojing"]["threshold"].items():
                            if average_level >= value:
                                alarming = int(key)
                                alarmingValue = value
                            else:
                                break
                    # push_alarm_self(assetId, pnCode, statementException, alarming//7+1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), threshold,modelCode)
                    push_over_threshold(assetId, pnCode, alarming//7+1)
        else:
            pass
        alarming = 0
        return (pd.DataFrame(), statementNormal, alarming)
        
def generateAlarmFit(name, pn_data, fit_fun,modelCode, measure_name, threshold, sample_interval, assetId,statementException='', statementNormal=''):
    # 将时间转换为日期偏移(时间戳)，以便进行线性拟合
    interval_value, interval_unit = time_util.split_time_delta(sample_interval)
    pn_data['time_since_epoch'] = (pn_data.index - pn_data.index.min())/np.timedelta64(interval_value, interval_unit)
    # # 进行线性拟合
    # x = data_df['time_since_epoch'].values.reshape(-1, 1)
    # y = data_df[measure_name]
    # model = LinearRegression()
    # model.fit(x, y)
    # 模型推理
    # 处理空数据
    pn_data.fillna(method='ffill', axis=0, inplace=True)
    pn_data.fillna(method='bfill', axis=0, inplace=True)
    # 加载模型
    # model = model_util.load_model(config.Wind_Farm, modelCode, assetId,modelCode)
    # 预测健康数据 并判断是否告警
    pn_data = pn_data.sort_index()
    pn_data['predict'] = fit_fun(pn_data[[measure_name]])
    # error = model_util.load_model(config.Wind_Farm, 'jiegou_sunshang', assetId,'error')
    # 阈值判断
    pn_data['result'] = np.abs(pn_data[measure_name] - pn_data['predict']) > threshold# | (np.abs(pn_data[measureName] - pn_data['predict']) < -3*error)
    pn_data = pn_data.sort_index()
    
    x = [str(tick) for tick in list(pn_data.index)]
    x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
    x = [int(tick.timestamp()*1000) for tick in x]
    y1 = [str(round(num,4)) for num in list(pn_data['predict'])]
    y2 = [str(round(num,4)) for num in list(pn_data[measure_name])]
    y3 = [str(round(num,4)) for num in list(pn_data['predict']+threshold)]
    y4 = [str(round(num,4)) for num in list(pn_data['predict']-threshold)]
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
    data3 = pd.DataFrame({'x': x, 'y': y3}).to_dict('records')
    data4 = pd.DataFrame({'x': x, 'y': y4}).to_dict('records')


    return data1, data2, data3, data4
    
def generateAlarmTrend(name, data_df, measure_name, threshold, sample_interval, assetId,statementException='', statementNormal=''):
    # 将时间转换为日期偏移(时间戳)，以便进行线性拟合
    interval_value, interval_unit = time_util.split_time_delta(sample_interval)
    data_df['time_since_epoch'] = (data_df.index - data_df.index.min())/np.timedelta64(interval_value, interval_unit)
    # 进行线性拟合
    x = data_df['time_since_epoch'].values.reshape(-1, 1)
    y = data_df[measure_name]
    model = LinearRegression()
    model.fit(x, y)
    # 预测未来数据
    horizon_value, horizon_unit = time_util.split_time_delta(threshold["levelline"])
    #单位转换成秒，因为np.timedelta64不接受小数
    timedelta_unit = np.timedelta64(horizon_value, horizon_unit)
    timedelta_s = timedelta_unit.astype('timedelta64[s]').astype(int)
    future_time = [np.timedelta64(int(i), 's').astype('timedelta64['+horizon_unit+']') for i in np.arange(1,timedelta_s, (timedelta_s-1)/9)]
    future_time = [(data_df.index.max() + i - data_df.index.min())/np.timedelta64(interval_value, interval_unit) for i in future_time]
    x_future = np.array([data_df.iloc[0]['time_since_epoch']]+future_time).reshape(-1, 1)

    y_future = model.predict(x_future)
    # 将未来的预测值转换回日期
    future_dates = x_future*np.timedelta64(interval_value, interval_unit) + data_df.index.min()#pd.to_datetime(x_future, unit=str(interval_value)+interval_unit)
 
    x1 = [str(tick) for tick in list(data_df.index)]
    x1 = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x1]
    x1 = [int(tick.timestamp()*1000) for tick in x1]
    y1 = [str(round(num,4)) for num in list(data_df[measure_name])]
    x2 = [str(pd.to_datetime(num.item())) for num in future_dates]
    x2 = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x2]
    x2 = [int(tick.timestamp()*1000) for tick in x2]
    y2 = [str(round(num,4)) for num in y_future]
    data1 = pd.DataFrame({'x': x1, 'y': y1}).to_dict('records')
    data2 = pd.DataFrame({'x': x2, 'y': y2}).to_dict('records')

    thre_value = threshold["yujing"]["threshold"]
    if  (not isinstance(thre_value, int) and not isinstance(thre_value, float)) and measure_name in thre_value:
        # 判断还有多少天到达阈值
        for i in np.arange(1,10):
            if y_future[i].item() >= threshold["yujing"]["threshold"][measure_name]:
                warning = 10 - i
                statementException = f"{measure_name}还有{i*interval_value}{interval_unit}到达阈值{thre_value[measure_name]}"
                # push_alarm(assetId, name, datetime.now(), datetime.fromtimestamp(x2[i]/1000), datetime.fromtimestamp(x2[-1]/1000), warning//7+1)
                return data1, data2, statementException, warning, x2[0], x2[-1]

        statementNormal = f"{measure_name}在{10*interval_value}{interval_unit}内没有达到阈值{thre_value[measure_name]}"
    else:
        # 判断还有多少天到达阈值
        for i in np.arange(1,10):
            if y_future[i].item() >= threshold["yujing"]["threshold"]:
                warning = 10 - i
                statementException = f"还有{i*interval_value}{interval_unit}到达阈值{thre_value}"
                # push_alarm(assetId, name, datetime.now(), datetime.fromtimestamp(x2[i]/1000), datetime.fromtimestamp(x2[-1]/1000), warning//7+1)
                return data1, data2, statementException, warning, x2[0], x2[-1]

        statementNormal = f"{10*interval_value}{interval_unit}内没有达到阈值{thre_value}"

    return data1, data2, statementNormal, 0, x2[0], x2[-1]

    # if delta <= threshold:
    #     print('没有异常数据')
    #     return pd.DataFrame()
    # else:
    #     abnomal_data = data_df.loc[start_time, end_time]
    #     # push_alarm(assetId, name, datetime.now(), start_time, end_time)
    #     return abnomal_data

    
def generateAlarmPercentage(name, modelCode, pnCode, data_df, error_percentage, assetId, threshold, statementException, statementNormal, idMaps):
    '''
    占比告警
    '''
    count = (data_df['result'] == True).sum()
    statementException = statementException + f'{error_percentage*100}%'
    statementNormal = statementNormal + f'{error_percentage*100}%'
    if len(data_df) > 0 and count / len(data_df) > error_percentage:
        alarm_logger.info('产生告警')
        alarming = 11
        abnormal_data = data_df[data_df['result'] == True]
        # push_alarm(assetId, name, datetime.now(), abnormal_data.index.min(), abnormal_data.index.max(), alarming//7+1)
        push_alarm(assetId, pnCode, statementException, (alarming-11)//3+1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), threshold,modelCode, idMaps)
        if isinstance(threshold, int) or isinstance(threshold, float):
            push_alarm_self(assetId, pnCode, statementException, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), threshold,modelCode)

        return (abnormal_data, statementException, alarming)#
    else:
        alarm_logger.info('不产生告警')
        alarming = 0
        return (pd.DataFrame(), statementNormal, alarming) 
    
    
def generateBaseAlarm(name, modelCode,pnCode, data_df, fault_flag, assetId, threshold, statement, idMaps):
    '''
    生成告警
    '''
    if fault_flag == True:
        if isinstance(threshold, int) or isinstance(threshold, float):
            push_alarm_self(assetId, pnCode, statement, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), threshold,modelCode)
        alarming = 11
        # push_alarm(assetId, name, datetime.now(), data_df.index.min(), data_df.index.max(), alarming//7+1)
        push_alarm(assetId, pnCode, statement, (alarming-11)//3+1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), threshold,modelCode, idMaps)
    else:
        alarming = 0
        data_df = pd.DataFrame()

    return data_df, statement, alarming


# def push_alarm(assetId, alarmName, alarmTime, error_start_time, error_end_time, level):
#     if ALARM_PUSH_MODE == 'http':
#         push_alarm_http(assetId, alarmName, alarmTime, error_start_time, error_end_time, level)
#     else:
#         save_alarm(assetId, alarmName, alarmTime, error_start_time, error_end_time)
def push_alarm(wind_turbine_code, pn_code, content, level, gather_time, alarm_value, model_code, idMaps):
    if ALARM_PUSH_MODE == 'http':
        push_alarm_http(wind_turbine_code, pn_code, content, level, gather_time, alarm_value, model_code, idMaps)

def push_alarm_self(wind_turbine_code, pn_code, content, level, gather_time, alarm_value, model_code):
    '''
    推送告警
    '''
    try:
        module_code_table = {
            "F0001": "1",
            "F0002": "2",
            "F0005": "3",
            "F0007": "4",
            "F0009": "5",
            "F0010": "6"
        }
        module_code, module_name = CheckModuleCode(model_code)
        module_num = module_code_table[module_code]
        payload = {
            "windTurbineCode": str(wind_turbine_code), #风机id
            "pnCode": str(pn_code), #测点名
            "content": str(content), #告警信息
            "level": str(level), #告警等级
            "gatherTime": str(gather_time), #告警时间
            'alarmType': str(module_num), #大部件
            "alarmValue": str(alarm_value), #告警阈值
            "modelCode": str(model_code), #模型code
            "alarmName": str(module_name) #模型名称
            }
        Url = AL_PUSH_URL_SELF #"http://"+DB_HOST+":8088/iwind-edge-api/base/DataAlarm/addAlarm"
        alarm_logger.info("push_alarm_self -> URL: "+Url)
        alarm_logger.info(f"push_alarm_self -> json: {str(payload)}")
        response = requests.post(Url, json=payload, timeout=10)
        alarm_logger.info(response)
    except Exception as e:
        errorInfomation = traceback.format_exc()
        alarm_logger.info(f'\033[31m{errorInfomation}\033[0m')
        alarm_logger.info(f'\033[33mpush_alarm_self->{e}\033[0m')

def push_over_threshold(wind_turbine_code, pn_code, level):
    '''
    推送告警
    '''
    try:
        payload = {
            "windTurbineCode": str(wind_turbine_code),
            "pnCode": str(pn_code),
            "level": str(level),
            }
        Url = OV_PUSH_URL_THR #"http://"+DB_HOST+":8088/iwind-edge-api/base/DataAlarm/addAlarm"
        alarm_logger.info("push_threshold_self -> URL: "+Url)
        alarm_logger.info(f"push_threshold_self -> json: {str(payload)}")
        response = requests.post(Url, json=payload, timeout=10)
        alarm_logger.info(response)
    except Exception as e:
        errorInfomation = traceback.format_exc()
        alarm_logger.info(f'\033[31m{errorInfomation}\033[0m')
        alarm_logger.info(f'\033[33mpush_threshold_self->{e}\033[0m')

# def push_alarm_http(assetId, alarmName, alarmTime, error_start_time, error_end_time, level):
#wind_turbine_code：风机编码
def push_alarm_http(wind_turbine_code, pn_code, content, level, gather_time, alarm_value, model_code, idMaps):
    '''
    推送告警
    '''
    try:
        module_code_table = {
                "F0001": "TW", #塔基及塔架
                "F0002": "BL", #叶片
                "F0005": "GB", #传动链
                "F0007": "XB", #箱变
                "F0009": "BT", #螺栓
                "F0010": "FJ"  #融合态势
        }
        inverse_level = {
            "1": 3,
            "3": 1,
            "4": 1,
            "2": 2
        }
        module_code, module_name = CheckModuleCode(model_code)
        module_num = module_code_table[module_code]
        #"analysisData": {"startTime": datetime.strftime(error_start_time, "%Y-%m-%d %H:%M:%S"), "endTime": datetime.strftime(error_end_time, "%Y-%m-%d %H:%M:%S")},
        turbine_number_name = ''.join([c for c in KKS_DEVICE[wind_turbine_code] if c.isdigit()])
        turbine_number_name = int(turbine_number_name)
        payload = {
            "warnDataType": "SC", #告警数据类型,SC-生产  SB-设备本体 AF-安防
            "moduleType": "FGJ", #业务模块, UGJ-无人机  RGJ-机器人 CGJ-摄像头 FGJ-风机振动 SGJ-安防
            "moduleSubType": module_num, # 大部件， JDX-集电线 GF-光伏 FJ-风机 SYZ-升压站 AF-安防  FJZD-风机振动 MB-主轴 GB-齿轮箱  GE-发电机 BT-螺栓  BL-叶片 W-塔筒 XB-箱变
            "deviceKKS": KKS_DEVICE[wind_turbine_code], # 设备 KKS 编码，设备唯一编码风机编码对应的kss码
            "warnTypeId": 'warn_'+model_code, #告警类型 id
            "warnTypeName": module_name, #告警类型名称 ID 和 name 配对
            'position': str(turbine_number_name)+'号风机: '+POSITION_CONFIG[pn_code], #告警定位，位置描述
            "diagnosis": content, #诊断结果，结果描述
            "identification": "告警", #识别结果，正常/告警
            "warnLevel": inverse_level[str(level)], #告警等级：1、2、3 级，1 最严重
            "taskNumber": idMaps[model_code], #任务编号
            "warnTime": str(gather_time), #datetime.strftime(alarmTime, "%Y-%m-%d %H:%M:%S"), #告警时间，YYYY-MM-DD hh24:mi:ss
            "endFlag": 0, # 告警是否结束，0:否，1:是
            'warnVender': "国核信息"#告警厂商（中文名字，简写）
            }
        Url = Alarm_Push_Url #"http://"+DB_HOST+":8088/iwind-edge-api/base/DataAlarm/addAlarm"
        alarm_logger.info("push_alarm -> URL: "+Url)
        alarm_logger.info(f"push_alarm -> json: {str(payload)}")
        response = requests.post(Url, json=payload, timeout=10)
        alarm_logger.info(response)
    except Exception as e:
        errorInfomation = traceback.format_exc()
        alarm_logger.info(f'\033[31m{errorInfomation}\033[0m')
        alarm_logger.info(f'\033[33mpush_alarm_self->{e}\033[0m')


if __name__ == '__main__':
    push_alarm_http('', '叶片角度不平衡', datetime.now(), datetime.strptime('2023-10-01 00:00:00', '%Y-%m-%d %H:%M:%S'), datetime.strptime('2023-10-02 00:00:00', '%Y-%m-%d %H:%M:%S'))