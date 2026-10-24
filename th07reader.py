"""th07 のプロセスメモリから値を読むクラス。

main.ipynb の get_xxx 関数群を1クラスにまとめたもの。
読み取りロジックは元のコードと同じで、以下だけ直している:
  - 反魂蝶判定で全項目が HANGONCHO_OFFSET_1 を読んでいたバグ
  - get_stage が th07stage.th07.STAGE_ADDR を参照していた点 (th07data に統一)
  - 難易度が想定外の値のとき KeyError で落ちる点
"""
from __future__ import annotations

from dataclasses import dataclass

import pymem

import th07data as d


@dataclass(frozen=True)
class GameState:
    difficulty: str
    character: str
    stage: int
    current_time: int      # ボス中は止まるフレームカウンター
    frame: int             # ボス中も動くフレームカウンター
    phase: int
    life: float
    cherry: int
    cherry_max: int
    cherry_plus: int
    prism: str | None
    hangoncho: tuple


class TH07Reader:
    def __init__(self, pm: pymem.Pymem):
        self.pm = pm

    # --- 基本情報 ---
    def difficulty(self) -> str:
        level = self.pm.read_int(d.DIFFICULTY_ADDR)
        return d.DIFFICULTY_ID_DIC.get(level, "UNKNOWN")

    def character(self) -> str:
        return d.CHARACTER_ID_DIC.get(self.pm.read_int(d.CHARACTER_ADDR), "UNKNOWN")

    def stage(self) -> int:
        return self.pm.read_int(d.STAGE_ADDR)

    def current_time(self) -> int:
        """ボス戦は基本ストップするフレームカウンター。
        早回しになるチルノ, 橙, リリーと(なぜか)レティは例外。"""
        return self.pm.read_int(d.FRAME_ADDR)

    def frame(self, timeline_index: int = 0) -> int:
        """ボス戦中も動作するフレームカウンター。"""
        enemy_manager = self.pm.read_uint(
            d.ENEMY_MANAGER_DRAW_HIGH_PRIO_CHAIN + d.CHAIN_ELEM_ARG_OFFSET
        )
        address = (
            enemy_manager
            + d.ENEMY_MANAGER_TIMELINES_OFFSET
            + timeline_index * d.ECL_TIMELINE_SIZE
            + d.ECL_TIMER_CURRENT_OFFSET
        )
        return self.pm.read_int(address)

    # --- ボス ---
    def phase(self) -> int:
        """ボスの残りフェーズ数。"""
        return self.pm.read_int(d.PHASE_ADDR)

    def life(self) -> float:
        """ボスの現在体力 0~1。"""
        return self.pm.read_float(d.LIFE_ADDR)

    # --- 桜 ---
    def cherry(self) -> tuple[int, int, int]:
        """(桜max, 桜, 桜+) を cherry_base からの相対値で返す。"""
        globals_address = self.pm.read_uint(d.GAME_MANAGER + d.GLOBALS_POINTER_OFFSET)
        cherry_base = self.pm.read_uint(globals_address + d.CHERRY_BASE_OFFSET)

        read = self.pm.read_uint
        cherry_max = read(d.GAME_MANAGER + d.CHERRY_MAX_OFFSET)
        cherry = read(d.GAME_MANAGER + d.CHERRY_OFFSET)
        cherry_plus = read(d.GAME_MANAGER + d.CHERRY_PLUS_OFFSET)
        return cherry_max - cherry_base, cherry - cherry_base, cherry_plus - cherry_base

    # --- ECL_MANAGER 経由 ---
    def _ecl_base(self) -> int:
        return self.pm.read_uint(d.ECL_MANAGER)

    def prism_river(self, base: int | None = None) -> str | None:
        """通常3, 2枚目のスペルカードで相手にしているプリズムリバー姉妹。"""
        base = self._ecl_base() if base is None else base
        return d.PRISM_RIVER_ID_DIC.get(self.pm.read_int(base + d.PRISM_OFFSET))

    def hangoncho_flags(self, base: int | None = None) -> tuple:
        """thprac機能で反魂蝶までスキップした時の判定用 (v1..v5)。"""
        base = self._ecl_base() if base is None else base
        readers = {"short": self.pm.read_short, "int": self.pm.read_int}
        return tuple(readers[kind](base + off) for off, kind in d.HANGONCHO_FIELDS)

    # --- まとめて取得 ---
    def snapshot(self) -> GameState:
        ecl_base = self._ecl_base()
        cherry_max, cherry, cherry_plus = self.cherry()
        return GameState(
            difficulty=self.difficulty(),
            character=self.character(),
            stage=self.stage(),
            current_time=self.current_time(),
            frame=self.frame(),
            phase=self.phase(),
            life=self.life(),
            cherry=cherry,
            cherry_max=cherry_max,
            cherry_plus=cherry_plus,
            prism=self.prism_river(ecl_base),
            hangoncho=self.hangoncho_flags(ecl_base),
        )
