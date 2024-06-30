# 変更点
loopserver.rbを追加しました。基本的には公式のサーバと同じですが、回数をnオプションで指定して連戦できます。
```
$ ruby source/loopserver.rb -n 5
```
nオプションをつけなければ1回対戦します。

rオプションをつけると先攻を毎回ランダムに決めます。
```
$ ruby source/loopserver.rb -r -n 10
```
rオプションをつけなければ、前半は先に接続したプレイヤー(player1)が先攻となり、後半は後から接続したプレイヤー(player2)が先攻となります。

ポート番号はデフォルトで2000なのでコマンドライン引数で指定する必要はありません(公式と同じ仕様です)。

既存のオプションについても、ショートオプションと説明を追加しました。詳細は以下のコマンドで確認できます。
```
$ ruby source/loopserver.rb -h
```
Pythonのプレイヤーがこのサーバを利用するには、main関数を以下の通りに書き換えてください(プレイヤーのクラス名は適宜変更してください)。
```
def main(host, port, seed=0):
    assert isinstance(host, str) and isinstance(port, int)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        completed = False
        with sock.makefile(mode="rw", buffering=1) as sockfile:
            while True:
                get_msg = sockfile.readline()
                print(get_msg)
                player = RandomPlayer()
                sockfile.write(player.initial_condition() + "\n")

                while True:
                    info = sockfile.readline().rstrip()
                    print(info)
                    if info == "your turn":
                        sockfile.write(player.action() + "\n")
                        get_msg = sockfile.readline()
                        player.update(get_msg)
                    elif info == "waiting":
                        get_msg = sockfile.readline()
                        player.update(get_msg)
                    elif info == "you win":
                        break
                    elif info == "you lose":
                        break
                    elif info == "even":
                        break
                    elif info == "you win.":
                        completed = True
                        break
                    elif info == "you lose.":
                        completed = True
                        break
                    elif info == "even.":
                        completed = True
                        break
                    else:
                        raise RuntimeError("unknown information")
                if completed:
                    for _ in range(5):
                        info = sockfile.readline()
                        print(info, end="")
                    break
```
manual_player.rbに対応するコードは準備中ですm(_ _)m

# submarine_game
人やAIが対戦できる潜水艦ゲーム。 
クライアントプログラム作成用の詳しい仕様は[こちら](/doc/document.md)

## ルール
1. 各プレイヤーはそれぞれ5x5のマス目上に戦艦、巡洋艦、潜水艦を配置する。位置は相手に伝えない。自分の艦同士を同じ場所に配置してはいけない。
2. 先行後攻を決める。
3. 手番が回ってきたプレイヤーは艦の移動か攻撃を行える。
    * 移動：自分の艦1隻を縦横のどちらかにいくらでも動かすことができる。ただし、自分の他の艦がいる場所には動かせない。相手の艦と位置が重複してしまっても構わない。移動を行った場合はどの艦をどちらに何マス動かしたかを報告する。
    * 攻撃：自分の艦がいる位置及び周囲1マスを攻撃することができる。この際どのマスを攻撃するかだけを報告すれば良い。攻撃を受けたプレイヤーはマス目を調べる。自分の艦があれば耐久力を1減らし艦種と命中したことを報告する。耐久力が0になった艦は沈没し、今後ゲームには登場しない。耐久力は戦艦3、巡洋艦2、潜水艦1である。攻撃対象が自分の艦の周囲1マスであった場合はその艦の名前を報告する。
4. 以上をいずれかのプレイヤーの艦が全て沈没するまで繰り返す。最後まで艦が残っていたプレイヤーが勝利する。

## ディレクトリ構成
[/doc](/doc) ドキュメント 
[/source](/source) サーバのプログラム 
[/players](/players) AIのプログラム 
[/lib](/lib) AIで共通に使う処理のライブラリ 


## 実行
- サーバー, マニュアルプレイヤー: ruby >= 2.0
- ランダムプレイヤー: python >= 3.5

まずポート番号を指定してサーバを起動する。
```
$ ruby source/server.rb 2000
```
サーバをつけたら、アドレスとポート番号を指定してクライアントを起動する。
```
$ python3 players/random_player.py localhost 2000
```
二つクライアントプログラムが繋がったらゲームが開始する。 
人間プレイ用に[manual_player.rb](/players/manual_player.rb)が用意してある。ターミナル上でキー入力をして行動を指示する。以下のような感じなのでターミナルを広めにして起動したほうが良い。 
マスには艦の種類のアルファベット1文字と、残りHPが表示される。自分あるいは相手が攻撃したマスには!がつく。その他相手の行動やHPなどの情報はテキストで出力される。 
```
$ ruby players/manual_player.rb localhost 2000
you are connected. please send me initial state.
please input x, y in 0 ~ 4
w
x = 0
y = 0
c
x = 4
y = 4
s
x = 2
y = 2
   | 0 | 1 | 2 | 3 | 4 |
------------------------
 0 | w3|   |   |   |   |
------------------------
 1 |   |   |   |   |   |
------------------------
 2 |   |   | s1|   |   |
------------------------
 3 |   |   |   |   |   |
------------------------
 4 |   |   |   |   | c2|
------------------------

waiting
enemy attacked [3, 4] near ["c"]
enemy ships: w:3 c:2 s:1
   | 0 | 1 | 2 | 3 | 4 |
------------------------
 0 | w3|   |   |   |   |
------------------------
 1 |   |   |   |   |   |
------------------------
 2 |   |   | s1|   |   |
------------------------
 3 |   |   |   |   |   |
------------------------
 4 |   |   |   |!  | c2|
------------------------

your turn
select your action:
m: move
a: attack
please input "a" or "m"
a
x = 3
y = 3
you attacked [3, 3] near ["w", "c"]
enemy ships: w:3 c:2 s:1
   | 0 | 1 | 2 | 3 | 4 |
------------------------
 0 | w3|   |   |   |   |
------------------------
 1 |   |   |   |   |   |
------------------------
 2 |   |   | s1|   |   |
------------------------
 3 |   |   |   |!  |   |
------------------------
 4 |   |   |   |   | c2|
------------------------

```
