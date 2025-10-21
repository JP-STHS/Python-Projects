How to use the license plate scanner:
Make sure docker is installed and your device has at least one working webcam.
Run simple_server.py to host a flask server streaming your webcam if a stream is not already set up.
Run these commands in terminal:
- docker pull chespinsdock/my_yolo_app
- docker run chespinsdock/my_yolo_app


If the docker run cmd doesn't work, try running:
Linux: - docker run --network="host" chespinsdock/my_yolo_app
Windows: - docker run -e HOST=host.docker.internal chespinsdock/my_yolo_app