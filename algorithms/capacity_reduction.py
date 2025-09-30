# -*- coding: utf-8 -*-
"""
风机降容预警
Created on Tue Aug 15 16:07:48 2023

@author: sunyan
"""
from pandas import DataFrame
from alarms import alarm
import numpy as np
from configs import config
import joblib
from utils import model_util
from sklearn import preprocessing
from utils.display_util import DisplayResultXY,DisplayFigures
from data.get_data import wash_data_for_train#, Pwrat_Rate, Rotspd_Rate, Rotspd_Connect, minPitch
import data.get_data as get_data
import pandas as pd
import utils.time_util as time_util
import asyncio
from datetime import datetime as datetime
from configs.config import algConfig, state, fitPrWt, fitWindSpd

name = algConfig['capacity_reduction']['name']#'风机降容预警'
# 把所需测点定义到每个算法里
ai_points = algConfig['capacity_reduction']['ai_points']
ai_rename = algConfig['capacity_reduction']['ai_rename']
di_points = algConfig['capacity_reduction']['di_points']
general_points = algConfig['capacity_reduction']['general_points']
private_points = algConfig['capacity_reduction']['private_points']
time_duration = algConfig['capacity_reduction']['time_duration']
resample_interval = algConfig['capacity_reduction']['resample_interval']
error_data_time_duration = algConfig['capacity_reduction']['error_data_time_duration']
need_all_turbines = algConfig['capacity_reduction']['need_all_turbines']
store_file = algConfig['capacity_reduction']['store_file']
Df_all_m = pd.DataFrame()

def wash_data(pn_data: DataFrame, ratedPower):
    global Df_all_m
    temp_data = pn_data[ai_points + di_points+ general_points]
    Df_all_m = temp_data
    '''
    剔除限功率，桨距角
    '''
    # return temp_data[(temp_data['WTUR.TurbineAIStatus'].isin([90001,90002])) 
    #         & (temp_data['WROT.Blade1Position'] > config.Pitch_Min + 2)]
    temp = wash_data_for_train(temp_data, ratedPower)
    if len(temp) >= 2000: # 判断是否满足模型执行的数据需求
        return temp, ''
    else:
        print(f'数据不满足模型需求，未执行模型{temp.shape[0]}')
        return pd.DataFrame(), f'清洗后的数据量小于2000'
    

def predict_result(pn_data: DataFrame):
    pass

#额定功率异常
def Pwrat_Rate_loss(data_,Pwrat_Rate):
    temp = data_[data_['clear']<=8]
    if ((np.nanmean(temp.loc[(temp['WROT.Blade1Position']>=5),('WGEN.GenActivePW')].nlargest(10))<0.95*Pwrat_Rate)):
        return True
    else:
        False

def pwratcurve_rho(data_,windbin,num):
    pc_df_rho = pd.DataFrame()
    for i in range(len(windbin)):
        temp = data_[(data_['WNAC.WindSpeed']>=windbin[i]-0.25) & (data_['WNAC.WindSpeed']<windbin[i]+0.25)]
        if len(temp) >= num:
            pc_df_rho.loc[i,'windbin'] = windbin[i]
            pc_df_rho.loc[i,'pwrat'] = np.mean(temp['WGEN.GenActivePW'])
            pc_df_rho.loc[i,'wspd_mean'] = np.mean(temp['WNAC.WindSpeed'])
            pc_df_rho.loc[i,'rotspd_mean'] = np.mean(temp['WGEN.GenSpd'])
            pc_df_rho.loc[i,'pwrat_std'] = np.std(temp['WGEN.GenActivePW'])            
        #pc_df = pc_df.append(pc_df)
    return pc_df_rho

def Wind_Power_Dissociation(data_,pw_df,turbine_name):
    pw_df_up = pd.DataFrame()
    pw_df_up['windbin'] = pw_df['windbin']-1.0
    pw_df_up['pwrat_up'] = pw_df[turbine_name]*1.05    
    pw_df_down = pd.DataFrame()
    pw_df_down['windbin'] = pw_df['windbin']+1.0
    pw_df_down['pwrat_down'] = pw_df[turbine_name]*0.95 
    
    pw_df_limit = pd.merge(pw_df,pw_df_up,how='inner',on='windbin')
    pw_df_limit = pd.merge(pw_df_limit,pw_df_down,how='inner',on='windbin')
    
    data_.reset_index(level=0,inplace=True)
    data_ = pd.merge(data_,pw_df_up,how='inner',on='windbin')
    data_ = pd.merge(data_,pw_df_down,how='inner',on='windbin')
    # data.set_index(('localtime',''),inplace= True)
    
    data_['dissociation'] = 0
    data_.loc[((data_['WGEN.GenActivePW']>data_['pwrat_up'])|(data_['WGEN.GenActivePW']<data_['pwrat_down'])),'dissociation'] = 1
    
    if len(data_[data_['dissociation']==1])/len(data_)>0.2:
        return data_,pw_df_limit
    else:
        data_ = pd.DataFrame()
        return data_,pw_df_limit

##单机自限电损失输入
def Turbine_Limit_Loss(data_,turbine_name,pw_df_temp,Pitch_Min,Pwrat_Rate,state): 
    limturbine_loss = False#pd.DataFrame()
    data_limt = data_[(data_['WTUR.TurbineAIStatus']==90002)&(data_['WTUR.TurbineSts']==state)]
    data_limt.reset_index(level=0,inplace=True)
    data_limt = pd.merge(data_limt,pw_df_temp,how='left',on='windbin')
    # data_limt.set_index(('localtime',''),inplace= True)
    
    pw_df_lim = pd.DataFrame()
    #pw_df_lim['windbin'] = pw_df_median['windbin']+1.0  #不能用中位数，如果某台机组功率曲线特别差，则很有可能大部分散点都在下边界以下，导致计算结果不对
    #pw_df_lim['pwrat'] = pw_df_median['pwrat']*0.95
    
    pw_df_lim['windbin'] = pw_df_temp['windbin']+1.0
    pw_df_lim['pwrat_lim'] = pw_df_temp[turbine_name]*0.95
    
    data_limt = pd.merge(data_limt,pw_df_lim,how='outer',on='windbin')#,suffixes=('_org','_lim'))
    #出图展示data_limt风速功率散点、风机功率曲线、功率曲线下线
    '''
    fig = plt.figure(figsize=(10,8),dpi=100)  
    plt.title(str(turbine_name))    
    with plt.style.context('ggplot'):  
        plt.scatter(data_limt['wspd','nanmean'],data_limt['pwrat','nanmean'],color='cornflowerblue',s=10) 
        plt.scatter(data_limt['windbin'],data_limt[turbine_name],color='r')
        plt.scatter(pw_df_lim['windbin'],pw_df_lim['pwrat_lim'],color='g')
        plt.grid()
        #plt.ylim(-3,25)
        plt.xlabel('风速(m/s)',fontsize=14)
        plt.ylabel('功率(kW)',fontsize=14)
        #plt.colorbar()
    fig.savefig(path + '/' +str(turbine_name) + '_限电2.png',dpi=100)
    '''
    data_limt_lim = data_limt[(data_limt['WGEN.GenActivePW']<data_limt['pwrat_lim'])&(data_limt['WGEN.GenActivePW']<Pwrat_Rate*0.8)&(data_limt['WGEN.GenActivePW']>100.0)&(data_limt['WROT.Blade1Position']>Pitch_Min+2.5)]
    
    if len(data_limt_lim) > 6:
        # limturbine_loss.loc[turbine_name,'loss'] = np.nansum(data_limt_lim[turbine_name] - data_limt_lim['pwrat','nanmean'])/6.0
        # limturbine_loss.loc[turbine_name,'time'] = len(data_limt_lim)/6.0
        # limturbine_loss.loc[turbine_name,'wspd'] = np.nanmean(data_limt_lim['wspd','nanmean'])
        limturbine_loss = True
    return data_limt,limturbine_loss
    
async def judge_model(Df_all_m_clear: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    assetId = Turbine_attr['mdmId']
    turbine_err_all = {}#pd.DataFrame()
    turbine_err_all['power_rate_err'] = 0  #额定功率异常
    turbine_err_all['torque_kopt_err'] = 0 #最佳Cp段转矩控制异常
    turbine_err_all['torque_rate_err'] = 0 #额定转速段转矩控制异常
    turbine_err_all['wspd_power_err'] = 0  #风速功率散点异常
    pw_df_all = pd.DataFrame()
    
    # windbinreg = np.arange(1.75,25.25,0.5)
    # windbin = np.arange(2.0,25.0,0.5)
    # pw_df_all['windbin'] = windbin
    turbine_name = assetId
    state = 6
    # Df_all_m['windbin'] = pd.cut(Df_all_m['WNAC.WindSpeed'],windbinreg,labels=windbin)
    minPitch = get_data.minPitch
    Pwrat_Rate = get_data.Pwrat_Rate


    ##绘制功率曲线
    # pw_df = pwratcurve_rho(df_all_clear,windbin,6)
    # pw_df = pw_df.loc[:,['windbin','pwrat']]
    # pw_df.rename(columns = {'pwrat':turbine_name},inplace = True) 
    # pw_df_all = pd.merge(pw_df_all,pw_df,how='outer',on='windbin')
    # data_limt = Df_all_m_clear
    # limturbine_loss = False

    #额定功率异常
    if Pwrat_Rate_loss(Df_all_m_clear,Pwrat_Rate):
        turbine_err_all['power_rate_err'] = 1
        df_all_clear = Df_all_m_clear[Df_all_m_clear['clear']<=8]
    else:
        turbine_err_all['power_rate_err'] = 0
        df_all_clear = Df_all_m_clear[Df_all_m_clear['clear'] == 2]
    #风速-功率散点异常离散(额定功率异常的不判别)
    # if (turbine_err_all['power_rate_err'] == 0):
    #     pw_df_temp = pw_df_all.loc[:,['windbin',turbine_name]]
    #     pw_df_temp = pw_df_temp.dropna()
    #     df_all_clear['windbin'] = pd.cut(df_all_clear['WNAC.WindSpeed'],windbinreg,labels=windbin)
    #     df_all_clear.reset_index(level=0,inplace=True)
    #     df_all_clear = pd.merge(df_all_clear,pw_df_temp,how='inner',on='windbin')
    #     # df_all_clear.set_index(('localtime',''),inplace= True) 
    #     (data_temp,pw_df_limit) =  Wind_Power_Dissociation(df_all_clear,pw_df_temp,turbine_name)
    #     if len(data_temp)>0:
    #         turbine_err_all['wspd_power_err'] = 1
    # if (turbine_err_all['wspd_power_err'] == 0):###风速功率散点异常不计算
    #     (data_limt,limturbine_loss) = Turbine_Limit_Loss(Df_all_m,turbine_name,pw_df_temp,minPitch,Pwrat_Rate,state)
    
    x = fitWindSpd #[str(round(tick,4)) for tick in list(df_all_clear['WGEN.GenSpd'])]
    y1 = fitPrWt
    #数据展示
    x = [str(round(tick,4)) for tick in list(x)]
    y1 = [str(round(num,4)) for num in list(y1)]
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    # if limturbine_loss == True:
    x2 = [str(round(tick,4)) for tick in list(df_all_clear['WNAC.WindSpeed'])]
    y2 = [str(round(num,4)) for num in list(df_all_clear['WGEN.GenActivePW'])]
    data2 = pd.DataFrame({'x': x2, 'y': y2}).to_dict('records')
    # interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
    # interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
    Figs = []
    curves1 = []
    curves1.append(DisplayResultXY('0', '理论风速-功率', '#FFFF00', 'Solid', data1))#{'type':'1', 'name': '转速-功率', "abscissaUnit": "rpm", "ordinateUnit": "kw", 'xyData': data1}
    # if limturbine_loss == True:
    curves1.append(DisplayResultXY('1', '风速-功率', '#00FF00', '', data2))#{'type':'1', 'name': '转速-功率', "abscissaUnit": "rpm", "ordinateUnit": "kw", 'xyData': data1}
    # bins = 30
    # rangeX = np.max(data_temp['WGEN.GenSpd'].values.reshape(-1,1)) - np.min(data_temp['WGEN.GenSpd'].values.reshape(-1,1))
    result1 = DisplayFigures(xUnit="风速[m/s]", yUnit="功率[kw]", time=0, multiDimensionDataxy=curves1)#DisplayResultXY(str(round(np.min(data_temp['WGEN.GenSpd'].values.reshape(-1,1)),4)), str(round(np.max(data_temp['WGEN.GenSpd'].values.reshape(-1,1)),4)), str(round(rangeX/bins,4)), '转速-功率', curves)
    Figs.append(result1)

    if turbine_err_all['power_rate_err'] == 1:
        statementException = f'从风速功率曲线看，当前电功率低于理论发电功率'
        limturbine_loss = True
    else:
        statementException = f'从风速功率曲线看，当前功率曲线正常'
        limturbine_loss = False
    
    # 生成告警
    data_, statement, alarming =  alarm.generateBaseAlarm(name,'capacity_reduction','WGEN.GenActivePW', df_all_clear, limturbine_loss, assetId, 2020, statementException, idMaps)
    return data_, statement, Figs, 0,1 # alarming, 0

    
def judge_model1(pn_data: DataFrame, assetId, threshold):
    # 低于标准功率曲线有多少百分比数据点
    # 加载标准风速功率曲线
    # function = joblib.load('model/speed_power.model')
    function = model_util.load_model(config.Wind_Farm, 'speed_power', assetId, 'speed_power')
    #归一化数据
    scalorWS = preprocessing.MinMaxScaler()
    pn_data['wsTransformed'] = scalorWS.fit_transform(pn_data[['WNAC.WindSpeed']])
    scalorPW = preprocessing.MinMaxScaler()
    pn_data['pwTransformed'] = scalorPW.fit_transform(pn_data[['WGEN.GenActivePW']])
    pn_data['theory_power_transformed'] = function(pn_data['wsTransformed'])
    #逆变换
    pn_data['theory_power'] = scalorPW.inverse_transform(pn_data[['theory_power_transformed']])
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
    x = [datetime.strptime(tick, "%Y-%m-%d %H:%M:%S") for tick in x]
    x = [int(tick.timestamp()*1000) for tick in x]
    y1 = [str(round(num,4)) for num in list(pn_data['theory_power'])]
    y2 = [str(round(num,4)) for num in list(pn_data['WGEN.GenActivePW'])]
    data1 = pd.DataFrame({'x': x, 'y': y1}).to_dict('records')
    data2 = pd.DataFrame({'x': x, 'y': y2}).to_dict('records')
    interval_value, interval_unit = time_util.split_time_delta(resample_interval) 
    interval_unit = time_util.__timedelta_resample_unit_dict[interval_unit].lower()
    Figs = []
    curves1 = []
    curves1.append(DisplayResultXY('0', '理论发电', data1))#0:线，1:点 .   {'type':'0', 'name': '理论发电', "abscissaUnit": interval_unit, "ordinateUnit": "kw", 'xyData': data1}
    curves1.append(DisplayResultXY('0', '当前桨距角发电', data2))#{'type':'0', 'name': '当前桨距角发电', "abscissaUnit": interval_unit, "ordinateUnit": "kw", 'xyData': data2}
    
    result1 = DisplayFigures(xUnit=interval_unit, yUnit="kw", time=1, multiDimensionDataxy=curves1)#(str(pn_data.index.min()), str(pn_data.index.max()), str(interval_value), '功率', curves)
    Figs.append(result1)

    statementException = f'从风速功率曲线看，当前功率低于理论发电功率的采样点数量超过'
    statementNormal = f'从风速功率曲线看，当前功率低于理论发电功率的采样点数量低于'
    
    # 生成告警
    data, statement, alarming =  alarm.generateAlarmPercentage(name,'capacity_reduction', pn_data, 0.2, assetId, statementException, statementNormal)
    return data, statement, Figs, alarming, 0
