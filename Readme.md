## Prospekting Tookit BSmarti


## Local run:

```sh
python manage.py runserver
```

```sh
celery -A config worker --loglevel=info
```

## Local server:
```sh
systemctl daemon-reload
systemctl enable prospecting-toolkit
systemctl start prospecting-toolkit
systemctl status prospecting-toolkit
```