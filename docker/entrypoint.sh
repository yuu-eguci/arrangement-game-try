#!/bin/sh
# 引数があればそれを実行 (pytest とか)。なければ仮想ディスプレイ上でゲームを動かしてブラウザに映す。
set -e
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

export DISPLAY=:0
Xvfb :0 -screen 0 640x480x24 &
while [ ! -e /tmp/.X11-unix/X0 ]; do sleep 0.1; done
x11vnc -display :0 -localhost -nopw -forever -quiet &
websockify --web /usr/share/novnc 6080 localhost:5900 &
echo "Open http://localhost:6080/vnc.html?autoconnect=1&resize=scale"
exec python ArrangementGameTry.py
