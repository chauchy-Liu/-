import mysql.connector
from datetime import datetime
from configs import config
from collections import Counter
import json
import redis

def get_connection():
 
    # 连接到Redis
    red = redis.Redis(host='localhost', port=6379, db=0)
    
    # 设置键和值，同时设置过期时间
    red.setex('my_key', 10, 'my_value')  # 这个键将在10秒后过期
    
    # 获取键的存储时间（TTL）
    ttl = red.ttl('my_key')
    # print(f'The TTL of "my_key" is: {ttl} seconds')
    return red