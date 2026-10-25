"""th07 のメモリを監視して log.csv に記録する。

使い方:  python main.py            (Ctrl+C で終了)
"""
from __future__ import annotations

import csv
import datetime
import os
import time
from pathlib import Path

import pymem
import pymem.exception

from th07reader import GameState, TH07Reader

from th07stage import th07  # ステージ/ボス名の判定ロジック


PROCESS_NAME = "th07.exe"
LOG_PATH = Path("log.csv")
LOG_ENCODING = "utf-8-sig"       # Excelで開いても文字化けしない
POLL_INTERVAL = 0.1              # 秒
RECONNECT_INTERVAL = 1.0         # 秒
MAX_CONSECUTIVE_ERRORS = 50      # これ以上連続で読めなかったら再アタッチ

HEADER = ["DateTime", "frame1", "frame2", "difficulty", "stage",
          "cherry", "cherry_max", "cherry_plus", "place", "phase", 'miss', 'bomb', 'score']

READ_ERRORS = (pymem.exception.WinAPIError, pymem.exception.MemoryReadError)


def attach(process_name: str = PROCESS_NAME) -> pymem.Pymem:
    """th07 が起動するまで待ってアタッチする。"""
    while True:
        try:
            pm = pymem.Pymem(process_name)
            print(f"{process_name}にアタッチ成功")
            return pm
        except pymem.exception.ProcessNotFound:
            print(f"{process_name}の起動待ち...", end="\r", flush=True)
            time.sleep(RECONNECT_INTERVAL)


def open_log(path: Path):
    """ログを追記モードで開く。新規ならヘッダーを書く。"""
    is_new = not path.exists() or path.stat().st_size == 0
    f = open(path, "a", encoding=LOG_ENCODING, newline="")
    writer = csv.writer(f)
    if is_new:
        writer.writerow(HEADER)
        f.flush()
    return f, writer


def render(s: GameState, p1, p2) -> str:
    return (
        f"frame:{s.current_time}\nStage:{s.stage}\n"
        f"cherry:{s.cherry}\ncherryMax:{s.cherry_max}\ncherry+:{s.cherry_plus}\n"
        f"{p1}\n{p2}\nmiss:{s.life}\nbomb:{s.bomb_used}\nscore:{s.score*10}"
    )


def main() -> None:
    os.system("")  # Windows で ANSI エスケープを有効化
    pm = attach()
    reader = TH07Reader(pm)

    log_file, writer = open_log(LOG_PATH)
    errors = 0
    previous = None
    try:
        while True:
            try:
                s = reader.snapshot()  # 難易度・キャラも毎回読む (別プレイに切替わっても追従)
            except READ_ERRORS:
                errors += 1
                if errors >= MAX_CONSECUTIVE_ERRORS:
                    print("\nゲームとの接続が切れました。再接続します...")
                    pm = attach()
                    reader = TH07Reader(pm)
                    errors = 0
                time.sleep(POLL_INTERVAL)
                continue
            errors = 0

            # th07() は対象外の状態(タイトル画面・ステージ0など)だと None を返す
            p1, p2 = th07(s.difficulty, s.stage, s.current_time, s.phase, s.life,
                          s.character, s.prism, *s.hangoncho) or ("UNKNOWN", "")

            print("\033[H\033[J" + render(s, p1, p2), flush=True)
            
            # 前の状態と比較して同じであれば記録は残さない
            # ポーズ放置の対策
            if previous != s:
                writer.writerow([
                    datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f"),
                    s.current_time, s.frame, s.difficulty, s.stage,
                    s.cherry, s.cherry_max, s.cherry_plus, p1, p2,
                    s.miss_count, s.bomb_used, s.score
                ])
                log_file.flush()
                previous = s

            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n終了します。")
    finally:
        log_file.close()


if __name__ == "__main__":
    main()
