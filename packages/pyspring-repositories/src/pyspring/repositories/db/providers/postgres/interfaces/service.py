from abc import ABC

from pyspring.repositories.db.service import IDBService


class IPostgresService(IDBService, ABC):
    """
    PostgreSQL服务接口
    """

    pass
