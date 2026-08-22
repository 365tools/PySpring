"""
PySpring 启动 Banner
生成类似 Spring Boot 风格的 ASCII 艺术启动 Banner
"""

BANNER = """
   ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄     ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ 
  █ ██╔══██║██╔════╝ ██╔════╝    ██╔════╝ ╚══██╔══╝ ██╔════╝ 
  █ ██║  ██║█████╗   █████╗      █████╗     ██║    █████╗   
  █ ██║  ██║██╔══╝   ██╔══╝      ██╔══╝     ██║    ██╔══╝   
  █ ██████╔╝███████╗ ███████╗    ██║        ██║    ███████╗ 
  █ ╚═════╝ ╚══════╝ ╚══════╝    ╚═╝        ╚═╝    ╚══════╝ 
  ╰──────────────────────────────────────────────────────────╮
    >_ PySpring Framework v{version}                          
    Python {python_version} | FastAPI {fastapi_version}                      
    ╰──────────────────────────────────────────────────────────╯
"""

BANNER_SIMPLE = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║    ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄     ▄▄   ▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄   ║
║    █ ██╔══██║██╔════╝ ██╔════╝    ██╗ ██╔╝██╔════╝ ██╔═══╝ ║
║    █ ██║  ██║█████╗   █████╗      ╚██╗██╔╝ █████╗   █████╗ ║
║    █ ██║  ██║██╔══╝   ██╔══╝       ╚███╔╝  ██╔══╝   ██╔══╝ ║
║    █ ██████╔╝███████╗ ███████╗     ╚██╔╝   ███████╗ ███████║
║    ╚═════╝ ╚══════╝ ╚══════╝      ╚═╝    ╚══════╝ ╚══════╝ ║
║                                                           ║
║    Enterprise Python Web Framework                        ║
║    "Spring Boot for Python" 🚀                            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""

BANNER_MINIMAL = """
┌───────────────────────────────────────────────────────────┐
│  PySpring Framework  •  Enterprise Python Web Framework   │
│  v{version}  |  Python {python_version}  |  FastAPI Powered           │
└───────────────────────────────────────────────────────────┘
"""

BANNER_SPRING_STYLE = """
  ____  _                          ____             _       
 |  _ \\| |__   __ _ _ __ ___  _ __|  _ \\ __ __ ___ (_) __ _ 
 | |_) | '_ \\ / _` | '_ ` _ \\| '_ \\ |_) | '__/ _` \\ |/ _` |
 |  __/| | | | (_| | | | | | | |_) |  __/| | | (_| | | (_| |
 |_|   |_| |_|\\__,_|_| |_| |_| .__/|_|   |_|  \\__,_|_|\\__,_|
                             |_|                            
  >_ PySpring Framework v{version}
  Python {python_version} | FastAPI {fastapi_version}
"""

BANNER_MODERN = """
  ╭───────────────────────────────────────────────────────────╮
  │                                                           │
  │   ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗             │
  │   ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝             │
  │   ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗             │
  │   ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║             │
  │   ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║             │
  │   ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝             │
  │                                                           │
  │   Enterprise Python Web Framework                         │
  │   "Spring Boot for Python" 🚀                             │
  │                                                           │
  │   Version: v{version:<20}  Python: {python_version:<12}                  │
  │                              FastAPI: {fastapi_version:<12}                  │
  │                                                           │
  ╰───────────────────────────────────────────────────────────╯
"""

BANNER_COLORED = """
   ▄▄▄▄▄▄  ▄▄     ▄▄ ▄▄▄▄▄▄▄ ▄▄▄    ▄▄   
  ██╔═══██╗██║    ██║██╔════╝████╗  ██║  
  ██║   ██║██║ █╗ ██║█████╗  ██╔██╗ ██║  
  ██║▄▄ ██║██║███╗██║██╔══╝  ██║╚██╗██║  
  ╚██████╔╝╚███╔███╔╝███████╗██║ ╚████║  
   ╚══▀▀═╝  ╚══╝╚══╝ ╚══════╝╚═╝  ╚═══╝  
  ╭─────────────────────────────────────────────╮
    >_ PySpring Framework v{version}             
    Python {python_version} | FastAPI {fastapi_version}             
  ╰─────────────────────────────────────────────╯
"""

BANNER_GRADIENT = """
  ╔═══════════════════════════════════════════════════════════╗
  ║                                                           ║
  ║     ██████╗ ███████╗ █████╗ ██████╗ ██╗   ██╗             ║
  ║     ██╔══██╗██╔════╝██╔══██╗██╔══██╗╚██╗ ██╔╝             ║
  ║     ██████╔╝█████╗  ███████║██║  ██║ ╚████╔╝              ║
  ║     ██╔══██╗██╔══╝  ██╔══██║██║  ██║  ╚██╔╝               ║
  ║     ██║  ██║███████╗██║  ██║██████╔╝   ██║                ║
  ║     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝    ╚═╝                ║
  ║                                                           ║
  ║   Enterprise Python Web Framework                         ║
  ║   "Spring Boot for Python" 🚀                             ║
  ║                                                           ║
  ║   Version: v{version:<20}  Python: {python_version:<12}                  ║
  ║                              FastAPI: {fastapi_version:<12}                  ║
  ║                                                           ║
  ╚═══════════════════════════════════════════════════════════╝
"""

# 新增：紧凑风格
BANNER_COMPACT = """
┏───────────────────────────────────────────────────────────┓
┃                                                           ┃
┃   ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗            ┃
┃   ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝            ┃
┃   ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗            ┃
┃   ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║            ┃
┃   ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║            ┃
┃   ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝            ┃
┃                                                           ┃
┃   PySpring Framework v{version:<20}           ┃
┃   Python {python_version:<12} | FastAPI {fastapi_version:<12}           ┃
┃                                                           ┃
┗───────────────────────────────────────────────────────────┛
"""


def get_banner(style: str = "modern", **kwargs: str) -> str:
    """
    获取指定风格的 Banner

    Args:
        style: Banner 风格，可选值：
               - "modern": 现代风格（推荐）
               - "simple": 简洁风格
               - "spring": Spring Boot 风格
               - "minimal": 极简风格
               - "colored": 彩色风格
               - "gradient": 渐变风格
               - "compact": 紧凑风格
        **kwargs: Banner 中的变量替换，如 version, python_version, fastapi_version

    Returns:
        格式化后的 Banner 字符串
    """
    from ._version import __version__

    banners = {
        "modern": BANNER_MODERN,
        "simple": BANNER_SIMPLE,
        "spring": BANNER_SPRING_STYLE,
        "minimal": BANNER_MINIMAL,
        "colored": BANNER_COLORED,
        "gradient": BANNER_GRADIENT,
        "compact": BANNER_COMPACT,
    }

    template = banners.get(style, BANNER_MODERN)

    # 默认版本信息（version 为 CLI 自身版本，来自统一入口）
    defaults = {
        "version": __version__,
        "python_version": "3.12+",
        "fastapi_version": "0.104+",
    }
    defaults.update(kwargs)

    return template.format(**defaults)


def print_banner(style: str = "modern", **kwargs: str) -> None:
    """
    打印 Banner 到控制台

    Args:
        style: Banner 风格
        **kwargs: Banner 中的变量替换
    """
    print(get_banner(style, **kwargs))


if __name__ == "__main__":
    # 预览所有风格
    print("\n" + "=" * 75)
    print("PySpring Banner 风格预览")
    print("=" * 75 + "\n")

    styles = ["modern", "simple", "spring", "minimal", "colored", "gradient", "compact"]

    for style in styles:
        print(f"\n【{style.upper()}】风格:\n")
        # version 省略时自动使用 _version.__version__（CLI 自身版本）
        print(get_banner(style, python_version="3.12.8", fastapi_version="0.104.0"))
        print()
