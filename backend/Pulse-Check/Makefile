.PHONY: start stop status clean

start:
	@if [ ! -d "venv" ]; then \
		python3 -m venv venv; \
	fi
	@./venv/bin/pip install -q -r requirements.txt
	@./venv/bin/python manage.py migrate
	@./venv/bin/python manage.py runserver & ./venv/bin/celery -A pulse_check worker --loglevel=info

stop:
	-@pkill -f "manage.py runserver" 2>/dev/null
	-@pkill -f "celery" 2>/dev/null

clean:
	rm -rf venv
	rm -rf staticfiles
	-@pkill -f "manage.py runserver" 2>/dev/null
	-@pkill -f "celery" 2>/dev/null
