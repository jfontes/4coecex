@echo off
echo Iniciando servidor Flask para desenvolvimento com acesso de rede...
echo.
echo O servidor estará disponível em:
echo - Local: http://localhost:5000
echo - Rede: http://[SEU_IP]:5000
echo.
echo Para descobrir seu IP, execute: ipconfig
echo.
echo Pressione Ctrl+C para parar o servidor
echo.

set FLASK_ENV=development
python app.py
