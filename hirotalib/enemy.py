import json
import itertools


# 敵の情報を表すクラス
class Enemy:
    FIELD_SIZE = 5

    # ありうる初期状態を全て列挙する。
    def __init__(self):
        self.charts = []
        coordinates = [(x, y) for x in range(Enemy.FIELD_SIZE) for y in range(Enemy.FIELD_SIZE)]
        for w, c, s in itertools.permutations(coordinates, 3):
            self.charts.append({"w": w, "c": c, "s": s})
        self.hps = {"w": 3, "c": 2, "s": 1}

    # プレイヤーの攻撃を反映する。
    def player_attack(self, position, hit, near_list):
        new_charts = []  # 次の状態
        for chart in self.charts:
            ok = True
            # 命中した場合
            if hit != None:
                # 命中した位置に敵艦がいなければ矛盾
                if chart[hit] != tuple(position):
                    ok = False
                # 撃沈した場合は海図から削除する。
                elif self.hps[hit] == 1:
                    del chart[hit]
            # 近傍にいる敵艦について
            for ship in near_list:
                # 近傍にいなければ矛盾
                if abs(chart[ship][0]-position[0]) > 1 or abs(chart[ship][1]-position[1]) > 1:
                    ok = False
                    break
            if ok:
                new_charts.append(chart)
        self.charts = new_charts

    # 敵の攻撃を反映する。
    def enemy_attack(self, position):
        new_charts = []  # 次の状態
        for chart in self.charts:
            for pos in chart.values():
                # 撃たれた位置の近傍にいずれかの敵艦がいればよい
                if abs(pos[0]-position[0]) <= 1 and abs(pos[1]-position[1]) <= 1:
                    new_charts.append(chart)
                    break
        self.charts = new_charts

    # 敵の移動を反映する。
    def enemy_move(self, ship, distance):
        new_charts = []  # 次の状態
        for chart in self.charts:
            x = chart[ship][0] + distance[0]  # 進んだ先の座標
            y = chart[ship][1] + distance[1]
            # はみ出さないかチェック
            if 0 <= x < Enemy.FIELD_SIZE and 0 <= y < Enemy.FIELD_SIZE:
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
        self.charts = new_charts

    # プレイヤーの手番に通知された情報で状態を更新する。
    def player_update(self, json_):
        if "result" in json.loads(json_):
            result = json.loads(json_)["result"]
            if "attacked" in result:
                attacked = result["attacked"]
                position = attacked["position"]
                hit = attacked["hit"] if "hit" in attacked else None
                near = attacked["near"] if "near" in attacked else []
                self.player_attack(position, hit, near)
        enemy_condition = json.loads(json_)["condition"]["enemy"]
        for ship in self.hps.keys():
            if ship in enemy_condition:
                self.hps[ship] = enemy_condition[ship]["hp"]
            else:
                self.hps[ship] = 0

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

    # 各マスに敵艦がいる確率
    def probability(self):
        prob = [[0 for _ in range(Enemy.FIELD_SIZE)] for _ in range(Enemy.FIELD_SIZE)]
        for chart in self.charts:
            for pos in chart.values():
                prob[pos[0]][pos[1]] += 1
        return prob


if __name__ == "__main__":
    enemy = Enemy()
