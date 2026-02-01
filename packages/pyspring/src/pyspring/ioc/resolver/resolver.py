"""
模块依赖解析器

负责解析服务之间的依赖关系，支持类型提示、命名注入和集合注入。
"""

class DependencyResolver:
    """
    依赖解析器
    
    负责解析服务的依赖关系，支持：
    - 类型注入
    - 命名注入
    - List[Type] 集合注入
    - 循环依赖检测与处理
    """
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self._instantiation_stack = []

    def resolve_dependencies(self, service_def: ServiceDefinition, container: Any) -> Dict[str, Any]:
        """
        解析服务定义的所有依赖
        
        Args:
            service_def: 服务定义
            container: 容器实例
            
        Returns:
            依赖字典
        """
        # 获取构造函数参数类型
        init_signature = get_type_hints(service_def.service_type.__init__)
        
        # 移除self参数
        if 'return' in init_signature:
            del init_signature['return']
        if 'self' in init_signature:
            del init_signature['self']
            
        dependencies = {}
        for param_name, param_type in init_signature.items():
            dep_info = self._create_dependency_info(param_name, param_type)
            dependencies[param_name] = self._resolve_dependency(dep_info, container, service_def.name)
            
        return dependencies

    def _create_dependency_info(self, param_name: str, param_type: type) -> DependencyInfo:
        """
        创建依赖信息对象
        
        Args:
            param_name: 参数名称
            param_type: 参数类型
            
        Returns:
            依赖信息
        """
        # 检查是否是List注入
        origin = get_origin(param_type)
        if origin is list or origin is List:
            type_args = get_args(param_type)
            if type_args:
                element_type = type_args[0]
                # 使用特殊前缀标记List注入
                service_name = f"__list_collection__:{param_name}"
                return DependencyInfo(
                    param_name=param_name,
                    param_type=param_type,
                    service_name=service_name,
                    is_list=True,
                    element_type=element_type
                )
        
        # 检查是否有@inject注解
        annotations = getattr(service_def.service_type, '__annotations__', {})
        inject_config = annotations.get(f"_{param_name}_inject", None)
        if inject_config:
            return DependencyInfo(
                param_name=param_name,
                param_type=param_type,
                service_name=inject_config.service_name,
                qualifier=inject_config.qualifier
            )
            
        # 默认按类型查找
        return DependencyInfo(
            param_name=param_name,
            param_type=param_type,
            service_name="",  # 空字符串表示按类型查找
            qualifier=None
        )

    def _resolve_dependency(
            self,
            dep_info: DependencyInfo,
            container: Any,
            current_service: str
    ) -> Any:
        """
        解析单个依赖，返回实例或代理
        
        Args:
            dep_info: 依赖信息
            container: 容器
            current_service: 当前正在实例化的服务名称
            
        Returns:
            依赖实例或代理
        """
        service_name = dep_info.service_name

        # 检查是否是List类型的集合注入
        if service_name.startswith("__list_collection__:"):
            # 提取原始参数名
            param_name = service_name.split(":", 1)[1]

            # 获取List的元素类型
            origin = get_origin(dep_info.param_type)
            type_args = get_args(dep_info.param_type)

            if type_args:
                element_type = type_args[0]
                # 获取所有该类型的实例
                instances = container.get_all_of_type(element_type)
                logger.debug(f"📦 为参数 '{param_name}' 收集了 {len(instances)} 个 {element_type.__name__} 实例")
                return instances

            # 如果无法获取元素类型，返回空列表
            logger.warning(f"⚠️ 无法解析 List 参数 '{param_name}' 的元素类型")
            return []

        # 检查是否会造成循环依赖
        if service_name in self._instantiation_stack:
            # 使用懒加载代理
            logger.debug(f"🔄 检测到潜在循环依赖 {current_service} -> {service_name}，使用代理")
            service_def = self.registry.get(service_name)
            LazyProxy = get_lazy_proxy_class()
            Container = get_container_class()
            return LazyProxy(container, service_name, service_def.service_type)

        # 正常获取实例
        return container.get(service_name)