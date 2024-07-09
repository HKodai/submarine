import json
import itertools
import seaborn as sns
import matplotlib.pyplot as plt
import sys
import os

sys.path.append(os.getcwd())
from hirotalib.util import near


# 自分と敵が得ている情報(海図)を管理するクラス
class Chart:
    FIELD_SIZE = 5
    SHIPS = ["w", "c", "s"]

    # ありうる初期状態を全て列挙する。
    def __init__(self):
        self.my_charts = []
        self.enemy_charts = []
        coordinates = [
            (x, y) for x in range(Chart.FIELD_SIZE) for y in range(Chart.FIELD_SIZE)
        ]
        for w, c, s in itertools.permutations(coordinates, 3):
            self.my_charts.append({"w": w, "c": c, "s": s})
            self.enemy_charts.append({"w": w, "c": c, "s": s})
        self.enemy_hps = {"w": 3, "c": 2, "s": 1}

    # 自分の攻撃を反映する。
    def my_attack(self, position, hit, near_list):
        # 敵の海図を更新
        new_charts = []  # 次の状態
        for chart in self.enemy_charts:
            ok = True
            # 命中した場合
            if hit is not None:
                # 命中した位置に該当する敵艦がいなければ矛盾
                if chart[hit] != tuple(position):
                    ok = False
                # 撃沈した場合は海図から削除する。
                elif self.enemy_hps[hit] == 1:
                    del chart[hit]
            # 命中しなかった場合
            else:
                # 撃った位置に敵艦がいれば矛盾
                for pos in chart.values():
                    if pos == tuple(position):
                        ok = False
                        break
                # near_listとの整合性を確認する。
                for ship in chart.keys():
                    if (ship in near_list) != near(chart[ship], position):
                        ok = False
                        break
            if ok:
                new_charts.append(chart)
        self.enemy_charts = new_charts

    # 自分の移動を反映する。
    def my_move(self, ship, distance):
        pass

    # 敵の攻撃を反映する。
    def enemy_attack(self, position):
        # 敵の海図を更新
        new_charts = []  # 次の状態
        for chart in self.enemy_charts:
            for pos in chart.values():
                # 撃たれた位置の近傍にいずれかの敵艦がいればよい
                if abs(pos[0] - position[0]) <= 1 and abs(pos[1] - position[1]) <= 1:
                    new_charts.append(chart)
                    break
        self.enemy_charts = new_charts

    # 敵の移動を反映する。
    def enemy_move(self, ship, distance):
        # 敵の海図を更新
        new_charts = []  # 次の状態
        for chart in self.enemy_charts:
            x = chart[ship][0] + distance[0]  # 進んだ先の座標
            y = chart[ship][1] + distance[1]
            # はみ出さないかチェック
            if 0 <= x < Chart.FIELD_SIZE and 0 <= y < Chart.FIELD_SIZE:
                # 他の敵艦と衝突しないかチェック
                ok = True
                for pos in chart.values():
                    if pos == (x, y):
                        ok = False
                        break
                if ok:
                    # 敵艦の位置を更新する。
                    chart[ship] = (x, y)
                    new_charts.append(chart)
        self.enemy_charts = new_charts

    # プレイヤーの手番に通知された情報で状態を更新する。
    def player_update(self, json_):
        if "result" in json.loads(json_):
            result = json.loads(json_)["result"]
            if "attacked" in result:
                attacked = result["attacked"]
                position = attacked["position"]
                hit = attacked["hit"] if "hit" in attacked else None
                near = attacked["near"] if "near" in attacked else []
                self.my_attack(position, hit, near)
        enemy_condition = json.loads(json_)["condition"]["enemy"]
        for ship in self.enemy_hps.keys():
            if ship in enemy_condition:
                self.enemy_hps[ship] = enemy_condition[ship]["hp"]
            else:
                self.enemy_hps[ship] = 0

    # 相手の手番に通知された情報で状態を更新する。
    def enemy_update(self, json_):
        if "result" in json.loads(json_):
            result = json.loads(json_)["result"]
            if "attacked" in result:
                position = result["attacked"]["position"]
                self.enemy_attack(position)
            if "moved" in result:
                ship = result["moved"]["ship"]
                distance = result["moved"]["distance"]
                self.enemy_move(ship, distance)

    # 各マスについて、敵艦がいる確率、スコア(確率/hp)、敵の射程内である確率を計算
    def info(self):
        ship_probs = {
            ship: [
                [0 for _ in range(Chart.FIELD_SIZE)] for _ in range(Chart.FIELD_SIZE)
            ]
            for ship in Chart.SHIPS
        }
        score = [[0 for _ in range(Chart.FIELD_SIZE)] for _ in range(Chart.FIELD_SIZE)]
        enemy_range = [
            [0 for _ in range(Chart.FIELD_SIZE)] for _ in range(Chart.FIELD_SIZE)
        ]
        for chart in self.enemy_charts:
            for ship, pos in chart.items():
                ship_probs[ship][pos[0]][pos[1]] += 1
                score[pos[0]][pos[1]] += 1 / self.enemy_hps[ship]
            for x in range(Chart.FIELD_SIZE):
                for y in range(Chart.FIELD_SIZE):
                    for pos in chart.values():
                        if abs(x - pos[0]) <= 1 and abs(y - pos[1]) <= 1:
                            enemy_range[x][y] += 1
                            break
        n = len(self.enemy_charts)
        for x in range(Chart.FIELD_SIZE):
            for y in range(Chart.FIELD_SIZE):
                for ship in Chart.SHIPS:
                    ship_probs[ship][x][y] /= n
                score[x][y] /= n
                enemy_range[x][y] /= n
        plt.figure(figsize=(9, 6))
        plt.subplots_adjust(wspace=0.2, hspace=0.3)
        plt.subplot(2, 3, 1)
        sns.heatmap(
            [list(x) for x in zip(*ship_probs["w"])],
            annot=True,
            cbar=False,
            cmap="Reds",
            vmin=0,
            vmax=1,
        )
        plt.title("warship")
        plt.subplot(2, 3, 2)
        sns.heatmap(
            [list(x) for x in zip(*ship_probs["c"])],
            annot=True,
            cbar=False,
            cmap="Reds",
            vmin=0,
            vmax=1,
        )
        plt.title("cruiser")
        plt.subplot(2, 3, 3)
        sns.heatmap(
            [list(x) for x in zip(*ship_probs["s"])],
            annot=True,
            cbar=False,
            cmap="Reds",
            vmin=0,
            vmax=1,
        )
        plt.title("submarine")
        plt.subplot(2, 3, 4)
        sns.heatmap(
            [list(x) for x in zip(*score)],
            annot=True,
            cbar=False,
            cmap="Reds",
            vmin=0,
            vmax=1,
        )
        plt.title("score")
        plt.subplot(2, 3, 5)
        sns.heatmap(
            [list(x) for x in zip(*enemy_range)],
            annot=True,
            cbar=False,
            cmap="Reds",
            vmin=0,
            vmax=1,
        )
        plt.title("enemy_range")
        plt.show()
        return score, enemy_range
