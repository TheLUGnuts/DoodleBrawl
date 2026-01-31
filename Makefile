.PHONY: deploy update-code restart-backend build-frontend
update: update-code build-frontend restart-backend
	@echo "Updating codebase"
deploy: build-frontend restart-backend
	@echo "Build completed"
update-code:
	@echo "Pulling latest changes from GitHub..."
	git pull
build-frontend:
	@echo "Building React/Vite frontend..."
	cd frontend && npm install && npm run build
restart-backend:
	@echo "Restarting Gunicorn System Service..."
	sudo systemctl restart doodle
