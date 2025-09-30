import numpy as np
import pandas as pd
from tqdm import tqdm_notebook as tqdm

import matplotlib.pyplot as plt
plt.switch_backend('agg')

from darts import TimeSeries, concatenate
from darts.dataprocessing.transformers import Scaler
from darts.models import TFTModel
from darts.metrics import mape
from darts.utils.statistics import check_seasonality, plot_acf
from darts.datasets import AirPassengersDataset, IceCreamHeaterDataset
from darts.utils.timeseries_generation import datetime_attribute_timeseries
from darts.utils.likelihood_models import QuantileRegression
import warnings

from typing import Union
import utils.time_util as time_util
from pytorch_lightning.callbacks.early_stopping import EarlyStopping
import pytorch_lightning as pl
from pytorch_lightning.callbacks import Callback
import os

# from lightning.pytorch import Trainer
# from lightning.pytorch.loggers import TensorBoardLogger
import torch
# import sys

warnings.filterwarnings("ignore")




#数据在某时间段内做平均值
def MeanOverTime(dfSeq:Union[pd.DataFrame, pd.Series], timeUnit:str):

    # dfSeq.to_csv('检测数据10分钟频率.csv', index=True)
    dfSeq = dfSeq.resample(timeUnit).mean() #.asfreq(timeUnit).fillna(method='ffill')
    #处理数据缺失和采样时间缺失
    date_index = pd.date_range(start=dfSeq.index[0], end=dfSeq.index[-1], freq=timeUnit)
    dfSeq = dfSeq.reindex(date_index).fillna(method='ffill')
    #输出数据
    # dfSeq.to_csv('检测数据1天频率.csv', index=True)

    #Dataframe转TimeSeries
    if type(dfSeq) == pd.DataFrame:
        series = TimeSeries.from_dataframe(dfSeq, freq=timeUnit)
    elif type(dfSeq) == pd.Series:
        series = TimeSeries.from_series(dfSeq, freq=timeUnit)
    # if timeUnit == "10minute":
    #     series = series.resample('10T').mean()
    # elif timeUnit == "hour":
    #     series = series.resample('H').mean()
    # elif timeUnit == "day":
    #     series = series.resample('D').mean()
    # elif timeUnit == "week":
    #     series = series.resample('W').mean()
    # elif timeUnit == "month":
    #     series = series.resample('M').mean()
    # elif timeUnit == "Quarter":
    #     series = series.resample('Q').mean()
    # elif timeUnit == "year":
    #     series = series.resample('Y').mean()
    series = series.astype(np.float32)
    return series

def SplitTrainAndTest(series:TimeSeries, cutOff:Union[pd.Timestamp, float, int]):
    train, val = series.split_after(cutOff)
    return train, val

#归一化数据
def NormalizeSeries(series:TimeSeries, cutOff:Union[pd.Timestamp, float, int]=None):
    if cutOff != None:
        train, val = SplitTrainAndTest(series, cutOff)
        transformer = Scaler()
        train_transformed = transformer.fit_transform(train)
        val_transformed = transformer.transform(val)
        series_transformed = transformer.transform(series)
    else:
        transformer = Scaler()
        train_transformed = None#transformer.fit_transform()
        val_transformed = None
        series_transformed = transformer.fit_transform(series)
    
    return train_transformed, val_transformed, series_transformed, transformer

def CreateCovariates(series:TimeSeries, cutOff:Union[pd.Timestamp, float, int]=None):
    # create year, month and integer index covariate series
    covariates = datetime_attribute_timeseries(series, attribute="year", one_hot=False)
    covariates = covariates.stack(
        datetime_attribute_timeseries(series, attribute="month", one_hot=False)
    )
    covariates = covariates.stack(
        datetime_attribute_timeseries(series, attribute="day", one_hot=False)
    )
    covariates = covariates.stack(
        TimeSeries.from_times_and_values(
            times=series.time_index,
            values=np.arange(len(series)),
            columns=["linear_increase"],
        )
    )
    covariates = covariates.astype(np.float32)
    
    return NormalizeSeries(covariates, cutOff=cutOff)
    # transform covariates (note: we fit the transformer on train split and can then transform the entire covariates series)
    # scaler_covs = Scaler()
    # if cutOff != None:
    #     cov_train, cov_val = covariates.split_after(cutOff)
    #     cov_train_transformed = scaler_covs.fit_transform(cov_train)
    #     cov_val_transformed = scaler_covs.fit_transform(cov_val)
    #     covariates_transformed = scaler_covs.transform(covariates)
    # else:
    #     cov_train_transformed, cov_val_transformed = None, None
    #     covariates_transformed = scaler_covs.fit_transform(covariates)



class CreateTFTModel:
    def __init__(self, series:TimeSeries, input_chunk_length = 24, out_chunck_length = 12, futureCovariates=None, numEpoch=300, cutOff:Union[pd.Timestamp, float, int]=None, stopThreshold=0.09, timeUnit='10T'):
        # before starting, we define some constants
        self.num_samples = 200

        self.figsize = (9, 6)
        self.lowest_q, self.low_q, self.high_q, self.highest_q = 0.01, 0.1, 0.9, 0.99
        self.label_q_outer = f"{int(self.lowest_q * 100)}-{int(self.highest_q * 100)}th percentiles"
        self.label_q_inner = f"{int(self.low_q * 100)}-{int(self.high_q * 100)}th percentiles"
        self.cutOff = cutOff
        self.futureCovariates = futureCovariates
        self.timeUnit = timeUnit
        # default quantiles for QuantileRegression
        quantiles = [
            0.01,
            0.05,
            0.1,
            0.15,
            0.2,
            0.25,
            0.3,
            0.4,
            0.5,
            0.6,
            0.7,
            0.75,
            0.8,
            0.85,
            0.9,
            0.95,
            0.99,
        ]
        # input_chunk_length = 24
        # forecast_horizon = 12
        #生成各数据集
        # self.trainTransformed, self.valTransformed, self.seriesTransformed, self.seriesScalor = SplitTrainAndTest(series, cutOff)
        self.trainTransformed, self.valTransformed, self.seriesTransformed, self.seriesScalor = NormalizeSeries(series, cutOff)
        if self.trainTransformed == None:
            self.trainTransformed = self.seriesTransformed
        #创建协变量
        self.trainCovariateTransformed, self.valCovariateTransformed, self.seriesCovariateTransformed, self.covariateScalor = CreateCovariates(series, cutOff)
        if self.trainCovariateTransformed == None:
            self.trainCovariateTransformed = self.seriesCovariateTransformed

        #回调函数
        stopper = EarlyStopping(
            monitor='train_loss',
            patience=numEpoch,
            stopping_threshold=stopThreshold,
            mode='min'
        )
        # #损失回调
        class LossLogger(Callback):
            def __init__(self):
                self.train_loss = []
                self.val_loss = []

            # will automatically be called at the end of each epoch
            def on_train_epoch_end(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule") -> None:
                self.train_loss.append(float(trainer.callback_metrics["train_loss"]))

            def on_validation_epoch_end(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule") -> None:
                self.val_loss.append(float(trainer.callback_metrics["val_loss"]))
            
        loss_logger = LossLogger()
        
        if futureCovariates != None:
            my_model = TFTModel(
                input_chunk_length=input_chunk_length,
                output_chunk_length=out_chunck_length,
                hidden_size=64,
                lstm_layers=1,
                num_attention_heads=4,
                dropout=0.1,
                batch_size=16,
                n_epochs=numEpoch,
                add_relative_index=False,
                add_encoders=None,
                likelihood=QuantileRegression(
                    quantiles=quantiles
                ),  # QuantileRegression is set per default
                # loss_fn=MSELoss(),
                random_state=42,
                pl_trainer_kwargs={"callbacks":[stopper,loss_logger], "accelerator":"cpu"},
                optimizer_cls=torch.optim.Adam,
                optimizer_kwargs={"lr":1e-1},
                lr_scheduler_cls=torch.optim.lr_scheduler.MultiStepLR,
                lr_scheduler_kwargs={"gamma":0.5, "milestones":[numEpoch//9, numEpoch//9*2, numEpoch//9*3, numEpoch//9*5, numEpoch//9*6, numEpoch//9*7, numEpoch//9*8]}
            )   

            my_model.fit(self.trainTransformed, future_covariates=self.trainCovariateTransformed, verbose=True)
            # trainer.fit(my_model,)

        else:
            my_model = TFTModel(
                input_chunk_length=input_chunk_length,
                output_chunk_length=out_chunck_length,
                hidden_size=32,
                lstm_layers=1,
                batch_size=16,
                n_epochs=numEpoch,
                dropout=0.1,
                add_encoders={ 
                    "cyclic": {"future": ["day", "week", "month"]},
                    "datetime_attribute":{"future": ["day", "week", "month"]}
                },
                add_relative_index=False,
                likelihood=QuantileRegression(
                    quantiles=quantiles
                ),
                #optimizer_kwargs={"lr": 1e-3},
                random_state=42,
                pl_trainer_kwargs={"callbacks":[stopper,loss_logger], "accelerator":"cpu"},
                optimizer_cls=torch.optim.Adam,
                optimizer_kwargs={"lr":1e-1},
                lr_scheduler_cls=torch.optim.lr_scheduler.MultiStepLR,
                lr_scheduler_kwargs={"gamma":0.5, "milestones":[numEpoch//9, numEpoch//9*2, numEpoch//9*3, numEpoch//9*5, numEpoch//9*6, numEpoch//9*7, numEpoch//9*8]}
                # log_tensorboard=True,
            )
            # with open('training_log.txt', 'w') as f:
                # 重定向标准输出到文件
                # sys.stdout = f
                # 训练模型
            my_model.fit(
                self.trainTransformed, past_covariates=self.trainCovariateTransformed, verbose=True,
            )
                # 恢复标准输出
                # sys.stdout = sys.__stdout__
        
        
        self.trainLoss = loss_logger.train_loss[-1]
        self.model = my_model


    def Predict(self, forcastHorizon):
        self.predSeriesTransformed = self.model.predict(n=forcastHorizon, num_samples=self.num_samples) #self.trainTransformed,
        self.predSeries =  self.seriesScalor.inverse_transform(self.predSeriesTransformed)
    
    def EvaluatePredict(self):

        if self.valTransformed == None:
            print("数据集为划分，无法给预测做评估")
            self.eval = -1
        else:
            self.eval =  mape(self.seriesScalor.inverse_transform(self.valTransformed), self.predSeries)

        return self.eval
    
    def PlotPredict(self, path:str=None):
        plt.figure(figsize=self.figsize)
        # plot actual series
        series = self.seriesScalor.inverse_transform(self.seriesTransformed)
        series[:self.predSeries.end_time()].plot(label='actual')

        # plot prediction with quantile ranges
        self.predSeries.plot(
            low_quantile=self.lowest_q, high_quantile=self.highest_q, label=self.label_q_outer
    )
        self.predSeries.plot(low_quantile=self.low_q, high_quantile=self.high_q, label=self.label_q_inner)

        plt.title("MAPE: {:.2f}% TrainLoss: {:.3f}".format(self.eval, self.trainLoss))
        plt.legend()
        plt.tight_layout()
        if path == None:
            plt.savefig("predict-actual.pdf")
        else:
            if os.path.exists(os.path.dirname(path+'-predict-actual.pdf')):
                plt.savefig(path+"-predict-actual.pdf")
            else:
                os.makedirs(os.path.dirname(path+'-predict-actual.pdf'))
                plt.savefig(path+"-predict-actual.pdf")
        plt.close()
    
    def BackTest(self, startTime, forcastHorizon, last_points_only=False, ):
        if self.futureCovariates == None:
            backTestSeriesTransformed = self.model.historical_forecasts(
                self.seriesTransformed,
                num_samples = self.num_samples,
                start = startTime,
                forecast_horizon=forcastHorizon,
                stride=1 if last_points_only else forcastHorizon,
                retrain=False,
                last_points_only=last_points_only,
                overlap_end=True,
                verbose=True,
            )
        else:
            backTestSeriesTransformed = self.model.historical_forecasts(
                self.seriesTransformed,
                future_covariates = self.futureCovariates,
                num_samples = self.num_samples,
                start = startTime,
                forecast_horizon=forcastHorizon,
                stride=1 if last_points_only else forcastHorizon,
                retrain=False,
                last_points_only=last_points_only,
                overlap_end=True,
                verbose=True,
            )


        self.backTestSeriesTransformed = (
            concatenate(backTestSeriesTransformed)
            if isinstance(backTestSeriesTransformed, list)
            else backTestSeriesTransformed
        )
        self.backTestSeries = self.seriesScalor.inverse_transform(self.backTestSeriesTransformed)

    def EvaluateBackTest(self, horizon, startTime, path:str=None):

        mapeValue = mape(
            self.seriesScalor.inverse_transform(self.seriesTransformed),
            # self.seriesScalor.inverse_transform(self.backTestSeries),
            self.backTestSeries,
        )
        interval_value, interval_unit = time_util.split_time_delta(self.timeUnit)
        plt.figure(figsize=self.figsize)
        self.seriesScalor.inverse_transform(self.seriesTransformed).plot(label="actual")
        # self.seriesScalor.inverse_transform(self.backTestSeries).plot(low_quantile=self.lowest_q, high_quantile=self.highest_q, label=self.label_q_outer)
        # self.seriesScalor.inverse_transform(self.backTestSeries).plot(low_quantile=self.low_q, high_quantile=self.high_q, label=self.label_q_inner)
        self.backTestSeries.plot(low_quantile=self.lowest_q, high_quantile=self.highest_q, label=self.label_q_outer)
        self.backTestSeries.plot(low_quantile=self.low_q, high_quantile=self.high_q, label=self.label_q_inner)
        
        plt.legend()
        plt.title(f"Backtest, starting {startTime}, {horizon*interval_value} {interval_unit} horizon, MAPE: {mapeValue:.2f}%, TrainLoss: {self.trainLoss:.3f}", fontdict={'fontsize':10})
        # print(
        #     "MAPE: {:.2f}%".format(
        #         mape(
        #             self.seriesScalor.inverse_transform(self.seriesTransformed),
        #             self.seriesScalor.inverse_transform(self.backTestSeries),
        #         )
        #     )
        # )
        plt.tight_layout()
        if path == None:
            plt.savefig("backtest.pdf")
        else:
            if os.path.exists(os.path.dirname(path+'-backtest.pdf')):
                plt.savefig(path+"-backtest.pdf")
            else:
                os.makedirs(os.path.dirname(path+'-backtest.pdf'))
                plt.savefig(path+"-backtest.pdf")
        plt.close()

def TimeDeviation(frontSeries:TimeSeries, backSeries:TimeSeries, highQuantile=0.9, lowQuantile=0.1, iouThreshold=0.5, distanceThreshold=0.5, timeUnit:str='1D'):
    frontHighQuantile = frontSeries.quantile(highQuantile)
    frontLowQuantile = frontSeries.quantile(lowQuantile)
    frontMedianQuantile = frontSeries.quantile(0.5)

    backHighQuantile = backSeries.quantile(highQuantile)
    backLowQuantile = backSeries.quantile(lowQuantile)
    backMedianQuantile = backSeries.quantile(0.5)

    #平均值
    frontHighQuantileMean = frontHighQuantile.mean(axis=0)
    frontLowQuantileMean = frontLowQuantile.mean(axis=0)
    frontMedianQuantileMean = frontMedianQuantile.mean(axis=0)

    backHighQuantileMean = backHighQuantile.mean(axis=0)
    backLowQuantileMean = backLowQuantile.mean(axis=0)
    backMedianQuantileMean = backMedianQuantile.mean(axis=0)

    #数据分布区间
    # frontInternal = frontHighQuantileMean-frontLowQuantileMean
    # backInternal = backHighQuantileMean-backLowQuantileMean
    #两区间的交集，并集范围
    #交集
    interactInternal = np.min((frontHighQuantileMean.last_value(), backHighQuantileMean.last_value())) - np.max((frontLowQuantileMean.last_value(), backLowQuantileMean.last_value()))
    interactInternal = np.max((0, interactInternal))
    #并集
    unionInternal = np.max((frontHighQuantileMean.last_value(), backHighQuantileMean.last_value())) - np.min((frontLowQuantileMean.last_value(), backLowQuantileMean.last_value()))

    #交并比
    iou = interactInternal/unionInternal
    
    #中心距，尺度大小
    centerDistance = np.abs(backMedianQuantileMean.last_value() - frontMedianQuantileMean.last_value())
    #距离比
    distanceRate = centerDistance/unionInternal

    interval_value, interval_unit = time_util.split_time_delta(timeUnit)

    if iou < iouThreshold and distanceRate > distanceThreshold:
        start_date = frontSeries.time_index[len(frontSeries)//2]
        end_date = backSeries.time_index[len(backSeries)//2]
        # if timeUnit == 'day':
        #     timeRange = pd.date_range(start=start_date, end=end_date, freq='D')
        # elif timeUnit == '10T':
        #     timeRange = pd.date_range(start=start_date, end=end_date, freq='10T')
        # elif timeUnit == 'month':
        #     timeRange = pd.date_range(start=start_date, end=end_date, freq='M')
        # elif timeUnit == 'quater':
        #     timeRange = pd.date_range(start=start_date, end=end_date, freq='Q')
        # elif timeUnit == 'year':
        #     timeRange = pd.date_range(start=start_date, end=end_date, freq='Y')
        timeRange = pd.date_range(start=start_date, end=end_date, freq=str(interval_value)+time_util.__timedelta_resample_unit_dict[interval_unit])
        timeDiff = timeRange[-1] - timeRange[0]
        #timedelta转float
        #numpy没有季度单位，用3M表示,所以要在提取一次数量
        sub_interval_value, sub_interval_unit = time_util.split_time_delta(time_util.__timedelta_numpy_unit_dict[interval_unit])
        timeDiff = timeDiff.to_numpy().astype('timedelta64['+str(interval_value*sub_interval_value)+sub_interval_unit+']')/np.timedelta64(1,str(interval_value*sub_interval_value)+sub_interval_unit)
        if timeDiff > 0:
            meanDeviation = centerDistance / timeDiff
        else:
            meanDeviation = None
    else:
        start_date = frontSeries.time_index[len(frontSeries)//2]
        end_date = backSeries.time_index[len(backSeries)//2]
        # if timeUnit == 'day':
        #     timeRange = pd.date_range(start=start_date, end=end_date, freq='D')
        # elif timeUnit == '10T':
        #     timeRange = pd.date_range(start=start_date, end=end_date, freq='10T')
        # elif timeUnit == 'month':
        #     timeRange = pd.date_range(start=start_date, end=end_date, freq='M')
        # elif timeUnit == 'quater':
        #     timeRange = pd.date_range(start=start_date, end=end_date, freq='Q')
        # elif timeUnit == 'year':
        #     timeRange = pd.date_range(start=start_date, end=end_date, freq='Y')
        timeRange = pd.date_range(start=start_date, end=end_date, freq=str(interval_value)+time_util.__timedelta_resample_unit_dict[interval_unit])
        timeDiff = timeRange[-1] - timeRange[0]
        #timedelta转float
        #numpy没有季度单位，用3M表示,所以要在提取一次数量
        sub_interval_value, sub_interval_unit = time_util.split_time_delta(time_util.__timedelta_numpy_unit_dict[interval_unit])
        timeDiff = timeDiff.to_numpy().astype('timedelta64['+str(interval_value*sub_interval_value)+sub_interval_unit+']')/np.timedelta64(interval_value*sub_interval_value,sub_interval_unit)
        centerDistance = 0.
        meanDeviation = 0.

    return frontMedianQuantileMean.last_value(), backMedianQuantileMean.last_value(), centerDistance, timeRange, meanDeviation, iou, distanceRate
            

def TFTAnalyse(series:TimeSeries, tftModel:CreateTFTModel, timeUnit:str, startTime, endTime, timeSampleNum:int=24, highQuantile=0.9, lowQuantile=0.1, forcastHorizon=12, iouThreshold=0.5, distanceThreshold=0.5):
    # #预测
    # tftModel.Predict(forcastHorizon=forcastHorizon)
    # #评估模型
    # tftModel.EvaluatePredict()
    # #作图
    # tftModel.PlotPredict()

    # #历史回溯
    # startTime_ = series.time_index[series.time_index >= startTime][0]
    # # endTime_ = series.time_index[series.time_index <= endTime][-1]
    # tftModel.BackTest(startTime_, forcastHorizon=forcastHorizon, last_points_only=False)
    # #评估模型并作图
    # tftModel.EvaluateBackTest(forcastHorizon, startTime_)

    #截取头尾部分序列, 转为原始数据
    historyOriginSeries = tftModel.backTestSeries
    # frontSeries = historyOriginSeries[historyOriginSeries.time_index>=startTime][:timeSampleNum]
    # backSeries = historyOriginSeries[historyOriginSeries.time_index<=endTime][-timeSampleNum:]
    if historyOriginSeries.time_index[-1] > endTime:
        frontSeries = historyOriginSeries.split_after(startTime)[1][:timeSampleNum]#[historyOriginSeries.time_index>=startTime][:timeSampleNum]
        backSeries = historyOriginSeries.split_after(endTime)[0][-timeSampleNum:]#[historyOriginSeries.time_index<=endTime][-timeSampleNum:]
    else:
        frontSeries = historyOriginSeries.split_after(startTime)[1][:timeSampleNum]
        if len(frontSeries) > 1:
            backSeries = frontSeries[len(frontSeries)//2:]#[historyOriginSeries.time_index<=endTime][-timeSampleNum:]
            frontSeries = frontSeries[:len(frontSeries)//2]#[historyOriginSeries.time_index<=endTime][-timeSampleNum:]
        # elif len(frontSeries) == 1:
        #     return frontSeries.last_value(), frontSeries.last_value(), 0., pd.date_range(start=frontSeries.time_index[0], end=frontSeries.time_index[0]), 0, 0, 0
        else:
            return 0, 0, 0., 0, 0, 0, 0

    #求平均变化量
    frontValue, backValue, centerDistance, timeRange, meanDeviation, iou, distanceRate = TimeDeviation(frontSeries, backSeries, highQuantile=highQuantile, lowQuantile=lowQuantile, iouThreshold=iouThreshold, distanceThreshold=distanceThreshold, timeUnit=timeUnit)

    return frontValue, backValue, centerDistance, timeRange, meanDeviation, iou, distanceRate

# def TFTAnalyse(dfSeq:pd.DataFrame, timeUnit:str, startTime, endTime, input_chunk_length = 24, out_chunck_length = 12, timeSampleNum:int=24, trainCutOff:Union[pd.Timestamp, float, int]=None, numEpoch=300, futureCovariates=None, forcastHorizon=12, iouThreshold=0.5, distanceThreshold=0.5):
    
#     #取平均
#     series = MeanOverTime(dfSeq, timeUnit)
#     # #归一化
#     # trainNormal, valNormal, seriesNormal, seriesTransformer = NormalizeSeries(series, trainCutOff)
#     # #协变量
#     # trainCovariate, valCovariate, seiresCovariate, covariateTransformer = CreateCovariates(seriesNormal, trainCutOff)

#     #创建模型并训练
#     tftModel = CreateTFTModel(series, input_chunk_length = input_chunk_length, out_chunck_length = out_chunck_length, futureCovariates=futureCovariates, numEpoch=numEpoch, cutOff=trainCutOff) 

#     #预测
#     tftModel.Predict(forcastHorizon=forcastHorizon)
#     #评估模型
#     tftModel.EvaluatePredic()
#     #作图
#     tftModel.PlotPredict()

#     #历史回溯
#     startTime_ = series.time_index[series.time_index >= startTime][0]
#     # endTime_ = series.time_index[series.time_index <= endTime][-1]
#     tftModel.BackTest(startTime_, forcastHorizon=forcastHorizon, last_points_only=False)
#     #评估模型并作图
#     tftModel.EvaluateBackTest(forcastHorizon, startTime_)

#     #截取头尾部分序列, 转为原始数据
#     historyOriginSeries = tftModel.seriesScalor.inverse_transform(tftModel.backTestSeries),
#     frontSeries = historyOriginSeries[historyOriginSeries.time_index>=startTime][:timeSampleNum]
#     backSeries = historyOriginSeries[historyOriginSeries.time_index<=endTime][-timeSampleNum:]
#     #求平均变化量
#     frontValue, backValue, centerDistance, timeRange, meanDeviation = tftModel.TimeDeviation(frontSeries, backSeries, iouThreshold=0.5, distanceThreshold=0.5, timeUnit=timeUnit)

#     return frontValue, backValue, centerDistance, timeRange, meanDeviation
#     #