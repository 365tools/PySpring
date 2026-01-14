from typing import List, Dict

from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService
from pyspring.log.instance import logger


class ItemService(ISingletonService):
    """
    商品服务 - 业务逻辑层
    继承 ISingletonService 后，PySpring 容器会自动将其注册为单例
    """

    def __init__(self):
        # 模拟数据库数据
        self._items = [
            {"id": 1, "name": "Python Book", "price": 29.99},
            {"id": 2, "name": "Mechanical Keyboard", "price": 199.50},
        ]
        logger.info("🛒 ItemService 初始化完成")

    def get_all_items(self) -> List[Dict]:
        """获取所有商品"""
        logger.debug("Executing get_all_items query")
        return self._items

    def get_item_by_id(self, item_id: int) -> Dict:
        """根据ID获取商品"""
        for item in self._items:
            if item["id"] == item_id:
                return item
        return None

    def add_item(self, name: str, price: float) -> Dict:
        """添加新商品"""
        new_id = len(self._items) + 1
        new_item = {"id": new_id, "name": name, "price": price}
        self._items.append(new_item)
        logger.info(f"✨ 新增商品: {name} (ID: {new_id})")
        return new_item
