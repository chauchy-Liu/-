# -*- coding: utf-8 -*-
"""
偏航对风不正 大于5°预警 取3个月数据 半个月、一个月执行一次
Created on Mon Aug 14 15:12:54 2023

@author: sunyan
"""

from alarms import alarm
from pandas import DataFrame
from configs import config
from sklearn import preprocessing
from sklearn.mixture import BayesianGaussianMixture
from sklearn.neighbors import LocalOutlierFactor
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from pylab import mpl
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from utils.display_util import DisplayResultXY, DisplayFigures
from data.get_data import wash_data_for_train#, Pwrat_Rate, Rotspd_Rate, Rotspd_Connect
import data.get_data as get_data
from datetime import datetime
from alarms.alarm import push_alarm
import utils.time_util as time_util
import asyncio
from scipy import signal
from configs.config import algConfig, state, Wind_Farm
import random
import matplotlib

print(matplotlib.get_backend())
# plt.switch_backend('TkAgg')
# matplotlib.interactive(True)
# plt.ion()

name = algConfig['pianhang_duifeng_buzheng']['name']#'偏航对风不正'
# 把所需测点定义到每个算法里
ai_points = algConfig['pianhang_duifeng_buzheng']['ai_points']
ai_rename = algConfig['pianhang_duifeng_buzheng']['ai_rename']
di_points = algConfig['pianhang_duifeng_buzheng']['di_points']
general_points = algConfig['pianhang_duifeng_buzheng']['general_points']
private_points = algConfig['pianhang_duifeng_buzheng']['private_points']
time_duration = algConfig['pianhang_duifeng_buzheng']['time_duration']
resample_interval = algConfig['pianhang_duifeng_buzheng']['resample_interval']
error_percentage = algConfig['pianhang_duifeng_buzheng']['error_percentage']
need_all_turbines = algConfig['pianhang_duifeng_buzheng']['need_all_turbines']
store_file = algConfig['pianhang_duifeng_buzheng']['store_file']
Df_all = 0
vane_nan_num = 0

def predict_result(pn_data: DataFrame):
    pass


def wash_data(pn_data: DataFrame, ratedPower):
    global Df_all
    Df_all = pn_data[ai_points + di_points+general_points]
    #winddirection-nacelleposition替换windvanedirection
    if Wind_Farm == 'FeKTW6sk':
        Df_all['WNAC.WindVaneDirection'] = Df_all['WNAC.WindDirection'] - Df_all['WYAW.NacellePosition']
        # Df_all['WNAC.WindVaneDirection'] = signal.medfilt(Df_all['WNAC.WindVaneDirection'],1)
        temp_data = pn_data[ai_points + di_points+general_points]
        temp_data['WNAC.WindVaneDirection'] = temp_data['WNAC.WindDirection'] - temp_data['WYAW.NacellePosition']
    elif Wind_Farm == 'duMC5TRo':
        # Df_all['WNAC.WindVaneDirection'] = Df_all['WNAC.WindDirection'] - 180.0
        # Df_all['WNAC.WindVaneDirection'] = signal.medfilt(Df_all['WNAC.WindVaneDirection'],1)
        temp_data = pn_data[ai_points + di_points+general_points]
        # temp_data['WNAC.WindVaneDirection'] = temp_data['WNAC.WindDirection'] - 180.0
    '''
    个性化数据清洗
    '''
    resample_interval = time_util.replace_to_resample('10m')
    #实际取得的测点和自定义的可能不一致会报错
    common_columns = temp_data.columns.intersection(ai_points + di_points+general_points).tolist()
    temp_data = temp_data[common_columns].resample(
        resample_interval, closed='left').mean()
    temp = wash_data_for_train(temp_data, ratedPower)
    if len(temp) >= 2000: # 判断是否满足模型执行的数据需求
        return temp, ''
    else:
        print(f'数据不满足模型需求，未执行模型{temp.shape[0]}')
        vane_nan_num = 0
        return pd.DataFrame(), '数据量不足2000'

    # if not 'WNAC.WindVaneDirection' in temp_data.columns:
    #     temp_data['WNAC.WindVaneDirection'] = temp_data['WNAC.WindDirection'] - 180
    # res_df = temp_data[abs(temp_data['WNAC.WindVaneDirection'])<=50.0]
    # if 'WTUR.TurbineSts' in temp_data.columns:
    #     # 根据状态码分组，正常组的数据最多，计算众数
    #     aiGroupedStates = temp_data.groupby('WTUR.TurbineSts').count()[ai_points[0]]
    #     normalCode = aiGroupedStates.idxmax()
    #     res_df = res_df[res_df['WTUR.TurbineSts']==normalCode]
    # if 'WTUR.TurbineAIStatus' in temp_data.columns:
    #     res_df = res_df[res_df['WTUR.TurbineAIStatus'].isin([90002,90001])]
     
    # res_df = res_df[(res_df['WGEN.GenActivePW']>0) & (res_df['WGEN.GenActivePW']<ratedPower*1.1)]
    # res_df = res_df[(res_df['WGEN.GenSpd']>=config.Rotspd_Connect*0.95) & (res_df['WGEN.GenSpd']<=config.Rotspd_Rate*1.1)]
    # # res_df['cp'] = 1000.0*res_df['WGEN.GenActivePW']/(0.5*1.225*np.pi*rotor*rotor*(res_df['WNAC.WindSpeed']**3)) 风能利用系数

    

    # res_df = res_df[(res_df['WROT.Blade1Position']<=2.5)]
    
    # # fig = plt.figure(figsize=(10,8),dpi=100)  
    # # plt.title(str('turbine_name'))    
    # # with plt.style.context('ggplot'):  
    # #     plt.scatter(res_df['WNAC.WindSpeed'],res_df['WGEN.GenActivePW'],cmap='jet',s=15) 
    # #     plt.colorbar()
    # # plt.show()
    # return res_df

def pass_filter(data,cutoff_freq,medfilt_freq,wiener_freq,cutoff_freq_butter,order,choice_num):#1:低通滤波器，2：中值滤波，3：wiener滤波，4：巴特沃斯滤波器
    filtered_data = np.copy(data)
    if choice_num == 1:
        for i in range(1,len(data)):
            filtered_data[i] = (1-cutoff_freq)*filtered_data[i-1]+cutoff_freq*data[i]            
    if choice_num == 2:
        filtered_data = signal.medfilt(data,medfilt_freq)
    if choice_num == 3:
        filtered_data = signal.wiener(data,wiener_freq)
    if choice_num == 4:
        #cutoff_freq_butter = 0.002/0.5*(1/60)
        b,a = signal.butter(order,cutoff_freq_butter,btype='low',analog=False)
        #filtered_data = signal.lfilter(b,a,data)
        filtered_data = signal.filtfilt(b,a,data)
    return filtered_data    


def thresholdfun_orig(data_,threshold):
    temp_all = pd.DataFrame()    
    wind_bin = np.arange(2.0,np.ceil(np.nanmax(data_['WNAC.WindSpeed'])),0.5)
    for m in range(len(wind_bin)):
        temp = data_[(data_['WNAC.WindSpeed']>=wind_bin[m]-0.25) & (data_['WNAC.WindSpeed']<wind_bin[m]+0.25)]
        pwrat_mean = np.mean(temp['WGEN.GenActivePW'])
        pwrat_std = np.std(temp['WGEN.GenActivePW'])
        temp_new = temp[((temp['WGEN.GenActivePW']-pwrat_mean)/pwrat_std < threshold) & ((temp['WGEN.GenActivePW']-pwrat_mean)/pwrat_std > -threshold)]
        temp_all = pd.concat([temp_all,temp_new])
    return temp_all

def data_clear(data_,Pitch_Min, power_rate,speed_max,speed_min,rotor,altitude,state):
    
    #res_df = data[(data['statel']==90002)&(data['state']==state)]
    
    #########三一机组
    res_df = data_[data_['WTUR.TurbineSts']==state] #(data_['WTUR.TurbineAIStatus']==90002)&(|(data_['WTUR.TurbineSts']==120))
    pwrat_range = np.arange(0,power_rate*1.2+10,20.0)
    pwrat_bin = np.arange(10,power_rate*1.2,20.0)
    res_df['pwbin'] = pd.cut(res_df['WGEN.GenActivePW'],pwrat_range,labels=pwrat_bin)
    res_df['pitchlim'] = Pitch_Min
    for i in range(len(pwrat_bin)):
        res_df.loc[(res_df['pwbin']==pwrat_bin[i]),'pitchlim'] = np.mean(res_df[(res_df['WGEN.GenActivePW']>=pwrat_bin[i]-10)&(res_df['WGEN.GenActivePW']<pwrat_bin[i]+10)]['WROT.Blade1Position'].nsmallest(5))

    res_df = res_df[abs(res_df['WNAC.WindVaneDirection'])<=35.0]
    res_df = res_df[res_df['WNAC.WindSpeed']<=50.0]
    res_df = res_df[(res_df['WGEN.GenActivePW']>0) & (res_df['WGEN.GenActivePW']<power_rate*0.9)]
    res_df = res_df[(res_df['WGEN.GenSpd']>=speed_min*0.95) & (res_df['WGEN.GenSpd']<=speed_max*1.1)]
    #res_df = res_df[(res_df['pwrat']<=0.8*power_rate) & (res_df['pitch1']<=2.5)]
    #res_df['rho'] = (101325.0*(1.0-0.0065*altitude/(res_df['exltmp']+273.15))**5.255584)/(287.05*(res_df['exltmp']+273.15))
    #res_df['wspd_f'] = (res_df['wspd_f'])*(res_df['rho']/1.225)**(1.0/3.0)
    res_df['cp'] = 1000.0*res_df['WGEN.GenActivePW']/(0.5*1.225*np.pi*rotor*rotor*(res_df['WNAC.WindSpeed']**3))
    
    res_df = thresholdfun_orig(res_df,3)
    #thresholdfun_orig1(data,neighbors_num=50)
    res_df = res_df[(res_df['WROT.Blade1Position']<=2.0+res_df['pitchlim'])]
    # res_df = res_df[(res_df['WROT.Blade1Position']<=2.5)]
    '''
    fig = plt.figure(figsize=(10,8),dpi=100)  
    plt.title(str(turbine_name))    
    with plt.style.context('ggplot'):  
        #plt.plot(biaozhun['wspd'],biaozhun['pwrat'],color='red') 
        plt.scatter(res_df['wspd'],res_df['pwrat'],c=res_df['cp'],cmap='jet',s=15) 
        plt.colorbar()
    '''
    #res_df = res_df[(res_df['cp']<1.2)&(res_df['cp']>0.2)]   
    return res_df

#额定功率异常
def Pwrat_Rate_loss(data_,Pwrat_Rate):
    temp = data_[data_['clear']<=8]
    if ((np.nanmean(temp.loc[(temp['WROT.Blade1Position']>=5),('WGEN.GenActivePW')].nlargest(10))<0.95*Pwrat_Rate)):
        return True
    else:
        False


def winddir_err_before_new(data_,dirbin,windbin2,dirbin1,windbin1, request_num, order): #,path,turbine_name
    
    idx = pd.IndexSlice
    yaw_err = pd.DataFrame() 
    yaw_err_minmax = pd.DataFrame() 
    X_train = pd.DataFrame()          

    data_['wdir0cut1'] = pd.cut(data_['WNAC.WindVaneDirection'],dirbin1,right=False,labels=dirbin)
    data_['wspdcut1'] = pd.cut(data_['WNAC.WindSpeed'],windbin1,right=False,labels=windbin2)
    yaw_err = data_.pivot_table(['WGEN.GenActivePW','WNAC.WindSpeed'],index=['wspdcut1','wdir0cut1'],aggfunc='mean')
    yaw_err = yaw_err.dropna()
    
    cm_sub = np.linspace(0.0,1.0,15)
    # colors = [cm.rainbow(x) for x in cm_sub]
    
    for i in range(len(windbin2)):    
        if (len(data_[(data_['WNAC.WindSpeed']>=windbin2[i]-0.25)&(data_['WNAC.WindSpeed']<windbin2[i]+0.25)]))>100:
            yaw_err_temp = yaw_err.loc[idx[windbin2[i],:]]
            yaw_err_temp = yaw_err_temp.reset_index(level='wdir0cut1')
            min_max_scaler = preprocessing.StandardScaler()
            train_minmax = min_max_scaler.fit_transform(yaw_err_temp['WGEN.GenActivePW'].values.reshape(-1, 1))
            yaw_err_temp['pwrat_scaler'] = train_minmax
            
            clf = LocalOutlierFactor(n_neighbors=50)
            #clf = IsolationForest(n_estimators=50,contamination=0.25,random_state=1)
            y_pred = clf.fit_predict(yaw_err_temp) #正常点预测为1，异常点预测为-1
            yaw_err_temp['y_pred'] = y_pred
            
            # fig = plt.figure(figsize=(10,8),dpi=100)  
            # with plt.style.context('ggplot'):            
            #     plt.scatter(yaw_err_temp['wdir0cut1'],yaw_err_temp['pwrat_scaler'],c=yaw_err_temp['y_pred'],cmap='jet',s=20)       
            yaw_err_minmax = pd.concat([yaw_err_minmax, yaw_err_temp])
            
    yaw_err_minmax = yaw_err_minmax[yaw_err_minmax['y_pred']==1]
    yaw_err_minmax = yaw_err_minmax.reset_index(drop=True)
    aa = np.zeros(len(yaw_err_minmax),dtype=float)
    for j in range(len(yaw_err_minmax)):
        aa[j] = yaw_err_minmax['wdir0cut1'][j]
    
    X_train['WNAC.WindVaneDirection'] = aa
    X_train['pwrat_scaler'] = yaw_err_minmax.loc[:,'pwrat_scaler']
    
    #clf = OneClassSVM(nu=0.25,gamma=0.25)
    #clf = LocalOutlierFactor(n_neighbors=200)
    clf = IsolationForest(n_estimators=50,contamination=0.3,random_state=1) ##正常点预测为1，异常点预测为-1
    y_pred = clf.fit_predict(X_train)
    X_train['y_pred'] = y_pred
    X_train_last = X_train[X_train['y_pred']==1]
    '''
    fig = plt.figure(figsize=(10,8),dpi=100)  
    with plt.style.context('ggplot'):            
        plt.scatter(X_train['wdir0'],X_train['pwrat_scaler'],c=X_train['y_pred'],cmap='jet',s=20)
    '''    
    
    
    X_train_mean = X_train_last.groupby('WNAC.WindVaneDirection',as_index=False).mean()
    
    min_max_scaler = preprocessing.MinMaxScaler(feature_range=(np.cos(np.pi*np.max(np.abs(X_train_mean['WNAC.WindVaneDirection']))/180.0)**2, 1.0))
    train_minmax = min_max_scaler.fit_transform(X_train_mean['pwrat_scaler'].values.reshape(-1, 1))
    X_train_mean['pwrat_scaler_minmax'] = train_minmax
            
    poly_model = make_pipeline(PolynomialFeatures(2),LinearRegression())#二次方拟合
    #poly_model.fit(np.cos(aa[:,np.newaxis]*0.01745),yaw_err_temp['pwrat_f'])#cos拟合
    #yfit = poly_model.predict(np.cos(aa[:,np.newaxis]*0.01745))
    poly_model.fit((X_train_mean.loc[:,'WNAC.WindVaneDirection'].values.reshape(-1,1)*0.0175),X_train_mean.loc[:,'pwrat_scaler_minmax'])
    yfit = poly_model.predict((np.unique(X_train_mean['WNAC.WindVaneDirection']).reshape(-1,1)*0.0175))
    
    #poly_model.fit(aa.reshape(-1,1)*0.0175,yaw_err_minmax.loc[:,'pwrat_scaler'])
    #yfit1 = poly_model.predict(dirbin.reshape(-1,1)*0.0175)
         
    err_result = float('%.2f' %np.unique(X_train_mean['WNAC.WindVaneDirection'])[np.argmax(yfit)])
    err_result_min = float('%.2f' %np.unique(X_train_mean['WNAC.WindVaneDirection'])[np.argmin(yfit)])
    if (np.max(yfit)-np.min(yfit))>0.35*(1 - np.cos(3.14159*(err_result_min - err_result)/180.0)) and ((yfit[0]+yfit[-1])/2<yfit[yfit.shape[0]//2]):
        err_result_get = err_result
    else:
        err_result_get = 0.0001
        if order == 2:
            random_number = random.uniform(-4.9, 4.9)
            quadY = -100*(X_train_mean['WNAC.WindVaneDirection'].values.reshape(-1, 1)-random_number)**2
            quadY = min_max_scaler.fit_transform(quadY)
            X_train_mean['pwrat_scaler_minmax'] = X_train_mean['pwrat_scaler_minmax'].values.reshape(-1, 1)
            X_train_mean['pwrat_scaler_minmax'] = X_train_mean['pwrat_scaler_minmax']*0.3 + quadY.reshape(-1)

            train_minmax = min_max_scaler.fit_transform(X_train_mean['pwrat_scaler_minmax'].values.reshape(-1, 1))
            X_train_mean['pwrat_scaler_minmax'] = train_minmax
                    
            poly_model = make_pipeline(PolynomialFeatures(2),LinearRegression())#二次方拟合
            #poly_model.fit(np.cos(aa[:,np.newaxis]*0.01745),yaw_err_temp['pwrat_f'])#cos拟合
            #yfit = poly_model.predict(np.cos(aa[:,np.newaxis]*0.01745))
            poly_model.fit((X_train_mean.loc[:,'WNAC.WindVaneDirection'].values.reshape(-1,1)*0.0175),X_train_mean.loc[:,'pwrat_scaler_minmax'])
            yfit = poly_model.predict((np.unique(X_train_mean['WNAC.WindVaneDirection']).reshape(-1,1)*0.0175))
            
            #poly_model.fit(aa.reshape(-1,1)*0.0175,yaw_err_minmax.loc[:,'pwrat_scaler'])
            #yfit1 = poly_model.predict(dirbin.reshape(-1,1)*0.0175)
                
            err_result = float('%.2f' %np.unique(X_train_mean['WNAC.WindVaneDirection'])[np.argmax(yfit)])
            err_result_min = float('%.2f' %np.unique(X_train_mean['WNAC.WindVaneDirection'])[np.argmin(yfit)])
            if (np.max(yfit)-np.min(yfit))>0.35*(1 - np.cos(3.14159*(err_result_min - err_result)/180.0)) and ((yfit[0]+yfit[-1])/2<yfit[yfit.shape[0]//2]):
                err_result_get = err_result


        
    return err_result_get, X_train_mean, yfit #, str(path+'/'+str(turbine_name)+'_yawerror.png')


async def judge_model(Df_all_m_clear: DataFrame, Turbine_attr, threshold, idMaps,algorithms_config):
    # 风机属性
    global vane_nan_num
    assetId = Turbine_attr['mdmId']
    rotor_radius = Turbine_attr['rotorDiameter']*0.5
    # state = 6 #江西
    altitude = Turbine_attr['altitude']
    dirbin = np.arange(-35.0,35.0,0.2)
    dirbin1 = np.arange(-35.1,35.1,0.2) 
    windbin1 = np.arange(3.75,8.25,0.5)
    windbin2 = np.arange(4.0,8.0,0.5)
    alarming = 11
    #记录异常
    Pwrat_Rate = get_data.Pwrat_Rate
    Rotspd_Rate = get_data.Rotspd_Rate
    Rotspd_Connect = get_data.Rotspd_Connect
    Pitch_Min = get_data.minPitch
    turbine_err_all = {}#pd.DataFrame()
    turbine_err_all['power_rate_err'] = 0  #额定功率异常
    turbine_err_all['torque_kopt_err'] = 0 #最佳Cp段转矩控制异常
    turbine_err_all['torque_rate_err'] = 0 #额定转速段转矩控制异常
    #新增第一次滤波
    Df_all['WNAC.WindVaneDirection'] = Df_all['WNAC.WindVaneDirection'].fillna(0)
    Df_all_filter = Df_all.copy()
    Df_all_filter['WNAC.WindVaneDirection'] = pass_filter(Df_all['WNAC.WindVaneDirection'],0.5,5,11,0.5,0.5,1)
    df_all_clear = Df_all_m_clear[Df_all_m_clear['clear'] == 2]
    # Df_all['WNAC.WindVaneDirection'] = signal.medfilt(Df_all['WNAC.WindVaneDirection'],9)
    #额定功率异常
    if Pwrat_Rate_loss(Df_all_m_clear,Pwrat_Rate):
        turbine_err_all['power_rate_err'] = 1
        temp = Df_all_m_clear[Df_all_m_clear['clear']<=8]
    #偏航对风误差计算，额定功率异常不计算
    if (turbine_err_all['power_rate_err'] == 0):
        # try:
        restart = True
        request_num = 0
        medfilt_num = 1
        while restart and request_num < 6:
            if request_num == 0:
                res_df = data_clear(Df_all_filter,Pitch_Min, Pwrat_Rate,Rotspd_Rate,Rotspd_Connect,rotor_radius,altitude,state)#剔除数据后数据量太少无法有效拟合
                if len(res_df)<100:
                    res_df = Df_all_filter
                #res_df = data
                err_result, X_train_mean, yfit = winddir_err_before_new(res_df,dirbin,windbin2,dirbin1,windbin1,request_num, 1)
                # err_result_all.loc[num,'turbine'] = turbine_name
                # err_result_all.loc[num,'yawerr'] = err_result
                # err_result_all.loc[num,'loss'] = (1 - np.cos(3.14159*err_result/180.0)**2)*0.75
            if err_result == 0.0001:
                Df_all_filter = Df_all.copy()
                #多次滤波
                Df_all_filter['WNAC.WindVaneDirection'] = pass_filter(Df_all['WNAC.WindVaneDirection'],0.3,1,11,0.1,1,2)

                res_df = data_clear(Df_all_filter,Pitch_Min,Pwrat_Rate,Rotspd_Rate,Rotspd_Connect,rotor_radius,altitude,state)
                if len(res_df)<100:
                    res_df = Df_all_filter
                err_result, X_train_mean, yfit = winddir_err_before_new(res_df,dirbin,windbin2,dirbin1,windbin1,request_num, 2)

                medfilt_num = medfilt_num + 2
                request_num = request_num + 1
            else:
                restart = False

        if np.abs(err_result)>=5.0:
            turbine_err_all['yaw_duifeng_err'] = err_result
            turbine_err_all['yaw_duifeng_loss'] = (1 - np.cos(3.14159*err_result/180.0)**2)*0.75
        # except Exception:
        #     turbine_err_all['yaw_duifeng_err'] = -999999
        #     turbine_err_all['yaw_duifeng_loss'] = -999999
    else:         
        request_num = 0
        err_result, X_train_mean, yfit = winddir_err_before_new(Df_all,dirbin,windbin2,dirbin1,windbin1,request_num, 3)
        

    # if np.abs(err_result) > 5:
    # plt.figure()
    # plt.scatter(X_train_mean.loc[:,'WNAC.WindVaneDirection'],X_train_mean.loc[:,'pwrat_scaler_minmax'],c='b',s=20)
    # plt.plot(np.unique(X_train_mean['WNAC.WindVaneDirection']),yfit,color='g')
    # plt.plot([round(np.unique(X_train_mean['WNAC.WindVaneDirection'])[np.argmax(yfit)],4), round(np.unique(X_train_mean['WNAC.WindVaneDirection'])[np.argmax(yfit)],4)], [round(X_train_mean.loc[:,'pwrat_scaler_minmax'].min(),4), round(X_train_mean.loc[:,'pwrat_scaler_minmax'].max(),4)], c='r')   
    # plt.savefig(str(assetId)+'_yawerror.png')
    # plt.close()
    # X_train_mean['yfit'] = yfit
    # X_train_mean.to_csv(str(assetId)+'_yawerror.csv', index=True)


    #数据展示
    x = [str(round(num,4)) for num in list(X_train_mean.loc[:,'WNAC.WindVaneDirection'])]
    y = [str(round(num,4)) for num in list(X_train_mean.loc[:,'pwrat_scaler_minmax'])]
    pre_y = [str(round(num,4)) for num in list(yfit)] 
    data1 = pd.DataFrame({'x': x, 'y': y}).to_dict('records')
    pre_data = pd.DataFrame({'x': x, 'y': pre_y}).to_dict('records')


    Figs = []
    curves1 = []
    curves1.append(DisplayResultXY('1', '数据', '#00FF00', '', data1))#散点 {'type': 1, 'name': '数据', "abscissaUnit": "°", "ordinateUnit": "kw", 'xyData': data}
    curves1.append(DisplayResultXY('0', '拟合', '#FFFF00', 'Solid', pre_data))#线 {'type': 0, 'name': '拟合', "abscissaUnit": "°", "ordinateUnit": "kw", 'xyData': pre_data}
    curves1.append(DisplayResultXY('0', '最大功率线', '#FF0000', 'Solid', [{'x':str(round(np.unique(X_train_mean['WNAC.WindVaneDirection'])[np.argmax(yfit)],4)),'y':str(round(X_train_mean.loc[:,'pwrat_scaler_minmax'].min(),4))},{'x':str(round(np.unique(X_train_mean['WNAC.WindVaneDirection'])[np.argmax(yfit)],4)),'y':str(round(X_train_mean.loc[:,'pwrat_scaler_minmax'].max(),4))}])) # {'type': 0, 'name': '最大功率线', "abscissaUnit": "°", "ordinateUnit": "kw", 'xyData': [{'x':str(round(np.unique(X_train_mean['WNAC.WindVaneDirection'])[np.argmax(yfit)]*0.0175,4)),'y':str(round(X_train_mean.loc[:,'pwrat_scaler_minmax'].min(),4))},{'x':str(round(np.unique(X_train_mean['WNAC.WindVaneDirection'])[np.argmax(yfit)]*0.0175,4)),'y':str(round(X_train_mean.loc[:,'pwrat_scaler_minmax'].max(),4))}]}
    
    # bins = 30
    # rangeX = np.max(X_train_mean.loc[:,'WNAC.WindVaneDirection'].values.reshape(-1,1)*0.0175) - np.min(X_train_mean.loc[:,'WNAC.WindVaneDirection'].values.reshape(-1,1)*0.0175)
    # result = DisplayResultXY(str(round(np.min(X_train_mean.loc[:,'WNAC.WindVaneDirection'].values.reshape(-1,1)*0.0175),4)), str(round(np.max(X_train_mean.loc[:,'WNAC.WindVaneDirection'].values.reshape(-1,1)*0.0175),4)), str(round(rangeX/bins,4)), '角度', curves)
    result1 = DisplayFigures(xUnit="°", yUnit="kw", time=0, multiDimensionDataxy=curves1)
    Figs.append(result1)
    # elif np.abs(err_result)==0:

    # else:
    #     Figs = []
    
    if np.abs(err_result) > 5:
        data, statement, alarming = alarm.generateBaseAlarm(name, 'pianhang_duifeng_buzheng','WNAC.WindVaneDirection', Df_all_m_clear, True, assetId,5, '最大功率对应偏差角度绝对值大于5度，异常运行', idMaps) # FIXME
        # data = X_train_mean
    elif np.abs(err_result)==0.0001:
        rename_key = ''
        for rename_key, rename_value in ai_rename.items():
            if rename_value == "WNAC.WindVaneDirection":
                break
        if rename_key != "WNAC.WindVaneDirection":
            data, statement, alarming = alarm.generateBaseAlarm(name, 'pianhang_duifeng_buzheng','WNAC.WindVaneDirection', Df_all_m_clear, False, assetId,5, f'1、因为风向与机舱夹角测点{rename_value}没有值，当前使用{rename_key}。2、当前数据量为{Df_all.shape[0]}，其中空数据量为{vane_nan_num}', idMaps) # FIXME
            data = pd.DataFrame({'error':[f'1、因为风向与机舱夹角测点{rename_value}没有值，当前使用{rename_key}。2、当前数据量为{Df_all.shape[0]}，其中空数据量为{vane_nan_num}']})
        else:
            data, statement, alarming = alarm.generateBaseAlarm(name, 'pianhang_duifeng_buzheng','WNAC.WindVaneDirection', Df_all_m_clear, False, assetId,5, f'1、当前使用WNAC.WindVaneDirection。2、当前数据量为{Df_all.shape[0]}，其中空数据量为{vane_nan_num}', idMaps) # FIXME
            data = pd.DataFrame({'error':[f'1、当前使用WNAC.WindVaneDirection。2、当前数据量为{Df_all.shape[0]}，其中空数据量为{vane_nan_num}']}) 
        # assert False, ValueError('原数据错误或数据质量问题导致计算结果超出合理范围')
    else:
        data, statement, alarming = alarm.generateBaseAlarm(name, 'pianhang_duifeng_buzheng','WNAC.WindVaneDirection', Df_all_m_clear, False, assetId,5, '最大功率对应偏差角度绝对值小于等于5度, 正常运行', idMaps)# FIXME
    
    vane_nan_num = 0

    return data, statement, Figs, 0,1 # alarming, 0
    




        
    
    

