#!/usr/bin/env python3
"""
检查FastAPI应用路由的脚本
"""
import sys
sys.path.append('/app')

from app.main import app

def check_routes():
    """检查应用中注册的所有路由"""
    print("🔍 检查FastAPI应用路由...")
    print("=" * 60)
    
    # 获取所有路由
    routes = app.routes
    print(f"总共找到 {len(routes)} 个路由:")
    print()
    
    websocket_routes = []
    http_routes = []
    
    for route in routes:
        route_info = f"{route.__class__.__name__}"
        if hasattr(route, 'path'):
            route_info += f" - {route.path}"
        if hasattr(route, 'methods'):
            route_info += f" - {route.methods}"
        
        if 'WebSocket' in route.__class__.__name__:
            websocket_routes.append(route_info)
        else:
            http_routes.append(route_info)
        
        print(f"  {route_info}")
    
    print()
    print("=" * 60)
    print(f"WebSocket路由数量: {len(websocket_routes)}")
    for ws_route in websocket_routes:
        print(f"  ✓ {ws_route}")
    
    print()
    print(f"HTTP路由数量: {len(http_routes)}")
    print("前5个HTTP路由:")
    for i, http_route in enumerate(http_routes[:5]):
        print(f"  • {http_route}")
    
    if len(websocket_routes) == 0:
        print()
        print("❌ 没有找到WebSocket路由！这说明路由注册有问题。")
    else:
        print()
        print("✅ 找到WebSocket路由")

if __name__ == "__main__":
    check_routes()