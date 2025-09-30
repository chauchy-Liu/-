# -*- coding: utf-8 -*-
"""
转矩控制异常
kopt已知 同叶轮转速不平衡
Created on Sat Aug 12 14:21:34 2023

@author: sunyan
"""
from alarms import alarm
from pandas import DataFrame
from configs import config
from sklearn import preprocessing
from sklearn.mixture import BayesianGaussianMixture
import pandas as pd
from utils.display_util import DisplayResultXY, DisplayFigures
import pandas as pd
import utils.time_util as time_util
import numpy as np
from data.get_data import wash_data_for_train#, Pwrat_Rate, Rotspd_Rate, Rotspd_Connect
import data.get_data as get_data
from datetime import datetime
from alarms.alarm import push_alarm, push_alarm_self
import asyncio
from configs.config import algConfig

name = algConfig['generator_zhuanju_kongzhi']['name']#'转矩控制异常'
# 把所需测点定义到每个算法里
ai_points = algConfig['generator_zhuanju_kongzhi']['ai_points']
ai_rename = algConfig['generator_zhuanju_kongzhi']['ai_rename']
di_points = algConfig['generator_zhuanju_kongzhi']['di_points']
general_points = algConfig['generator_zhuanju_kongzhi']['general_points']
private_points = algConfig['generator_zhuanju_kongzhi']['private_points']
time_duration = algConfig['generator_zhuanju_kongzhi']['time_duration']
resample_interval = algConfig['generator_zhuanju_kongzhi']['resample_interval']
error_percentage = algConfig['generator_zhuanju_kongzhi']['error_percentage']
need_all_turbines = algConfig['generator_zhuanju_kongzhi']['need_all_turbines']
store_file = algConfig['generator_zhuanju_kongzhi']['store_file']


def predict_result(pn_data: DataFrame):
    pass


def wash_data(pn_data: DataFrame, ratedPower):
    temp_data = pn_data[ai_points + di_points+general_points]
    '''
    个性化数据清洗
    '''
    temp = wash_data_for_train(temp_data, ratedPower)
    if len(temp) >= 2000: # 判断是否满足模型执行的数据需求
        return temp, ''
    else:
        print(f'数据不满足模型需求，未执行模型{temp.shape[0]}')
        return pd.DataFrame(), f'清洗数据后数据量小于2000'
    


#最佳Cp段转矩控制异常异常
def Torque_Cp_kopt_loss(data,Pwrat_Rate,Rotspd_Connect,Rotspd_Rate,mytol=0.1,myreg=0.02):
    data['kopt_err'] = 1
    kopt_err = 0
    #gmm = GaussianMixture(n_components=2,covariance_type='full',random_state=0,tol=0.01,reg_covar=0.000005)
    gmm = BayesianGaussianMixture(n_components=2, covariance_type="full",random_state=0,tol=mytol,reg_covar=myreg)
    #gmm = DBSCAN(eps=0.1,min_samples=10)
    #gmm = SpectralClustering(n_clusters=2,assign_labels='discretize',eigen_solver='arpack',affinity='nearest_neighbors',n_neighbors=500,random_state=0,n_jobs=-1)
    temp = data[(data['WGEN.GenSpd']>Rotspd_Connect*1.2)&(data['WGEN.GenSpd']<Rotspd_Rate*0.9)]
    if len(temp)>0.2*len(data):
        xx = temp.loc[:,[('kopt')]].values
        min_max_scaler = preprocessing.StandardScaler()
        train_minmax = min_max_scaler.fit_transform(xx)
        #labels = gmm.fit(train_minmax).labels_
        labels = gmm.fit(train_minmax).predict(train_minmax)
        #labels = gmm.fit(xx).predict(xx)
        temp['kopt_err'] = labels
        #data.loc[temp.index.values,'kopt_err'] = labels
        kopt_err_temp = np.abs(np.nanmean(temp[temp['kopt_err']==1]['kopt']) - np.nanmean(temp[temp['kopt_err']==0]['kopt']))/np.nanmean(temp[temp['kopt_err']==1]['kopt'])
    
        if ((temp['kopt_err'].value_counts().iloc[-1] / len(temp) > 0.05)&(kopt_err_temp > 0.18)):
            kopt_err = 1
            return kopt_err,temp
        else:
            return kopt_err,temp
    else:
        return kopt_err,temp


            
#额定功率段转矩控制异常异常
def Torque_Rotspd_Rate_loss(data,Pwrat_Rate,Rotspd_Rate,Rotspd_Connect):
    rate_kopt_err = 0
    if np.abs(np.nanmean(data.loc[data['WGEN.GenActivePW'].nlargest(20).index,('WGEN.GenSpd')]) - Rotspd_Rate)/Rotspd_Rate>0.03:
        Rotspd_Rate = np.nanmean(data.loc[data['WGEN.GenActivePW'].nlargest(20).index,('WGEN.GenSpd')])
    temp = data[(data['WGEN.GenSpd']>Rotspd_Rate*0.97)&(data['WGEN.GenActivePW']<=Pwrat_Rate)]
    temp_kopt = data[np.abs(data['WGEN.GenSpd']-(Rotspd_Connect+Rotspd_Rate)*0.5)/((Rotspd_Connect+Rotspd_Rate)*0.5)<=0.1]
    kopt_temp = np.nanmean(temp_kopt['WGEN.GenActivePW'] / (temp_kopt['WGEN.GenSpd']**3))
    rotspd_power_nihe = pd.DataFrame()
    if len(temp)>100:
        rotspd_small = np.nanmean(temp.loc[temp['WGEN.GenActivePW'].nsmallest(20).index,('WGEN.GenSpd')])
        rotspd_large = np.nanmean(temp.loc[temp['WGEN.GenActivePW'].nlargest(20).index,('WGEN.GenSpd')])    
        if (np.abs(rotspd_large - rotspd_small)/(0.5*(rotspd_large + rotspd_small))<0.01)&((np.nanmean(temp['WGEN.GenActivePW'].nlargest(20)) - np.nanmean(temp['WGEN.GenActivePW'].nsmallest(20)))<0.15*Pwrat_Rate):
            rate_kopt_err = 1
            rotspd_power_nihe['rotspd'] = np.arange(Rotspd_Connect,Rotspd_Rate+(Rotspd_Rate-Rotspd_Connect)*0.0001,(Rotspd_Rate-Rotspd_Connect)*0.0001)
            rotspd_power_nihe['pwrat'] = kopt_temp*rotspd_power_nihe['rotspd']**3
            new_row = {'rotspd':Rotspd_Connect,'pwrat':0}
            rotspd_power_nihe = rotspd_power_nihe.append(new_row,ignore_index=True)
            new_row = {'rotspd':Rotspd_Rate,'pwrat':Pwrat_Rate}
            rotspd_power_nihe = rotspd_power_nihe.append(new_row,ignore_index=True)
            rotspd_power_nihe = rotspd_power_nihe.sort_values(by='pwrat',ascending=True)
            return rate_kopt_err,rotspd_power_nihe
        else:
            return rate_kopt_err,rotspd_power_nihe
    else:
        return rate_kopt_err,rotspd_power_nihe

#额定功率异常
def Pwrat_Rate_loss(data,Pwrat_Rate):
    temp = data[data['clear']<=8]
    if ((np.nanmean(temp.loc[(temp['WROT.Blade1Position']>=5),('WGEN.GenActivePW')].nlargest(10))<0.95*Pwrat_Rate)):
        return True
    else:
        False

async def judge_model(Df_all_m_clear: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    hub_high = Turbine_attr['hubHeight']
    altitude = Turbine_attr['altitude']
    rotor_radius = Turbine_attr['rotorDiameter']*0.5
    alarming = 11
    #记录异常
    # global Pwrat_Rate
    Rotspd_Connect =  get_data.Rotspd_Connect
    Pwrat_Rate =  get_data.Pwrat_Rate
    Rotspd_Rate =  get_data.Rotspd_Rate
    turbine_err_all = {}#pd.DataFrame()
    turbine_err_all['power_rate_err'] = 0  #额定功率异常
    turbine_err_all['torque_kopt_err'] = 0 #最佳Cp段转矩控制异常
    turbine_err_all['torque_rate_err'] = 0 #额定转速段转矩控制异常
    df_all_clear = Df_all_m_clear[Df_all_m_clear['clear'] == 2]
    df_all_clear['rho'] = 1.293*(10.0**(-(altitude+hub_high)/(18400.0*(1.0+0.003674*df_all_clear['WNAC.TemOut']))))/(1.0+0.003674*df_all_clear['WNAC.TemOut'])
    df_all_clear['cp'] =  2000.0*df_all_clear['WGEN.GenActivePW'] / df_all_clear['rho'] / (np.pi*rotor_radius*rotor_radius) / df_all_clear['WNAC.WindSpeed']**3
    df_all_clear['kopt'] = df_all_clear['WGEN.GenActivePW'] / (df_all_clear['WGEN.GenSpd']*0.10471)**3
    #额定功率异常
    if Pwrat_Rate_loss(Df_all_m_clear,Pwrat_Rate):
        turbine_err_all['power_rate_err'] = 1
        temp = Df_all_m_clear[Df_all_m_clear['clear']<=8]
    #最佳Cp段转矩控制异常异常
    if (turbine_err_all['power_rate_err'] == 0):
        (kopt_err,data_temp) = Torque_Cp_kopt_loss(df_all_clear,Pwrat_Rate,Rotspd_Connect,Rotspd_Rate,mytol=0.1,myreg=0.02)
        if (kopt_err==1):
            turbine_err_all['torque_kopt_err'] = 1

            cp0 = np.nanmean(data_temp[data_temp['kopt_err']==0]['cp'])
            cp1 = np.nanmean(data_temp[data_temp['kopt_err']==1]['cp'])
            if (cp0 != np.nan)&(cp1 != np.nan):
                turbine_err_all['torque_kopt_loss'] = 0.1*np.abs(cp0 - cp1) / np.nanmax([cp0,cp1])
            else:
                turbine_err_all['torque_kopt_loss'] = -999999
            cp0 = data_temp[data_temp['kopt_err']==0]
            cp1 = data_temp[data_temp['kopt_err']==1]
            #数据展示
            if cp0.shape[0] > cp1.shape[0]:
                x = [str(round(tick,4)) for tick in list(cp0['WGEN.GenSpd'])] #data_temp['WGEN.GenSpd']
                y1 = [str(round(num,4)) for num in list(cp0['WGEN.GenActivePW'])] #data_temp['WGEN.GenActivePW']
                x2 = [str(round(tick,4)) for tick in list(cp1['WGEN.GenSpd'])]#df_all_clear['WNAC.WindSpeed']
                y2 = [str(round(num,4)) for num in list(cp1['WGEN.GenActivePW'])] #df_all_clear['WGEN.GenActivePW']
            else:
                x = [str(round(tick,4)) for tick in list(cp1['WGEN.GenSpd'])] #data_temp['WGEN.GenSpd']
                y1 = [str(round(num,4)) for num in list(cp1['WGEN.GenActivePW'])] #data_temp['WGEN.GenActivePW']
                x2 = [str(round(tick,4)) for tick in list(cp0['WGEN.GenSpd'])]#df_all_clear['WNAC.WindSpeed']
                y2 = [str(round(num,4)) for num in list(cp0['WGEN.GenActivePW'])] #df_all_clear['WGEN.GenActivePW']
            data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
            data2 = pd.DataFrame({'x': x2, 'y': y2}).to_dict('records')
            # interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
            # interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
            Figs = []
            curves1 = []
            # curves2 = []
            curves1.append(DisplayResultXY('1', '正常转速-功率', '#FFFF00', '', data1))#{'type':'1', 'name': '转速-功率', "abscissaUnit": "rpm", "ordinateUnit": "kw", 'xyData': data1}
            curves1.append(DisplayResultXY('1', '异常转速-功率', '#FF0000', '', data2))#{'type':'1', 'name': '转速-功率', "abscissaUnit": "rpm", "ordinateUnit": "kw", 'xyData': data1}
            # curves2.append(DisplayResultXY('1', '风速-功率', data2))#{'type':'1', 'name': '风速-功率', "abscissaUnit": "m/s", "ordinateUnit": "kw", 'xyData': data2}
            # bins = 30
            # rangeX = np.max(data_temp['WGEN.GenSpd'].values.reshape(-1,1)) - np.min(data_temp['WGEN.GenSpd'].values.reshape(-1,1))
            result1 = DisplayFigures(xUnit="转速[rpm]", yUnit="功率[kw]", time=0, multiDimensionDataxy=curves1)#DisplayResultXY(str(round(np.min(data_temp['WGEN.GenSpd'].values.reshape(-1,1)),4)), str(round(np.max(data_temp['WGEN.GenSpd'].values.reshape(-1,1)),4)), str(round(rangeX/bins,4)), '转速-功率', curves)
            Figs.append(result1)
            # result2 = DisplayFigures(xUnit="m/s", yUnit="kw", time=0, multiDimensionDataxy=curves2)
            # Figs.append(result2)

            statementException = f'最佳Cp段转矩控制异常。'
            # 生成告警
            # push_alarm(assetId, name, datetime.now(), Df_all_m_clear.index[0], Df_all_m_clear.index[-1], alarming//7+1, idMaps)
            push_alarm(assetId, 'WGEN.GenActivePW', statementException, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), float(y2[-1]),'generator_zhuanju_kongzhi', idMaps)
            push_alarm_self(assetId, 'WGEN.GenActivePW', statementException, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), float(y2[-1]),'generator_zhuanju_kongzhi', idMaps)

            return data_temp, statementException, Figs, 0,1 # alarming, 0
        
    temp = df_all_clear[(df_all_clear['WGEN.GenSpd']>Rotspd_Connect*1.2)&(df_all_clear['WGEN.GenSpd']<Rotspd_Rate*0.9)]
    #数据展示
    x = [str(round(tick,4)) for tick in list(temp['WGEN.GenSpd'])] #data_temp['WGEN.GenSpd']
    y1 = [str(round(num,4)) for num in list(temp['WGEN.GenActivePW'])]
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    statementNormal = f'最佳Cp段转矩控制正常。'
    Figs = []
    curves1 = []
    curves1.append(DisplayResultXY('1', '转速-功率', '#FFFF00', '', data1))
    result1 = DisplayFigures(xUnit="转速[rpm]", yUnit="功率[kw]", time=0, multiDimensionDataxy=curves1)
    Figs.append(result1)
    # 生成告警
    return pd.DataFrame(), statementNormal, Figs, 0, 0

# #额定功率段转矩控制异常异常
#         else:
#             (rate_kopt_err,rotspd_power_nihe) = Torque_Rotspd_Rate_loss(df_all_clear,Pwrat_Rate,Rotspd_Rate,Rotspd_Connect)
#             #数据展示
#             x = [str(round(tick,4)) for tick in list(df_all_clear['WGEN.GenSpd'])]#'WGEN.GenSpd' .  rotspd_power_nihe['rotspd']
#             y1 = [str(round(num,4)) for num in list(df_all_clear['WGEN.GenActivePW'])]#'WGEN.GenActivePW' .  rotspd_power_nihe['pwrat']
#             x2 = [str(round(tick,4)) for tick in list(df_all_clear['WNAC.WindSpeed'])]
#             y2 = [str(round(num,4)) for num in list(df_all_clear['WGEN.GenActivePW'])]
#             data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
#             data2 = pd.DataFrame({'x': x2, 'y': y2}).to_dict('records')
#             # interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
#             # interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
#             Figs = []
#             curves1 = []
#             curves2 = []
#             curves1.append(DisplayResultXY('1', '转速-功率', data1))#{'type':'1', 'name': '转速-功率', "abscissaUnit": "rpm", "ordinateUnit": "kw", 'xyData': data1}
#             curves2.append(DisplayResultXY('1', '风速-功率', data2))#{'type':'1', 'name': '风速-功率', "abscissaUnit": "m/s", "ordinateUnit": "kw", 'xyData': data2}
#             # bins = 30
#             # rangeX = np.max(data_temp['WGEN.GenSpd'].values.reshape(-1,1)) - np.min(data_temp['WGEN.GenSpd'].values.reshape(-1,1))
#             result1 = DisplayFigures(xUnit="rpm", yUnit="kw", time=0, multiDimensionDataxy=curves1)#DisplayResultXY(str(round(np.min(data_temp['WGEN.GenSpd'].values.reshape(-1,1)),4)), str(round(np.max(data_temp['WGEN.GenSpd'].values.reshape(-1,1)),4)), str(round(rangeX/bins,4)), '转速-功率', curves)
#             Figs.append(result1)
#             result2 = DisplayFigures(xUnit="m/s", yUnit="kw", time=0, multiDimensionDataxy=curves2)
#             Figs.append(result2)
#             if (rate_kopt_err == 1):
#                 turbine_err_all['torque_rate_err'] = 1
#                 statementException = f'额定功率正常，额定转速段转矩控制异常'
#                 # 生成告警
#                 push_alarm(assetId, name, datetime.now(), Df_all_m_clear.index[0], Df_all_m_clear.index[-1], alarming//7+1)
#                 return data_temp, statementException, Figs, 0,1 # alarming, 0
#             else:
#                 statementNormal = f'额定功率正常，最佳Cp段和额定转速段转矩控制无异常' 
#                 # 生成告警
#                 return pd.DataFrame(), statementNormal, Figs, 0, 0
    # else:
    #     statementNormal = f'额定功率有异常，最佳Cp段和额定功率段转矩控制正常'
    #     #数据展示
    #     x = [str(round(tick,4)) for tick in list(temp['WGEN.GenSpd'])]
    #     y1 = [str(round(num,4)) for num in list(temp['WGEN.GenActivePW'])]
    #     x2 = [str(round(tick,4)) for tick in list(temp['WNAC.WindSpeed'])]
    #     y2 = [str(round(num,4)) for num in list(temp['WGEN.GenActivePW'])]
    #     data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    #     data2 = pd.DataFrame({'x': x2, 'y': y2}).to_dict('records')
    #     # interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
    #     # interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
    #     Figs = []
    #     curves1 = []
    #     curves2 = []
    #     curves1.append(DisplayResultXY('1', '转速-功率', data1))#{'type':'1', 'name': '转速-功率', "abscissaUnit": "rpm", "ordinateUnit": "kw", 'xyData': data1}
    #     curves2.append(DisplayResultXY('1', '风速-功率', data2))#{'type':'1', 'name': '风速-功率', "abscissaUnit": "m/s", "ordinateUnit": "kw", 'xyData': data2}
    #     # bins = 30
    #     # rangeX = np.max(data_temp['WGEN.GenSpd'].values.reshape(-1,1)) - np.min(data_temp['WGEN.GenSpd'].values.reshape(-1,1))
    #     result1 = DisplayFigures(xUnit="rpm", yUnit="kw", time=0, multiDimensionDataxy=curves1)#DisplayResultXY(str(round(np.min(data_temp['WGEN.GenSpd'].values.reshape(-1,1)),4)), str(round(np.max(data_temp['WGEN.GenSpd'].values.reshape(-1,1)),4)), str(round(rangeX/bins,4)), '转速-功率', curves)
    #     Figs.append(result1)
    #     result2 = DisplayFigures(xUnit="m/s", yUnit="kw", time=0, multiDimensionDataxy=curves2)
    #     Figs.append(result2)

def judge_model1(pn_data: DataFrame, assetId, threshold):
    gmm = BayesianGaussianMixture(n_components=2, covariance_type="full",random_state=0,tol=0.1,reg_covar=0.02)
    # 转矩系数
    pn_data['kopt'] = pn_data['WGEN.GenActivePW'] / (pn_data['WGEN.GenSpd']*0.10471)**3
    xx = pn_data.loc[:,[('kopt')]].values
    min_max_scaler = preprocessing.StandardScaler()
    train_minmax = min_max_scaler.fit_transform(xx)
    labels = gmm.fit(train_minmax).predict(train_minmax)
    # temp['kopt_err'] = labels
    pn_data['result'] = (labels == 1)

    #数据展示
    x = [str(tick) for tick in list(pn_data.index)]
    y1 = [str(round(num,4)) for num in list(train_minmax.reshape(-1))]
    y2 = [str(round(num,4)) for num in list(labels)]
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
    interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
    interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
    curves = []
    curves.append({'type':'0', 'name': '归一化转矩系数', "abscissaUnit": interval_unit, "ordinateUnit": "", 'xyData': data1})
    curves.append({'type':'0', 'name': '贝叶斯高斯后验分布', "abscissaUnit": interval_unit, "ordinateUnit": "", 'xyData': data2})
    
    result = DisplayResultXY(str(pn_data.index.min()), str(pn_data.index.max()), str(interval_value), '转矩系数', curves)

    statementException = f'对比转速功率曲线，当前功率低于理论发电功率的占比超过'
    statementNormal = f'对比转速功率曲线，当前功率低于理论发电功率的占比低于'
    # 生成告警
    data, statement = alarm.generateAlarmPercentage(name, pn_data, error_percentage, assetId, statementException, statementNormal)
    return data, statement, result, 1, 0
    
    

