ArrangementGameTry
===

pygameお試し作品。床と椅子を置ける。ディクショナリを使えて喜んでいるのが微笑ましい一品。

- Docker: 対応!
- Python: 3.15!
- Linter: Ruff!
- Test: pytest!
- pygame-ce: 2.5!

## パッと実行してみたい

```bash
docker compose up --build
# ブラウザで http://localhost:6080/vnc.html?autoconnect=1&resize=scale を開く
```

ブラウザの中にゲーム画面が出る。グレーの背景にひし形 10x5 マスの床下地と、ぴょこぴょこ動く水色の矢印が見えたら OK。
矢印キーで矢印を動かして、Z で床、A で椅子を置ける。
Docker の中では音は鳴らない (ブラウザ越しには音が届かないので)。止めるときは Ctrl+C。

![1](media/CHAIRS.jpg)

## Usage

    KEYS: ACTION
    Arrow keys: Move cursor
    Z: Put floor
    X: Remove item
    C: Roll item which will be put next time
    A: Put chair
    Alt+F4: Quit

    MOUSE: ACTION
    Left click: Z
    Middle click: A
    Right click: X
    Wheel up / down: Up / Down

## Docker なしで動かす

[uv](https://docs.astral.sh/uv/) があれば、ウィンドウで遊べて音も鳴る。

```bash
uv sync
uv run python ArrangementGameTry.py
```

## 開発

```bash
docker compose run --rm game ruff check .
docker compose run --rm game ruff format --check .
docker compose run --rm game pytest
```

テストは SDL の dummy ドライバで動くので、画面がなくても回る。
`tests/golden/original.png` は 2019 年のオリジナル版 (commit e815bd4) が描いた画面で、いまの実装が同じ絵を描けているかの見張り番。
