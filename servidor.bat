set FLASK_ENV=production
waitress-serve --host=192.168.226.216 --port=5000 --threads=8 app:app