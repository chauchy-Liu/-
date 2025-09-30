# -*- coding: utf-8 -*-
"""
Created on Wed Jul 26 10:34:15 2023

@author: sunyan
"""

import joblib
from sklearn.neighbors import LocalOutlierFactor
from functools import partial #偏函数，用于map传递多个参数
from datetime import datetime
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import math
import numpy as np
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent)) 
# 导包是基于当前工作目录的，如果直接运行此文件，此文件相当于主脚本，找不到data模块，所以要添加到sys.path中
# 项目的所有模块的导包，都是基于主脚本工作目录的
# from data.get_data import getDataCommon, getWindTurbines, wash_data_for_train
from data.get_data_async import getDataCommon, getWindTurbines, wash_data_for_train, getWindTurbinesNode, getDataForMultiAlgorithms
from sklearn.metrics import mean_squared_error
from poseidon import poseidon
import os
from configs import config
from sklearn import preprocessing
import importlib
import asyncio


# 数据预处理
def preProcessData(Df_all):
    stsValues = Df_all['WTUR.TurbineSts_Map'].unique()
    # codeValues = Df_all['WTUR.AIStatusCode_Map'].unique()
    print(stsValues)
    # print(codeValues)
    
    noneColor = 'purple'
    stsColorDict = {0: 'r', 64: 'g', 2: 'b', 128: 'c', 16: 'y', 32: 'k', 1: 'orange', 65518: 'k'} # k none
    # codeColorDict = {20300000: 'r', 0: 'g', 21724000: 'b', 20300004: 'c', 21010004: 'y', 20452000: 'k'} # g
    stsColorList = []
    # codeColorList = []
    for index, row in Df_all.iterrows():
        if pd.isna(row['WTUR.TurbineSts_Map']):
            stsColorList.append(noneColor)
        else:
            stsColorList.append(stsColorDict[row['WTUR.TurbineSts_Map']])
        # if pd.isna(row['WTUR.AIStatusCode_Map']):
        #     codeColorList.append(noneColor)
        # else:
        #     codeColorList.append(codeColorDict[row['WTUR.AIStatusCode_Map']])
    Df_all['stsColor'] = stsColorList
    # Df_all['codeColor'] = codeColorList
    Df_all.plot(x='WNAC.WindSpeed', y='WGEN.GenActivePW', c='stsColor', kind='scatter', s=1)
    plt.show()
    # Df_all.plot(x='WNAC.WindSpeed', y='WGEN.GenActivePW', c='codeColor', kind='scatter', s=1)
    # plt.show()


def washData(finalDf):
    '''
    通用数据清洗（针对三一机型）
    '''
    # 获取di数据
    assetId = finalDf['assetId'][0]
    startTime=finalDf.index.min()
    endTime=finalDf.index.max()
    getDiDataWithTimeFunc = partial(getDiData,assetId=assetId,points='WTUR.TurbineSts_Map')
    df_di = getDiDataWithTimeFunc(startTime=startTime.strftime('%Y-%m-%d %H:%M:%S'), endTime=endTime.strftime('%Y-%m-%d %H:%M:%S'))
    df_di.set_index('localtime',inplace= True)
    df_di.index = pd.to_datetime(df_di.index)
    df_di.drop('assetId', axis=1, inplace=True)
    df_di.drop('timestamp', axis=1, inplace=True)
    
    # 1.根据状态码清洗
    finalDf.drop('assetId', axis=1, inplace=True)
    finalDf.drop('timestamp', axis=1, inplace=True)
    finalDf = finalDf.join(df_di,how='outer')
    finalDf['WTUR.TurbineSts_Map'].fillna(method='ffill', inplace=True)
    finalDf = finalDf[(finalDf['WTUR.TurbineSts_Map']==16)|(finalDf['WTUR.TurbineSts_Map']==32)|(finalDf['WTUR.TurbineSts_Map']==64)]
    
    # 2.过滤na数据
    finalDf.dropna(inplace=True)
    
    # 3.基于LOF算法去除异常点（风速-功率）
    X_train = finalDf[['WNAC.WindSpeed','WGEN.GenActivePW']]
    lof = LocalOutlierFactor(n_neighbors=100)
    y_pred = lof.fit_predict(X_train)
    finalDf['lof_result'] = y_pred
    finalDf = finalDf[finalDf['lof_result'] == 1]
    finalDf.drop('lof_result', axis=1, inplace=True)
    
    # 4.根据正态分布过滤异常值
    last_df = pd.DataFrame()
    bins = np.arange(0, math.ceil(finalDf['WNAC.WindSpeed'].max()),0.1)
    for i in range(len(bins) - 1):
        bin_data = finalDf[(finalDf['WNAC.WindSpeed']>bins[i]) & (finalDf['WNAC.WindSpeed']<=bins[i+1])]
        mean = np.mean(bin_data['WGEN.GenActivePW'])
        std = np.std(bin_data['WGEN.GenActivePW'])
        temp = bin_data[abs(bin_data['WGEN.GenActivePW']-mean)/std<2]
        last_df=last_df.append(temp)
        
    
    # 根据DBSCAN过滤异常值
    from sklearn.cluster import DBSCAN
    db = DBSCAN(min_samples=200)
    y_pred_db = db.fit_predict(X_train)
    plt.scatter(X_train[y_pred_db == -1])
    finalDf['dbscan_result'] = y_pred_db
    tempDf = finalDf[finalDf['dbscan_result'] != -1]
        
    return last_df


# if __name__ == '__main__':
async def main():
    algName = 'capacity_reduction'
    algorithm = importlib.import_module('algorithms.'+algName)
    Input_farmIds = config.Wind_Farm
    Input_startTime = datetime.strptime('2024-02-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    Input_endTime = datetime.strptime('2024-04-25 00:00:00', '%Y-%m-%d %H:%M:%S')
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
    
    # points = ['WNAC.WindSpeed','WGEN.GenActivePW', 'WGEN.GenSpd', 'WROT.Blade1Position']
    name = 'speed_power' #algorithm.__name__.split('.')[-1]
    df_wind_turbine = await getWindTurbines(Input_farmIds)
    turbineNameList = ["13#","14#","15#","16#","17#"]
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

        if os.path.exists(os.path.join('model',config.Wind_Farm, name, assetId, 'speed_power.model')):
            continue
        # if assetId != '1eA6pUMl':
        #     continue

        algorithmData = await getDataForMultiAlgorithms(algorithms_configs)#getDataCommon(Input_startTime, Input_endTime, [assetId], aipoints, ['WTUR.TurbineSts'], ['WTUR.TurbineAIStatus'], '10m')

        # plt.scatter(x=Df_all['WNAC.WindSpeed'], y=Df_all['WGEN.GenActivePW'], s=1)
        # plt.show()
        Df_all = algorithmData[algName]
        finalDf = wash_data_for_train(Df_all, ratedPower)
        finalDf = finalDf[finalDf['clear'] <= 5]
        if finalDf.empty == True:
            continue
        # plt.scatter(x=finalDf['WNAC.WindSpeed'], y=finalDf['WGEN.GenActivePW'], s=1)
        # plt.show()
        if len(algorithm.private_points) > 0:
            private_points = []
            for modelKey, pointValue in algorithm.private_points.items():
                private_points += pointValue
        else:
            private_points = []
        sortedDf = finalDf.sort_values(by='WNAC.WindSpeed')
        sortedDf.set_index('WNAC.WindSpeed', inplace=True)
        sortedDf['WNAC.WindSpeed'] = sortedDf.index
        #归一化处理
        # scalorWS = preprocessing.MinMaxScaler()
        # sortedDf['wsTransformed'] = scalorWS.fit_transform(sortedDf[['WNAC.WindSpeed']])
        # scalorPW = preprocessing.MinMaxScaler()
        # sortedDf['pwTransformed'] = scalorPW.fit_transform(sortedDf[['WGEN.GenActivePW']])
        # 每隔0.5取平均
        # bins = np.arange(0, math.ceil(sortedDf['wsTransformed'].max()),0.08)
        bins = np.arange(0, math.ceil(sortedDf['WNAC.WindSpeed'].max()),0.08)
        print(bins)
        test = pd.cut(sortedDf['WNAC.WindSpeed'], bins)
        miniDf = sortedDf[['WNAC.WindSpeed', 'WGEN.GenActivePW']]
        test1 = miniDf.groupby(test).mean()
        func=interp1d(test1['WNAC.WindSpeed'], test1['WGEN.GenActivePW'], bounds_error=False, fill_value="extrapolate")
        # func=interp1d(test1['wsTransformed'], test1['pwTransformed'], bounds_error=False, fill_value="extrapolate")
        # plt.figure()
        # plt.plot(test1['WNAC.WindSpeed'], func(test1['WNAC.WindSpeed']), label='fit', color='g')
        # plt.show()
        # prefitTransformed = func(sortedDf[['wsTransformed']])
        # prefit = scalorPW.inverse_transform(prefitTransformed)
        prefit = func(sortedDf['WNAC.WindSpeed'])
        prefit = pd.DataFrame(prefit)
        prefit = prefit.ffill()
        prefit = prefit.bfill()
        prefit = prefit.to_numpy()
        mse = mean_squared_error(sortedDf[['WGEN.GenActivePW']], prefit)
        print(mse)
        print(np.sqrt(mse))

        #撤销重命名
        if len(algorithm.ai_rename) != 0:
            for key, evalue in algorithm.ai_rename.items():
                if evalue in Df_all.columns.tolist():
                    if evalue in algorithm.ai_points:
                        index_key = algorithm.ai_points.index(evalue)
                        algorithm.ai_points[index_key] = key
        
        # 持久化
        # os.makedirs(os.path.join('model', assetId), exist_ok=True)
        if os.path.exists(os.path.dirname(os.path.join('model',config.Wind_Farm, name, assetId, 'speed_power.model'))):
            pass
        else:
            os.makedirs(os.path.dirname(os.path.join('model',config.Wind_Farm, name, assetId, 'speed_power.model')))
        joblib.dump(func, os.path.join('model',config.Wind_Farm, name, assetId, 'speed_power.model'))
        joblib.dump(np.sqrt(mse), os.path.join('model',config.Wind_Farm, name, assetId, 'error.model'))
        # 保存图片
        # plt.savefig(os.path.join('model', assetId, 'assetId_speed_power.png'), format='png')

asyncio.run(main())   