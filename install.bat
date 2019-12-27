@echo off
CALL venv\Scripts\activate.bat
pip install -r requeriments.txt
python manage.py migrate
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'suporte@implanti.com.br', 'd35$admin'); exit();"
echo Tudo certo, o CMD fechara em 5 segundo
timeout 5