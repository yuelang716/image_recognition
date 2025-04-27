import time
from datetime import datetime, timedelt


# 使用time模块获取时间戳
print("当前时间戳:", time.time)

# 使用datetime模块创建日期时间对象
now = datetime.now
print("当前时间:", now)

# 计算3天后的日期
future = now + timedelta(days=3)
print("3天后日期:", future)


