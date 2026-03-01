## Prospekting Tookit BSmarti


## Local run:

```sh
python manage.py runserver
```

```sh
celery -A config worker --loglevel=info
```

## Server run:
```sh
systemctl daemon-reload
systemctl enable prospecting-toolkit
systemctl start prospecting-toolkit
systemctl status prospecting-toolkit
```

```sh
systemctl daemon-reload
systemctl enable prospecting-celery
systemctl start prospecting-celery
systemctl status prospecting-celery
```