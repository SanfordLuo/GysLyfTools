import threading


class Singleton(object):
    _instances = {}  # 存储 {类: 实例} 的映射
    _lock = threading.Lock()  # 类级别的锁

    @classmethod
    def instance(cls):
        # 第一次检查：无锁快速检查
        if cls not in cls._instances:
            with cls._lock:  # 加锁
                # 第二次检查：持锁状态下检查
                if cls not in cls._instances:
                    cls._instances[cls] = cls()  # 创建实例
        return cls._instances[cls]
