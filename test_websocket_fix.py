"""
测试修复后的WebSocket数据流
"""
import asyncio
import websockets
import json
import requests

async def test_websocket():
    print('测试修复后的WebSocket数据流...')
    
    # 确保数据流停止
    try:
        requests.post('http://localhost:8000/api/v1/ui-tars/stream/stop')
    except:
        pass
    
    uri = 'ws://localhost:8000/api/v1/ui-tars/stream/ws'
    
    try:
        async with websockets.connect(uri) as websocket:
            print('✅ WebSocket连接成功')
            
            for i in range(5):
                message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                print(f'收到消息 {i+1}: {msg_type}')
                
                if 'window_info' in data:
                    title = data['window_info']['title'][:30]
                    print(f'  窗口: {title}...')
                elif msg_type == 'heartbeat':
                    stream_active = data.get('stream_active', False)
                    frame_count = data.get('frame_count', 0)
                    print(f'  流状态: {stream_active}, 帧数: {frame_count}')
                elif msg_type == 'connected':
                    fps = data.get('fps', 0)
                    print(f'  已连接, FPS: {fps}')
            
            print('✅ WebSocket测试完成')
            return True
            
    except Exception as e:
        print(f'❌ WebSocket测试失败: {e}')
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    print(f"\n测试结果: {'成功' if result else '失败'}") 