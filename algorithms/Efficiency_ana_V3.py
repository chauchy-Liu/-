from alarms import alarm
from pandas import DataFrame
from configs import config
from configs.faultcode_SANY import fault as fault_code
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
from configs.config import algConfig, state
from algorithms.turbine_efficiency_function_V3 import mymode
import algorithms.turbine_efficiency_function_V3 as turbine_efficiency_function
from db.db import InsertIndex, get_connection_efficiency
import os

name = algConfig['Efficiency_ana_V3']['name']#'能效指标'
# 把所需测点定义到每个算法里
ai_points = algConfig['Efficiency_ana_V3']['ai_points']
ai_rename = algConfig['Efficiency_ana_V3']['ai_rename']
di_points = algConfig['Efficiency_ana_V3']['di_points']
general_points = algConfig['Efficiency_ana_V3']['general_points']
private_points = algConfig['Efficiency_ana_V3']['private_points']
time_duration = algConfig['Efficiency_ana_V3']['time_duration']
resample_interval = algConfig['Efficiency_ana_V3']['resample_interval']
error_percentage = algConfig['Efficiency_ana_V3']['error_percentage']
need_all_turbines = algConfig['Efficiency_ana_V3']['need_all_turbines']
store_file = algConfig['Efficiency_ana_V3']['store_file']
Df_all = 0
vane_nan_num = 0

Df_all_all = pd.DataFrame()
Df_all_m_all = pd.DataFrame()
def wash_data(pn_data: DataFrame, Turbine_attr):
    tur_num = len(Turbine_attr)
    global ai_points
    global di_points
    global general_points
    global Df_all_all
    global Df_all_m_all
    #统一处理能效指标的重命名
    #分列数据测点、状态测点、故障测点
    dataList = pn_data.columns.to_list()
    ai_points = [x for x in ai_points if x in dataList]
    di_points = [x for x in di_points if x in dataList]
    general_points = [x for x in general_points if x in dataList]

    for num in range(tur_num):
        turbine_name = Turbine_attr.iloc[num]['name']
        Df_all_m = pd.DataFrame()
        Df_all = pn_data[pn_data['wtid']==turbine_name][ai_points]
        state_all = pn_data[pn_data['wtid']==turbine_name][di_points]
        fault_all = pn_data[pn_data['wtid']==turbine_name][general_points]
        #数据测点----------------------------------
        Df_all['localtime'] = pd.to_datetime(Df_all.index,errors='coerce')
        Df_all.set_index('localtime',inplace= True)
        # Df_all.drop('timestamp',axis=1,inplace=True)
        # Df_all.drop('assetId',axis=1,inplace=True)
        Df_all.rename(columns = {'WGEN.GenActivePW':'pwrat','WROT.Blade1Position':'pitch1','WROT.Blade2Position':'pitch2','WROT.Blade3Position':'pitch3',
                                        'WNAC.WindSpeed':'wspd','WNAC.WindVaneDirection':'wdir0','WNAC.WindDirection1':'wdir25','WNAC.WindDirection':'wdir',
                                        'WWPP.APProduction':'pwp','WWPP.APConsumed':'pwcs','WTUR.MainFaultCode':'faultmain',
                                        'WROT.TemB1Mot':'mot1tmp','WROT.TemB2Mot':'mot2tmp','WROT.TemB3Mot':'mot3tmp','WTRM.RotorPDM':'rotspdzz',
                                        'WROT.CurBlade1Motor':'mot1cur','WROT.CurBlade2Motor':'mot2cur','WROT.CurBlade3Motor':'mot3cur',
                                        'WROT.PtCptTmpBl1':'cp1tmp','WROT.PtCptTmpBl2':'cp2tmp','WROT.PtCptTmpBl3':'cp3tmp',
                                        'WROT.VolB1Cap':'cap1vol','WROT.VolB2Cap':'cap2vol','WROT.VolB3Cap':'cap3vol',
                                        'WNAC.TemOut':'exltmp','WNAC.TemNacelle':'nactmp','WGEN.GenSpdInstant':'rotspd','WGEN.GenSpd':'rotspd',
                                        'WROT.Blade1Speed':'pitch1spd','WROT.Blade2Speed':'pitch2spd','WROT.Blade3Speed':'pitch3spd',
                                        'WGEN.TemGenDriEnd':'gen_zcd_tmp','WGEN.TemGenNonDE':'gen_zcnd_tmp','WGEN.GenSenMaxTmp':'genmaxtmp',
                                        'WGEN.GenSenTmp1':'gen1tmp','WGEN.GenSenTmp2':'gen2tmp','WGEN.GenSenTmp3':'gen3tmp',
                                        'WGEN.GenSenTmp4':'gen4tmp','WGEN.GenSenTmp5':'gen5tmp','WGEN.GenSenTmp6':'gen6tmp',
                                        'WYAW.NacellePosition':'yaw','WYAW.YawSpeed':'yawspd','WVIB.VibrationValid':'accxy',
                                        'WVIB.VibrationV':'accx','WVIB.VibrationVFil':'accxfil','WVIB.VibrationL':'accy','WVIB.VibrationLFil':'accyfil',
                                        'WYAW.YawMotor1RunTime':'yaw1time','WYAW.YawMotor2RunTime':'yaw2time','WYAW.YawMotor3RunTime':'yaw3time',
                                        'WTRM.HubAngle':'yaw','WTRM.RotorSpd':'rotspdzz','WNAC.TemNacelleCab':'nacelcabtmp',
                                        'WCNV.CVTTemWaterCoolInlet':'cvintmp','WCNV.CVTTemWaterCoolOutlet':'cvouttmp','WYAW.YawOpWind5sAVG':'wdirs',
                                        'WTRM.TemMainBearing':'mainbeartmp','WYAW.YawCountSum':'yawsum','WNAC.WindDirectionInstant':'wdirs','WTUR.SITURAI17':'wdirs',
                                        'WNAC.WindVaneDirectionInstant':'wdir0','WTRM.TemGeaMSND':'gear_msnd_tmp','WTRM.TemGeaMSDE':'gear_msde_tmp',
                                        'WGEN.TemGenStaU':'genUtmp','WGEN.TemGenStaV':'genVtmp','WGEN.TemGenStaW':'genWtmp','WTRM.TemGeaOil':'gear_oil_tmp',
                                        'WTRM.TemGeaLSDE':'gear_lsde_tmp','WTRM.TemGeaLSND':'gear_lsnd_tmp','WTRM.TrmTmpShfBrg':'zztmp',
                                        'WNAC.WindDirection_AVG_10m':'wdir25'
                                        },inplace = True)
                
        Df_all.index = pd.to_datetime(Df_all.index)
        Df_all = Df_all.dropna(axis=1,thresh=int(len(Df_all)*0.1))#某列非空值数量小于总数的10%剔除该列
        Df_all = Df_all.loc[:,~Df_all.columns.duplicated()]
        Df_all.loc[:,Df_all.dtypes=='float64'] = Df_all.loc[:,Df_all.dtypes=='float64'].astype('float32')

        #状态测点------------------------------------
        state_all['localtime'] = pd.to_datetime(state_all.index,errors='coerce')
        state_all.set_index('localtime',inplace= True)
        # state_all.drop('timestamp',axis=1,inplace=True)
        # state_all.drop('assetId',axis=1,inplace=True)
        state_all.rename(columns = {'WTUR.TurbineAIStatus':'statel'},inplace = True)
        state_all.rename(columns = {'WTUR.TurbineSts':'state','WTUR.TurbineSts_Map':'state'},inplace = True)
        state_all = state_all.loc[:,~state_all.columns.duplicated()]
        state_all.rename(columns = {'WTUR.TurbineUnionSts':'statety'},inplace = True)
        
        if 'statel' in state_all.columns.to_list():
            state_all['sta1'] = state_all['statel'].shift(periods=1,axis=0)
            state_all['shift'] = state_all['statel']-state_all['sta1']
            state_allf = state_all.loc[state_all['shift']!=0,'statel']####剔除连续时间重复状态
            #tempf = tempf[~tempf['shift'].isnull()]
            Df_all = Df_all.join(state_allf,how='outer')
            Df_all['statel'] = Df_all['statel'].fillna(method='ffill')
        else:
            Df_all['statel'] = 90002
        if 'state' in state_all.columns.to_list():
            state_all['sta1'] = state_all['state'].shift(periods=1,axis=0)
            state_all['shift'] = state_all['state']-state_all['sta1']
            state_allf = state_all.loc[state_all['shift']!=0,'state']####剔除连续时间重复状态
            #tempf = tempf[~tempf['shift'].isnull()]
            Df_all = Df_all.join(state_allf,how='outer')
            Df_all['state'] = Df_all['state'].fillna(method='ffill')
        else:
            Df_all['state'] = state
        if 'statety' in state_all.columns.to_list():
            state_all['sta1'] = state_all['statety'].shift(periods=1,axis=0)
            state_all['shift'] = state_all['statety']-state_all['sta1']
            state_allf = state_all.loc[state_all['shift']!=0,'statety']####剔除连续时间重复状态
            #tempf = tempf[~tempf['shift'].isnull()]
            Df_all = Df_all.join(state_allf,how='outer')
            Df_all['statety'] = Df_all['statety'].fillna(method='ffill')
        else:
            Df_all['statety'] = 71

        #故障测点----------------------------------
        if len(fault_all) > 0:
            fault_all['localtime'] = pd.to_datetime(fault_all.index,errors='coerce')    
            fault_all.set_index('localtime',inplace= True)
            # fault_all.drop('timestamp',axis=1,inplace=True)
            # fault_all.drop('assetId',axis=1,inplace=True)
            fault_all.rename(columns = {'WTUR.AIStatusCode':'fault','WTUR.AIStatusCode_Map':'fault'},inplace = True)
            fault_all = fault_all.dropna(axis=1,how='all')
            fault_all = fault_all.loc[:,~fault_all.columns.duplicated()]
                        
            fault_all['flt1'] = fault_all['fault'].shift(periods=1,axis=0)
            fault_all['shift'] = fault_all['fault']-fault_all['flt1']
            fault_allf = fault_all.loc[fault_all['shift']!=0,'fault']####剔除连续时间重复故障
            Df_all = Df_all.join(fault_allf,how='outer')
            Df_all['fault'] = Df_all['fault'].fillna(method='ffill')
        else:
            Df_all['fault'] = 0

        #10m采样
        Df_all_m = Df_all.resample('10min',closed='left').apply({mymode,np.nanmean,np.nanmax,np.nanmin,np.nanstd})
        Df_all_m.insert(0,'wtid',turbine_name)  
        Df_all.insert(0,'wtid',turbine_name) 
        # Df_all_all = Df_all_all.append(Df_all)#全场1min数据
        Df_all_all = pd.concat([Df_all_all, Df_all])
        # Df_all_m_all = Df_all_m_all.append(Df_all_m)#全10min场数据  
        Df_all_m_all = pd.concat([Df_all_m_all, Df_all_m])
    data = {
    'Column1': ['finished'],
    }
    temp_data = pd.DataFrame(data)
    return temp_data, ''

async def judge_model(pn_data: DataFrame, Turbine_attr, threshold, idMaps, configAlgorithm):

    #额定功率
    Pwrat_Rate = Turbine_attr.iloc[0]['ratedPower']
    #叶轮半径
    rotor_radius = Turbine_attr.iloc[0]['rotorDiameter']*0.5#Turbine_attr_type.loc[0,'attributes']['rotorDiameter']*0.5
    #轮毂高度
    hub_high = Turbine_attr.iloc[0]['hubHeight']


    turbine_err_all = pd.DataFrame()
    turbine_err_all['wtid'] = Turbine_attr.loc[:,'name']
    turbine_err_all['power_rate_err'] = 0  #额定功率异常
    turbine_err_all['wspd_power_err'] = 0  #风速功率散点异常
    turbine_err_all['torque_kopt_err'] = 0 #最佳Cp段转矩控制异常
    turbine_err_all['torque_rate_err'] = 0 #额定转速段转矩控制异常
    turbine_err_all['yaw_duifeng_err'] = 0 #对风偏航角度过大
    turbine_err_all['yaw_leiji_err'] = 0 #偏航控制误差过大
    turbine_err_all['pitch_min_err'] = 0 #最小桨距角异常
    turbine_err_all['pitch_control_err'] = 0 #变桨控制异常
    turbine_err_all['pitch_balance_err'] = 0 #三叶片变桨不平衡
    
    turbine_err_all['power_rate_loss'] = 0
    turbine_err_all['wspd_power_loss'] = 0
    turbine_err_all['torque_kopt_loss'] = 0
    turbine_err_all['torque_rate_loss'] = 0
    turbine_err_all['yaw_duifeng_loss'] = 0
    turbine_err_all['yaw_leiji_loss'] = 0
    turbine_err_all['pitch_min_loss'] = 0
    turbine_err_all['pitch_control_loss'] = 0
    turbine_err_all['pitch_balance_loss'] = 0
    turbine_err_all['pwrat_order'] = 1
    
    turbine_param_all = pd.DataFrame()
    
    #表1
    table_situation_power = pd.DataFrame(data=None, columns=['farm_name', 'average_wspd', 'practical_power', 'valid_hour', 'utilize_rate', 'time_rate', 'MTBT', 'loss_power', 'loss_power_fractor'])
    
    ####全场某一机型数据读取
    global Df_all_all
    global Df_all_m_all

    ##############关键参数确定
    wtids =  np.unique(Df_all_m_all[('wtid')])
    for i in range(len(wtids)):
        Df_all_m = Df_all_m_all[Df_all_m_all['wtid'] == wtids[i]]
        turbine_param_all.loc[i,'wtid'] = wtids[i]
        
        temp = Df_all_m[(Df_all_m['pwrat','nanmean']>10.0)&(Df_all_m['pwrat','nanmean']<Pwrat_Rate*0.2)&(Df_all_m['statel','nanmean']==90002)&(Df_all_m['state','nanmean']==state)&(Df_all_m['statety','nanmean']==71)]
        if len(temp)>0:
            Pitch_Min = round((np.mean(temp['pitch1','nanmean'].nsmallest(20)) + np.mean(temp['pitch1','nanmax'].nsmallest(20))) * 0.5,1)
        else:
            Pitch_Min = 0.0
        turbine_param_all.loc[i,'Pitch_Min'] = Pitch_Min
        
        temp = Df_all_m[(Df_all_m['pwrat','nanmean']>Pwrat_Rate*0.95)&(Df_all_m['pwrat','nanmean']<Pwrat_Rate*1.1)&(Df_all_m['rotspd','nanmean']>1.1)&(Df_all_m['state','nanmean']==state)&(Df_all_m['statety','nanmean']==71)]
        if len(temp)>0:
            Rotspd_Rate = round(np.nanmean(temp['rotspd','nanmean']),1)
        else:
            Rotspd_Rate = np.nan
        turbine_param_all.loc[i,'Rotspd_Rate'] = Rotspd_Rate
        
        temp = Df_all_m[(Df_all_m['pwrat','nanmean']>10.0)&(Df_all_m['pwrat','nanmean']<Pwrat_Rate*0.08)&(Df_all_m['pitch1','mymode']<=(Pitch_Min+1.0))&(Df_all_m['state','nanmean']==state)&(Df_all_m['statety','nanmean']==71)]
        if len(temp)>0:
            Rotspd_Connect = round(np.mean(temp['rotspd','nanmean'].nlargest(50)),1)
        else:
            Rotspd_Connect = np.nan
        turbine_param_all.loc[i,'Rotspd_Connect'] = Rotspd_Connect
    turbine_param_all['Rotspd_Rate'].fillna(value=np.nanmean(turbine_param_all['Rotspd_Rate']),inplace=True)
    turbine_param_all['Rotspd_Connect'].fillna(value=np.nanmean(turbine_param_all['Rotspd_Connect']),inplace=True)
        
    threshold = 3.0
    neighbors_num = 10

    #单层列名索引转多层列名索引
    columnList = []
    for elemColumn in fault_code.columns.to_list():
            columnList.append((elemColumn, ''))
    fault_code.columns = pd.MultiIndex.from_tuples(columnList)
    
    ##################################
    ############功率曲线绘制、风资源分析、发电量计算###########                
    zuobiao = pd.DataFrame()
    pw_df_all = pd.DataFrame()
    windbinreg = np.arange(1.75,25.25,0.5)
    windbin = np.arange(2.0,25.0,0.5)
    pw_df_all['windbin'] = windbin
    wind_ti_all = pd.DataFrame()
    wind_ti_all['windbin'] = windbin
    for num in range(len(Turbine_attr)): 
        turbine_name = wtids[num]
            
        Pitch_Min = turbine_param_all.loc[turbine_param_all['wtid']==turbine_name,'Pitch_Min'].values[0]
        Rotspd_Connect = turbine_param_all.loc[turbine_param_all['wtid']==turbine_name,'Rotspd_Connect'].values[0]
        Rotspd_Rate = turbine_param_all.loc[turbine_param_all['wtid']==turbine_name,'Rotspd_Rate'].values[0]
        
        Df_all_m = Df_all_m_all[Df_all_m_all['wtid'] == turbine_name]
        #10min数据清洗
        try:
            Df_all_m_clear = turbine_efficiency_function.data_min_clear(Df_all_m,state,Rotspd_Connect,Rotspd_Rate,Pwrat_Rate,Pitch_Min,neighbors_num=20,threshold=3)
            df_all_clear = Df_all_m_clear[Df_all_m_clear['clear'] == 2]#1为干净值
        except Exception:
            Df_all_m_clear = Df_all_m
            df_all_clear = Df_all_m
            Df_all_m_clear['clear'] = 2
        
        ##绘制功率曲线
        pw_df = turbine_efficiency_function.pwratcurve_rho(df_all_clear,windbin,6)
        pw_df = pw_df.loc[:,['windbin','pwrat']]
        pw_df.rename(columns = {'pwrat':turbine_name},inplace = True) 
        pw_df_all = pd.merge(pw_df_all,pw_df,how='outer',on='windbin')

    #####全场功率曲线及功率曲线中位数
    pw_df_all = pw_df_all.dropna(axis=0,how='all',subset=pw_df_all.columns[1:],inplace=False)
    pw_df_all.insert(1,'pwrat',0)
    for i in range(len(pw_df_all)):
        pw_df_all.iloc[i,1] = np.nanmedian(pw_df_all.iloc[i,2:]) 

    ############损失电量计算、指标计算###########   
    fault_loss_all = pd.DataFrame()
    limgrid_loss_all = pd.DataFrame()
    limturbine_loss_all = pd.DataFrame()
    stop_loss_all = pd.DataFrame()
    faultgrid_loss_all = pd.DataFrame()
    Technology_loss_all = pd.DataFrame()
    Df_all_m_range_all = pd.DataFrame()

    #截取时间范围
    endTime = configAlgorithm['endTime']#datetime.now()
    date = endTime.date()
    days = str(date).split('-')[2]
    if days[0] == '0':
        days = days[1]
    startTime = endTime - pd.to_timedelta(days+'D')
    
    for num in range(len(Turbine_attr)):
        
        fault_loss = pd.DataFrame()
        limgrid_loss = pd.DataFrame()
        limturbine_loss = pd.DataFrame()
        stop_loss = pd.DataFrame()
        faultgrid_loss = pd.DataFrame()
        Technology_loss = pd.DataFrame()
        
        turbine_name = wtids[num]
        pw_df_temp = pw_df_all.loc[:,['windbin','pwrat',turbine_name]]
        pw_df_temp[turbine_name] = pw_df_temp[turbine_name].fillna(pw_df_temp.loc[pw_df_temp[turbine_name].isnull(),'pwrat'])
        
        Df_all_m = Df_all_m_all[Df_all_m_all['wtid'] == turbine_name]
        Df_all_m['windbin'] = pd.cut(Df_all_m['wspd','nanmean'],windbinreg,labels=windbin)

        
        Df_all_m_range = Df_all_m[(Df_all_m.index>pd.to_datetime(startTime)) & (Df_all_m.index<pd.to_datetime(endTime))]
        Df_all_m_range_all = pd.concat([Df_all_m_range_all,Df_all_m_range])
        #单层列名索引转多层列名索引
        columnList = []
        for elemColumn in pw_df_temp.columns.to_list():
            columnList.append((elemColumn, ''))
        pw_df_temp.columns = pd.MultiIndex.from_tuples(columnList)
        columnList = []
        
        ###单机故障损失计算(分仓、功率曲线合并后的数据框---未知故障解释的停机全部归到故障停机中)###有故障时故障码不为0！！！！！！！！！！！！！！
        ##金风机组发生编码为733的故障时，风速不更新，导致损失电量计算不准确
        fault_loss = turbine_efficiency_function.Turbine_Fault_Loss(Df_all_m_range,turbine_name,pw_df_temp,fault_code)   
        
        ###单机电网限电损失(不包括限功率停机)，最小桨距角异常、额定功率异常不计算，这两种控制异常中台都会标记为90001！！！！！！
        if (turbine_err_all.loc[turbine_err_all['wtid']==turbine_name,'power_rate_err'].values == 0)&(turbine_err_all.loc[turbine_err_all['wtid']==turbine_name,'pitch_min_err'].values == 0):
            limgrid_loss = turbine_efficiency_function.Grid_Limit_Loss(Df_all_m_range,turbine_name,pw_df_temp,fault_code)
        
        ###单机计划停机损失
        stop_loss = turbine_efficiency_function.Stop_Loss(Df_all_m_range,turbine_name,pw_df_temp,fault_code)
        
        #单机电网故障损失
        faultgrid_loss = turbine_efficiency_function.Grid_Fault_Loss(Df_all_m_range,turbine_name,pw_df_temp,fault_code)
        
        ##单机自限电损失输入
        if (turbine_err_all.loc[turbine_err_all['wtid']==turbine_name,'wspd_power_err'].values == 0):###风速功率散点异常不计算
            (data_limt,limturbine_loss) = turbine_efficiency_function.Turbine_Limit_Loss(Df_all_m_range,turbine_name,pw_df_temp,Pitch_Min,Pwrat_Rate,state)
        
        #单机技术待命损失    
        Technology_loss = turbine_efficiency_function.Turbine_Technology_Loss(Df_all_m_range,turbine_name,pw_df_temp,fault_code) 

        ##全场损失统计
        fault_loss_all = pd.concat([fault_loss, fault_loss_all])
        faultgrid_loss_all = pd.concat([faultgrid_loss_all, faultgrid_loss]) #faultgrid_loss_all.append(faultgrid_loss)
        limgrid_loss_all = pd.concat([limgrid_loss_all, limgrid_loss]) #limgrid_loss_all.append(limgrid_loss)
        stop_loss_all = pd.concat([stop_loss_all, stop_loss]) # stop_loss_all.append(stop_loss)
        limturbine_loss_all = pd.concat([limturbine_loss_all, limturbine_loss]) #limturbine_loss_all.append(limturbine_loss) 
        Technology_loss_all = pd.concat([Technology_loss_all, Technology_loss]) #Technology_loss_all.append(Technology_loss)

    #汇总指标--------------------
    reason_loss = pd.DataFrame(None, columns=['机组故障损失', '电网故障损失', '计划停机损失', '电网限电损失', '机组自限电损失', '技术待机损失'])

    if len(fault_loss_all) <= 0:
        fault_loss_all['loss'] = 0
        reason_loss.loc[0, '机组故障损失'] = 0
    else:
        reason_loss.loc[0, '机组故障损失'] = fault_loss_all['loss'].sum()/10000.0
    if len(limgrid_loss_all) <= 0:
        limgrid_loss_all['loss'] = 0
        reason_loss.loc[0, '电网限电损失'] = 0
    else:
        reason_loss.loc[0, '电网限电损失'] = limgrid_loss_all['loss'].sum()/10000.0

    if len(faultgrid_loss_all) <= 0:
        faultgrid_loss_all['loss'] = 0
        reason_loss.loc[0, '电网故障损失'] = 0
    else:
        reason_loss.loc[0, '电网故障损失'] = faultgrid_loss_all['loss'].sum()/10000.0

    if len(limturbine_loss_all) <= 0:
        limturbine_loss_all['loss'] = 0
        reason_loss.loc[0, '机组自限电损失'] = 0
    else:
        reason_loss.loc[0, '机组自限电损失'] = limturbine_loss_all['loss'].sum()/10000.0

    if len(stop_loss_all) <= 0:
        stop_loss_all['loss'] = 0
        reason_loss.loc[0, '计划停机损失'] = 0
    else:
        reason_loss.loc[0, '计划停机损失'] = stop_loss_all['loss'].sum()/10000.0

    if len(Technology_loss_all) <= 0:
        Technology_loss_all['loss'] = 0
        reason_loss.loc[0, '技术待机损失'] = 0
    else:
        reason_loss.loc[0, '技术待机损失'] = stop_loss_all['loss'].sum()/10000.0

    table_situation_power.loc[0,'average_wspd'] = np.nanmean(Df_all_m_range_all['wspd','nanmean'])
    table_situation_power.loc[0,'practical_power'] = np.nansum(Df_all_m_range_all['pwrat','nanmean'])/6.0/10000.0
    table_situation_power.loc[0,'valid_hour'] = np.nansum(Df_all_m_range_all['pwrat','nanmean'])/6.0/(len(Turbine_attr)*Pwrat_Rate)

    loss_sum = np.nansum(fault_loss_all['loss']) + np.nansum(limgrid_loss_all['loss']) + np.nansum(faultgrid_loss_all['loss']) + np.nansum(limturbine_loss_all['loss']) + np.nansum(Technology_loss_all['loss']) + np.nansum(stop_loss_all['loss'])
    table_situation_power.loc[0,'loss_power']  = loss_sum/10000.0
    table_situation_power.loc[0,'loss_power_fractor'] = table_situation_power.loc[0,'loss_power']/(table_situation_power.loc[0,'loss_power']+table_situation_power.loc[0,'practical_power'])
    table_situation_power.loc[0,'time_rate'] = turbine_efficiency_function.Time_Avail(Df_all_m_range_all,wtids)
    table_situation_power.loc[0,'utilize_rate'] = turbine_efficiency_function.Eny_Avail(Df_all_m_range_all,np.nansum(fault_loss_all['loss']),np.nansum(limgrid_loss_all['loss']),np.nansum(faultgrid_loss_all['loss']),np.nansum(limturbine_loss_all['loss']),np.nansum(Technology_loss_all['loss']),np.nansum(stop_loss_all['loss']))
    table_situation_power.loc[0,'MTBT'] = turbine_efficiency_function.MTBT_Calculate(Df_all_m_range_all,fault_loss_all,wtids)
    #+++++++++++++++++++++++++++++++++++++++++++++++++++
    startTime = startTime.strftime("%Y-%m-%d %H:%M:%S")
    endTime = endTime.strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection_efficiency(os.path.join("configs/", "config.yaml"))
    InsertIndex(conn, table_situation_power.iloc[0]["average_wspd"], table_situation_power.iloc[0]["practical_power"], table_situation_power.iloc[0]["loss_power"], table_situation_power.iloc[0]["valid_hour"], table_situation_power.iloc[0]["utilize_rate"], table_situation_power.iloc[0]["time_rate"], startTime, endTime)

    return pd.DataFrame(), '', [], 0, 0