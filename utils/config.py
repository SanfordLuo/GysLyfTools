"""
@Author  :   luoyafei
@Time    :   2025/7/27 23:30
@Desc    :   None
"""
# 服务端口
APP_PORT = 7777

# 日志路径
LOG_PATH = "/var/log/"
# 数据路径
DATA_PATH = "/var/data/"

# MYSQL
MYSQL_CONFIG = {
    # 私网：172.25.31.63
    # "host": "172.25.31.63",
    # 公网
    "host": "120.26.122.115",
    "port": 3306,
    "user": "gyslyfuser",
    "password": "GysLyf200128",
    "db": "gys_lyf"
}
