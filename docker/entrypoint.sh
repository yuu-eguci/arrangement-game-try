#!/bin/sh
# 引数があればそれを実行 (pytest とか)。なければ仮想ディスプレイ上でゲームを動かしてブラウザに映す。
set -e
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

export DISPLAY=:0 SDL_VIDEODRIVER=x11
# docker compose stop/start で前回のロックが残っていると Xvfb が起動しないので消しておく
rm -f /tmp/.X0-lock /tmp/.X11-unix/X0
Xvfb :0 -screen 0 640x480x24 &
i=0
while [ ! -e /tmp/.X11-unix/X0 ]; do
    i=$((i + 1))
    if [ "$i" -gt 100 ]; then
        echo "Xvfb did not start" >&2
        exit 1
    fi
    sleep 0.1
done
x11vnc -display :0 -localhost -nopw -forever -quiet &
websockify --web /usr/share/novnc 6080 localhost:5900 &
echo "Open http://localhost:6080/vnc.html?autoconnect=1&resize=scale"
exec python ArrangementGameTry.py
