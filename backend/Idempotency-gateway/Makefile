.PHONY: start

start:
	@echo "Starting Redis using Docker..."
	-@sudo docker run -d -p 6379:6379 --name gateway-redis redis:alpine 2>/dev/null || sudo docker start gateway-redis 2>/dev/null
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv venv; \
	fi
	@echo "Activating and Installing dependencies..."
	@./venv/bin/pip install -q -r requirements.txt
	@echo "Running migrations..."
	@./venv/bin/python manage.py migrate
	@echo "Starting server..."
	@./venv/bin/python manage.py runserver
