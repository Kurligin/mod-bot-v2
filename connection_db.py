import pymysql.cursors


def get_connection():
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='QWER2006ZXCV',
                                 db='support',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    
    return connection
