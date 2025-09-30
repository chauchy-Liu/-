# -*- coding: utf-8 -*-
"""
Created on Wed Mar 15 10:49:50 2023

@author: itadmin
"""


#import requests
#import time
import pandas as pd
from datetime import datetime
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
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent)) 
from data.get_data_async import getDataCommon, getWindTurbines, wash_data_for_train, getWindTurbinesNode, getDataForMultiAlgorithms
from poseidon import poseidon
import os
from configs import config
import asyncio
    

def execute(pn_data, title, judgeFunction):
    pn_data['result'] = pn_data.apply(judgeFunction, axis=1)
        
    
    pn_data['date'] = pn_data.index
    print(pn_data)
    
    # pn_data.plot(x='date', y='result', kind='scatter', s=1, title=title)
    pn_data.plot(x='date', y=['WROT.TemAxis1Ctrl','WROT.TemAxis2Ctrl','WROT.TemAxis3Ctrl','WNAC.TemOut', 'result'], kind='line', title=title)
    plt.show()
    
        
# 数据预处理
def preProcessData(Df_all):
    stsValues = Df_all['WTUR.TurbineSts_Map'].unique()
    # codeValues = Df_all['WTUR.AIStatusCode_Map'].unique()
    print(stsValues)
    # print(codeValues)
    
    noneColor = 'purple'
    stsColorDict = {1: 'r', 64: 'g', 2: 'b', 8: 'c', 16: 'y', 128: 'k', 32: 'orange', 65518: 'm', 0: 'c'} # k none
    # stsColorDict = {1: 'r', 2: 'g', 3: 'b', 4: 'c', 5: 'y', 6: 'k'} # k none
    
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



# if __name__=='__main__':
async def main():
    algName = 'jiegou_sunshang'
    import importlib
    algorithm = importlib.import_module('algorithms.'+algName)
    name = algorithm.__name__.split('.')[-1]
    Input_farmIds = config.Wind_Farm
    Input_startTime = datetime.strptime('2024-07-08 00:00:00', '%Y-%m-%d %H:%M:%S')
    Input_endTime = datetime.strptime('2024-08-13 00:00:00', '%Y-%m-%d %H:%M:%S')
    extraModelName = config.extraModelName
    algorithms_configs = {}
    algorithms_configs[algName] = {
        'startTime':Input_startTime, 
        'endTime': Input_endTime, 
        #'resampleTime':multi_algorithms[-1].resample_interval, 
        'aiPoints':algorithm.ai_points, 
        "diPoints":algorithm.di_points, 
        "generalPoints":algorithm.general_points, 
        "privatePoints":algorithm.private_points,
        "executeTime": ""
    }

    df_wind_turbine = await getWindTurbines(Input_farmIds)
    turbineNameList = ["#02"]
    df_wind_turbine = df_wind_turbine[df_wind_turbine["name"].isin(turbineNameList)]
    assetIds = df_wind_turbine['mdmId']
    multiModelAssetIds = await getWindTurbinesNode(assetIds, algorithms_configs, nameConstrain=extraModelName) #一个风机可能会有多个模型资产Id
    algorithms_configs[algName]['resampleTime'] = algorithm.resample_interval
    count = 0
    for index, row in df_wind_turbine.iterrows():
        print(f"{count+1}/{len(df_wind_turbine)}")
        count += 1
        
        assetId = row['mdmId']
        ratedPower = row['ratedPower']
        algorithms_configs[algName]['PrepareTurbines'] = True
        algorithms_configs[algName]['param_private_assetIds'] = [multiModelAssetIds[count-1][algName]]
        algorithms_configs[algName]['param_assetIds'] = [assetId]
        algorithms_configs[algName]['param_turbine_num'] = [row['name']]

        if os.path.exists(os.path.join('model',config.Wind_Farm, name, assetId, algName+'.model')):
            continue

        
        # Df_all = getDataCommon(Input_startTime, Input_endTime, [assetId], algorithm.ai_points, algorithm.di_points, algorithm.general_points, '10m')
        algorithmData = await getDataForMultiAlgorithms(algorithms_configs)

        # plt.scatter(x=Df_all['WNAC.WindSpeed'], y=Df_all['WGEN.GenActivePW'], s=1)
        # plt.show()
        Df_all = algorithmData[algName]
        final_df = wash_data_for_train(Df_all, ratedPower)
        final_df = final_df[final_df['clear'] == 2]
        if final_df.empty == True:
            #撤销重命名
            if len(algorithm.ai_rename) != 0:
                for key, evalue in algorithm.ai_rename.items():
                    if evalue in Df_all.columns.tolist():
                        if evalue in algorithm.ai_points:
                            index_key = algorithm.ai_points.index(evalue)
                            algorithm.ai_points[index_key] = key
            continue
        
        # 拟合 随机森林 SVM
        # 求平均温度
        # final_df['mean_tem'] = np.mean(final_df[['WGEN.TemGenStaU','WGEN.TemGenStaV','WGEN.TemGenStaW']], axis=1)
        if len(algorithm.private_points) > 0:
            private_points = []
            for modelKey, pointValue in algorithm.private_points.items():
                private_points += pointValue
        else:
            private_points = []
        final_df = final_df.dropna(subset=set(algorithm.ai_points + algorithm.di_points+algorithm.general_points+private_points))
        X = final_df[algorithm.ai_points] # 'WGEN.LHDLGENAI31','WGEN.LHDLGENAI103'
        y = final_df[private_points[-1]]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        # rf.fit(X_train, y_train)  
        # y_predict = rf.predict(X_test)
        # mse = mean_squared_error(y_test, y_predict)
        
        # 500 5
        search_space = {
            'n_estimators':[400,500,600,700],
            'max_features':[2,3,4,5]
            # 'n_estimators':[500],
            # 'max_features':[5]
        }
        rf = RandomForestRegressor()
        
        gs = GridSearchCV(estimator=rf, param_grid=search_space, scoring='neg_mean_squared_error')
        gs.fit(X_train, y_train)
        print(gs.best_score_)
        print(gs.best_estimator_)
        print(gs.best_params_)
        print(gs.best_estimator_)
        # print(gs.cv_results_)
        
        y_predict = gs.predict(X_test)
        mse = mean_squared_error(y_test, y_predict)
        print(mse)
        print(np.sqrt(mse))

        #撤销重命名
        if len(algorithm.ai_rename) != 0:
            for key, evalue in algorithm.ai_rename.items():
                if evalue in Df_all.columns.tolist():
                    if evalue in algorithm.ai_points:
                        index_key = algorithm.ai_points.index(evalue)
                        algorithm.ai_points[index_key] = key

        import joblib
        if os.path.exists(os.path.dirname(os.path.join('model',config.Wind_Farm, name, assetId, algName+'.model'))):
            pass
        else:
            os.makedirs(os.path.dirname(os.path.join('model',config.Wind_Farm, name, assetId, algName+'.model')))
        joblib.dump(gs.best_estimator_, os.path.join('model',config.Wind_Farm, name, assetId, algName+'.model'))
        joblib.dump(np.sqrt(mse), os.path.join('model',config.Wind_Farm, name, assetId, 'error'+'.model'))
        # break
        
asyncio.run(main())   
        
    
        # from pandas.plotting import scatter_matrix
        # scatter_matrix(final_df[['mean_tem','WGEN.GenActivePW','WNAC.TemOut','WNAC.TemNacelle','WGEN.LHDLGENAI31','WGEN.GenSpd','WNAC.WindSpeed','WGEN.LHDLGENAI103']])
        # final_df.corr().sort_values('mean_tem')['mean_tem']