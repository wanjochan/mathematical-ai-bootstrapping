@echo off
echo Installing dependencies for CyberCorp Node System...

echo.
echo Installing server dependencies...
cd cybercorp_nodeserver
call npm install
cd ..

echo.
echo Installing client dependencies...
cd cybercorp_node
call npm install
cd ..

echo.
echo Installation complete!
echo.
echo To run:
echo 1. Start server: cd cybercorp_nodeserver && npm start
echo 2. Start client: cd cybercorp_node && npm start
echo 3. Run test: node test_cybercorp.js
pause