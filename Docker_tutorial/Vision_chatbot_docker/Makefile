.PHONY: setup train test up down logs build clean
setup:
	cp -n .env.example .env || true
train:
	python -m ml.train
test:
	pytest -q
up:
	docker compose up --build -d
down:
	docker compose down
logs:
	docker compose logs -f api
build:
	docker compose build
clean:
	docker compose down -v
