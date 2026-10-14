#!/bin/sh
# CI 用: noVNC のページが出て、VNC サーバが応答して、ゲームが動いていることを確かめる
for _ in $(seq 30); do
    if curl -fsS -o /dev/null http://localhost:6080/vnc.html \
        && docker compose exec -T game python -c "import socket; assert socket.create_connection(('localhost', 5900)).recv(3) == b'RFB'"; then
        sleep 3
        docker compose logs
        docker compose ps --status running --services | grep -x game
        exit
    fi
    sleep 1
done
docker compose logs
exit 1
