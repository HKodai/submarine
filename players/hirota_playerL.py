import json
import os
import random
import socket
import sys

sys.path.append(os.getcwd())

from lib.player_base import Player
from hirotalib.chart import Chart
from hirotalib.util import make_initial


class HirotaPlayer(Player):

    def __init__(self):
        # フィールドを2x2の配列として持っている．
        self.field = [
            [i, j] for i in range(Player.FIELD_SIZE) for j in range(Player.FIELD_SIZE)
        ]
        ps = make_initial(self.field)
        positions = {"w": ps[0], "c": ps[1], "s": ps[2]}
        super().__init__(positions)

    def action(self, prob, score, enemy_range, hps):
        candidate = []  # 攻撃するマスの候補
        max_score = 0  # 射程内におけるスコアの最大値
        for x in range(Player.FIELD_SIZE):
            for y in range(Player.FIELD_SIZE):
                if not self.can_attack([x, y]):
                    continue
                if score[x][y] > max_score:
                    candidate = []
                    max_score = score[x][y]
                if score[x][y] == max_score:
                    candidate.append([x, y])
        # 射程内のスコアが全て0の場合
        if max_score == 0:
            # 自艦隊のhpが敵艦隊以下の場合
            if sum(hps["me"].values()) <= sum(hps["enemy"].values()):
                # 味方の艦がいる確率が最も高いマスに射撃(不用意に情報を与えないため)
                max_prob = 0
                for x in range(Player.FIELD_SIZE):
                    for y in range(Player.FIELD_SIZE):
                        if not self.can_attack([x, y]):
                            continue
                        prob_sum = sum(
                            [prob["me"][ship][x][y] for ship in self.ships.keys()]
                        )
                        if prob_sum >= max_prob:
                            to = [x, y]
                            max_prob = prob_sum
                return json.dumps(self.attack(to))
            # 自艦隊のhpが敵艦隊より多い場合
            else:
                # 敵の射程に入ろうとする
                max_prob = 0
                for ship in self.ships.values():
                    if ship.hp == 0:
                        continue
                    for x in range(Player.FIELD_SIZE):
                        for y in range(Player.FIELD_SIZE):
                            if (
                                not ship.can_reach([x, y])
                                or self.overlap([x, y]) is not None
                            ):
                                continue
                            if enemy_range[x][y] >= max_prob:
                                ship_type = ship.type
                                to = [x, y]
                                max_prob = enemy_range[x][y]
                return json.dumps(self.move(ship_type, to))
        return json.dumps(self.attack(random.choice(candidate)))


# 仕様に従ってサーバとソケット通信を行う．
def main(host, port):
    assert isinstance(host, str) and isinstance(port, int)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        completed = False
        with sock.makefile(mode="rw", buffering=1) as sockfile:
            while True:
                get_msg = sockfile.readline()
                print(get_msg)
                player = HirotaPlayer()
                chart = Chart(
                    {ship: player.ships[ship].position for ship in ["w", "c", "s"]}
                )
                sockfile.write(player.initial_condition() + "\n")

                while True:
                    info = sockfile.readline().rstrip()
                    print(info)
                    if info == "your turn":
                        prob, score, enemy_range = chart.info()
                        sockfile.write(
                            player.action(prob, score, enemy_range, chart.hps) + "\n"
                        )
                        get_msg = sockfile.readline()
                        player.update(get_msg)
                        chart.player_update(get_msg)
                    elif info == "waiting":
                        get_msg = sockfile.readline()
                        player.update(get_msg)
                        chart.enemy_update(get_msg)
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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sample Player for Submaline Game")
    parser.add_argument(
        "host",
        metavar="H",
        type=str,
        help="Hostname of the server. E.g., localhost",
    )
    parser.add_argument(
        "port",
        metavar="P",
        type=int,
        help="Port of the server. E.g., 2000",
    )
    args = parser.parse_args()

    main(args.host, args.port)
