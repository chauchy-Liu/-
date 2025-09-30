# -*- coding: utf-8 -*-
"""
Created on Wed Mar 15 10:49:50 2023

@author: itadmin
"""

from poseidon import poseidon
#import requests
#import time
import pandas as pd
import datetime
from multiprocessing import Pool,TimeoutError   #计算密集型采用该并行
#from multiprocessing.dummy import Pool as ThreadPool   #IO密集型采用该并行
from functools import  partial #偏函数，用于map传递多个参数
from pylab import mpl
import numpy as np
from scipy import signal
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import math
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import LocalOutlierFactor
from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn import svm



mpl.rcParams['font.sans-serif'] = ['SimHei']
Input_AccessKey = '3f207c85-64b4-476c-a23d-64624bbc0669'
Input_SecretKey = 'f30502cc-2b51-41d0-a95b-6275d609e5bf'
Input_OrgId = "o16323808037221371"
Input_url_asset = 'https://ag-spic1.eniot.io/cds-asset-service/v1.0/hierarchy?orgId=o16323808037221371'
Input_url_data = 'https://ag-spic1.eniot.io/tsdb-service/v2.1/ai-normalized?orgId=o16323808037221371'
#Input_url_data = 'https://ag-spic1.eniot.io/tsdb-service/v2.1/ai?orgId=o16323808037221371'
Input_url_state = 'https://ag-spic1.eniot.io/tsdb-service/v2.1/raw?orgId=o16323808037221371'
Url_di = 'https://ag-spic1.eniot.io/tsdb-service/v2.1/di?orgId=' + Input_OrgId


Input_startTime = '2023-03-01'
Input_endTime = '2023-06-01'
Input_farmIds = "hdn2xwpU"
Input_turbineId = 'tmMX10OH'
Input_pointIds = "WROT.Blade1Position,WROT.Blade2Position,WROT.Blade3Position,WNAC.WindSpeed,WGEN.GenActivePW,WNAC.TemNacelle,WTRM.TemGeaOil,WTRM.TemGeaMSDE,WGEN.GenSpd"
Input_Di_pointIds = 'WTUR.TurbineSts_Map'
Input_Generic_pointIds = 'WTUR.AIStatusCode_Map'

df_generic = pd.DataFrame()
df_di = pd.DataFrame()

#每次取12h的数据
day = pd.date_range(Input_startTime,Input_endTime,freq="12H").strftime('%Y-%m-%d %H:%M:%S').to_list()
day = day[0:-1]

#########风机信息读取
def Turbine_attributes_Enos(AccessKey,SecretKey,assetIds,url):
    Turbine_attr = pd.DataFrame()
    url_asset = str(str(url) + '&mdmIds=' + str(assetIds) + '&mdmTypes=EnOS_Wind_Turbine&attributes=mdmId,name,ratedPower,rotorDiameter,turbineTypeID,altitude')
    
    ResponsePoint = poseidon.urlopen(AccessKey, SecretKey, url_asset)
    #print(req)
    if ResponsePoint['pagination']['pageSize'] > 0:
        Turbine_attr = pd.DataFrame(ResponsePoint['data'][assetIds]['mdmObjects']['EnOS_Wind_Turbine'][:])
        
    # 过滤出某台风机的数据
    result = Turbine_attr[Turbine_attr['mdmId'] == Input_turbineId]
    result = result.reset_index(drop=True)
    return result

#Turbine_attr = Turbine_attributes_Enos(Input_AccessKey,Input_SecretKey,Input_farmIds,Input_url_asset)


#########读取风机数据

def ReadData_Enos(startTime,SecretKey,AccessKey,assetIds,pointIds,url):
    DfTemp = pd.DataFrame()
    endTime = (datetime.datetime.strptime(startTime,"%Y-%m-%d %H:%M:%S") + datetime.timedelta(days=0.5)).strftime("%Y-%m-%d %H:%M:%S")
    print(startTime, endTime)
    params = {"Access Key":AccessKey,
              "Secret Key":SecretKey,
              "assetIds":assetIds,
              "pointIdsWithLogic":pointIds,#pointIdsWithLogic
              "startTime":startTime,
              "endTime":endTime,
              "interval":"0",
              "itemFormat":"1",
              "pageSize":"20000"}
    
    ResponsePoint = poseidon.urlopen(AccessKey, SecretKey, url,params)
    # print(ResponsePoint)
    if len(ResponsePoint['data']['items']) > 0:
        DfTemp = pd.DataFrame(ResponsePoint['data']['items'])
    return DfTemp


def getDiData(startTime, SecretKey,AccessKey, assetIds, url):
    DfTemp = pd.DataFrame()
    endTime = (datetime.datetime.strptime(startTime,"%Y-%m-%d %H:%M:%S") + datetime.timedelta(days=0.5)).strftime("%Y-%m-%d %H:%M:%S")
    params = {"assetIds":assetIds,
              "pointIds":"WTUR.TurbineSts_Map",
              "startTime":startTime,
              "endTime":endTime,
              "autoInterpolate":True,
              "itemFormat":"1"}
    
    ResponsePoint = poseidon.urlopen(Input_AccessKey, Input_SecretKey, Url_di, params)
    if len(ResponsePoint['data']['items']) > 0:
        DfTemp = pd.DataFrame(ResponsePoint['data']['items'])
    return DfTemp

    

def execute(pn_data, title, judgeFunction):
    pn_data['result'] = pn_data.apply(judgeFunction, axis=1)
        
    
    pn_data['date'] = pn_data.index
    print(pn_data)
    
    # pn_data.plot(x='date', y='result', kind='scatter', s=1, title=title)
    pn_data.plot(x='date', y=['WROT.TemAxis1Ctrl','WROT.TemAxis2Ctrl','WROT.TemAxis3Ctrl','WNAC.TemOut', 'result'], kind='line', title=title)
    plt.show()
    

# 获取数据
def getData(Input_assetIds, turbine_name, Input_url_data, Input_pointIds, readDataFunction):
    # num = 22
    warning_text = str()
    Df_all = pd.DataFrame()
    Df_all_m = pd.DataFrame()
    state_all = pd.DataFrame()
    print(turbine_name)
    try:
        PoolNum = 24
        pnum = len(day)//PoolNum
        rem = len(day)%PoolNum
        if pnum > 0:       
            for i in range(pnum+1):
                try:
                    pool = Pool()
                    DaylistStart = day[i*PoolNum:(i+1)*PoolNum]
                    map_result = pool.map_async(partial(readDataFunction,AccessKey = Input_AccessKey,SecretKey = Input_SecretKey,assetIds = Input_assetIds,pointIds = Input_pointIds,url = Input_url_data),DaylistStart)  #并行计算需执行py文件运行
                    state_result = pool.map_async(partial(getDiData,AccessKey = Input_AccessKey,SecretKey = Input_SecretKey,assetIds = Input_assetIds,url = Input_url_state),DaylistStart)
                    map_result.get(timeout=300)
                    state_result.get(timeout=300)
                    pool.close()
                    pool.join()
                    mylist = map_result.get()
                    Df_temp = pd.concat(mylist)
                    Df_all = Df_all.append(Df_temp)
                    
                    statelist = state_result.get()
                    state_temp = pd.concat(statelist)
                    state_all = state_all.append(state_temp)
                    
                    text = str('进程数:'+str(i)+'/'+str(pnum)+';'+'数据长度'+str(len(Df_all)))
                    print(text)
                except TimeoutError:
                    pool.terminate()
                    warning_text = str(turbine_name + '数据获取超时')
    
        else:
            try:
                pool = Pool()
                DaylistStart = day
                map_result = pool.map_async(partial(readDataFunction,AccessKey = Input_AccessKey,SecretKey = Input_SecretKey,assetIds = Input_assetIds,pointIds = Input_pointIds,url = Input_url_data),DaylistStart)  #并行计算需执行py文件运行
                state_result = pool.map_async(partial(getDiData,AccessKey = Input_AccessKey,SecretKey = Input_SecretKey,assetIds = Input_assetIds,url = Input_url_state),DaylistStart)
                map_result.get(timeout=300)
                state_result.get(timeout=300)
                pool.close()
                pool.join()
                mylist = map_result.get()
                Df_temp = pd.concat(mylist)
                Df_all = Df_all.append(Df_temp)
                
                statelist = state_result.get()
                state_temp = pd.concat(statelist)
                state_all = state_all.append(state_temp)
                    
                text = str('数据长度'+str(len(Df_all)))
                print(text)
            except TimeoutError:
                pool.terminate()
                warning_text = str(turbine_name + '数据获取超时')
        
        Df_all['localtime'] = pd.to_datetime(Df_all['localtime'],errors='coerce')    
        Df_all.set_index('localtime',inplace= True)
        Df_all.drop('assetId', axis=1, inplace=True)
        Df_all.drop('timestamp', axis=1, inplace=True)
        
        state_all['localtime'] = pd.to_datetime(state_all['localtime'],errors='coerce')    
        state_all.set_index('localtime',inplace= True)
        state_all.drop('assetId', axis=1, inplace=True)
        state_all.drop('timestamp', axis=1, inplace=True)
        return Df_all, state_all
    except Exception:
        warning_text = str(turbine_name + '数据获取失败')
        
        
# 数据预处理
def preProcessData(Df_all):
    stsValues = Df_all['WTUR.TurbineSts_Map'].unique()
    # codeValues = Df_all['WTUR.AIStatusCode_Map'].unique()
    print(stsValues)
    # print(codeValues)
    
    noneColor = 'purple'
    stsColorDict = {1: 'r', 64: 'g', 2: 'b', 8: 'c', 16: 'y', 128: 'k', 32: 'orange', 65518: 'm', 0: 'c'} # k none
    # codeColorDict = {20300000: 'r', 0: 'g', 21724000: 'b', 20300004: 'c', 21010004: 'y', 20452000: 'k'} # g
    stsColorList = []
    codeColorList = []
    for index, row in Df_all.iterrows():
        if pd.isna(row['WTUR.TurbineSts_Map']):
            stsColorList.append(noneColor)
        else:
            stsColorList.append(stsColorDict[row['WTUR.TurbineSts_Map']])
        # if pd.isna(row['WTUR.AIStatusCode_Map']):
            # codeColorList.append(noneColor)
        # else:
            # codeColorList.append(codeColorDict[row['WTUR.AIStatusCode_Map']])
    Df_all['stsColor'] = stsColorList
    # Df_all['codeColor'] = codeColorList
    Df_all.plot(x='WNAC.WindSpeed', y='WGEN.GenActivePW', c='stsColor', kind='scatter', s=1)
    plt.show()
    # Df_all.plot(x='WNAC.WindSpeed', y='WGEN.GenActivePW', c='codeColor', kind='scatter', s=1)
    # plt.show()



if __name__=='__main__':
    
    Turbine_attr = Turbine_attributes_Enos(Input_AccessKey,Input_SecretKey,Input_farmIds,Input_url_asset)
    
    for num in range(len(Turbine_attr)):
        Turbine_attr.loc[num,'name'] = Turbine_attr.loc[num,'attributes']['name']
        Turbine_attr.loc[num,'turbineTypeID'] = Turbine_attr.loc[num,'attributes']['turbineTypeID']
  
    for num in range(len(Turbine_attr)):
        Df_all, state_df = getData(Turbine_attr.loc[num,'mdmId'], Turbine_attr.loc[num,'name'], Input_url_data, Input_pointIds, ReadData_Enos)
        Df_all_copy = Df_all[::]
        # 数据清洗
        # 1.根据状态码清洗
        Df_all = Df_all.join(state_df,how='outer')
        Df_all['WTUR.TurbineSts_Map'].fillna(method='ffill', inplace=True)
        Df_all = Df_all[(Df_all['WTUR.TurbineSts_Map']==16)|(Df_all['WTUR.TurbineSts_Map']==32)|(Df_all['WTUR.TurbineSts_Map']==64)]
        
        # 2.过滤na数据及功率大于0
        Df_all.dropna(subset=['WGEN.GenActivePW','WNAC.WindSpeed'], inplace=True)
        Df_all = Df_all[Df_all['WGEN.GenActivePW']>0]
        
        # 3.基于LOF算法去除异常点（风速-功率）
        X_train = Df_all[['WNAC.WindSpeed','WGEN.GenActivePW']]
        lof = LocalOutlierFactor(n_neighbors=30)
        y_pred = lof.fit_predict(X_train)
        Df_all['lof_result'] = y_pred
        Df_all = Df_all[Df_all['lof_result'] == 1]
        Df_all.drop('lof_result', axis=1, inplace=True)
        
        # 4.根据正态分布过滤异常值
        final_df = pd.DataFrame()
        bins = np.arange(0, math.ceil(Df_all['WNAC.WindSpeed'].max()),0.1)
        for i in range(len(bins) - 1):
            bin_data = Df_all[(Df_all['WNAC.WindSpeed']>bins[i]) & (Df_all['WNAC.WindSpeed']<=bins[i+1])]
            mean = np.mean(bin_data['WGEN.GenActivePW'])
            std = np.std(bin_data['WGEN.GenActivePW'])
            temp = bin_data[abs(bin_data['WGEN.GenActivePW']-mean)/std<2]
            final_df=final_df.append(temp)
            
        plt.figure()
        plt.scatter(final_df['WNAC.WindSpeed'], final_df['WGEN.GenActivePW'], s=1)
        plt.xlabel('风速(m/s)',fontsize=14)
        plt.ylabel('功率(kW)',fontsize=14)
        plt.show()
        
        plt.figure()
        plt.scatter(final_df['WNAC.WindSpeed'], final_df['WGEN.GenActivePW'], s=1)
        plt.xlabel('风速(m/s)',fontsize=14)
        plt.ylabel('功率(kW)',fontsize=14)
        plt.show()
        
        import numpy as np
        df_noP=final_df[(final_df['WROT.Blade1Position']<5) | ((final_df['WROT.Blade1Position']>5 ) & (final_df['WGEN.GenActivePW']>(np.percentile(final_df['WGEN.GenActivePW'],98))))]
        plt.figure()
        plt.scatter(df_noP['WNAC.WindSpeed'], df_noP['WGEN.GenActivePW'], s=1)
        plt.xlabel('风速(m/s)',fontsize=14)
        plt.ylabel('功率(kW)',fontsize=14)
        plt.show()
        
        from mpl_toolkits.mplot3d import Axes3D
        fig=plt.figure()
        ax=fig.add_subplot(111,projection='3d')
        ax.scatter(final_df['WNAC.WindSpeed'], final_df['WROT.Blade1Position'],final_df['WGEN.GenActivePW'], s=1,marker='.')
        ax.set_xlabel('风速(m/s)',fontsize=14)
        ax.set_ylabel('桨距角(°)',fontsize=14)
        ax.set_zlabel('功率(kW)',fontsize=14)
        plt.show()
        
        # 风速-桨距角 功率-桨距角 风速-功率
        plt.figure()
        plt.scatter(final_df['WNAC.WindSpeed'], final_df['WROT.Blade1Position'], s=1)
        plt.xlabel('风速(m/s)',fontsize=14)
        plt.ylabel('桨距角(°)',fontsize=14)
        plt.show()
        
        plt.figure()
        plt.scatter(final_df['WGEN.GenActivePW'], final_df['WROT.Blade1Position'], s=1)
        plt.xlabel('功率(kW)',fontsize=14)
        plt.ylabel('桨距角(°)',fontsize=14)
        plt.show()
        
        # final_df.hist()
        
        # 拟合 SVM 贝叶斯分析 LSTM
        final_df = Df_all.dropna(subset=['WNAC.TemNacelle', 'WTR.TemGeaOil', 'WGEN.GenSpd', 'WGEN.GenActivePW', 'WTRM.TemGeaMSDE'])
        X = final_df[['WGEN.GenActivePW','WNAC.TemNacelle','WTRM.TemGeaOil','WGEN.GenSpd']]
        y = final_df['WTRM.TemGeaMSDE']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        # rf.fit(X_train, y_train)  
        # y_predict = rf.predict(X_test)
        # mse = mean_squared_error(y_test, y_predict)
        
        search_space = {
            'n_estimators':[100, 200, 250,300,350,400],
            # 'max_features':[1,2,3,4,5]
        }
        rf = RandomForestRegressor()
        
        gs = GridSearchCV(estimator=rf, param_grid=search_space, scoring='neg_mean_squared_error')
        gs.fit(X_train, y_train)
        print(gs.best_score_)
        print(gs.best_estimator_)
        print(gs.best_params_)
        # print(gs.cv_results_)
        
        y_predict = gs.predict(X_test)
        mse = mean_squared_error(y_test, y_predict)
        print(np.sqrt(mse))
        
        
        import statsmodels.api as sm
        sm.qqplot(y_predict-y_test)
        plt.show()
        plt.hist(y_predict-y_test,bins=20)
        plt.show()
        
        # final_df.corr()['WTRM.TemGeaMSDE'].sort_values(ascending=False)
        # 试验线性回归
        lr = LinearRegression()
        lr.fit(X_train, y_train)
        y_predict = lr.predict(X_test)
        mse = mean_squared_error(y_test, y_predict)
        print(np.sqrt(mse))
        
        from pandas.plotting import scatter_matrix
        scatter_matrix(final_df[['WGEN.GenActivePW','WNAC.TemNacelle','WTRM.TemGeaOil','WGEN.GenSpd','WTRM.TemGeaMSDE']])

        