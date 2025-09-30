# -*- coding: utf-8 -*-
"""
常量值
"""

# 应用风场的assetId
Wind_Farm = 'duMC5TRo' #江西



#模块附加区分名
extraModelName = None #'B' #江西保留

# 告警推送url
# Alarm_Push_Url = 'https://xxxx/warn/receiveWarn'
# Alarm_Push_Url = 'http://172.16.3.232:9000/api-smartisolar/sub-warn/warn/receiveWarnInfo'
Alarm_Push_Url = 'http://10.67.68.188:9001/api/v1/standardAlarmGateway/attributes'

# 并网转速
Rotspd_Connect = 7.5
# 额定转速
Rotspd_Rate = 14.5
# 转矩控制系数

# 最小桨距角
Pitch_Min = 0.0

# 并网状态
state = 6

# 合计风速
fitWindSpd = [3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5, 10, 10.5, 11, 11.5, 12, 12.5, 13]
# 合计功率
fitPrWt = [63.62, 117.74, 188.03, 268.94, 370.20, 493.22, 640.86, 814.65, 1017.48, 1251.46, 1518.81, 1812.87, 2020, 2020, 2020, 2020, 2020, 2020, 2020, 2020, 2020]


AccessKey = '3f207c85-64b4-476c-a23d-64624bbc0669'
SecretKey = 'f30502cc-2b51-41d0-a95b-6275d609e5bf'
OrgId = "o16323808037221371"
GW_Url = 'https://ag-spic1.eniot.io'

# 告警推送目标 db/http
# ALARM_PUSH_MODE = 'db'
ALARM_PUSH_MODE = 'http'

# 数据展示存放目录
Path = '/opt/app/wind-algorithm-model/fileData/'#部署  '/opt/app/wind-algorithm-model/fileData/'#'./result/Display/'#/opt/app/wind-algorithm-model/fileData
# Path = './result/Display/'# 调试  /opt/app/wind-algorithm-model/fileData/'#'./result/Display/'#/opt/app/wind-algorithm-model/fileData

# 数据库配置
DB_HOST = '127.0.0.1'#'172.17.11.95' #部署
# DB_HOST = '172.17.11.95'#'172.17.11.95' #'127.0.0.1' 调试


DB_USERNAME = 'iwind'#'iwind2' 'iwind' 部署
# DB_USERNAME = 'iwind2'#'iwind2' 调试

# 想自己的服务器推送警告
AL_PUSH_URL_SELF = "http://127.0.0.1:8088/iwind-edge-api-jx/base/DataAlarm/addAlarm"
# 向自己的服务器推送超过阈值
OV_PUSH_URL_THR = "" #"http://127.0.0.1:8088/iwind-edge-api-jx/base/DataAlarm/upPnState"

DB_PORT = 3306
DB_PASSWORD = 'IotPlatform!v1.0'
DB_DATABASE = 'ewind'

# AL_PORT = 8088

KKS_DEVICE = {
    "7abOi7vl" : "kksSJJFJ0000000001",
    "X4sahNnm" : "kksSJJFJ0000000002",
    "KlE0ZgCn" : "kksSJJFJ0000000003",
    "8lK7h1Hn" : "kksSJJFJ0000000004",
    "NBuLy66Q" : "kksSJJFJ0000000005",
    "agnLwAui" : "kksSJJFJ0000000006",
    "GEVBFQ6T" : "kksSJJFJ0000000007",
    "IY2BuUEV" : "kksSJJFJ0000000008",
    "o4TKefAk" : "kksSJJFJ0000000009",
    "RSPazngf" : "kksSJJFJ0000000010",
    "6Sx893Sv" : "kksSJJFJ0000000011",
    "kYduHbsq" : "kksSJJFJ0000000012",
    "yQJdcdDQ" : "kksSJJFJ0000000013",
    "ELKsH15I" : "kksSJJFJ0000000014",
    "fjCNdWFa" : "kksSJJFJ0000000015",
    "6DjPkDvu" : "kksSJJFJ0000000016",
    "xry27k3m" : "kksSJJFJ0000000017",
    "C11Pi21g" : "kksSJJFJ0000000018",
    "yQ1nDyVL" : "kksSJJFJ0000000019",
    "6fVEVWaM" : "kksSJJFJ0000000020"
}


POSITION_CONFIG = {
   'WROT.Blade1Position': "轮毂", #桨叶角度
   'WNAC.TemOut': "舱外", #舱外温度
   'WGEN.GenActivePW': "发电机",#发电机有功功率
   'WTRM.TemGeaLSND': "齿轮箱内部",#齿轮箱低速轴非驱动端轴承温度
   'WTRM.TemGeaMSND': "齿轮箱内部",#齿轮箱高速轴非驱动端轴承温度
   'WTRM.TemGeaOil': "齿轮箱内部",#齿轮箱油池温度
   'WNAC.TemNacelleCab': "机舱控制柜",#机舱控制柜温
   'WNAC.TemNacelle': "机舱内",#舱内温度	
   'WGEN.TemGenNonDE': "发电机",#发电机非驱动端轴承温度	
   'WGEN.TemGenDriEnd': "发电机",#发电机驱动端轴承温度	
   'WGEN.TemGenStaU': "发电机",#发电机定子U相线圈温度
   'WGEN.GenSpd': "发电机",#发电机转速	
   'LOW_A_TMP': "箱变",#箱变温度检测：低压侧A相温度	
   'Vibration_Strength': "塔筒顶部",#塔筒振动强度
   'BLADE1_BLOT_ANGLE_1': "叶根螺栓",#螺栓检测：叶片1法兰1号螺栓反旋角度
   'WROT.PtCapTemBl1': "轮毂电容柜",#叶片1超级电容柜温度	
   'WROT.TemB1Mot': "变桨电机",#1号桨电机温度	
   'WROT.TemBlade1Inver': "轮毂变桨柜",#变桨驱动器1温度	
   'WNAC.WindVaneDirection': "机舱顶部",#机舱与风向夹角	
   'TOAT': "塔基",#塔底倾斜角度
   'BLD_DEFECTZ_FACTOR': "桨叶"#叶片缺陷系数	

}

# 执行时排除的模型列表
EXCEPT_MODLES = ["a", "b", "c",'chilunxiang_disu_zhoucheng_temperature','chilunxiang_gaosu_zhoucheng_temperature','chilunxiang_sanre', 'generator_houzhoucheng_temperature','generator_qianzhoucheng_temperature','generator_zhuzhou_rpm_not_balance','oar_electric_capacity_temperature','oar_machine_temperature'] #"tatong_qingjiao", ,  "luoshuansongdong", "hongwaicewen", 'WROT.Blade1Position','WNAC.WindSpeed', ,'chuandonglian'
# EXCEPT_MODLES = ['chilunxiang_disu_zhoucheng_temperature',
#                  'chilunxiang_gaosu_zhoucheng_temperature',
#                  'chilunxiang_sanre',
#                  'generator_houzhoucheng_temperature',
#                  'generator_qianzhoucheng_temperature',
#                  'generator_zhuzhou_rpm_not_balance',
#                  'oar_electric_capacity_temperature',
#                  'oar_machine_temperature']

#schedule
scheduleConfig = {
    "minunte-1": ['tatong_qingjiao', 'hongwaicewen'],
    "minunte-2":['jiegou_sunshang','chuandonglian'],
    "hour":['weathercock_freeze','blade_freeze', 'hongwai_sanxiang','pianhang_duifeng_buzheng', 'generator_zhuanju_kongzhi', 'luoshuansongdong'],
    "halfday-1":['pianhang_duifeng_buzheng'],
    # "halfday-2":['jiegou_sunshang', ],#['generator_zhuanju_kongzhi'],
    "day":[],
    "clock-1":['blade_angle_not_balance','wind_speed_fault','capacity_reduction','chilunxiang_disu_zhoucheng_temperature','chilunxiang_gaosu_zhoucheng_temperature','chilunxiang_sanre','engine_cabinet_temperature','engine_env_temperature','generator_houzhoucheng_temperature','generator_qianzhoucheng_temperature','generator_raozu_not_balance','generator_temperature','generator_zhuzhou_rpm_not_balance','oar_electric_capacity_temperature','oar_engine_performance','oar_engine_temperature','oar_machine_temperature', 'yepian_kailie'],
    "clock-2":['Efficiency_ana_V3']
}

# turbine number setup
turbineConfig = {
    'turbineNameList' : ["13#","14#","15#","16#","17#"]
}

#各算法测点配置
algConfig = {
    'blade_angle_not_balance':{
        'name' : '叶片角度不平衡',
        # 把所需测点定义到每个算法里
        'ai_points' : ['WGEN.GenActivePW','WROT.Blade1Position', 'WROT.Blade2Position', 'WROT.Blade3Position'],
        'ai_rename' : {},
        'di_points' : [],
        'general_points' : [],
        'private_points' : {},
        'time_duration' : '1D',
        'resample_interval' : '10m', # 原始数据采样间隔
        'error_data_time_duration' : '60m', #'500m',
        'need_all_turbines' : False,
        'store_file' : True,
        'threshold': {}
    },
    'blade_freeze':{
        'name' : '叶片结冰',
        # 把所需测点定义到每个算法里
        'ai_points' : ['WNAC.TemOut', 'WNAC.WindSpeed', 'WROT.Blade1Position', 'WGEN.GenActivePW','WTRM.RotorSpd', 'WYAW.YawOpWind5sAVG'],
        'ai_rename' : {'WYAW.YawOpWind5sAVG':'WNAC.WindVaneDirection', 'WTRM.RotorSpd':'WGEN.GenSpd'},
        'di_points' : ['WTUR.TurbineSts'],
        'general_points' : ['WTUR.TurbineAIStatus'],
        'private_points' : {"SPIC_JX_CMS_Blade":['BLD_FREEZE_FACTOR']},#江西保留
        'time_duration' : '1D',
        'resample_interval' : '1m', # 原始数据采样间隔
        'error_data_time_duration' : '30m',
        'need_all_turbines' : False,
        'store_file' : True, 
        'threshold': {}
        # modelId = "SPIC_ZD_CMS_Blade"
    },
    'capacity_reduction':{
        'name' : '风机降容预警',
        # 把所需测点定义到每个算法里
        "ai_points" : ['WNAC.WindSpeed', 'WROT.Blade1Position', 'WGEN.GenActivePW','WTRM.RotorSpd'],
        "ai_rename" : {'WYAW.YawOpWind5sAVG':'WNAC.WindVaneDirection', 'WTRM.RotorSpd':'WGEN.GenSpd'},
        "di_points" : ['WTUR.TurbineSts'],
        "general_points" : ['WTUR.TurbineAIStatus'],
        "private_points" : {},
        "time_duration" : '60D',
        "resample_interval" : '10m', # 原始数据采样间隔
        "error_data_time_duration" : '30m',
        "need_all_turbines" : False,
        'store_file' : True, 
        'threshold': {}
    },
    'chilunxiang_disu_zhoucheng_temperature':{
        "name" : '齿轮箱低速轴轴承温度异常',
        # 把所需测点定义到每个算法里
        "ai_points" : ['WROT.Blade1Position','WNAC.WindSpeed','WGEN.GenActivePW','WNAC.TemNacelle','WTRM.RotorSpd','WTRM.TemMainBearing2'],
        "ai_rename" : {'WYAW.YawOpWind5sAVG':'WNAC.WindVaneDirection', 'WTRM.RotorSpd':'WGEN.GenSpd', 'WTRM.TemMainBearing2':'WTRM.TemGeaLSND'},
        "di_points" : ['WTUR.TurbineSts'],
        "general_points" : ['WTUR.TurbineAIStatus'],
        "private_points" : {},
        "time_duration" : '1D', # 取多长时间范围的数据做预测
        "resample_interval" : '10m', # 原始数据采样间隔
        "error_data_time_duration" : '500m', # 异常数据持续多长时间报警
        "need_all_turbines" : False, # 是否需要场站全量数据做判断
        'store_file' : True, 
        'threshold': {}
    },
    'chilunxiang_gaosu_zhoucheng_temperature':{
        "name" : '齿轮箱高速轴轴承温度异常',
        # 把所需测点定义到每个算法里
        "ai_points" : ['WROT.Blade1Position','WNAC.WindSpeed','WGEN.GenActivePW','WNAC.TemNacelle','WTRM.RotorSpd','WTRM.TemMainBearing'],#WTRM.TemGeaMSDE,'WGEN.GenSpdInstant','WTRM.TemGeaOil','WTRM.TemGeaMSND'
        "ai_rename" : {'WYAW.YawOpWind5sAVG':'WNAC.WindVaneDirection', 'WTRM.RotorSpd':'WGEN.GenSpd', 'WTRM.TemMainBearing':'WTRM.TemGeaMSND'},
        "di_points" : ['WTUR.TurbineSts','WTUR.TurbineSts_Map'],
        "general_points" : ['WTUR.TurbineAIStatus'],
        "private_points" : {},
        "time_duration" : '1D', # 取多长时间范围的数据做预测
        "resample_interval" : '10m', # 原始数据采样间隔
        "error_data_time_duration" : '500m', # 异常数据持续多长时间报警
        "need_all_turbines" : False, # 是否需要场站全量数据做判断
        'store_file' : True, 
        'threshold': {}
    },
    'chilunxiang_sanre':{
        'name' : '齿轮箱散热异常',
        # 把所需测点定义到每个算法里
        'ai_points' : ['WROT.Blade1Position', 'WNAC.WindSpeed', 'WGEN.GenActivePW', 'WNAC.TemNacelle', 'WTRM.RotorSpd', 'WTRM.TemGeaOil'], #齿轮箱油池温度、舱内温度
        'ai_rename' : {'WYAW.YawOpWind5sAVG':'WNAC.WindVaneDirection', 'WTRM.RotorSpd':'WGEN.GenSpd'},
        'di_points' : ['WTUR.TurbineSts'],
        'general_points' : ['WTUR.TurbineAIStatus'],
        'private_points' : {},
        'time_duration' : '1D', # 取多长时间范围的数据做预测
        'resample_interval' : '10m', # 原始数据采样间隔
        'error_data_time_duration' : '500m', # 异常数据持续多长时间报警
        'need_all_turbines' : False, # 是否需要场站全量数据做判断
        'store_file' : True, 
        'threshold': {}
    },
    'engine_cabinet_temperature':{
        'name' : '机舱柜温度异常',
        # 把所需测点定义到每个算法里
        'ai_points' : ['WNAC.TemNacelleCab'], #, 'WNAC.TemOut', 'WNAC.TemNacelle'] # 机舱控制柜温度 环境温度（舱外温度） 机舱温度（舱内温度）
        'ai_rename' : {},
        'di_points' : [],
        'general_points' : [],
        'private_points' : {},
        'time_duration' : '1D',
        'resample_interval' : '10m', # 原始数据采样间隔
        'error_data_time_duration' : '500m',
        'need_all_turbines' : False,
        'store_file' : True, 
        'threshold': {}
    },
    'engine_env_temperature':{
        'name' : '机舱环境温度异常',
        # 把所需测点定义到每个算法里
        'ai_points' : ['WNAC.TemNacelle'], # 机舱温度（舱内温度） 'WNAC.TemOut'
        'ai_rename' : {},
        'di_points' : [],
        'general_points' : [],
        'private_points' : {},
        'time_duration' : '1D',
        'resample_interval' : '10m', # 原始数据采样间隔
        'error_data_time_duration' : '500m',
        'need_all_turbines' : False,
        'store_file' : True, 
        'threshold': {}
    },
    'generator_houzhoucheng_temperature':{
        'name' : '发电机非驱动端轴承温度异常',
        # 把所需测点定义到每个算法里
        'ai_points' : [
            'WROT.Blade1Position',
            'WNAC.WindSpeed',
            'WGEN.GenActivePW',
            'WNAC.TemNacelle',
            'WTRM.RotorSpd',
            'WGEN.TemGenNonDE'
            ], # 发电机非驱动端轴承温度 机舱温度（舱内温度）    'WTUR.SETURAI57',
        'ai_rename' : {'WYAW.YawOpWind5sAVG':'WNAC.WindVaneDirection', 'WTRM.RotorSpd':'WGEN.GenSpd'},
        'di_points' : ['WTUR.TurbineSts'],
        'general_points' : ['WTUR.TurbineAIStatus'],
        'private_points' : {},
        'time_duration' : '1D',
        'resample_interval' : '10m', # 原始数据采样间隔
        'error_data_time_duration' : '500m',
        'need_all_turbines' : False,
        'store_file' : True, 
        'threshold': {}
    },
    'generator_qianzhoucheng_temperature':{
        'name' : '发电机驱动端轴承温度异常',
        # 把所需测点定义到每个算法里
        'ai_points' : [
            'WROT.Blade1Position',
            'WNAC.WindSpeed',
            'WGEN.GenActivePW',
            'WNAC.TemNacelle',
            'WTRM.RotorSpd',
            'WGEN.TemGenDriEnd'
            ],
        'ai_rename' : {'WYAW.YawOpWind5sAVG':'WNAC.WindVaneDirection', 'WTRM.RotorSpd':'WGEN.GenSpd'},
        'di_points' : ['WTUR.TurbineSts'],
        'general_points' : ['WTUR.TurbineAIStatus'],
        'private_points' : {},
        'time_duration' : '1D',
        'resample_interval' : '10m', # 原始数据采样间隔
        'error_data_time_duration' : '500m',
        'need_all_turbines' : False,
        'store_file' : True, 
        'threshold': {}
    },
    'generator_raozu_not_balance':{
        'name' : '发电机定子线圈温度三相不平衡',
        # 把所需测点定义到每个算法里
        'ai_points' : ['WGEN.GenSenTmp1','WGEN.GenSenTmp2','WGEN.GenSenTmp3'], # 发电机定子U相线圈温度 发电机定子V相线圈温度 发电机定子W相线圈温度 环境温度（舱外温度）
        'ai_rename' : {'WYAW.YawOpWind5sAVG':'WNAC.WindVaneDirection', 'WTRM.RotorSpd':'WGEN.GenSpd', 'WGEN.GenSenTmp1':'WGEN.TemGenStaU', 'WGEN.GenSenTmp2':'WGEN.TemGenStaV', 'WGEN.GenSenTmp3':'WGEN.TemGenStaW'},
        'di_points' : [],
        'general_points' : [],
        'private_points' : {},
        'time_duration' : '1D',
        'resample_interval' : '10m', # 原始数据采样间隔
        'error_data_time_duration' : '500m',
        'need_all_turbines' : False,
        'store_file' : True, 
        'threshold': {}
    },
    'generator_temperature':{
        'name' : '发电机定子绕组温度异常',
        # 把所需测点定义到每个算法里
        'ai_points' : ['WROT.Blade1Position','WNAC.WindSpeed','WGEN.GenActivePW', 'WGEN.GenSenTmp1', 'WGEN.GenSenTmp2', 'WGEN.GenSenTmp3','WNAC.TemOut','WNAC.TemNacelle','WTRM.RotorSpd'], # 发电机定子U相线圈温度 发电机定子V相线圈温度 发电机定子W相线圈温度 环境温度（舱外温度） 'WGEN.LHDLGENAI31','WGEN.LHDLGENAI103'
        'ai_rename' : {'WYAW.YawOpWind5sAVG':'WNAC.WindVaneDirection', 'WTRM.RotorSpd':'WGEN.GenSpd', 'WGEN.GenSenTmp1':'WGEN.TemGenStaU', 'WGEN.GenSenTmp2':'WGEN.TemGenStaV', 'WGEN.GenSenTmp3':'WGEN.TemGenStaW'},
        'di_points' : ['WTUR.TurbineSts'],
        'general_points' : ['WTUR.TurbineAIStatus'],
        'private_points' : {},
        'time_duration' : '1D',
        'resample_interval' : '10m', # 原始数据采样间隔
        'error_data_time_duration' : '500m',
        'need_all_turbines' : False,
        'store_file' : True, 
        'threshold': {}
    },
    'generator_zhuanju_kongzhi':{
        'name' : '转矩控制异常',
        # 把所需测点定义到每个算法里
        'ai_points' : ['WGEN.GenActivePW','WTRM.RotorSpd', 'WNAC.WindSpeed', 'WROT.Blade1Position', 'WNAC.TemOut'],
        'ai_rename' : {'WYAW.YawOpWind5sAVG':'WNAC.WindVaneDirection', 'WTRM.RotorSpd':'WGEN.GenSpd'},
        'di_points' : ['WTUR.TurbineSts'],
        'general_points' : ['WTUR.TurbineAIStatus'],
        'private_points' : {},
        'time_duration' : '60D',
        'resample_interval' : '10m', # 原始数据采样间隔
        'error_percentage' : 0.03,
        'need_all_turbines' : False,
        'store_file' : True, 
        'threshold': {}
    },
    'generator_zhuzhou_rpm_not_balance':{
        'name' : '主轴转速和发电机转速不平衡',
        # 把所需测点定义到每个算法里
        'ai_points' : ['WGEN.GenSpd','WTRM.RotorSpd','WNAC.WindSpeed', 'WGEN.GenActivePW', 'WROT.Blade1Position'],
        'ai_rename' : {'WYAW.YawOpWind5sAVG':'WNAC.WindVaneDirection'},#, 'WTRM.RotorSpd':'WGEN.GenSpd'
        'di_points' : ['WTUR.TurbineSts'],
        'general_points' : ['WTUR.TurbineAIStatus'],
        'private_points' : {},
        'time_duration' : '7D',
        'resample_interval' : '10m', # 原始数据采样间隔
        'error_data_time_duration' : '3500m',
        'need_all_turbines' : False,
        'store_file' : True, 
        'threshold': {}
    },
    'chuandonglian':{
        'name' : '传动链齿轮箱、主轴承、发电机转速',
        # 把所需测点定义到每个算法里
        'ai_points' : ['WGEN.GenActivePW'],
        'ai_rename' : {},
        'di_points' : [],
        'general_points' : [],
        'private_points' : {"SPIC_JX_CMS_Transfer":['GBXHSSA1_RMS','GENDER1_RMS', 'MBA1_RMS']},#保留江西的, GBXHSSA1_RMS:齿轮箱高速轴轴向1（振动有效值）,GENDER1_RMS:发电机驱动端径向1（振动有效值）,MBA1_RMS:主轴轴承轴向1（振动有效值）	
        # modelId : "SPIC_ZD_CMS_Tower"
        'time_duration' : '1D', #数据持续时间
        'resample_interval' : '10m',#'10T' # 原始数据采样间隔
        'error_data_time_duration' : '288m', #和resample_interval同单位
        'need_all_turbines' : False,
        'store_file' : True, 
        'threshold': {
            "levelline": "60m",
            "executeTime":{
                "minute":{
                    "duration": "1D",
                    "kelidu": "10m",
                    "levelline": "60m",
                    "continue": "288m"
                },
                "hour":{
                    "duration": "5D",
                    "kelidu": "1h",
                    "levelline": "5D",
                    "continue": "30h"
                },
                "halfday":{
                    "duration": "15D",
                    "kelidu": "4h",
                    "levelline": "10D",
                    "continue": "80h"
                },
                "day":{
                    "duration": "90D",
                    "kelidu": "1D",
                    "levelline": "30D",
                    "continue": "20D"
                }
            },
            "yujing":{
                "threshold": {
                    "GBXHSSA1_RMS": 7.5,
                    "GENDER1_RMS": 10,
                    "MBA1_RMS": 0.3
                }
            },
            "gaojing":{
                "threshold": {
                    "GBXHSSA1_RMS":{
                        "10": 7.5,
                        "13": 12,
                        "17": 16.5
                    },
                    "GENDER1_RMS":{
                        "10": 10,
                        "13": 16,
                        "17": 22
                    },
                    "MBA1_RMS":{
                        "10": 0.3,
                        "13": 0.5,
                        "17": 1
                    }
                }           
            }
        }
    },
    'hongwaicewen':{
        'name' : '红外测温',
        # 把所需测点定义到每个算法里
        'ai_points' : [],
        'ai_rename' : {},
        'di_points' : [],
        'general_points' : [],
        'private_points' : {"SPIC_JX_CMS_Transformer":['LOW_A_TMP','LOW_B_TMP','LOW_C_TMP']},#保留江西的
        # modelId : "SPIC_ZD_CMS_Transformer"
        'time_duration' : '1h',
        'resample_interval' : '1m',#'10T' # 原始数据采样间隔
        'error_data_time_duration' : '12m',
        'horizonTime' : '30D',
        'need_all_turbines' : False,
        'input_chunk_length' : 12,
        'out_chunck_length' : 6,
        'futureCovariates' : None,
        'numEpoch' : 70,
        'trainCutOff' : None,
        'timeSampleNum' : 5,
        'store_file' : True, 
        'threshold': {
            "levelline": "60m",
            "executeTime":{
                "minute":{
                    "duration": "1h",
                    "kelidu": "1m",
                    "levelline": "60m",
                    "continue": "12m"
                },
                "hour":{
                    "duration": "5D",
                    "kelidu": "1h",
                    "levelline": "5D",
                    "continue": "30h"
                },
                "halfday":{
                    "duration": "15D",
                    "kelidu": "4h",
                    "levelline": "10D",
                    "continue": "80h"
                },
                "day":{
                    "duration": "90D",
                    "kelidu": "1D",
                    "levelline": "30D",
                    "continue": "20D"
                }
            },
            "yujing":{
                "threshold": 105
            },
            "gaojing":{
                "threshold": {
                    "10": 105,
                    "11": 115,
                    "12": 125,
                    "13": 135,
                    "14": 145,
                    "15": 155,
                    "16": 165,
                    "17": 175
                }           
            }
        }
    },
    'hongwai_sanxiang':{
        'name' : '箱变接线端子三相温度',
        # 把所需测点定义到每个算法里
        'ai_points' : [], #,'WROT.Blade1Position','WROT.Blade2Position','WROT.Blade3Position','WROT.CurBlade1Motor','WROT.CurBlade2Motor','WROT.CurBlade3Motor'] # 1号桨电机温度 2 3
        'ai_rename' : {},
        'di_points' : [],
        'general_points' : [],
        'private_points' : {"SPIC_JX_CMS_Transformer":['LOW_A_TMP','LOW_B_TMP','LOW_C_TMP']},
        'time_duration' : '1D',
        'resample_interval' : '10m',
        'error_data_time_duration' : '500m',
        'need_all_turbines' : False,
        'store_file' : True, 
        'threshold': {}
    },
    'jiegou_sunshang':{
        'name' : '塔筒结构损伤',
        # 把所需测点定义到每个算法里
        'ai_points' : ['WGEN.GenActivePW','WTRM.RotorSpd', 'WNAC.WindSpeed', 'WROT.Blade1Position', 'WYAW.YawOpWind5sAVG'], #, 'WNAC.TemOut', 'WNAC.TemNacelle'] # 机舱控制柜温度 环境温度（舱外温度） 机舱温度（舱内温度）
        'ai_rename' : {'WYAW.YawOpWind5sAVG':'WNAC.WindVaneDirection', 'WTRM.RotorSpd':'WGEN.GenSpd'},
        'di_points' : ['WTUR.TurbineSts'],
        'general_points' : ['WTUR.TurbineAIStatus'],
        'private_points' : {"SPIC_JX_CMS_Tower":['Vibration_Strength']},#保留江西的 , 'TOTTSK'
        'time_duration' : '1D',
        'resample_interval' : '10m', # 原始数据采样间隔
        'error_data_time_duration' : '288m',
        'need_all_turbines' : False,
        'store_file' : True, 
        'threshold': {
            "levelline": "10D",
            "executeTime":{
                "minute":{
                    "duration": "1D",
                    "kelidu": "10m",
                    "levelline": "60m",
                    "continue": "288m"
                },
                "hour":{
                    "duration": "5D",
                    "kelidu": "1h",
                    "levelline": "5D",
                    "continue": "30h"
                },
                "halfday":{
                    "duration": "15D",
                    "kelidu": "4h",
                    "levelline": "10D",
                    "continue": "80h"
                    # "duration": "1D",
                    # "kelidu": "10m",
                    # "levelline": "10D",
                    # "continue": "288m"
                },
                "day":{
                    "duration": "90D",
                    "kelidu": "1D",
                    "levelline": "30D",
                    "continue": "20D"
                }
            },
            "yujing":{
                "threshold": 0.5
            },
            "gaojing":{
                "threshold": {
                    "10": 0.5,
                    "11": 0.7,
                    "12": 0.9,
                    "13": 1.1,
                    "14": 1.3,
                    "15": 1.5,
                    "16": 1.7,
                    "17": 1.9
                }           
            }
        }
    },
    'luoshuansongdong':{
        'name' : '风机螺栓松动',
        # 把所需测点定义到每个算法里
        'ai_points' : [],
        'ai_rename' : {},
        'di_points' : [],
        'general_points' : [],
        'private_points' : {"SPIC_JX_CMS_Bolt":['BLADE1_BLOT_ANGLE_1','BLADE1_BLOT_ANGLE_2','BLADE1_BLOT_ANGLE_3','BLADE1_BLOT_ANGLE_4','BLADE1_BLOT_ANGLE_5','BLADE1_BLOT_ANGLE_6','BLADE1_BLOT_ANGLE_7','BLADE1_BLOT_ANGLE_8',
        'BLADE2_BLOT_ANGLE_1','BLADE2_BLOT_ANGLE_2','BLADE2_BLOT_ANGLE_3','BLADE2_BLOT_ANGLE_4','BLADE2_BLOT_ANGLE_5','BLADE2_BLOT_ANGLE_6','BLADE2_BLOT_ANGLE_7','BLADE2_BLOT_ANGLE_8',
        'BLADE3_BLOT_ANGLE_1','BLADE3_BLOT_ANGLE_2','BLADE3_BLOT_ANGLE_3','BLADE3_BLOT_ANGLE_4','BLADE3_BLOT_ANGLE_5','BLADE3_BLOT_ANGLE_6','BLADE3_BLOT_ANGLE_7','BLADE3_BLOT_ANGLE_8',
        'TOWERL1_BLOT_ANGLE_1','TOWERL1_BLOT_ANGLE_2','TOWERL1_BLOT_ANGLE_3','TOWERL1_BLOT_ANGLE_4','TOWERL1_BLOT_ANGLE_5','TOWERL1_BLOT_ANGLE_6','TOWERL1_BLOT_ANGLE_7','TOWERL1_BLOT_ANGLE_8',
        'TOWERL2_BLOT_ANGLE_1','TOWERL2_BLOT_ANGLE_2','TOWERL2_BLOT_ANGLE_3','TOWERL2_BLOT_ANGLE_4','TOWERL2_BLOT_ANGLE_5','TOWERL2_BLOT_ANGLE_6','TOWERL2_BLOT_ANGLE_7','TOWERL2_BLOT_ANGLE_8',
        'TOWERL3_BLOT_ANGLE_1','TOWERL3_BLOT_ANGLE_2','TOWERL3_BLOT_ANGLE_3','TOWERL3_BLOT_ANGLE_4','TOWERL3_BLOT_ANGLE_5','TOWERL3_BLOT_ANGLE_6','TOWERL3_BLOT_ANGLE_7','TOWERL3_BLOT_ANGLE_8',
        'TOWERL4_BLOT_ANGLE_1','TOWERL4_BLOT_ANGLE_2','TOWERL4_BLOT_ANGLE_3','TOWERL4_BLOT_ANGLE_4','TOWERL4_BLOT_ANGLE_5','TOWERL4_BLOT_ANGLE_6','TOWERL4_BLOT_ANGLE_7','TOWERL4_BLOT_ANGLE_8'
        ]},#保留江西的, ,'BLADE1_BLOT_ANGLE_2','BLADE1_BLOT_ANGLE_3','BLADE1_BLOT_ANGLE_4','BLADE1_BLOT_ANGLE_5','BLADE1_BLOT_ANGLE_6','BLADE1_BLOT_ANGLE_7','BLADE1_BLOT_ANGLE_8'
        # modelId : "SPIC_ZD_CMS_Bolt"
        'nameMaps': {
            'BLADE1_BLOT_ANGLE_1': '叶片1法兰1号螺栓反旋角度','BLADE1_BLOT_ANGLE_2': '叶片1法兰2号螺栓反旋角度','BLADE1_BLOT_ANGLE_3': '叶片1法兰3号螺栓反旋角度','BLADE1_BLOT_ANGLE_4': '叶片1法兰4号螺栓反旋角度','BLADE1_BLOT_ANGLE_5': '叶片1法兰5号螺栓反旋角度','BLADE1_BLOT_ANGLE_6': '叶片1法兰6号螺栓反旋角度','BLADE1_BLOT_ANGLE_7': '叶片1法兰7号螺栓反旋角度','BLADE1_BLOT_ANGLE_8': '叶片1法兰8号螺栓反旋角度',
            'BLADE2_BLOT_ANGLE_1': '叶片1法兰1号螺栓反旋角度','BLADE2_BLOT_ANGLE_2': '叶片1法兰2号螺栓反旋角度','BLADE2_BLOT_ANGLE_3': '叶片1法兰3号螺栓反旋角度','BLADE2_BLOT_ANGLE_4': '叶片1法兰4号螺栓反旋角度','BLADE2_BLOT_ANGLE_5': '叶片1法兰5号螺栓反旋角度','BLADE2_BLOT_ANGLE_6': '叶片1法兰6号螺栓反旋角度','BLADE2_BLOT_ANGLE_7': '叶片1法兰7号螺栓反旋角度','BLADE2_BLOT_ANGLE_8': '叶片1法兰8号螺栓反旋角度',
            'BLADE3_BLOT_ANGLE_1': '叶片1法兰1号螺栓反旋角度','BLADE3_BLOT_ANGLE_2': '叶片1法兰2号螺栓反旋角度','BLADE3_BLOT_ANGLE_3': '叶片1法兰3号螺栓反旋角度','BLADE3_BLOT_ANGLE_4': '叶片1法兰4号螺栓反旋角度','BLADE3_BLOT_ANGLE_5': '叶片1法兰5号螺栓反旋角度','BLADE3_BLOT_ANGLE_6': '叶片1法兰6号螺栓反旋角度','BLADE3_BLOT_ANGLE_7': '叶片1法兰7号螺栓反旋角度','BLADE3_BLOT_ANGLE_8': '叶片1法兰8号螺栓反旋角度',
            'TOWERL1_BLOT_ANGLE_1': '塔筒L1层法兰1号螺栓反旋角度','TOWERL1_BLOT_ANGLE_2': '塔筒L1层法兰2号螺栓反旋角度','TOWERL1_BLOT_ANGLE_3': '塔筒L1层法兰3号螺栓反旋角度','TOWERL1_BLOT_ANGLE_4': '塔筒L1层法兰4号螺栓反旋角度','TOWERL1_BLOT_ANGLE_5': '塔筒L1层法兰5号螺栓反旋角度','TOWERL1_BLOT_ANGLE_6': '塔筒L1层法兰6号螺栓反旋角度','TOWERL1_BLOT_ANGLE_7': '塔筒L1层法兰7号螺栓反旋角度','TOWERL1_BLOT_ANGLE_8': '塔筒L1层法兰8号螺栓反旋角度',
            'TOWERL2_BLOT_ANGLE_1': '塔筒L1层法兰1号螺栓反旋角度','TOWERL2_BLOT_ANGLE_2': '塔筒L1层法兰2号螺栓反旋角度','TOWERL2_BLOT_ANGLE_3': '塔筒L1层法兰3号螺栓反旋角度','TOWERL2_BLOT_ANGLE_4': '塔筒L1层法兰4号螺栓反旋角度','TOWERL2_BLOT_ANGLE_5': '塔筒L1层法兰5号螺栓反旋角度','TOWERL2_BLOT_ANGLE_6': '塔筒L1层法兰6号螺栓反旋角度','TOWERL2_BLOT_ANGLE_7': '塔筒L1层法兰7号螺栓反旋角度','TOWERL2_BLOT_ANGLE_8': '塔筒L1层法兰8号螺栓反旋角度',
            'TOWERL3_BLOT_ANGLE_1': '塔筒L1层法兰1号螺栓反旋角度','TOWERL3_BLOT_ANGLE_2': '塔筒L1层法兰2号螺栓反旋角度','TOWERL3_BLOT_ANGLE_3': '塔筒L1层法兰3号螺栓反旋角度','TOWERL3_BLOT_ANGLE_4': '塔筒L1层法兰4号螺栓反旋角度','TOWERL3_BLOT_ANGLE_5': '塔筒L1层法兰5号螺栓反旋角度','TOWERL3_BLOT_ANGLE_6': '塔筒L1层法兰6号螺栓反旋角度','TOWERL3_BLOT_ANGLE_7': '塔筒L1层法兰7号螺栓反旋角度','TOWERL3_BLOT_ANGLE_8': '塔筒L1层法兰8号螺栓反旋角度',
            'TOWERL4_BLOT_ANGLE_1': '塔筒L1层法兰1号螺栓反旋角度','TOWERL4_BLOT_ANGLE_2': '塔筒L1层法兰2号螺栓反旋角度','TOWERL4_BLOT_ANGLE_3': '塔筒L1层法兰3号螺栓反旋角度','TOWERL4_BLOT_ANGLE_4': '塔筒L1层法兰4号螺栓反旋角度','TOWERL4_BLOT_ANGLE_5': '塔筒L1层法兰5号螺栓反旋角度','TOWERL4_BLOT_ANGLE_6': '塔筒L1层法兰6号螺栓反旋角度','TOWERL4_BLOT_ANGLE_7': '塔筒L1层法兰7号螺栓反旋角度','TOWERL4_BLOT_ANGLE_8': '塔筒L1层法兰8号螺栓反旋角度'
        },
        'time_duration' : '6h',
        'resample_interval' : '1h',#'10T' # 原始数据采样间隔
        'error_data_time_duration' : '4h',
        # 'changeMeasurePointQueue': [],
        # 'changeDataThreshold': 5,
        # 'changeDateRange':'7D',
        # 'changeDateFreq':'1h',
        # 'changeErrorContinue':'72h',
        'horizonTime' : '30D',
        'need_all_turbines' : False,
        'input_chunk_length' : 12,
        'out_chunck_length' : 6,
        'futureCovariates' : None,
        'numEpoch' : 70,
        'trainCutOff' : None,
        'timeSampleNum' : 5,
        'store_file' : True, 
        'threshold': {
            "levelline": "60m",
            "executeTime":{
                "minute":{
                    "duration": "6h",
                    "kelidu": "1h",
                    "levelline": "60m",
                    "continue": "4h"
                },
                "hour":{
                    "duration": "5D",
                    "kelidu": "1h",
                    "levelline": "5D",
                    "continue": "30h"
                },
                "halfday":{
                    "duration": "15D",
                    "kelidu": "4h",
                    "levelline": "10D",
                    "continue": "80h"
                },
                "day":{
                    "duration": "90D",
                    "kelidu": "1D",
                    "levelline": "30D",
                    "continue": "20D"
                }
            },
            "yujing":{
                "threshold": {
                    'BLADE1_BLOT_ANGLE_1': 5,
                    'BLADE1_BLOT_ANGLE_2': 5,
                    'BLADE1_BLOT_ANGLE_3': 5,
                    'BLADE1_BLOT_ANGLE_4': 5,
                    'BLADE1_BLOT_ANGLE_5': 5,
                    'BLADE1_BLOT_ANGLE_6': 5,
                    'BLADE1_BLOT_ANGLE_7': 5,
                    'BLADE1_BLOT_ANGLE_8': 5,

                    'BLADE2_BLOT_ANGLE_1': 5,
                    'BLADE2_BLOT_ANGLE_2': 5,
                    'BLADE2_BLOT_ANGLE_3': 5,
                    'BLADE2_BLOT_ANGLE_4': 5,
                    'BLADE2_BLOT_ANGLE_5': 5,
                    'BLADE2_BLOT_ANGLE_6': 5,
                    'BLADE2_BLOT_ANGLE_7': 5,
                    'BLADE2_BLOT_ANGLE_8': 5,

                    'BLADE3_BLOT_ANGLE_1': 5,
                    'BLADE3_BLOT_ANGLE_2': 5,
                    'BLADE3_BLOT_ANGLE_3': 5,
                    'BLADE3_BLOT_ANGLE_4': 5,
                    'BLADE3_BLOT_ANGLE_5': 5,
                    'BLADE3_BLOT_ANGLE_6': 5,
                    'BLADE3_BLOT_ANGLE_7': 5,
                    'BLADE3_BLOT_ANGLE_8': 5,

                    'TOWERL1_BLOT_ANGLE_1': 5,
                    'TOWERL1_BLOT_ANGLE_2': 5,
                    'TOWERL1_BLOT_ANGLE_3': 5,
                    'TOWERL1_BLOT_ANGLE_4': 5,
                    'TOWERL1_BLOT_ANGLE_5': 5,
                    'TOWERL1_BLOT_ANGLE_6': 5,
                    'TOWERL1_BLOT_ANGLE_7': 5,
                    'TOWERL1_BLOT_ANGLE_8': 5,

                    'TOWERL2_BLOT_ANGLE_1': 5,
                    'TOWERL2_BLOT_ANGLE_2': 5,
                    'TOWERL2_BLOT_ANGLE_3': 5,
                    'TOWERL2_BLOT_ANGLE_4': 5,
                    'TOWERL2_BLOT_ANGLE_5': 5,
                    'TOWERL2_BLOT_ANGLE_6': 5,
                    'TOWERL2_BLOT_ANGLE_7': 5,
                    'TOWERL2_BLOT_ANGLE_8': 5,

                    'TOWERL3_BLOT_ANGLE_1': 5,
                    'TOWERL3_BLOT_ANGLE_2': 5,
                    'TOWERL3_BLOT_ANGLE_3': 5,
                    'TOWERL3_BLOT_ANGLE_4': 5,
                    'TOWERL3_BLOT_ANGLE_5': 5,
                    'TOWERL3_BLOT_ANGLE_6': 5,
                    'TOWERL3_BLOT_ANGLE_7': 5,
                    'TOWERL3_BLOT_ANGLE_8': 5,

                    'TOWERL4_BLOT_ANGLE_1': 5,
                    'TOWERL4_BLOT_ANGLE_2': 5,
                    'TOWERL4_BLOT_ANGLE_3': 5,
                    'TOWERL4_BLOT_ANGLE_4': 5,
                    'TOWERL4_BLOT_ANGLE_5': 5,
                    'TOWERL4_BLOT_ANGLE_6': 5,
                    'TOWERL4_BLOT_ANGLE_7': 5,
                    'TOWERL4_BLOT_ANGLE_8': 5
                }

            },
            "gaojing":{
                "threshold": {
                    'BLADE1_BLOT_ANGLE_1': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE1_BLOT_ANGLE_2': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE1_BLOT_ANGLE_3': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE1_BLOT_ANGLE_4': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE1_BLOT_ANGLE_5': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE1_BLOT_ANGLE_6': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE1_BLOT_ANGLE_7': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE1_BLOT_ANGLE_8': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },

                    'BLADE2_BLOT_ANGLE_1': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE2_BLOT_ANGLE_2': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE2_BLOT_ANGLE_3': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE2_BLOT_ANGLE_4': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE2_BLOT_ANGLE_5': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE2_BLOT_ANGLE_6': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE2_BLOT_ANGLE_7': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE2_BLOT_ANGLE_8': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },

                    'BLADE3_BLOT_ANGLE_1': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE3_BLOT_ANGLE_2': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE3_BLOT_ANGLE_3': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE3_BLOT_ANGLE_4': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE3_BLOT_ANGLE_5': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE3_BLOT_ANGLE_6': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE3_BLOT_ANGLE_7': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },
                    'BLADE3_BLOT_ANGLE_8': {
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    },

                    'TOWERL1_BLOT_ANGLE_1':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL1_BLOT_ANGLE_2':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL1_BLOT_ANGLE_3':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL1_BLOT_ANGLE_4':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL1_BLOT_ANGLE_5':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL1_BLOT_ANGLE_6':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL1_BLOT_ANGLE_7':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL1_BLOT_ANGLE_8':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,

                    'TOWERL2_BLOT_ANGLE_1':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL2_BLOT_ANGLE_2':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL2_BLOT_ANGLE_3':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL2_BLOT_ANGLE_4':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL2_BLOT_ANGLE_5':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL2_BLOT_ANGLE_6':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL2_BLOT_ANGLE_7':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL2_BLOT_ANGLE_8':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,

                    'TOWERL3_BLOT_ANGLE_1':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL3_BLOT_ANGLE_2':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL3_BLOT_ANGLE_3':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL3_BLOT_ANGLE_4':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL3_BLOT_ANGLE_5':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL3_BLOT_ANGLE_6':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL3_BLOT_ANGLE_7':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL3_BLOT_ANGLE_8':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,

                    'TOWERL4_BLOT_ANGLE_1':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL4_BLOT_ANGLE_2':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL4_BLOT_ANGLE_3':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL4_BLOT_ANGLE_4':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL4_BLOT_ANGLE_5':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL4_BLOT_ANGLE_6':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL4_BLOT_ANGLE_7':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } ,
                    'TOWERL4_BLOT_ANGLE_8':{
                        "10": 5.0,
                        "11": 5.1,
                        "12": 5.2,
                        "13": 5.3,
                        "14": 5.4,
                        "15": 5.5,
                        "16": 5.6,
                        "17": 5.7
                    } 

                }           
            }
        }
    },
    'oar_electric_capacity_temperature':{
        'name' : '变桨电容温度异常',
        # 把所需测点定义到每个算法里
        'ai_points' : ['WROT.PtCapTemBl1','WROT.PtCapTemBl2', 'WROT.PtCapTemBl3', 'WROT.VolB1Cap', 'WROT.VolB2Cap','WROT.VolB3Cap',],# ,	'WROT.Blade1Position','WROT.Blade2Position','WROT.Blade3Position','WNAC.TemOut'] # 叶片1超级电容柜温度 叶片2超级电容柜温度 叶片3超级电容柜温度
        'ai_rename' : {},
        'di_points' : [],
        'general_points' : [],
        'private_points' : {},
        'time_duration' : '1D',
        'resample_interval' : '10m',
        'error_data_time_duration' : '500m',
        'need_all_turbines' : False,
        'store_file' : True, 
        'threshold': {}
    },
    'oar_engine_performance':{
        'name' : '变桨电机性能异常',
        # 把所需测点定义到每个算法里
        'ai_points' : ['WROT.TemB1Mot', 'WROT.TemB2Mot', 'WROT.TemB3Mot',
                    'WROT.CurBlade1Motor', 'WROT.CurBlade2Motor', 'WROT.CurBlade3Motor'],  # 1号桨电机温度 2 3
        'ai_rename' : {},
        'di_points' : [],
        'general_points' : [],
        'private_points' : {},
        'time_duration' : '1D',
        'resample_interval' : '10m',
        'error_data_time_duration' : '500m',
        'need_all_turbines' : False,
        'store_file' : True, 
        'threshold': {}
    },
    'oar_engine_temperature':{
        'name' : '变桨电机温度异常',
        # 把所需测点定义到每个算法里
        'ai_points' : ['WROT.TemB1Mot','WROT.TemB2Mot','WROT.TemB3Mot'], #,'WROT.Blade1Position','WROT.Blade2Position','WROT.Blade3Position','WROT.CurBlade1Motor','WROT.CurBlade2Motor','WROT.CurBlade3Motor'] # 1号桨电机温度 2 3
        'ai_rename' : {},
        'di_points' : [],
        'general_points' : [],
        'private_points' : {},
        'time_duration' : '1D',
        'resample_interval' : '10m',
        'error_data_time_duration' : '500m',
        'need_all_turbines' : False,
        'store_file' : True, 
        'threshold': {}
    },
    'oar_machine_temperature':{
        'name' : '变桨逆变器温度异常',
        # 把所需测点定义到每个算法里
        'ai_points' : ['WROT.TemBlade1Inver', 'WROT.TemBlade2Inver', 'WROT.TemBlade3Inver'], # 变桨驱动器1温度 变桨驱动器2温度 变桨驱动器3温度
        'ai_rename' : {},
        'di_points' : [],
        'general_points' : [],
        'private_points' : {},
        'time_duration' : '1D',
        'resample_interval' : '10m',
        'error_data_time_duration' : '500m',
        'need_all_turbines' : False,
        'store_file' : True, 
        'threshold': {}
    },
    'pianhang_duifeng_buzheng':{
        'name' : '偏航对风不正',
        # 把所需测点定义到每个算法里
        'ai_points' : ['WTRM.RotorSpd', 'WYAW.YawOpWind5sAVG', 'WNAC.WindDirection','WNAC.WindSpeed','WGEN.GenActivePW', 'WROT.Blade1Position'], #机舱与风向夹角 风向
        'ai_rename' : {'WYAW.YawOpWind5sAVG':'WNAC.WindVaneDirection', 'WTRM.RotorSpd':'WGEN.GenSpd'},
        'di_points' : ['WTUR.TurbineSts_Map','WTUR.TurbineSts'],
        'general_points' : ['WTUR.TurbineAIStatus'],
        'private_points' : {},
        'time_duration' : '90D',
        'resample_interval' : '1m', # 原始数据采样间隔
        'error_percentage' : 0.03,
        'need_all_turbines' : False,
        'store_file' : True, 
        'threshold': {}
    },
    'Efficiency_ana_V3':{
        'name' : '能效分析指标',
        # 把所需测点定义到每个算法里
        #'ai_points' : ["WNAC.WindSpeed,WGEN.GenActivePW,WWPP.APProduction,WWPP.APConsumed,WROT.Blade1Position,WROT.Blade2Position,WROT.Blade3Position,WROT.Blade1Speed,WROT.Blade2Speed,WROT.Blade3Speed,WYAW.NacellePosition,WYAW.YawSpeed,WVIB.VibrationValid,WVIB.VibrationV,WVIB.VibrationVFil,WVIB.VibrationL,WVIB.VibrationLFil,WGEN.GenSpdInstant,WNAC.WindVaneDirection,WNAC.WindDirection1,WNAC.WindDirection,WROT.TemB1Mot,WROT.TemB2Mot,WROT.TemB3Mot,WROT.CurBlade1Motor,WROT.CurBlade2Motor,WROT.CurBlade3Motor,WROT.PtCptTmpBl1,WROT.PtCptTmpBl2,WROT.PtCptTmpBl3,WGEN.TemGenDriEnd,WGEN.TemGenNonDE", "WNAC.TemNacelle,WNAC.TemOut,WGEN.GenSenTmp1,WGEN.GenSenTmp2,WGEN.GenSenTmp3,WGEN.GenSenTmp4,WGEN.GenSenTmp5,WGEN.GenSenTmp6,WYAW.YawMotor1RunTime,WYAW.YawMotor2RunTime,WYAW.YawMotor3RunTime,WROT.VolB1Cap,WROT.VolB2Cap,WROT.VolB3Cap,WGEN.GenSenMaxTmp,WGEN.GenSpd,WTUR.MainFaultCode,WTRM.HubAngle,WTRM.RotorSpd,WNAC.TemNacelleCab,WCNV.CVTTemWaterCoolInlet,WCNV.CVTTemWaterCoolOutlet,WTRM.TemMainBearing,WYAW.YawCountSum,WTUR.SITURAI17,WNAC.XDNACAI01,WNAC.WindDirectionInstant,WTRM.RotorPDM,WNAC.WindVaneDirectionInstant", "WTRM.TemGeaMSND,WTRM.TemGeaMSDE,WGEN.TemGenStaU,WGEN.TemGenStaV,WGEN.TemGenStaW,WTRM.TemGeaOil,WTRM.TemGeaLSDE,WTRM.TemGeaLSND,WTRM.TrmTmpShfBrg,WYAW.YawOpWind5sAVG,WNAC.WindDirection_AVG_10m"], 
        'ai_points' : ["WNAC.WindSpeed","WGEN.GenActivePW","WROT.Blade1Position","WROT.Blade2Position","WROT.Blade3Position","WGEN.GenSpdInstant","WGEN.GenSpd","WTRM.RotorSpd","WTRM.RotorPDM"], 
        'ai_rename' : {},
        'di_points' : ['WTUR.TurbineSts_Map','WTUR.TurbineSts', "WTUR.TurbineUnionSts"],
        'general_points' : ['WTUR.TurbineAIStatus',"WTUR.AIStatusCode","WTUR.AIStatusCode_Map"],
        'private_points' : {},
        'time_duration' : '90D',
        'resample_interval' : '1m', # 原始数据采样间隔
        'error_percentage' : 0.03,
        'need_all_turbines' : True,
        'store_file' : False, 
        'threshold': {}
    },
    'tatong_qingjiao':{
        'name' : '风机基础不均匀沉降',
        # 把所需测点定义到每个算法里
        'ai_points' : [],
        'ai_rename' : {},
        'di_points' : [],
        'general_points' : [],
        'private_points' : {"SPIC_JX_CMS_Tower":['TOTT','TOAT']},#保留江西的
        # modelId : "SPIC_ZD_CMS_Tower"
        'nameMaps': {'TOTT':'塔顶倾斜角度','TOAT':'塔底倾斜角度'},
        'time_duration' : '1h', #数据持续时间
        'resample_interval' : '1m',#'10T' # 原始数据采样间隔
        'error_data_time_duration' : '12m', #和resample_interval同单位
        'horizonTime' : '30D',
        'need_all_turbines' : False,
        'input_chunk_length' : 12, #输入数据点数量
        'out_chunck_length' : 6, #输出预测点数量
        'futureCovariates' : None,
        'numEpoch' : 70,
        'trainCutOff' : None,
        'timeSampleNum' : 5,
        'store_file' : True, 
        'threshold': {
            "levelline": "60m",
            "executeTime":{
                "minute":{
                    "duration": "1h",
                    "kelidu": "1m",
                    "levelline": "60m",
                    "continue": "12m"
                },
                "hour":{
                    "duration": "5D",
                    "kelidu": "1h",
                    "levelline": "5D",
                    "continue": "30h"
                },
                "halfday":{
                    "duration": "15D",
                    "kelidu": "4h",
                    "levelline": "10D",
                    "continue": "80h"
                },
                "day":{
                    "duration": "90D",
                    "kelidu": "1D",
                    "levelline": "30D",
                    "continue": "20D"
                }
            },
            "yujing":{
                "threshold": {
                    "TOAT": 0.3,
                    "TOTT": 3
                }
            },
            "gaojing":{
                "threshold": {
                    "TOAT":{
                        "10": 0.3,
                        "11": 0.4,
                        "12": 0.5,
                        "13": 0.6,
                        "14": 0.7,
                        "15": 0.8,
                        "16": 0.9,
                        "17": 1
                    },
                    "TOTT":{
                        "10": 3,
                        "11": 4,
                        "12": 5,
                        "13": 6,
                        "14": 7,
                        "15": 8,
                        "16": 9,
                        "17": 10
                    },
                }           
            }
        }
    },
    'weathercock_freeze':{
        'name' : '风向标冻结',
        # 把所需测点定义到每个算法里
        'ai_points' : ['WNAC.WindSpeed',
            'WGEN.GenActivePW',
            'WROT.Blade1Position',
            'WTRM.RotorSpd', 'WYAW.YawOpWind5sAVG', 'WNAC.WindDirection','WNAC.TemOut'], # 风速 发电机有功功率 风向
        'ai_rename' : {'WYAW.YawOpWind5sAVG':'WNAC.WindVaneDirection', 'WTRM.RotorSpd':'WGEN.GenSpd'},
        'di_points' : ['WTUR.TurbineSts'],
        'general_points' : ['WTUR.TurbineAIStatus'],
        'private_points' : {},
        'time_duration' : '1D', # 取多长时间范围的数据做预测
        'resample_interval' : '1m', # 原始数据采样间隔
        'error_data_time_duration' : '50m', # 异常数据持续多长时间报警
        'need_all_turbines' : False, # 是否需要场站全量数据做判断
        'store_file' : True, 
        'threshold': {}
    },
    'wind_speed_fault':{
        'name' : '风速仪故障',
        # 把所需测点定义到每个算法里
        'ai_points' : [
            'WNAC.WindSpeed',
            'WGEN.GenActivePW',
            'WROT.Blade1Position',
            'WTRM.RotorSpd', 'WYAW.YawOpWind5sAVG', 'WNAC.WindDirection'
            ],
        'ai_rename' : {'WYAW.YawOpWind5sAVG':'WNAC.WindVaneDirection', 'WTRM.RotorSpd':'WGEN.GenSpd'},
        'di_points' : ['WTUR.TurbineSts', 'WTUR.TurbineUnionSts'],
        'general_points' : ['WTUR.TurbineAIStatus'],
        'private_points' : {},
        'time_duration' : '1D', # 取多长时间范围的数据做预测
        'resample_interval' : '10m', # 原始数据采样间隔
        'error_data_time_duration' : '120m', #'500m', # 异常数据持续多长时间报警
        'need_all_turbines' : False, # 是否需要场站全量数据做判断
        'store_file' : True, 
        'threshold': {}
    },
    'yepian_kailie':{
        "name" : '叶尖开裂、叶片外衣裂开',
        # 把所需测点定义到每个算法里
        "ai_points" : [], #, 'WNAC.TemOut', 'WNAC.TemNacelle'] # 机舱控制柜温度 环境温度（舱外温度） 机舱温度（舱内温度）
        "ai_rename" : {},
        "di_points" : [],
        "general_points" : [],
        "private_points" : {"SPIC_JX_CMS_Blade":["BLD_DEFECTZ_FACTOR"]}, #江西保留
        "time_duration" : '1D',
        "resample_interval" : '10m', # 原始数据采样间隔
        "error_data_time_duration" : '500m',
        "need_all_turbines" : False,
        # modelId = "SPIC_ZD_CMS_Blade"
        "store_file" : True,    # modelId = "SPIC_ZD_CMS_Blade"
        'threshold': {}
    }
}
