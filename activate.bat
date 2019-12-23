CALL venv\Scripts\activate.bat
python manage.py migrate
python manage.py runserver %computername%:8182