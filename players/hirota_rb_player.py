import json
import os
import random
import socket
import sys

sys.path.append(os.getcwd())

from lib.player_base import Player
from hirotalib.chart import Chart
from hirotalib.util import make_initial


class HirotaRB(Player):

    def __init__(self):
        # フィールドを2x2の配列として持っている．
        self.field = [
            [i, j] for i in range(Player.FIELD_SIZE) for j in range(Player.FIELD_SIZE)
        ]
        ps = make_initial(self.field)
        positions = {"w": ps[0], "c": ps[1], "s": ps[2]}
        super().__init__(positions)

    def action(self, score, enemy_range):
        # act = random.choice(["move", "attack"])
        act = "attack"

        if act == "move":
            ship = random.choice(list(self.ships.values()))
            to = random.choice(self.field)
            while not ship.can_reach(to) or not self.overlap(to) is None:
                to = random.choice(self.field)
            return json.dumps(self.move(ship.type, to))

        elif act == "attack":
            candidate = []  # 攻撃対象の候補
            max_score = 0  # 射程内における敵艦がいる確率の最大値
            for x in range(Player.FIELD_SIZE):
                for y in range(Player.FIELD_SIZE):
                    if not self.can_attack([x, y]):
                        continue
                    if score[x][y] > max_score:
                        candidate = []
                        max_score = score[x][y]
                    if score[x][y] == max_score:
                        candidate.append([x, y])
            to = random.choice(candidate)

            return json.dumps(self.attack(to))


# 仕様に従ってサーバとソケット通信を行う．
def main(host, port):
    assert isinstance(host, str) and isinstance(port, int)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        with sock.makefile(mode="rw", buffering=1) as sockfile:
            get_msg = sockfile.readline()
            print(get_msg)
            player = HirotaRB()
            chart = Chart()
            sockfile.write(player.initial_condition() + "\n")

            while True:
                info = sockfile.readline().rstrip()
                print(info)
                if info == "your turn":
                    score, enemy_range = chart.info()
                    sockfile.write(player.action(score, enemy_range) + "\n")
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
                else:
                    raise RuntimeError("unknown information")


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
