import mysql.connector
from datetime import datetime
from configs import config
from collections import Counter
import json
import os
import yaml as yl

exceptAlgorithmList = ['Efficiency_ana_V3']

def removeElementFromList(originList, exceptList):
    return [x for x in originList if x not in exceptList]

def get_connection():
    conn = mysql.connector.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USERNAME,
        password=config.DB_PASSWORD,
        database=config.DB_DATABASE,
        buffered=True
    )
    return conn
def get_connection_efficiency(config_path):
    sql_config = os.path.join(config_path)
    with open(sql_config, "r") as f:
        ylv = yl.load(f.read(), Loader=yl.FullLoader)
    conn = mysql.connector.connect(
        host=ylv["DB_HOST"],
        port=ylv["DB_PORT"],
        user=ylv["DB_USERNAME"],
        password=ylv["DB_PASSWORD"],
        database=ylv["DB_DATABASE"]
    )
    return conn
def InsertIndex(conn, average_wind_speed, actual_power_generation, loss_of_electricity, equivalent_hours, wind_rate, time_rate, start_time, end_time):
    cursor = conn.cursor()
    insert_query = "INSERT INTO operation_index (average_wind_speed, \
                        actual_power_generation, \
                        loss_of_electricity, \
                        equivalent_hours, \
                        wind_rate, \
                        time_rate, \
                        create_time, \
                        start_time, \
                        end_time \
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    data_to_insert = (average_wind_speed, actual_power_generation, loss_of_electricity, equivalent_hours, wind_rate*100, time_rate*100, datetime.now(), start_time, end_time)
    cursor.execute(insert_query, data_to_insert)
    conn.commit()
    cursor.close()

def insert_alarm(assetId, alarmName, alarmTime, error_start_time, error_end_time):#conn, 
    conn = get_connection()
    cursor = conn.cursor()
    insert_query = "INSERT INTO data_alarm (wind_turbine_code, \
                        content, \
                        level, \
                        state, \
                        create_time, \
                        update_time, \
                        gather_time, \
                        source, \
                        alarm_type, \
                        category,\
                        group_id) VALUES ((select code from base_asset where enos_id=%s), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    data_to_insert = (assetId, alarmName, 1, 0, datetime.now(), datetime.now(), alarmTime, 1, 3, 1, alarmName)
    cursor.execute(insert_query, data_to_insert)
    conn.commit()
    cursor.close()

def InsertAlgorithmDetail(headId,wind_num,start_time,status, turbineId, result, warning=0, alert=0): #warning预警， alert告警 conn,
    if headId == None or headId == 'None':
        return None
    conn = get_connection()
    cursor = conn.cursor()
    addItem = "insert into algorithm_execute_detail (\
        head_id, \
        wind_num, \
        execute_time, \
        status, \
        enos_id, \
        analysis_result, \
        warning_level, \
        alarm_level) values (%s, %s, %s, %s, %s, %s, %s, %s)"
    dataItem = (headId, wind_num, start_time, status, turbineId, result, warning, alert)
    cursor.execute(addItem, dataItem)
    itemId = cursor.lastrowid

    conn.commit()
    cursor.close()
    conn.close()

    return itemId


# def UpdateAlgorithmDetail(conn):
#     cursor = conn.cursor()

def InsertAlgorithmHead(code, start_time, data_start_time, data_end_time):#conn,
    if code in exceptAlgorithmList:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    queryItem = "select id, name from algorithm_model where code=%s"
    dataQuery = (code,)
    cursor.execute(queryItem, dataQuery)
    queryResult = cursor.fetchall()

    addItem = "insert into algorithm_execute_head (\
        model_id, \
        model_name, \
        start_time, \
        data_start_time, \
        data_end_time, \
        model_code) values (%s, %s, %s, %s, %s, %s)"
    dataItem = (queryResult[-1][0], queryResult[-1][1], start_time, data_start_time, data_end_time, code)
    cursor.execute(addItem, dataItem)
    itemId = cursor.lastrowid

    conn.commit()
    cursor.close()
    conn.close()

    return itemId


def UpdateAlgorithmHead(ids):#ids:{algorithmCode:headId}     删#{headId:(algorithmCode,turbineIndex)} . conn, 
    for key, value in ids.items():
        if value == None or value == 'None':
            continue
        conn = get_connection()
        cursor = conn.cursor()
        queryItem = "select last_end_time, last_result_normal, last_result_abnormal, last_result_fail from algorithm_model where code=%s"
        dataQuery = (key,)
        cursor.execute(queryItem, dataQuery)
        queryResult = cursor.fetchall()

        updateItem = "update algorithm_execute_head \
        set end_time=%s, \
        result_normal=%s, \
        result_abnormal=%s,\
        result_fail=%s \
        where id=%s"
        dataItem = (queryResult[-1][0], queryResult[-1][1], queryResult[-1][2], queryResult[-1][3], value)
        cursor.execute(updateItem, dataItem)
        conn.commit()
        cursor.close()
        conn.close()

def ResetTubineNum(modeCode, totalTurbineNum, currentTurbineNum):#conn, 
    modeCode_ = removeElementFromList([modeCode] if isinstance(modeCode,str) else modeCode, exceptAlgorithmList)
    if len(modeCode_) > 0:
        conn = get_connection()
        cursor = conn.cursor()
        values = "(%s)" % ','.join(['%s'] * len(modeCode_))
        update_info = "update algorithm_model \
                        set sum_num=%s, \
                        current_num=%s \
                        where code in " + values
        data_to_insert = (totalTurbineNum, currentTurbineNum, *modeCode_)  
        cursor.execute(update_info, data_to_insert)
        
        conn.commit()
        cursor.close()
        conn.close()

def ReviewTubineNum(modeCode, currentTurbineNum):#conn, 
    modeCode_ = removeElementFromList([modeCode] if isinstance(modeCode,str) else modeCode, exceptAlgorithmList)
    if len(modeCode_) == 0:
        return []
    conn = get_connection()
    cursor = conn.cursor()
    values = "(%s)" % ','.join(['%s'] * len(modeCode_))
    #检查,算法列表中sum_num>0只更新current_num; sum_num=0传出待重置算法名列表
    # greaterZeroCode = "select code from algorithm_model \
    #                    where code in " + values + " \
    #                    and sum_num > 0"
    equalZeroCode = "select code from algorithm_model \
                       where code in " + values + " \
                       and sum_num = 0"
    #更新
    update_info = "update algorithm_model \
                    set current_num=%s \
                    where code in " + values + " \
                    and sum_num > 0" 
    data_to_insert = (currentTurbineNum, *modeCode_)  
    cursor.execute(update_info, data_to_insert)

    #筛选待重置算法
    dataQuery = (*modeCode_,)
    cursor.execute(equalZeroCode, dataQuery)
    queryResult = cursor.fetchall()                

    conn.commit()
    cursor.close()
    conn.close()

    resetSumNames = [i[0] for i in queryResult]
    

    return resetSumNames

def UpdateTubineNum(modeCode,last_start_time, last_end_time, totalTurbineNum, currentTurbineNum):#conn, 
    modeCode_ = removeElementFromList([modeCode] if isinstance(modeCode,str) else modeCode, exceptAlgorithmList)
    if len(modeCode_) == 0:
        return
    conn = get_connection()
    cursor = conn.cursor()
    if currentTurbineNum == 1 and currentTurbineNum!=totalTurbineNum:
        update_info = "update algorithm_model \
                        set status=%s, \
                        last_start_time=%s, \
                        sum_num=%s, \
                        last_result_normal=%s, \
                        last_result_abnormal=%s, \
                        last_result_fail=%s, \
                        current_num=%s \
                        where code=%s"
        # update_query = "UPDATE algorithm_model \
        #                SET status = %s, \
        #                last_start_time = %s \
        #                WHERE code = %s"
        data_to_insert = (1, last_start_time, totalTurbineNum, 0, 0, 0, currentTurbineNum, *modeCode_)  
        cursor.execute(update_info, data_to_insert)
    elif currentTurbineNum == totalTurbineNum and currentTurbineNum!=1:
        update_info = "update algorithm_model \
                        set last_end_time=%s, \
                        current_num=%s \
                        where code=%s"
        data_to_insert = (last_end_time, currentTurbineNum, *modeCode_)  
        cursor.execute(update_info, data_to_insert)
    elif currentTurbineNum== totalTurbineNum and currentTurbineNum==1:
        update_info = "update algorithm_model \
                        set status=%s, \
                        last_start_time=%s, \
                        last_end_time=%s, \
                        sum_num=%s, \
                        last_result_normal=%s, \
                        last_result_abnormal=%s, \
                        last_result_fail=%s, \
                        current_num=%s \
                        where code=%s"
        data_to_insert = (1, last_start_time, last_end_time, totalTurbineNum, 0, 0, 0, currentTurbineNum, *modeCode_)  
        cursor.execute(update_info, data_to_insert)
    else:
        update_info = "update algorithm_model \
                        set current_num=%s \
                        where code=%s"
        data_to_insert = (currentTurbineNum, *modeCode_)  
        cursor.execute(update_info, data_to_insert)
    conn.commit()
    cursor.close()
    conn.close()

def UpdateAlgorithmInfo(multi_algorithms, no_alarm_models, alarm_models, exception_models):#conn, 
    counterNoAlarm = Counter(no_alarm_models)
    counterAlarm = Counter(alarm_models)
    counterException = Counter(exception_models)

    for algorithm in multi_algorithms:
        conn = get_connection()
        cursor = conn.cursor()
        name = algorithm.__name__.split('.')[-1]
        if name in exceptAlgorithmList:
            continue
        countAlarm = 0
        countNoAlarm = 0
        countExcept = 0
        if name in counterNoAlarm.keys():
            countNoAlarm = counterNoAlarm[name]
        if name in counterAlarm.keys():
            countAlarm = counterAlarm[name]
        if name in counterException.keys():
            countExcept = counterException[name]
        update_info = "update algorithm_model \
                        set sum_abnormal=%s, \
                        last_result_normal=%s, \
                        last_result_abnormal=%s, \
                        last_result_fail=%s \
                        where code=%s"
        data_to_insert = (countAlarm, countNoAlarm, countAlarm, countExcept, name) 
        cursor.execute(update_info, data_to_insert)
        conn.commit()
        cursor.close()
        conn.close()

def UpdateResult(multi_algorithms, no_alarm_models, alarm_models, exception_models, data_empty_models):#conn, 
    counterNoAlarm = Counter(no_alarm_models)
    counterAlarm = Counter(alarm_models)
    counterException = Counter(exception_models)
    counterDataEmpty = Counter(data_empty_models)

    for algorithm in multi_algorithms:
        conn = get_connection()
        cursor = conn.cursor()
        name = algorithm.__name__.split('.')[-1]
        if name in exceptAlgorithmList:
            continue
        countAlarm = 0
        countNoAlarm = 0
        countExcept = 0
        countDataEmpty = 0
        if name in counterNoAlarm.keys():
            countNoAlarm = counterNoAlarm[name]
        if name in counterAlarm.keys():
            countAlarm = counterAlarm[name]
        if name in counterException.keys():
            countExcept = counterException[name]
        if name in counterDataEmpty.keys():
            countDataEmpty = counterDataEmpty[name]
        update_info = "update algorithm_model \
                        set status=%s, \
                        last_result_content=%s \
                        where code=%s"
        strContent = f"算法生成报警次数:{countAlarm},算法未产生报警次数{countNoAlarm},算法执行异常次数{countExcept},未获得原始数据或清洗后无数据的次数{countDataEmpty}。"
        data_to_insert = (0, strContent, name) 
        cursor.execute(update_info, data_to_insert)
        conn.commit()
        cursor.close()
        conn.close()

def CheckThreshold(multi_algorithms, algorithm_configs):#conn, 
    for algorithm in multi_algorithms:
        conn = get_connection()
        cursor = conn.cursor()
        name = algorithm.__name__.split('.')[-1]
        if name in exceptAlgorithmList(algorithm):
            algorithm_configs[name]['threshold'] = {}
            continue
        queryItem = "select threshold from algorithm_model where code=%s"
        dataQuery = (name,)
        cursor.execute(queryItem, dataQuery)
        conn.commit()
        queryResult = cursor.fetchall()
        threshold = eval(queryResult[-1][0])
        if type(threshold) == type(None) or len(threshold) == 0:
            algorithm_configs[name]['threshold'] = {}
        else:
            algorithm_configs[name]['threshold'] = threshold
        cursor.close()
        conn.close()

    return algorithm_configs

def CheckModuleCode(modeCode):
    conn = get_connection()
    cursor = conn.cursor()
    # values = "(%s)" % ','.join(['%s'] * len(modeCode))
    #筛选model_code，输出module_code
    module_query = "select module_code,name from algorithm_model \
                       where code=%s"
    
    #筛选待重置算法
    dataQuery = (modeCode,)
    cursor.execute(module_query, dataQuery)
    queryResult = cursor.fetchall()                

    conn.commit()
    cursor.close()
    conn.close()
    module_code = queryResult[-1][0]
    module_name = queryResult[-1][1]

    return module_code, module_name

def save_alarm(assetId, alarmName, alarmTime, error_start_time, error_end_time):
    conn = get_connection()
    insert_alarm(conn, assetId, alarmName, alarmTime, error_start_time, error_end_time)

if __name__ == '__main__':
    save_alarm('xxx', '偏航一场', datetime.now(), datetime.now(), datetime.now())
