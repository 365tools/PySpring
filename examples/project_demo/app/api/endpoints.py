from fastapi import APIRouter, HTTPException
from pyspring.ioc.manager import AppContainerManager
from pyspring.web.core.response import Response, HttpResponse

# 使用绝对路径导入，确保 IoC 能够正确解析（在实际项目中通常不需要这么长，因为有 sys.path 设置）
from examples.project_demo.app.services.item_service import ItemService

router = APIRouter(prefix="/items", tags=["Items"])


@router.get("/", response_model=HttpResponse)
async def list_items():
    """获取商品列表"""
    # 从容器获取服务实例 (依赖注入的替代方案，也支持构造函数注入)
    item_service = AppContainerManager.service(ItemService)
    items = item_service.get_all_items()

    return Response.success(items)


@router.get("/{item_id}", response_model=HttpResponse)
async def get_item(item_id: int):
    """获取单个商品"""
    item_service = AppContainerManager.service(ItemService)
    item = item_service.get_item_by_id(item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return Response.success(item)


@router.post("/", response_model=HttpResponse)
async def create_item(name: str, price: float):
    """创建商品"""
    item_service = AppContainerManager.service(ItemService)
    new_item = item_service.add_item(name, price)
    return Response.success(new_item, business_code=201)
