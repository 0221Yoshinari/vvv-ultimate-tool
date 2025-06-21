import streamlit as st
from scipy.stats import poisson

# --- 定義データ ---
# 各設定ごとのスペック・確率情報
# 数値は全て1/X.Xの場合のX.X、または%の場合の小数（例: 0.27%は0.0027）
GAME_DATA = {
    "ボーナス初当り確率": {1: 519.0, 2: 516.0, 3: 514.0, 4: 507.0, 5: 499.0, 6: 490.0}, # 革命/決戦ボーナス合算
    "CZ_共闘Vチャレンジ_出現率": {1: 277.0, 2: 275.0, 3: 274.0, 4: 269.0, 5: 264.0, 6: 258.0},
    "ハラキリドライブ発生率": {1: 0.06, 2: 0.095, 3: 0.13, 4: 0.165, 5: 0.20, 6: 0.25}, # %表記
    "超革命ラッシュ_セットゲーム_10G": {1: 0.583, 2: 0.540, 3: 0.498, 4: 0.458, 5: 0.419, 6: 0.375}, # %表記
    "超革命ラッシュ_セットゲーム_20G": {1: 0.357, 2: 0.365, 3: 0.372, 4: 0.377, 5: 0.381, 6: 0.375}, # %表記
    "超革命ラッシュ_セットゲーム_50G": {1: 0.035, 2: 0.076, 3: 0.098, 4: 0.118, 5: 0.133, 6: 0.150}, # %表記
    "超革命ラッシュ_セットゲーム_100G": {1: 0.025, 2: 0.019, 3: 0.032, 4: 0.047, 5: 0.067, 6: 0.100}, # %表記
    "有利区間切断時ハラキリドライブ発生率": {1: 0.08, 2: 0.15, 3: 0.30, 4: 0.55, 5: 0.70, 6: 0.85}, # %表記
    "通常時モード比率_モードA": {1: 0.40, 2: 0.35, 3: 0.30, 4: 0.25, 5: 0.20, 6: 0.15}, # %表記
    "通常時モード比率_モードB": {1: 0.35, 2: 0.37, 3: 0.39, 4: 0.41, 5: 0.43, 6: 0.45}, # %表記
    "通常時モード比率_モードC": {1: 0.20, 2: 0.20, 3: 0.20, 4: 0.20, 5: 0.20, 6: 0.20}, # %表記
    "通常時モード比率_モードD": {1: 0.05, 2: 0.08, 3: 0.11, 4: 0.14, 5: 0.17, 6: 0.20}, # %表記
}

# CZ/ボーナス終了画面、獲得枚数表示、ラウンド開始画面などの示唆
HINT_DATA = {
    # CZ/ボーナス終了画面の示唆 (ヴァルヴレイヴ固有の項目のみ)
    "CZボーナス終了画面_白枠1(2人)": {"type": "odd_settings", "settings": [1, 3, 5], "value_multiplier": 3.0, "exclude_multiplier": 0.3},
    "CZボーナス終了画面_白枠2(3人)": {"type": "even_settings", "settings": [2, 4, 6], "value_multiplier": 3.0, "exclude_multiplier": 0.3},
    "CZボーナス終了画面_白枠3(4人)": {"type": "normal"}, # 基本パターン、尤度変更なし
    "CZボーナス終了画面_革命ボーナス後": {"type": "min_setting", "setting": 2, "value_multiplier": 5.0, "exclude_multiplier": 0.1}, # 設定2以上確定!?
    "CZボーナス終了画面_赤枠1(男性キャラ集合)": {"type": "odd_settings", "settings": [1, 3, 5], "value_multiplier": 5.0, "exclude_multiplier": 0.1},
    "CZボーナス終了画面_赤枠2(水着)": {"type": "even_settings", "settings": [2, 4, 6], "value_multiplier": 5.0, "exclude_multiplier": 0.1},
    "CZボーナス終了画面_金枠(ドルシア軍服)": {"type": "min_setting", "setting": 4, "value_multiplier": 10.0, "exclude_multiplier": 1e-3},
    "CZボーナス終了画面_虹枠(咲)": {"type": "exact_setting", "setting": 6, "value_multiplier": 1000.0, "exclude_multiplier": 1e-10},
    
    # 獲得枚数での示唆
    "獲得枚数表示_456枚OVER": {"type": "min_setting", "setting": 4, "value_multiplier": 10.0, "exclude_multiplier": 1e-3},
    "獲得枚数表示_555枚OVER": {"type": "min_setting", "setting": 5, "value_multiplier": 50.0, "exclude_multiplier": 1e-3}, # 設定5以上濃厚
    "獲得枚数表示_666枚OVER": {"type": "exact_setting", "setting": 6, "value_multiplier": 1000.0, "exclude_multiplier": 1e-10},
    
    # ラウンド開始画面
    "ラウンド開始画面_ビーストハイ": {"type": "min_setting", "setting": 4, "value_multiplier": 10.0, "exclude_multiplier": 1e-3},
    "ラウンド開始画面_リーゼロッテ": {"type": "exact_setting", "setting": 6, "value_multiplier": 1000.0, "exclude_multiplier": 1e-10},
}

# --- カスタムCSS ---
CUSTOM_CSS = """
<style>
/* 全体背景画像 */
body {
    background-image: url("https://i.imgur.com/SzeFpg7.jpg"); /* CZ前兆のステージ */
    background-size: cover;
    background-attachment: fixed; /* スクロールしても背景を固定 */
    background-position: center center;
    color: #E0E0E0; /* 全体テキスト色を明るいグレーに */
}

/* サイドバーの背景色とテキスト色 */
[data-testid="stSidebar"] {
    background-color: rgba(30, 0, 0, 0.8); /* 半透明の暗い赤 */
    color: #FF4B4B; /* 赤系のテキスト */
}
[data-testid="stSidebar"] .stButton > button {
    background-color: #FF4B4B; /* サイドバーボタンの背景色 */
    color: white;
    border: 1px solid #FF4B4B;
    box-shadow: 0 0 5px #FF4B4B;
}

/* メインコンテンツの背景を少し透過させる */
[data-testid="stAppViewBlockContainer"] {
    background-color: rgba(0, 0, 0, 0.7); /* 半透明の黒 */
    padding: 20px;
    border-radius: 10px;
}

/* タイトルとサブタイトル */
h1, h2, h3 {
    color: #FF4B4B; /* 赤色 */
    text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);
}

/* セクション区切りの破線 */
hr {
    border-top: 2px dashed #990000; /* 赤系の破線 */
}

/* ナンバーインプット、セレクトボックスなどの入力フィールド */
.stNumberInput > div > div > input, .stSelectbox > div > div > button {
    background-color: #333333; /* 暗いグレーの背景 */
    color: #ADD8E6; /* 明るい水色の文字 */
    border: 1px solid #990000; /* 赤い枠線 */
    border-radius: 5px;
    box-shadow: 0 0 5px #FF4B4B; /* 赤い光る影 */
}

/* ボタン */
.stButton > button {
    background-color: #990000; /* 赤色 */
    color: white;
    border: 1px solid #FF4B4B; /* 明るい赤の枠線 */
    border-radius: 10px;
    box-shadow: 0 0 10px #FF4B4B; /* 赤い光る影 */
    font-weight: bold;
    padding: 10px 20px;
    transition: all 0.3s ease; /* ホバー時のアニメーション */
}
.stButton > button:hover {
    background-color: #FF4B4B; /* ホバーで明るい赤 */
    box-shadow: 0 0 15px #FF4B4B, 0 0 20px #990000;
    transform: translateY(-2px);
}

/* st.infoのスタイル（ヒントボックス） */
.stAlert {
    background-color: rgba(50, 50, 100, 0.7); /* 少し青みがかった半透明 */
    color: #ADD8E6;
    border-left: 5px solid #ADD8E6;
}

/* 結果表示部分の背景（脳汁演出） */
.result-section {
    position: relative;
    padding: 20px;
    margin-top: 20px;
    border-radius: 10px;
    overflow: hidden; /* 背景画像がはみ出ないように */
    background-color: rgba(0,0,0,0.8); /* デフォルトの黒 */
    transition: background-image 1s ease-in-out; /* 背景画像変更のアニメーション */
}
.result-background {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: url("https://i.imgur.com/ps5TdGS.jpg"); /* ハラキリドライブ確定演出の画像 */
    background-size: cover;
    background-position: center;
    opacity: 0; /* 最初は透明 */
    transition: opacity 1s ease-in-out;
    z-index: -1; /* コンテンツの下に配置 */
}
.result-background.active {
    opacity: 1; /* アクティブ時に不透明に */
}
</style>
"""

# --- 推測ロジック関数 ---
def calculate_likelihood(observed_count, total_count, target_rate_value, is_probability_rate=True):
    """
    実測値と解析値から尤度を計算する。
    target_rate_value: 1/X形式の場合のX、または%形式の小数。
    is_probability_rate: Trueなら確率（%表示の小数）、Falseなら分母（1/XのX）
    """
    if total_count <= 0: # 試行回数がゼロ以下なら計算に影響を与えない
        return 1.0
    
    # 観測回数もゼロなら影響を与えない（データがないのと同じ）
    if observed_count <= 0 and total_count > 0:
        # ただし、解析値が0%なのに観測値が0なら尤度が高い
        if (is_probability_rate and target_rate_value <= 1e-10) or \
           (not is_probability_rate and target_rate_value == float('inf')): # 分母無限大=確率0
           return 1.0 # 観測0で解析値も0なら尤度高い

    if is_probability_rate: # %形式の確率の場合
        expected_value = total_count * target_rate_value
    else: # 1/X形式の分母の場合
        if target_rate_value <= 1e-10: # 分母が0はありえないが念のため
            return 1e-10 # 確率無限大になるので極めて低い尤度
        expected_value = total_count / target_rate_value
    
    # 期待値が0の場合
    if expected_value <= 1e-10: # 非常に小さい値で0とみなす
        return 1.0 if observed_count == 0 else 1e-10 # 期待値0で観測も0なら尤度1、観測1以上ならほぼ0

    # ポアソン分布のPMF (確率質量関数) を使用して尤度を計算
    likelihood = poisson.pmf(observed_count, expected_value)
    
    # 尤度がゼロになることを避けるため、非常に小さい値を下限とする
    return max(likelihood, 1e-10)

# 天井期待値、機械割のデータ (ボーナス・AT間天井)
BONUS_AT_CEILING_DATA = {
    0: {"初当り確率_分母": 1, "機械割": 100.0}, # 開始時
    100: {"初当り確率_分母": 392, "機械割": 96.3},
    150: {"初当り確率_分母": 375, "機械割": 97.4},
    200: {"初当り確率_分母": 355, "機械割": 100.3},
    250: {"初当り確率_分母": 344, "機械割": 101.4},
    300: {"初当り確率_分母": 338, "機械割": 102.0},
    350: {"初当り確率_分母": 333, "機械割": 102.5},
    400: {"初当り確率_分母": 330, "機械割": 103.0},
    450: {"初当り確率_分母": 327, "機械割": 103.4},
    500: {"初当り確率_分母": 324, "機械割": 103.8},
    550: {"初当り確率_分母": 321, "機械割": 104.2},
    600: {"初当り確率_分母": 319, "機械割": 104.5},
    650: {"初当り確率_分母": 317, "機械割": 104.8},
    700: {"初当り確率_分母": 315, "機械割": 105.2},
    750: {"初当り確率_分母": 313, "機械割": 105.6},
    800: {"初当り確率_分母": 310, "機械割": 106.0},
    850: {"初当り確率_分母": 307, "機械割": 106.4},
    900: {"初当り確率_分母": 304, "機械割": 106.8},
    950: {"初当り確率_分母": 301, "機械割": 107.4},
    1000: {"初当り確率_分母": 298, "機械割": 108.0},
    1050: {"初当り確率_分母": 294, "機械割": 108.8},
    1100: {"初当り確率_分母": 290, "機械割": 109.8},
    1150: {"初当り確率_分母": 286, "機械割": 110.8},
    1200: {"初当り確率_分母": 282, "機械割": 112.0},
    1250: {"初当り確率_分母": 277, "機械割": 113.4},
    1300: {"初当り確率_分母": 272, "機械割": 115.1},
    1350: {"初当り確率_分母": 266, "機械割": 117.2},
    1400: {"初当り確率_分母": 260, "機械割": 119.8},
}

# CZ天井期待値データ
CZ_CEILING_DATA = {
    0: {"初当り確率_分母": 1, "機械割": 100.0},
    50: {"初当り確率_分母": 243, "機械割": 98.3},
    100: {"初当り確率_分母": 222, "機械割": 99.6},
    150: {"初当り確率_分母": 210, "機械割": 101.9},
    200: {"初当り確率_分母": 200, "機械割": 103.9},
    250: {"初当り確率_分母": 185, "機械割": 107.9},
    300: {"初当り確率_分母": 173, "機械割": 111.2},
    350: {"初当り確率_分母": 163, "機械割": 113.4},
    400: {"初当り確率_分母": 154, "機械割": 116.4},
    450: {"初当り確率_分母": 140, "機械割": 118.5},
    500: {"初当り確率_分母": 131, "機械割": 124.0},
}

# 引き戻し期待値データ (ミミズモード以外)
PULLBACK_DATA = {
    "単発後": {"引き戻し期待度": 0.160, "出玉率": 1.194},
    "2連後": {"引き戻し期待度": 0.168, "出玉率": 1.297},
    "3連後": {"引き戻し期待度": 0.161, "出玉率": 1.394},
    "超革命後": {"引き戻し期待度": 0.171, "出玉率": 1.412},
}

# 役名リスト
RARE_ROLES = ["スイカ", "チャンス目", "強チャンス目", "チェリー", "強チェリー", "共闘役"]
OTHER_ROLES = ["共通ベル", "1枚役", "3枚役", "ハズレ目"] # リプレイは別途判定

# CZキャラ名リスト (色と対応)
CZ_CHARS = {
    "キューマ": "🟦",
    "ライゾウ": "🟡",
    "サキ": "🟢",
    "アキラ": "🟣",
    "マリエ": "💖"
}

# --- カスタムCSS ---
CUSTOM_CSS = """
<style>
/* 全体背景画像 */
body {
    background-image: url("https://i.imgur.com/SzeFpg7.jpg"); /* CZ前兆のステージ */
    background-size: cover;
    background-attachment: fixed; /* スクロールしても背景を固定 */
    background-position: center center;
    color: #E0E0E0; /* 全体テキスト色を明るいグレーに */
}

/* サイドバーの背景色とテキスト色 */
[data-testid="stSidebar"] {
    background-color: rgba(30, 0, 0, 0.8); /* 半透明の暗い赤 */
    color: #FF4B4B; /* 赤系のテキスト */
}
[data-testid="stSidebar"] .stButton > button {
    background-color: #FF4B4B; /* サイドバーボタンの背景色 */
    color: white;
    border: 1px solid #FF4B4B;
    box-shadow: 0 0 5px #FF4B4B;
}

/* メインコンテンツの背景を少し透過させる */
[data-testid="stAppViewBlockContainer"] {
    background-color: rgba(0, 0, 0, 0.7); /* 半透明の黒 */
    padding: 20px;
    border-radius: 10px;
}

/* タイトルとサブタイトル */
h1, h2, h3 {
    color: #FF4B4B; /* 赤色 */
    text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);
}

/* セクション区切りの破線 */
hr {
    border-top: 2px dashed #990000; /* 赤系の破線 */
}

/* ナンバーインプット、セレクトボックスなどの入力フィールド */
.stNumberInput > div > div > input, .stSelectbox > div > div > button {
    background-color: #333333; /* 暗いグレーの背景 */
    color: #ADD8E6; /* 明るい水色の文字 */
    border: 1px solid #990000; /* 赤い枠線 */
    border-radius: 5px;
    box-shadow: 0 0 5px #FF4B4B; /* 赤い光る影 */
}

/* ボタン */
.stButton > button {
    background-color: #990000; /* 赤色 */
    color: white;
    border: 1px solid #FF4B4B; /* 明るい赤の枠線 */
    border-radius: 10px;
    box-shadow: 0 0 10px #FF4B4B; /* 赤い光る影 */
    font-weight: bold;
    padding: 10px 20px;
    transition: all 0.3s ease; /* ホバー時のアニメーション */
}
.stButton > button:hover {
    background-color: #FF4B4B; /* ホバーで明るい赤 */
    box-shadow: 0 0 15px #FF4B4B, 0 0 20px #990000;
    transform: translateY(-2px);
}

/* st.infoのスタイル（ヒントボックス） */
.stAlert {
    background-color: rgba(50, 50, 100, 0.7); /* 少し青みがかった半透明 */
    color: #ADD8E6;
    border-left: 5px solid #ADD8E6;
}

/* 結果表示部分の背景（脳汁演出） */
.result-section {
    position: relative;
    padding: 20px;
    margin-top: 20px;
    border-radius: 10px;
    overflow: hidden; /* 背景画像がはみ出ないように */
    background-color: rgba(0,0,0,0.8); /* デフォルトの黒 */
    transition: background-image 1s ease-in-out; /* 背景画像変更のアニメーション */
}
.result-background {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: url("https://i.imgur.com/ps5TdGS.jpg"); /* ハラキリドライブ確定演出の画像 */
    background-size: cover;
    background-position: center;
    opacity: 0; /* 最初は透明 */
    transition: opacity 1s ease-in-out;
    z-index: -1; /* コンテンツの下に配置 */
}
.result-background.active {
    opacity: 1; /* アクティブ時に不透明に */
}
</style>
"""

# --- 推測ロジック関数 ---
def calculate_likelihood(observed_count, total_count, target_rate_value, is_probability_rate=True):
    """
    実測値と解析値から尤度を計算する。
    target_rate_value: 1/X形式の場合のX、または%形式の小数。
    is_probability_rate: Trueなら確率（%表示の小数）、Falseなら分母（1/XのX）
    """
    if total_count <= 0: # 試行回数がゼロ以下なら計算に影響を与えない
        return 1.0
    
    # 観測回数もゼロなら影響を与えない（データがないのと同じ）
    if observed_count <= 0 and total_count > 0:
        # ただし、解析値が0%なのに観測値が0なら尤度が高い
        if (is_probability_rate and target_rate_value <= 1e-10) or \
           (not is_probability_rate and target_rate_value == float('inf')): # 分母無限大=確率0
           return 1.0 # 観測0で解析値も0なら尤度高い

    if is_probability_rate: # %形式の確率の場合
        expected_value = total_count * target_rate_value
    else: # 1/X形式の分母の場合
        if target_rate_value <= 1e-10: # 分母が0はありえないが念のため
            return 1e-10 # 確率無限大になるので極めて低い尤度
        expected_value = total_count / target_rate_value
    
    # 期待値が0の場合
    if expected_value <= 1e-10: # 非常に小さい値で0とみなす
        return 1.0 if observed_count == 0 else 1e-10 # 期待値0で観測も0なら尤度1、観測1以上ならほぼ0

    # ポアソン分布のPMF (確率質量関数) を使用して尤度を計算
    likelihood = poisson.pmf(observed_count, expected_value)
    
    # 尤度がゼロになることを避けるため、非常に小さい値を下限とする
    return max(likelihood, 1e-10)

# 天井期待値、機械割のデータ (ボーナス・AT間天井)
BONUS_AT_CEILING_DATA = {
    0: {"初当り確率_分母": 1, "機械割": 100.0}, # 開始時
    100: {"初当り確率_分母": 392, "機械割": 96.3},
    150: {"初当り確率_分母": 375, "機械割": 97.4},
    200: {"初当り確率_分母": 355, "機械割": 100.3},
    250: {"初当り確率_分母": 344, "機械割": 101.4},
    300: {"初当り確率_分母": 338, "機械割": 102.0},
    350: {"初当り確率_分母": 333, "機械割": 102.5},
    400: {"初当り確率_分母": 330, "機械割": 103.0},
    450: {"初当り確率_分母": 327, "機械割": 103.4},
    500: {"初当り確率_分母": 324, "機械割": 103.8},
    550: {"初当り確率_分母": 321, "機械割": 104.2},
    600: {"初当り確率_分母": 319, "機械割": 104.5},
    650: {"初当り確率_分母": 317, "機械割": 104.8},
    700: {"初当り確率_分母": 315, "機械割": 105.2},
    750: {"初当り確率_分母": 313, "機械割": 105.6},
    800: {"初当り確率_分母": 310, "機械割": 106.0},
    850: {"初当り確率_分母": 307, "機械割": 106.4},
    900: {"初当り確率_分母": 304, "機械割": 106.8},
    950: {"初当り確率_分母": 301, "機械割": 107.4},
    1000: {"初当り確率_分母": 298, "機械割": 108.0},
    1050: {"初当り確率_分母": 294, "機械割": 108.8},
    1100: {"初当り確率_分母": 290, "機械割": 109.8},
    1150: {"初当り確率_分mu": 286, "機械割": 110.8}, # Typo here: '分mu' instead of '分母'
    1200: {"初当り確率_分母": 282, "機械割": 112.0},
    1250: {"初当り確率_分母": 277, "機械割": 113.4},
    1300: {"初当り確率_分母": 272, "機械割": 115.1},
    1350: {"初当り確率_分母": 266, "機械割": 117.2},
    1400: {"初当り確率_分母": 260, "機械割": 119.8},
}

# CZ天井期待値データ
CZ_CEILING_DATA = {
    0: {"初当り確率_分母": 1, "機械割": 100.0},
    50: {"初当り確率_分母": 243, "機械割": 98.3},
    100: {"初当り確率_分母": 222, "機械割": 99.6},
    150: {"初当り確率_分母": 210, "機械割": 101.9},
    200: {"初当り確率_分母": 200, "機械割": 103.9},
    250: {"初当り確率_分母": 185, "機械割": 107.9},
    300: {"初当り確率_分母": 173, "機械割": 111.2},
    350: {"初当り確率_分母": 163, "機械割": 113.4},
    400: {"初当り確率_分母": 154, "機械割": 116.4},
    450: {"初当り確率_分母": 140, "機械割": 118.5},
    500: {"初当り確率_分mu": 131, "機械割": 124.0}, # Typo here: '分mu' instead of '分母'
}

# 引き戻し期待値データ (ミミズモード以外)
PULLBACK_DATA = {
    "単発後": {"引き戻し期待度": 0.160, "出玉率": 1.194},
    "2連後": {"引き戻し期待度": 0.168, "出玉率": 1.297},
    "3連後": {"引き戻し期待度": 0.161, "出玉率": 1.394},
    "超革命後": {"引き戻し期待度": 0.171, "出玉率": 1.412},
}

# 役名リスト
RARE_ROLES = ["スイカ", "チャンス目", "強チャンス目", "チェリー", "強チェリー", "共闘役"]
OTHER_ROLES = ["共通ベル", "1枚役", "3枚役", "ハズレ目"] # リプレイは別途判定

# CZキャラ名リスト (色と対応)
CZ_CHARS = {
    "キューマ": "🟦",
    "ライゾウ": "🟡",
    "サキ": "🟢",
    "アキラ": "🟣",
    "マリエ": "💖"
}

# --- カスタムCSS ---
CUSTOM_CSS = """
<style>
/* 全体背景画像 */
body {
    background-image: url("https://i.imgur.com/SzeFpg7.jpg"); /* CZ前兆のステージ */
    background-size: cover;
    background-attachment: fixed; /* スクロールしても背景を固定 */
    background-position: center center;
    color: #E0E0E0; /* 全体テキスト色を明るいグレーに */
}

/* サイドバーの背景色とテキスト色 */
[data-testid="stSidebar"] {
    background-color: rgba(30, 0, 0, 0.8); /* 半透明の暗い赤 */
    color: #FF4B4B; /* 赤系のテキスト */
}
[data-testid="stSidebar"] .stButton > button {
    background-color: #FF4B4B; /* サイドバーボタンの背景色 */
    color: white;
    border: 1px solid #FF4B4B;
    box-shadow: 0 0 5px #FF4B4B;
}

/* メインコンテンツの背景を少し透過させる */
[data-testid="stAppViewBlockContainer"] {
    background-color: rgba(0, 0, 0, 0.7); /* 半透明の黒 */
    padding: 20px;
    border-radius: 10px;
}

/* タイトルとサブタイトル */
h1, h2, h3 {
    color: #FF4B4B; /* 赤色 */
    text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);
}

/* セクション区切りの破線 */
hr {
    border-top: 2px dashed #990000; /* 赤系の破線 */
}

/* ナンバーインプット、セレクトボックスなどの入力フィールド */
.stNumberInput > div > div > input, .stSelectbox > div > div > button {
    background-color: #333333; /* 暗いグレーの背景 */
    color: #ADD8E6; /* 明るい水色の文字 */
    border: 1px solid #990000; /* 赤い枠線 */
    border-radius: 5px;
    box-shadow: 0 0 5px #FF4B4B; /* 赤い光る影 */
}

/* ボタン */
.stButton > button {
    background-color: #990000; /* 赤色 */
    color: white;
    border: 1px solid #FF4B4B; /* 明るい赤の枠線 */
    border-radius: 10px;
    box-shadow: 0 0 10px #FF4B4B; /* 赤い光る影 */
    font-weight: bold;
    padding: 10px 20px;
    transition: all 0.3s ease; /* ホバー時のアニメーション */
}
.stButton > button:hover {
    background-color: #FF4B4B; /* ホバーで明るい赤 */
    box-shadow: 0 0 15px #FF4B4B, 0 0 20px #990000;
    transform: translateY(-2px);
}

/* st.infoのスタイル（ヒントボックス） */
.stAlert {
    background-color: rgba(50, 50, 100, 0.7); /* 少し青みがかった半透明 */
    color: #ADD8E6;
    border-left: 5px solid #ADD8E6;
}

/* 結果表示部分の背景（脳汁演出） */
.result-section {
    position: relative;
    padding: 20px;
    margin-top: 20px;
    border-radius: 10px;
    overflow: hidden; /* 背景画像がはみ出ないように */
    background-color: rgba(0,0,0,0.8); /* デフォルトの黒 */
    transition: background-image 1s ease-in-out; /* 背景画像変更のアニメーション */
}
.result-background {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: url("https://i.imgur.com/ps5TdGS.jpg"); /* ハラキリドライブ確定演出の画像 */
    background-size: cover;
    background-position: center;
    opacity: 0; /* 最初は透明 */
    transition: opacity 1s ease-in-out;
    z-index: -1; /* コンテンツの下に配置 */
}
.result-background.active {
    opacity: 1; /* アクティブ時に不透明に */
}
</style>
"""

# --- 推測ロジック関数 ---
def get_nearest_machine_performance(current_g, data_table):
    """
    現在のゲーム数に最も近い期待値テーブルの機械割を取得
    """
    if current_g < min(data_table.keys()):
        return data_table[min(data_table.keys())]["機械割"]
    
    # キーをソートして、現在のゲーム数に最も近いものを探す
    sorted_keys = sorted(data_table.keys())
    for i in range(len(sorted_keys)):
        if current_g <= sorted_keys[i]:
            return data_table[sorted_keys[i]]["機械割"]
    
    return data_table[sorted_keys[-1]]["機械割"] # テーブルの最大値を超える場合


def predict_setting(data_inputs):
    # Overall likelihoods initialized for each setting
    overall_likelihoods = {setting: 1.0 for setting in range(1, 7)}
    
    # データが一つも入力されていない場合のチェック
    if not data_inputs.get('total_game_count', 0) > 0:
        return "データが入力されていません。推測を行うには、少なくとも1つの判別要素を入力してください。"

    # --- 確率系の要素の計算 ---
    total_game_count = data_inputs.get('total_game_count', 0) # グローバル集計値
    
    # ボーナス初当り確率
    if total_game_count > 0 and data_inputs.get('at_first_hit_count', 0) >= 0:
        for setting, rate_val in GAME_DATA.get("ボーナス初当り確率", {}).items(): # .get()を使用
            likelihood = calculate_likelihood(data_inputs['at_first_hit_count'], total_game_count, rate_val, is_probability_rate=False)
            overall_likelihoods[setting] *= likelihood

    # CZ_共闘Vチャレンジ_出現率
    if data_inputs.get('cz_kyoutou_v_challenge_total_count', 0) > 0 and data_inputs.get('cz_kyoutou_v_challenge_count', 0) >= 0:
        for setting, rate_val in GAME_DATA.get("CZ_共闘Vチャレンジ_出現率", {}).items(): # .get()を使用
            likelihood = calculate_likelihood(data_inputs['cz_kyoutou_v_challenge_count'], data_inputs['cz_kyoutou_v_challenge_total_count'], rate_val, is_probability_rate=False)
            overall_likelihoods[setting] *= likelihood
            
    # ハラキリドライブ発生率
    if data_inputs.get('harikiri_drive_total_count', 0) > 0 and data_inputs.get('harikiri_drive_count', 0) >= 0:
        for setting, rate_val in GAME_DATA.get("ハラキリドライブ発生率", {}).items(): # .get()を使用
            likelihood = calculate_likelihood(data_inputs['harikiri_drive_count'], data_inputs['harikiri_drive_total_count'], rate_val, is_probability_rate=True)
            overall_likelihoods[setting] *= likelihood
    
    # 超革命ラッシュ_セットゲーム振り分け
    if data_inputs.get('total_ssr_sets', 0) > 0:
        ssr_counts = {
            "10G": data_inputs.get('ssr_10g_count', 0), "20G": data_inputs.get('ssr_20g_count', 0),
            "50G": data_inputs.get('ssr_50g_count', 0), "100G": data_inputs.get('ssr_100g_count', 0)
        }
        for setting in range(1, 7):
            ssr_likelihood_for_setting = 1.0
            for game_type, count in ssr_counts.items():
                if count > 0: # 観測回数がある場合のみ尤度を計算
                    target_rate = GAME_DATA.get(f"超革命ラッシュ_セットゲーム_{game_type}", {}).get(setting, 0) # .get()を使用
                    likelihood = calculate_likelihood(count, data_inputs['total_ssr_sets'], target_rate, is_probability_rate=True)
                    ssr_likelihood_for_setting *= likelihood
            overall_likelihoods[setting] *= ssr_likelihood_for_setting


    # 有利区間切断時ハラキリドライブ発生率
    if data_inputs.get('yurikuukan_cut_total_count', 0) > 0 and data_inputs.get('yurikuukan_cut_hd_count', 0) >= 0:
        for setting, rate_val in GAME_DATA.get("有利区間切断時ハラキリドライブ発生率", {}).items(): # .get()を使用
            likelihood = calculate_likelihood(data_inputs['yurikuukan_cut_hd_count'], data_inputs['yurikuukan_cut_total_count'], rate_val, is_probability_rate=True)
            overall_likelihoods[setting] *= likelihood
            
    # モード比率の尤度計算（調整版）
    if data_inputs.get('mode_total_count', 0) > 0: # モードデータがある場合のみ
        for setting in range(1, 7):
            mode_likelihood_for_setting = 1.0
            for mode_char, observed_count in data_inputs.get('mode_observed_counts', {}).items(): # .get()を使用
                if observed_count > 0: # そのモードの観測があれば
                    expected_rate = GAME_DATA.get(f"通常時モード比率_モード{mode_char}", {}).get(setting, 0) # .get()を使用
                    # 確率の適合度を評価
                    likelihood = 1.0 - abs(observed_count / data_inputs['mode_total_count'] - expected_rate) / max(observed_count / data_inputs['mode_total_count'], expected_rate, 0.001)
                    mode_likelihood_for_setting *= (max(likelihood, 1e-5) ** 0.25) # 0.25乗で影響を弱める
            overall_likelihoods[setting] *= mode_likelihood_for_setting


    # 示唆系の要素の計算
    for hint_key, observed_count in data_inputs.get('hints_observed_counts', {}).items(): # .get()を使用
        if observed_count > 0:
            hint_info = HINT_DATA.get(hint_key, None) # .get()を使用
            if hint_info is None: # 示唆データが見つからない場合
                continue

            hint_type = hint_info["type"]
            for setting in range(1, 7):
                multiplier = 1.0 

                if hint_type == "even_settings":
                    if setting in hint_info["settings"]: multiplier = hint_info.get("value_multiplier", 1.0)
                    else: multiplier = hint_info.get("exclude_multiplier", 1e-3)
                elif hint_type == "odd_settings":
                    if setting in hint_info["settings"]: multiplier = hint_info.get("value_multiplier", 1.0)
                    else: multiplier = hint_info.get("exclude_multiplier", 1e-3)
                elif hint_type == "min_setting":
                    if setting >= hint_info["setting"]: multiplier = hint_info.get("value_multiplier", 1.0)
                    else: multiplier = hint_info.get("exclude_multiplier", 1e-3)
                elif hint_type == "exact_setting":
                    if setting == hint_info["setting"]: multiplier = hint_info.get("value_multiplier", 1.0)
                    else: multiplier = hint_info.get("exclude_multiplier", 1e-10)
                elif hint_type == "exclude_setting":
                    if setting in hint_info["settings"]: multiplier = hint_info.get("value_multiplier", 1e-10)
                    else: multiplier = hint_info.get("exclude_multiplier", 1.0)
                elif hint_type == "normal": multiplier = 1.0
                elif hint_type == "high_settings":
                    if setting in hint_info["settings"]: multiplier = hint_info.get("value_multiplier", 1.0)
                    else: multiplier = hint_info.get("exclude_multiplier", 1e-3)

                overall_likelihoods[setting] *= (multiplier ** observed_count)


    # --- みみずモードの尤度計算 ---
    mimizu_likelihood_multiplier = {setting: 1.0 for setting in range(1, 7)}
    is_mimizu_confirmed = False # みみずモード濃厚フラグ (ヤメ時表示用)
    
    # 朝一1G/2Gレバーのミミズ否定ロジック
    morning_lever_denies_mimizu_general = False
    morning_1g_lever = data_inputs.get('morning_1g_lever_global', '不明') # グローバルから取得
    morning_2g_lever = data_inputs.get('morning_2g_lever_global', '不明') # グローバルから取得

    if morning_1g_lever in RARE_ROLES:
        morning_lever_denies_mimizu_general = True
    elif morning_1g_lever == "リプレイ" and morning_2g_lever in RARE_ROLES:
        morning_lever_denies_mimizu_general = True
    
    # 下限みみずの優先判定 (朝一否定を上書き)
    total_mimizu_behaviors = data_inputs.get('mimizu_400_600p_rb_count', 0) + \
                             data_inputs.get('mimizu_cz_blank_win_count', 0) + \
                             data_inputs.get('mimizu_no_pullback_count', 0)

    if data_inputs.get('current_sasamai', 0) <= -4000 and total_mimizu_behaviors >= 3:
        is_mimizu_confirmed = True 
        for setting, rate in GAME_DATA.get("みみずモード発生率", {}).items(): # .get()を使用
            if rate > 0:
                mimizu_likelihood_multiplier[setting] *= (rate * 100)**3 # 確定なので非常に強く反映
            else:
                mimizu_likelihood_multiplier[setting] *= 1e-10 # 0%なら発生でほぼ否定

    elif not morning_lever_denies_mimizu_general and total_mimizu_behaviors > 0:
        # 朝一否定がなく、かつミミズ挙動が1回でもあればミミズの可能性あり
        for setting, rate in GAME_DATA.get("みみずモード発生率", {}).items(): # .get()を使用
            if rate > 0:
                mimizu_likelihood_multiplier[setting] *= (rate * 100)**(total_mimizu_behaviors * 0.5) # 挙動の回数で強度調整
            else:
                mimizu_likelihood_multiplier[setting] *= 1e-10
        is_mimizu_confirmed = True # ユーザーへの表示のため


    # 全体尤度にミミズ尤度を乗算
    for setting in range(1, 7):
        overall_likelihoods[setting] *= mimizu_likelihood_multiplier[setting]


    # --- 最終結果の処理 ---
    total_overall_likelihood_sum = sum(overall_likelihoods.values())
    if total_overall_likelihood_sum == 0: 
        return "データが不足しているか、矛盾しているため、推測が困難です。入力値を見直してください。"

    normalized_probabilities = {s: (p / total_overall_likelihood_sum) * 100 for s, p in overall_likelihoods.items()}

    predicted_setting = max(normalized_probabilities, key=normalized_probabilities.get)
    max_prob_value = normalized_probabilities[predicted_setting]

    result_str = f"## ✨ 推測される設定: 設定{predicted_setting} (確率: 約{max_prob_value:.2f}%) ✨\n\n"
    result_str += "--- 各設定の推測確率 ---\n"
    for setting, prob in sorted(normalized_probabilities.items(), key=lambda item: item[1], reverse=True):
        result_str += f"  - 設定{setting}: 約{prob:.2f}%\n"

    # --- やめ時判断と追加メッセージ ---
    result_str += "\n\n---\n\n"
    result_str += "### 💡 やめ時判断 💡\n"
    
    # みみずモードが濃厚な場合
    if is_mimizu_confirmed:
        result_str += "🚨 **みみずモード濃厚です！設定不問でヤメ推奨！** 🚨\n"
        result_str += "（有利区間切断時まで脱出できません。引き戻しもありません。）\n"
    else:
        # 天井到達条件4: AT非当選決戦ボーナスが4回連続
        if data_inputs.get('max_kessen_bonus_no_at_consecutive_count', 0) >= 4:
            result_str += "⚠️ **決戦ボーナスAT非当選4連続天井到達！ボーナス当選でAT濃厚！続行推奨！** ⚠️\n"
            
        # CZスルー7回天井
        if data_inputs.get('cz_pass_through_count_for_yame', 0) >= 7:
            result_str += "⚠️ **CZスルー7回天井到達！ボーナス当選濃厚！続行推奨！** ⚠️\n"

        # 機械割100%以上の判断
        current_machine_performance_yame = 0.0
        current_g = data_inputs.get('total_game_count_for_yame', 0)
        
        if current_g > 0 and BONUS_AT_CEILING_DATA: 
            current_machine_performance_yame = get_nearest_machine_performance(current_g, BONUS_AT_CEILING_DATA)
            if current_machine_performance_yame > 100.0:
                result_str += f"✅ **現在のボーナス/AT間ゲーム数 ({current_g}G) では機械割が約{current_machine_performance_yame:.1f}%で100%以上です。続行推奨！**\n"
        
        # 引き戻しゾーンの機械割
        at_renchan_pattern_for_yame = data_inputs.get('at_renchan_pattern_for_yame', '選択なし')
        if at_renchan_pattern_for_yame != "選択なし" and PULLBACK_DATA and data_inputs.get('current_g_after_at_for_yame', 0) <= 66:
            if at_renchan_pattern_for_yame in PULLBACK_DATA:
                pullback_payout_rate = PULLBACK_DATA[at_renchan_pattern_for_yame]["出玉率"] * 100
                if pullback_payout_rate > 100.0:
                    result_str += f"✅ **{at_renchan_pattern_for_yame}での引き戻しゾーン(0〜66G)は出玉率{pullback_payout_rate:.1f}%で100%以上です。続行推奨！**\n"
                else:
                    result_str += f"ℹ️ {at_renchan_pattern_for_yame}での引き戻しゾーン(0〜66G)は出玉率{pullback_payout_rate:.1f}%です。\n"
            result_str += "👉 **ミミズモードでない場合の引き戻し確認（0〜66Gまで）を推奨します。**\n"
        
        # 上記以外で特に「続行推奨」ではない場合
        if not ("✅" in result_str or "⚠️" in result_str or "ℹ️" in result_str):
            result_str += "ℹ️ **現在の状況で特に続行を強く推奨する要素はありません。**\n"
            result_str += "（みみずモードではないこと、機械割100%未満の可能性、特定の天井・ゾーン外の場合など）\n"


    return result_str


# --- Streamlit UI 部分 ---

st.set_page_config(
    page_title="ヴァルヴレイヴ 設定判別 & やめ時ツール",
    layout="centered",
    initial_sidebar_state="expanded",
    page_icon="🤖" # 新しいタブアイコン
)

# カスタムCSSの注入 (背景画像、UI要素のスタイリング)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


st.title("🚀 革命機ヴァルヴレイヴ 🎰")
st.title("設定判別 & やめ時ツール")

st.markdown(
    """
    ヴァルヴレイヴの設定判別、みみずモードの兆候、そして詳細なやめ時をサポートするツールです。
    遊技中の各イベントを記録し、総合的な分析を行いましょう！
    """
)

# クイックジャンプナビゲーション（サイドバー）
with st.sidebar:
    st.markdown("## 🚀 クイックジャンプ")
    st.markdown("---")
    if st.button("設定判別へ", key="jump_setting_sidebar"):
        st.write('<script>window.location.href="#section_setting_inputs";</script>', unsafe_allow_html=True)
    if st.button("みみずモードへ", key="jump_mimizu_sidebar"):
        st.write('<script>window.location.href="#section_mimizu_inputs";</script>', unsafe_allow_html=True)
    if st.button("やめ時判断へ", key="jump_yamedoki_sidebar"):
        st.write('<script>window.location.href="#section_yamedoki_inputs";</script>', unsafe_allow_html=True)
    if st.button("結果表示へ", key="jump_results_sidebar"):
        st.write('<script>window.location.href="#section_results";</script>', unsafe_allow_html=True)
    st.markdown("---")
    st.info("💡 **ヒント:** スクロールして全ての項目を確認してくださいね！")


# --- 入力セクション ---
st.header("▼データ入力▼")
st.markdown("設定判別に影響する確率系、示唆系のデータを入力します。")
st.markdown('<a name="section_setting_inputs"></a>', unsafe_allow_html=True) # クイックジャンプ用アンカー

with st.container(border=True): # コンテナで囲んで視覚的にグループ化
    st.subheader("1. 基本データ (通常時・AT合算) 🎯")
    st.markdown("全体の遊技データと、ボーナス初当りの回数を入力します。")
    col1, col2, col3 = st.columns(3)
    with col1:
        total_game_count = st.number_input("総ゲーム数", min_value=0, value=0, help="通常時とAT中の合計ゲーム数を入力します。", key="total_game_count")
        cz_total_count = st.number_input("CZ総回数", min_value=0, value=0, help="CZに突入した合計回数を入力します。", key="cz_total_count")
    with col2:
        kakumei_bonus_count = st.number_input("革命ボーナス初当り回数", min_value=0, value=0, help="革命ボーナスの初当り回数を入力します。", key="kakumei_bonus_count")
        kessen_bonus_count = st.number_input("決戦ボーナス初当り回数", min_value=0, value=0, help="決戦ボーナスの初当り回数を入力します。", key="kessen_bonus_count")
    with col3:
        harikiri_drive_total_count = st.number_input("ハラキリドライブ抽選総回数", min_value=0, value=0, help="ハラキリドライブ抽選の合計回数を入力します。（通常時・AT中問わず）", key="harikiri_drive_total_count")
        harikiri_drive_count = st.number_input("ハラキリドライブ発生回数", min_value=0, value=0, key="harikiri_drive_count")
    st.markdown("---")

    st.subheader("2. CZ関連データ 💥")
    col_cz_v_challenge1, col_cz_v_challenge2 = st.columns(2)
    with col_cz_v_challenge1:
        cz_kyoutou_v_challenge_count = st.number_input("共闘Vチャレンジ出現回数", min_value=0, value=0, key="cz_kyoutou_v_challenge_count")
    with col_cz_v_challenge2:
        cz_kyoutou_v_challenge_total_count = st.number_input("└ 試行G数", min_value=0, value=0, help="共闘Vチャレンジの当選分母となるゲーム数を入力します。", key="cz_kyoutou_v_challenge_total_count")
    
    st.subheader("3. 超革命ラッシュのセットゲーム振り分け 🚀")
    st.markdown("超革命ラッシュで獲得したセットのゲーム数（10G/20G/50G/100G）ごとの回数を入力します。")
    col_ssr_total = st.columns(1)
    with col_ssr_total[0]:
        total_ssr_sets = st.number_input("超革命ラッシュ総セット数", min_value=0, value=0, help="超革命ラッシュ中に獲得したセットの合計数を入力します。", key="total_ssr_sets")
    col_ssr_10, col_ssr_20, col_ssr_50, col_ssr_100 = st.columns(4)
    with col_ssr_10:
        ssr_10g_count = st.number_input("└ 10Gセット回数", min_value=0, value=0, key="ssr_10g_count")
    with col_ssr_20:
        ssr_20g_count = st.number_input("└ 20Gセット回数", min_value=0, value=0, key="ssr_20g_count")
    with col_ssr_50:
        ssr_50g_count = st.number_input("└ 50Gセット回数", min_value=0, value=0, key="ssr_50g_count")
    with col_ssr_100:
        ssr_100g_count = st.number_input("└ 100Gセット回数", min_value=0, value=0, key="ssr_100g_count")
    st.markdown("---")

    st.subheader("4. 有利区間切断時ハラキリドライブ発生状況 ⚡")
    st.markdown("差枚+2400枚到達時にハラキリドライブが発生したか否かを入力します。")
    col_yurikuukan_cut_total, col_yurikuukan_cut_hd = st.columns(2)
    with col_yurikuukan_cut_total:
        yurikuukan_cut_total_count = st.number_input("有利区間切断総回数", min_value=0, value=0, help="有利区間が切断された合計回数を入力します。", key="yurikuukan_cut_total_count")
    with col_yurikuukan_cut_hd:
        yurikuukan_cut_hd_count = st.number_input("有利区間切断時HD発生回数", min_value=0, value=0, key="yurikuukan_cut_hd_count")
    st.markdown("---")

    st.subheader("5. 通常時モード比率 (現在判明しているモード) 🧭")
    st.markdown("モード移行が判明した総回数と、各モードに滞在した回数を入力します。")
    mode_total_count = st.number_input("モード判明総回数", min_value=0, value=0, help="モード移行が判明した合計回数を入力します。", key="mode_total_count")
    col_mode_a, col_mode_b, col_mode_c, col_mode_d = st.columns(4)
    with col_mode_a:
        mode_a_count = st.number_input("└ モードA回数", min_value=0, value=0, key="mode_a_count")
    with col_mode_b:
        mode_b_count = st.number_input("└ モードB回数", min_value=0, value=0, key="mode_b_count")
    with col_mode_c:
        mode_c_count = st.number_input("└ モードC回数", min_value=0, value=0, key="mode_c_count")
    with col_mode_d:
        mode_d_count = st.number_input("└ モードD回数", min_value=0, value=0, key="mode_d_count")
    st.markdown("---")

    st.subheader("6. 示唆系の出現回数 🔔")
    st.markdown("各示唆が出現した回数を入力してください。")
    
    st.markdown("##### CZ/ボーナス終了画面")
    col_czb_end1, col_czb_end2, col_czb_end3 = st.columns(3)
    with col_czb_end1:
        czb_end_shiro1_count = st.number_input("白枠1(2人)", min_value=0, value=0, key="czb_end_shiro1_count")
        czb_end_aka1_count = st.number_input("赤枠1(男性キャラ)", min_value=0, value=0, key="czb_end_aka1_count")
        czb_end_kanemaru_count = st.number_input("金枠(ドルシア軍服)", min_value=0, value=0, key="czb_end_kanemaru_count")
    with col_czb_end2:
        czb_end_shiro2_count = st.number_input("白枠2(3人)", min_value=0, value=0, key="czb_end_shiro2_count")
        czb_end_aka2_count = st.number_input("赤枠2(水着)", min_value=0, value=0, key="czb_end_aka2_count")
        czb_end_niji_count = st.number_input("虹枠(咲)", min_value=0, value=0, key="czb_end_niji_count")
    with col_czb_end3:
        czb_end_shiro3_count = st.number_input("白枠3(4人)", min_value=0, value=0, key="czb_end_shiro3_count")
        czb_end_kakumei_count = st.number_input("革命ボーナス後", min_value=0, value=0, key="czb_end_kakumei_count")
    
    st.markdown("##### 獲得枚数表示")
    col_get_count1, col_get_count2, col_get_count3 = st.columns(3)
    with col_get_count1:
        get_count_456_count = st.number_input("456枚OVER", min_value=0, value=0, key="get_count_456_count")
    with col_get_count2:
        get_count_555_count = st.number_input("555枚OVER", min_value=0, value=0, key="get_count_555_count")
    with col_get_count3:
        get_count_666_count = st.number_input("666枚OVER", min_value=0, value=0, key="get_count_666_count")

    st.markdown("##### ラウンド開始画面")
    col_round_start1, col_round_start2 = st.columns(2)
    with col_round_start1:
        round_start_beast_count = st.number_input("ビーストハイ", min_value=0, value=0, key="round_start_beast_count")
    with col_round_start2:
        round_start_liese_count = st.number_input("リーゼロッテ", min_value=0, value=0, key="round_start_liese_count")
st.markdown("---")


# --- みみずモード判別セクション ---
st.header("▼みみずモード判別▼")
st.markdown("ミミズモードの可能性を判断するための情報を入力します。")
st.markdown('<a name="section_mimizu_inputs"></a>', unsafe_allow_html=True) # クイックジャンプ用アンカー
with st.container(border=True):
    st.markdown("##### 7-1. 朝一1G/2Gレバーオン時の状況")
    morning_1g_lever = st.selectbox("朝一1G目レバー", ["不明", "リプレイ"] + RARE_ROLES + OTHER_ROLES, key="morning_1g_lever")
    if morning_1g_lever == "リプレイ":
        morning_2g_lever = st.selectbox("└ 2G目レバー", ["不明"] + RARE_ROLES + OTHER_ROLES, key="morning_2g_lever")
    else:
        morning_2g_lever = "N/A"
        st.markdown("_(1G目がリプレイの場合のみ2G目を参照)_")

    st.markdown("##### 7-2. 現在の総差枚数")
    current_sasamai = st.number_input("現在の総差枚数 (プラス/マイナス)", min_value=-100000, value=0, step=100, help="プラスなら正の数、マイナスなら負の数で入力 (-4000枚で下限ミミズの可能性)", key="current_sasamai")

    st.markdown("##### 7-3. みみず挙動カウンター (複数回の発生で濃厚度UP)")
    col_mimizu_count1, col_mimizu_count2, col_mimizu_count3 = st.columns(3)
    with col_mimizu_count1:
        mimizu_400_600p_rb_count = st.number_input("400-600P 革命ボーナス当選", min_value=0, value=0, help="400-600Pで革命ボーナスに当選した回数", key="mimizu_400_600p_rb_count")
    with col_mimizu_count2:
        mimizu_cz_blank_win_count = st.number_input("CZ中ハズレ当選", min_value=0, value=0, help="CZ中、何も引かずに当選した回数", key="mimizu_cz_blank_win_count")
    with col_mimizu_count3:
        mimizu_no_pullback_count = st.number_input("引き戻しなし", min_value=0, value=0, help="ボーナス/AT終了後、引き戻しゾーン（0-66G）で何も起こらなかった回数", key="mimizu_no_pullback_count")
    
st.markdown("---")

# --- やめ時判断セクション ---
st.header("▼やめ時判断▼")
st.markdown("現在の遊技状況と期待値から、やめ時を判断します。")
st.markdown('<a name="section_yamedoki_inputs"></a>', unsafe_allow_html=True) # クイックジャンプ用アンカー
with st.container(border=True):
    st.markdown("##### 8-1. 現在の遊技状況入力")
    col_yame1, col_yame2, col_yame3 = st.columns(3)
    with col_yame1:
        current_g_for_yame = st.number_input("ボーナス/AT間G数", min_value=0, value=0, help="最後のボーナス/ATからのゲーム数", key="current_g_for_yame")
    with col_yame2:
        cz_pass_through_count_for_yame = st.number_input("CZスルー回数", min_value=0, value=0, key="cz_pass_through_count_for_yame")
    with col_yame3:
        kessen_bonus_no_at_consecutive_count_for_yame = st.number_input("決戦ボーナスAT非当選連続回数", min_value=0, value=0, help="AT非当選の決戦ボーナスが連続した回数", key="kessen_bonus_no_at_consecutive_count_for_yame")
    
    at_renchan_pattern_for_yame = st.selectbox("最後のAT終了パターン", ["選択なし", "単発後", "2連後", "3連後", "超革命後"], key="at_renchan_pattern_for_yame")

    st.markdown("##### 8-2. 特定のボーナス契機")
    col_boost_total, col_boost_bonus = st.columns(2)
    with col_boost_total:
        boost_chance_total_count_for_yame = st.number_input("Boost Chance経由ボーナス発生総回数", min_value=0, value=0, help="Boost Chance経由でボーナスに当選した回数", key="boost_chance_total_count_for_yame")
    with col_boost_bonus:
        boost_chance_bonus_count_for_yame = st.number_input("Boost Chance経由ボーナス当選回数", min_value=0, value=0, key="boost_chance_bonus_count_for_yame")

st.markdown("---")


# --- 推測実行ボタン ---
st.subheader("▼結果表示▼")
st.markdown("全てのデータ入力が終わったら、以下のボタンをクリックしてください。")
st.markdown('<a name="section_results"></a>', unsafe_allow_html=True) # クイックジャンプ用アンカー
result_button_clicked = st.button("✨ 推測結果を表示 ✨", type="primary")

# 結果表示エリア（脳汁演出用コンテナ）
result_container = st.empty() # 結果表示用のプレースホルダー

# st.session_stateに `show_harikiri_background` がなければ初期化
if 'show_harikiri_background' not in st.session_state:
    st.session_state.show_harikiri_background = False

if result_button_clicked:
    st.session_state.show_harikiri_background = True # ボタン押下でフラグをTrueに
    
    with result_container.container():
        # CSSクラスを追加するためのダミー要素
        st.markdown(
            f"""
            <div id="result-background-wrapper" class="result-background {'active' if st.session_state.get('show_harikiri_background', False) else ''}"></div>
            """,
            unsafe_allow_html=True
        )
        # JavaScriptでopacityを制御 (StreamlitのレンダリングタイミングとCSSトランジションの組み合わせ)
        st.markdown(
            """
            <script>
                const wrapper = document.getElementById("result-background-wrapper");
                if (wrapper) {
                    if (wrapper.classList.contains("active")) {
                        wrapper.style.opacity = 1;
                    }
                }
            </script>
            """,
            unsafe_allow_html=True
        )

        # predict_setting関数に渡す入力データを収集
        user_inputs_for_prediction = {
            'total_game_count': total_game_count,
            'kakumei_bonus_count': kakumei_bonus_count,
            'kessen_bonus_count': kessen_bonus_count,
            'at_first_hit_count': kakumei_bonus_count + kessen_bonus_count, # ボーナス初当り合計
            'cz_total_count': cz_total_count,
            'cz_kyoutou_v_challenge_count': cz_kyoutou_v_challenge_count,
            'cz_kyoutou_v_challenge_total_count': cz_kyoutou_v_challenge_total_count,
            'harikiri_drive_count': harikiri_drive_count,
            'harikiri_drive_total_count': harikiri_drive_total_count,
            'total_ssr_sets': total_ssr_sets,
            'ssr_10g_count': ssr_10g_count,
            'ssr_20g_count': ssr_20g_count,
            'ssr_50g_count': ssr_50g_count,
            'ssr_100g_count': ssr_100g_count,
            'yurikuukan_cut_hd_count': yurikuukan_cut_hd_count,
            'yurikuukan_cut_total_count': yurikuukan_cut_total_count,
            'mode_observed_counts': {'モードA': mode_a_count, 'モードB': mode_b_count, 'モードC': mode_c_count, 'モードD': mode_d_count},
            'mode_total_count': mode_total_count,
            'hints_observed_counts': {
                "CZボーナス終了画面_白枠1(2人)": czb_end_shiro1_count,
                "CZボーナス終了画面_白枠2(3人)": czb_end_shiro2_count,
                "CZボーナス終了画面_白枠3(4人)": czb_end_shiro3_count,
                "CZボーナス終了画面_革命ボーナス後": czb_end_kakumei_count,
                "CZボーナス終了画面_赤枠1(男性キャラ集合)": czb_end_aka1_count,
                "CZボーナス終了画面_赤枠2(水着)": czb_end_aka2_count,
                "CZボーナス終了画面_金枠(ドルシア軍服)": czb_end_kanemaru_count,
                "CZボーナス終了画面_虹枠(咲)": czb_end_niji_count,
                "獲得枚数表示_456枚OVER": get_count_456_count,
                "獲得枚数表示_555枚OVER": get_count_555_count,
                "獲得枚数表示_666枚OVER": get_count_666_count,
                "ラウンド開始画面_ビーストハイ": round_start_beast_count,
                "ラウンド開始画面_リーゼロッテ": round_start_liese_count,
            },
            'mimizu_400_600p_rb_count': mimizu_400_600p_rb_count,
            'mimizu_cz_blank_win_count': mimizu_cz_blank_win_count,
            'mimizu_no_pullback_count': mimizu_no_pullback_count,
            'morning_1g_lever_global': morning_1g_lever, # UI入力値
            'morning_2g_lever_global': morning_2g_lever, # UI入力値
            'current_sasamai': current_sasamai, # UI入力値
            'cz_pass_through_count_for_yame': cz_pass_through_count_for_yame, # UI入力値
            'kessen_bonus_no_at_consecutive_count': kessen_bonus_no_at_consecutive_count_for_yame, # UI入力値
            'total_game_count_for_yame': current_g_for_yame, # UI入力値
            'at_renchan_pattern_for_yame': at_renchan_pattern_for_yame, # UI入力値
            'boost_chance_total_count': boost_chance_total_count_for_yame, # UI入力値
            'boost_chance_bonus_count': boost_chance_bonus_count_for_yame, # UI入力値
            'current_g_after_at_for_yame': st.session_state.get('last_bonus_at_g_count_display', 0), # やめ時判断用
        }
        
        result_content = predict_setting(user_inputs_for_prediction)
        st.markdown(result_content)

# 結果表示ボタンが押されていない状態に戻った場合、脳汁演出を非表示に
if not result_button_clicked and st.session_state.get('show_harikiri_background', False):
    st.session_state.show_harikiri_background = False
    # st.experimental_rerun() はユーザーの操作を妨げる可能性があるので、コメントアウト