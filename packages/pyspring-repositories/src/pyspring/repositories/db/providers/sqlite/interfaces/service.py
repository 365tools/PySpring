from abc import ABC

from pyspring.repositories.db.service import IDBService


class ISqliteService(IDBService, ABC):
    """
    SQLite服务接口
    """

    pass
