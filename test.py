# -*- coding: utf-8 -*-

from poseidon import poseidon  # 打包时注意
import pandas as pd
from functools import partial  # 偏函数，用于map传递多个参数
from multiprocessing import Pool  # 计算密集型采用该并行
import numpy as np
from sklearn.neighbors import LocalOutlierFactor
from itertools import product
import utils.time_util as time_util
from datetime import timedelta
from configs import config
import logging
from configs.config import AccessKey, SecretKey, GW_Url, OrgId
from db.db import save_alarm
from datetime import datetime


Url_asset = GW_Url + '/cds-asset-service/v1.0/hierarchy?orgId=' + OrgId  # 这个api哪里来的？
Url_ai_normalized = GW_Url + '/tsdb-service/v2.1/ai-normalized?orgId=' + OrgId
Url_ai = GW_Url + '/tsdb-service/v2.1/ai?orgId=' + OrgId
Url_raw = GW_Url + '/tsdb-service/v2.1/raw?orgId=' + OrgId
Url_di = GW_Url + '/tsdb-service/v2.1/di?orgId=' + OrgId
Url_generic = GW_Url + '/tsdb-service/v2.1/generic?orgId=' + OrgId


def getGenericData(startTime, endTime, points, assetId):
    DfTemp = pd.DataFrame()
    params = {"assetIds": assetId,
              "pointIds": points,
              "startTime": startTime,
              "endTime": endTime,
              "itemFormat": "1"}

    ResponsePoint = poseidon.urlopen(AccessKey, SecretKey, Url_generic, params)
    if len(ResponsePoint['data']['items']) > 0:
        DfTemp = pd.DataFrame(ResponsePoint['data']['items'])
    return DfTemp


def getDiData(startTime, endTime, points, assetId):
    # print(startTime, endTime, points, assetId)
    DfTemp = pd.DataFrame()
    params = {"assetIds": assetId,
              "pointIds": points,
              "startTime": startTime,
              "endTime": endTime,
              "autoInterpolate": True,
              "itemFormat": "1"}

    ResponsePoint = poseidon.urlopen(AccessKey, SecretKey, Url_di, params)
    if len(ResponsePoint['data']['items']) > 0:
        DfTemp = pd.DataFrame(ResponsePoint['data']['items'])
    return DfTemp


def getAiData(startTime, endTime, assetId: str, points, resample_interval):
    # print(startTime, endTime, assetId, points, resample_interval)
    ResponsePoint = None
    if time_util.use_raw_api(resample_interval):
        params = {"assetIds": assetId,
                  "pointIds": ','.join(points),
                  "startTime": startTime,
                  "endTime": endTime,
                  "itemFormat": "1",
                  "pageSize": "20000",
                  "boundaryType": 'inside'}
        ResponsePoint = poseidon.urlopen(AccessKey, SecretKey, Url_ai, params)
    else:
        params = {"assetIds": assetId,
                  "pointIdsWithLogic": ','.join(points),
                  "startTime": startTime,
                  "endTime": endTime,
                  "interval": "0",
                  "itemFormat": "1",
                  "pageSize": "20000"}
        ResponsePoint = poseidon.urlopen(
            AccessKey, SecretKey, Url_ai_normalized, params)
    DfTemp = pd.DataFrame()
    if len(ResponsePoint['data']['items']) > 0:
        DfTemp = pd.DataFrame(ResponsePoint['data']['items'])
        DfTemp.set_index('localtime', inplace=True)
        DfTemp.index = pd.to_datetime(DfTemp.index)
        if time_util.split_time_delta(resample_interval)[0] > 1:
            resample_interval = time_util.replace_to_resample(
                resample_interval)
            DfTemp = DfTemp.resample(
                resample_interval, closed='left').mean()  # FIXME
        DfTemp['assetId'] = assetId
        DfTemp = DfTemp.round(2)
    return DfTemp



def getRawData(startTime, endTime, points, assetIds):
    DfTemp = pd.DataFrame()
    params = {"assetIds": ','.join(assetIds),
              "pointIds": points,
              "startTime": startTime,
              "endTime": endTime,
              "itemFormat": "1",
            #   "type": "ai_normalized",  # ai,ai_normalized,di,pi,generic
            #   "boundaryType": "sample",
            #   "interval": 600,
            #   "interpolation": "near",
            #   "pageSize": "20000"
              }

    ResponsePoint = poseidon.urlopen(AccessKey, SecretKey, Url_raw, params)
    if len(ResponsePoint['data']['items']) > 0:
        DfTemp = pd.DataFrame(ResponsePoint['data']['items'])
    return DfTemp

def DartsTest1():
    from darts.datasets import AirPassengersDataset, MonthlyMilkDataset
    import numpy as np

    series_air = AirPassengersDataset().load().astype(np.float32)
    series_milk = MonthlyMilkDataset().load().astype(np.float32)

    # set aside last 36 months of each series as validation set:
    train_air, val_air = series_air[:-36], series_air[-36:]
    train_milk, val_milk = series_milk[:-36], series_milk[-36:]

    train_air.plot()
    val_air.plot()
    train_milk.plot()
    val_milk.plot()

    from darts.dataprocessing.transformers import Scaler

    scaler = Scaler()
    train_air_scaled, train_milk_scaled = scaler.fit_transform([train_air, train_milk])

    train_air_scaled.plot()
    train_milk_scaled.plot()

    from darts.models import NBEATSModel

    model = NBEATSModel(input_chunk_length=24, output_chunk_length=12, random_state=42,pl_trainer_kwargs={"accelerator": "cpu"})

    model.fit([train_air_scaled,train_milk_scaled], epochs=50, verbose=True)#, [train_milk_scaled] , num_loader_workers=0

    pred_air = model.predict(series=train_air_scaled, n=36)
    # pred_milk = model.predict(series=train_milk_scaled, n=36)

    # scale back:
    # pred_air, pred_milk = scaler.inverse_transform([pred_air, pred_milk])

    # from matplotlib import pyplot as plt
    # plt.figure(figsize=(10, 6))
    # series_air.plot(label="actual (air)")
    # series_milk.plot(label="actual (milk)")
    # pred_air.plot(label="forecast (air)")
    # pred_milk.plot(label="forecast (milk)")

if __name__=='__main__':
    # turbines = getWindTurbines('VbaHqckJ')
    # print(turbines)

    # data = getRawData('2023-08-01 00:00:00', '2023-08-31 00:00:00', 'WTUR.TurbineSts', '1eA6pUMl')
    # data = getDiData('2023-08-01 00:00:00', '2023-08-31 00:00:00', 'WTUR.TurbineSts', '1eA6pUMl')
    # data = getGenericData('2023-04-01 00:00:00', '2023-08-31 00:00:00', 'WTUR.AIStatusCode', '1eA6pUMl')

    # print(data)

    # save_alarm('xxx', '偏航一场', datetime.now(), datetime.now(), datetime.now())

    DartsTest1()
    
        