"""th07 のステージ/ボス/スペルカード判定。

難易度ごとに違うのは主にスペル名(と一部の閾値)だけなので、
  - 判定ロジック: ステージごとに1関数 (_stage1 ~ _stage6, _extra_phantasm)
  - 難易度ごとの差分: SPELLS / EXTRA / PHANTASM のデータ
に分けてある。難易度を追加・修正するときはデータだけ触ればよい。

戻り値は (場所, スペル名) のタプル。判定対象外の状態では None を返す。
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# 共通定数
# ---------------------------------------------------------------------------
PRISM_BY_CHARACTER = {  # 通常1/2 で相手になるプリズムリバー姉妹
    '霊符': 'ルナサ', '夢符': 'ルナサ',
    '魔符': 'リリカ', '恋符': 'リリカ',
    '時符': 'メルラン', '幻符': 'メルラン',
}
PRISM_ALL = 'プリズムリバー三姉妹'
HANGONCHO_PATTERN = (0x9D7, 0x3E, 0, 0, 0)  # thprac で反魂蝶へスキップした時の値

# ---------------------------------------------------------------------------
# 難易度ごとのスペル名
# ---------------------------------------------------------------------------
SPELLS = {
    'Easy': {
        1: dict(chirno=None,
                letty1='寒符「リンガリングコールド -Easy-」',
                letty2='冬符「フラワーウィザラウェイ -Easy-」'),
        2: dict(mid='仙符「鳳凰卵 -Easy-」',
                p1='式符「飛翔晴明 -Easy-」',
                p0a='天符「天仙鳴動 -Easy-」',
                p0b='仙符「屍解永遠 -Easy-」'),
        3: dict(mid2=None,
                p2='蒼符「博愛の仏蘭西人形 -Easy-」',
                p1='紅符「紅毛の和蘭人形 -Easy-」',
                p0a='闇符「霧の倫敦人形 -Easy-」',
                p0b='咒詛「魔彩光の上海人形 -Easy-」'),
        4: dict(p2='騒符「ファントムディニング -Easy-」',
                p1={'ルナサ': '弦奏「グァルネリ・デル・ジェス -Easy-」',
                    'リリカ': '冥鍵「ファツィオーリ冥奏 -Easy-」',
                    'メルラン': '管霊「ヒノファンタズム -Easy-」'},
                p0a='合葬「プリズムコンチェルト -Easy-」',
                p0b='大合葬「霊車コンチェルトグロッソ -Easy-」'),
        5: dict(mid='幽鬼剣「妖童餓鬼の断食 -Easy-」',
                p2='獄界剣「二百由旬の一閃 -Easy-」',
                p1='畜趣剣「無為無策の冥罰 -Easy-」',
                p0a='人界剣「悟入幻想 -Easy-」',
                p0b='天上剣「天人の五衰 -Easy-」'),
        6: dict(boss_start=0x9DA,
                mid='六道剣「一念無量劫 -Easy-」',
                p4='亡郷「亡我郷 -さまよえる魂-」',
                p3='亡舞「生者必滅の理 -眩惑-」',
                p2='華霊「ゴーストバタフライ」',
                p1='幽曲「リポジトリ・オブ・ヒロカワ -偽霊-」',
                sakura='桜符「完全なる墨染の桜 -封印-」',
                hangoncho='「反魂蝶 -一分咲-」'),
    },
    'Normal': {
        1: dict(chirno=None,
                letty1='寒符「リンガリングコールド」',
                letty2='冬符「フラワーウィザラウェイ」'),
        2: dict(mid='仙符「鳳凰卵」',
                p1='式符「飛翔晴明」',
                p0a='天符「天仙鳴動」',
                p0b='仙符「屍解永遠」'),
        3: dict(mid2=None,
                p2='蒼符「博愛の仏蘭西人形」',
                p1='紅符「紅毛の和蘭人形」',
                p0a='闇符「霧の倫敦人形」',
                p0b='咒詛「魔彩光の上海人形」'),
        4: dict(p2='騒符「ファントムディニング」',
                p1={'ルナサ': '弦奏「グァルネリ・デル・ジェス」',
                    'リリカ': '冥鍵「ファツィオーリ冥奏」',
                    'メルラン': '管霊「ヒノファンタズム」'},
                p0a='合葬「プリズムコンチェルト」',
                p0b='大合葬「霊車コンチェルトグロッソ」'),
        5: dict(mid='幽鬼剣「妖童餓鬼の断食」',
                p2='獄界剣「二百由旬の一閃」',
                p1='畜趣剣「無為無策の冥罰」',
                p0a='人界剣「悟入幻想」',
                p0b='天上剣「天人の五衰」'),
        6: dict(boss_start=0x9DA,
                mid='六道剣「一念無量劫」',
                p4='亡郷「亡我郷 -宿罪-」',
                p3='亡舞「生者必滅の理 -死蝶-」',
                p2='華霊「スワローテイルバタフライ」',
                p1='幽曲「リポジトリ・オブ・ヒロカワ -亡霊-」',
                sakura='桜符「完全なる墨染の桜 -亡我-」',
                hangoncho='「反魂蝶 -参分咲-」'),
    },
    'Hard': {
        1: dict(chirno='霜符「フロストコラムス」',
                letty1='寒符「リンガリングコールド -Hard-」',
                letty2='白符「アンデュレイションレイ」'),
        2: dict(mid='仙符「鳳凰展翅」',
                p1='陰陽「道満晴明」',
                p0a='翔符「飛翔韋駄天」',
                p0b='鬼符「鬼門金神」'),
        3: dict(mid2=('アリス1', '操符「乙女文楽」'),  # ※ラベルが 'アリス1' (2回目なので 'アリス2' の誤記?)
                p2='蒼符「博愛のオルレアン人形」',
                p1='蒼符「博愛の仏蘭西人形 -Hard-」',
                p0a='廻符「輪廻の西蔵人形」',
                p0b='咒詛「魔彩光の上海人形 -Hard-」'),
        4: dict(p2='騒符「ライブポルターガイスト」',
                p1={'ルナサ': '神弦「ストラディヴァリウス」',
                    'リリカ': '鍵霊「ベーゼンドルファー神奏」',
                    'メルラン': '冥管「ゴーストクリフォード」'},
                p0a='騒葬「スティジャンリバーサイド」',
                p0b='大合葬「霊車コンチェルトグロッソ改」'),
        5: dict(mid='餓鬼剣「餓鬼道草紙」',
                p2='獄炎剣「業風閃影陣」',
                p1='修羅剣「現世妄執」',
                p0a='人世剣「大悟顕晦」',
                p0b='天界剣「七魄忌諱」'),
        6: dict(boss_start=0x9DA,
                mid='六道剣「一念無量劫 -Hard-」',
                p4='亡郷「亡我郷 -道無き道-」',
                p3='亡舞「生者必滅の理 -毒蛾-」',
                p2='華霊「ディープルーティドバタフライ」',
                p1='幽曲「リポジトリ・オブ・ヒロカワ -幻霊-」',
                sakura='桜符「完全なる墨染の桜 -春眠-」',
                hangoncho='「反魂蝶 -伍分咲-」'),
    },
    'Lunatic': {
        1: dict(chirno='霜符「フロストコラムス -Lunatic-」',
                letty1='寒符「リンガリングコールド -Lunatic-」',
                letty2='怪符「テーブルターニング」'),
        2: dict(mid='仙符「鳳凰展翅 -Lunatic-」',
                p1='陰陽「晴明大紋」',
                p0a='童符「護法天童乱舞」',
                p0b='方符「奇門遁甲」'),
        3: dict(mid2=('アリス1', '操符「乙女文楽 -Lunatic-」'),  # ※Hard と同じく 'アリス1'
                p2='蒼符「博愛のオルレアン人形」',
                p1='白符「白亜の露西亜人形 -Lunatic-」',
                p0a='雅符「春の京人形」',
                p0b='咒詛「首吊り蓬莱人形」'),
        4: dict(p2='騒符「ライブポルターガイスト -Lunatic-」',
                p1={'ルナサ': '偽弦「スードストラディヴァリウス」',
                    'リリカ': '鍵霊「ベーゼンドルファー神奏 -Lunatic-」',
                    'メルラン': '管霊「ゴーストクリフォード -Lunatic-」'},
                p0a='騒葬「スティジャンリバーサイド -Lunatic-」',
                p0b='大合葬「霊車コンチェルトグロッソ怪」'),
        5: dict(mid='餓王剣「餓鬼十王の報い」',
                p2='獄神剣「業風神閃斬」',
                p1='修羅剣「現世妄執 -Lunatic-」',
                p0a='人神剣「俗諦常住」',
                p0b='天神剣「三魂七魄」'),
        6: dict(boss_start=0x9D8,  # ※他難易度は 0x9DA
                mid='六道剣「一念無量劫 -Lunatic-」',
                p4='亡郷「亡我郷 -自尽-」',
                p3='亡舞「生者必滅の理 -魔境-」',
                p2='華霊「バタフライディルージョン」',
                p1='幽曲「リポジトリ・オブ・ヒロカワ -神霊-」',
                sakura='桜符「完全なる墨染の桜 -開花-」',
                hangoncho='「反魂蝶 -八分咲-」'),
    },
}

# Extra / Phantasm: ステージ区別なし。
#   mid_start / boss_start : 中ボス登場フレーム / ボス戦開始フレーム
#   mid_*                  : 中ボス(名前, 通常→スペルの体力閾値, phase==1 のスペル, それ以外のスペル)
#   phases                 : {残りフェーズ: (通常→スペルの体力閾値, スペル名)}
#                            閾値が None のフェーズは通常攻撃なしで常にスペル
#   通常攻撃のラベルは first_normal_phase から数えて「通常1, 通常2, ...」
EXTRA = dict(
    mid_start=0xFE4, boss_start=0x2261,
    mid_name='橙', mid_threshold=0.14814814925193787,
    mid_spell1='鬼符「青鬼赤鬼」', mid_spell0='鬼神「飛翔毘沙門天」',
    boss='八雲藍',
    phases={
        9: (0.12999999523162842, '式神「仙狐思念」'),
        8: (0.11999999731779099, '式神「十二神将の宴」'),
        7: (0.10000000149011612, '式輝「狐狸妖怪レーザー」'),
        6: (0.14000000059604645, '式輝「四面楚歌チャーミング」'),
        5: (0.07000000029802322, '式輝「プリンセス天狐 -Illusion-」'),
        4: (0.13500000536441803, '式弾「アルティメットブディスト」'),
        3: (0.13500000536441803, '式弾「ユーニラタルコンタクト」'),
        2: (0.15000000596046448, '式神「橙」'),
    },
    first_normal_phase=9,
    spell_phase1='「狐狗狸さんの契約」', spell_phase0='幻神「飯綱権現降臨」',
)
PHANTASM = dict(
    mid_start=0xF80, boss_start=0x242E,
    mid_name='八雲藍', mid_threshold=0.14814814925193787,
    mid_spell1='式神「前鬼後鬼の守護」', mid_spell0='式神「憑依荼吉尼天」',
    boss='八雲紫',
    phases={
        10: (0.12999999523162842, '結界「夢と現の呪」'),
        9: (0.09444444626569748, '結界「動と静の均衡」'),
        8: (0.11999999731779099, '結界「光と闇の網目」'),
        7: (0.14000000059604645, '罔両「ストレートとカーブの夢郷」'),
        6: (0.07000000029802322, '罔両「八雲紫の神隠し」'),
        5: (0.13500000536441803, '罔両「禅寺に棲む妖蝶」'),
        4: (0.13500000536441803, '魍魎「二重黒死蝶」'),
        3: (0.10000000149011612, '式神「八雲藍」'),
        2: (None, '「人間と妖怪の境界」'),
    },
    first_normal_phase=10,
    spell_phase1='結界「生と死の境界」', spell_phase0='紫奥義「弾幕結界」',
)


# ---------------------------------------------------------------------------
# 判定ロジック
# ---------------------------------------------------------------------------
def _pick(life, threshold, normal, spell):
    """体力が閾値より多ければ通常攻撃、以下ならスペル。"""
    return normal if life > threshold else spell


def _stage1(timer, phase, life, sp, **_):
    if timer < 0x0A60:
        return ('道中前半', '')
    elif 0x0A60 <= timer <= 0xF5B and life > 0:
        if sp['chirno'] is None:
            return ('チルノ', '通常')
        return ('チルノ', _pick(life, 0.11999999731779099, '通常', sp['chirno']))
    elif 0x0A60 < timer < 0x13B5 and life == 0:
        return ('道中後半', '')
    elif phase == 1:
        return ('レティ', _pick(life, 0.1133333370089531, '通常1', sp['letty1']))
    else:
        return ('レティ', _pick(life, 0.13333334028720856, '通常2', sp['letty2']))


def _stage2(timer, phase, life, sp, **_):
    if timer < 0xB0A:
        return ('道中前半', '')
    elif 0xB0A <= timer < 0x1DE2 and life > 0.14482758939266205:
        return ('橙', '通常')
    elif 0xB0A <= timer < 0x1DE2 and 0 < life <= 0.14482758939266205:
        return ('橙', sp['mid'])
    elif 0xB0A < timer < 0x1DE2:
        return ('道中後半', '')
    elif phase == 1:
        return ('橙', _pick(life, 0.0882352963089943, '通常1', sp['p1']))
    elif phase == 0:
        if life > 0.2230769246816635:
            return ('橙', '通常2')
        elif 0.10769230872392654 < life <= 0.2230769246816635:
            return ('橙', sp['p0a'])
        else:
            return ('橙', sp['p0b'])
    return None


def _stage3(timer, phase, life, sp, **_):
    if timer < 0x356:
        return ('道中1', '')
    elif timer == 0x356:
        return ('アリス1', '通常')
    elif 0x356 < timer < 0x742:
        return ('道中2', '')
    elif timer == 0x743:
        if sp['mid2'] is None or life > 0.08571428805589676:
            return ('アリス2', '通常')
        return sp['mid2']
    elif 0x743 < timer <= 0xD42:
        return ('道中3', '')
    elif phase == 2:
        return ('アリス', _pick(life, 0.10526315867900848, '通常1', sp['p2']))
    elif phase == 1:
        return ('アリス', sp['p1'])
    elif life > 0.17599999904632568:
        return ('アリス', '通常3')
    elif 0.07999999821186066 < life <= 0.17599999904632568:
        return ('アリス', sp['p0a'])
    else:
        return ('アリス', sp['p0b'])


def _stage4(timer, phase, life, sp, character=None, prism=None, **_):
    if timer < 0x1BD2:
        return ('道中前半', '')
    elif 0x1BD2 <= timer <= 0x3A46 and life > 0:
        return ('リリー', '通常')
    elif 0x1BD2 < timer <= 0x3A46:
        return ('道中後半', '')
    elif phase == 3:
        boss = PRISM_BY_CHARACTER.get(character)
        return (boss, '通常1') if boss else None
    elif phase == 2:
        if life > 0.12894736230373383:
            boss = PRISM_BY_CHARACTER.get(character)
            return (boss, '通常2') if boss else None
        return (PRISM_ALL, sp['p2'])
    elif phase == 1:
        if prism in sp['p1']:
            return (prism, _pick(life, 0.10499999672174454, '通常3', sp['p1'][prism]))
        return None
    else:
        return (PRISM_ALL, _pick(life, 0.4615384638309479, sp['p0a'], sp['p0b']))


def _stage5(timer, phase, life, sp, **_):
    if timer < 0x12D7:
        return ('道中前半', '')
    elif timer == 0x12D7:
        return ('妖夢', _pick(life, 0.10000000149011612, '通常', sp['mid']))
    elif 0x12D7 < timer <= 0x17E2:
        return ('道中後半', '')
    elif phase == 2:
        return ('妖夢', _pick(life, 0.10526315867900848, '通常1', sp['p2']))
    elif phase == 1:
        return ('妖夢', _pick(life, 0.13326667249202728, '通常2', sp['p1']))
    else:
        return ('妖夢', _pick(life, 0.4502272605895996, sp['p0a'], sp['p0b']))


def _stage6(timer, phase, life, sp, hangoncho=(), **_):
    if timer < 0x77D:
        return ('道中前半', '')
    elif timer == 0x77D:
        return ('妖夢', _pick(life, 0.10000000149011612, '通常', sp['mid']))
    elif 0x77D < timer <= 0x9D7:
        return ('道中後半', '')
    elif sp['boss_start'] <= timer:
        if phase == 4:
            return ('幽々子', _pick(life, 0.10000000149011612, '通常1', sp['p4']))
        elif phase == 3:
            return ('幽々子', _pick(life, 0.09375, '通常2', sp['p3']))
        elif phase == 2:
            return ('幽々子', _pick(life, 0.09375, '通常3', sp['p2']))
        elif phase == 1:
            return ('幽々子', _pick(life, 0.10000000149011612, '通常4', sp['p1']))
        elif tuple(hangoncho) == HANGONCHO_PATTERN:
            return ('幽々子', sp['hangoncho'])
        else:
            return ('幽々子', _pick(life, 0.00016666666488163173, sp['sakura'], sp['hangoncho']))
    return None


_STAGES = {1: _stage1, 2: _stage2, 3: _stage3, 4: _stage4, 5: _stage5, 6: _stage6}


def _extra_phantasm(timer, phase, life, cfg):
    """Extra / Phantasm 共通: 中ボス(橙/藍) → ボス(藍/紫)。"""
    if timer < cfg['mid_start']:
        return ('道中前半', '')
    elif timer == cfg['mid_start']:
        if phase == 1:
            return (cfg['mid_name'],
                    _pick(life, cfg['mid_threshold'], '通常', cfg['mid_spell1']))
        return (cfg['mid_name'], cfg['mid_spell0'])
    elif cfg['mid_start'] < timer < cfg['boss_start']:
        return ('道中後半', '')

    boss, phases = cfg['boss'], cfg['phases']
    if phase in phases:
        threshold, spell = phases[phase]
        if threshold is None:
            return (boss, spell)
        normal = f"通常{cfg['first_normal_phase'] - phase + 1}"
        return (boss, _pick(life, threshold, normal, spell))
    if phase == 1:
        return (boss, cfg['spell_phase1'])
    return (boss, cfg['spell_phase0'])


def th07(difficulty_level, stage, timer, phase, life, character, prism,
         v1, v2, v3, v4, v5):
    """
    difficulty_level: 難易度 str
    stage: ステージ番号 int
    timer: フレーム数 int
    phase: ボス中の残りフェーズ数 int
    life: ボスの体力 float
    character: 自機 str
    prism: 虹川の相手 str | None
    v1..v5: 反魂蝶のプラかどうかの判定パラメータ
    """
    if difficulty_level == 'Extra':
        return _extra_phantasm(timer, phase, life, EXTRA)
    if difficulty_level == 'Phantasm':
        return _extra_phantasm(timer, phase, life, PHANTASM)

    sp = SPELLS.get(difficulty_level, {}).get(stage)
    if sp is None:
        return None
    return _STAGES[stage](timer, phase, life, sp, character=character,
                          prism=prism, hangoncho=(v1, v2, v3, v4, v5))
