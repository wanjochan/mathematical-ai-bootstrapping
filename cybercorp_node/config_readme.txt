CyberCorp 端口配置说明
=====================

统一端口配置：9998
-----------------

原因：
- 8888 端口经常被其他服务占用
- 9999 端口也有冲突
- 统一使用 9998 端口避免混乱

启动方式：
--------

1. 服务器端（控制端）：
   运行: start_server_unified.bat
   或者: set CYBERCORP_PORT=9998 && python server.py

2. 客户端（受控端）：
   运行: start_client_unified.bat
   或者: set CYBERCORP_PORT=9998 && python client.py

3. 如果服务器在其他机器：
   编辑 start_client_unified.bat
   修改 SERVER_IP 为实际IP地址
   
   或者设置环境变量：
   set CYBERCORP_SERVER=ws://服务器IP:9998
   python client.py

重要提示：
---------
- 请使用 unified 版本的启动脚本
- 旧的脚本可能使用错误的端口
- 确保防火墙允许 9998 端口通信