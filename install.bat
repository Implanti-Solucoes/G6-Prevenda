CALL venv\Scripts\activate.bat
pip install -r requeriments.txt
python manage.py migrate
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'suporte@implanti.com.br', 'd35$admin')" | python manage.py shell