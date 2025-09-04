import os
import re
import cv2
import math
import pandas as pd

# ====== 入力ファイル（添付に合わせて固定）======
VIDEO_PATH = r"/home/kota/ドキュメント/data_creator/cap-2025-08-27-08-37-02.mp4"
CSV_PATH   = r"/home/kota/ドキュメント/data_creator/xy_log_2025-08-27_083636.csv"

# ====== 出力先 ======
OUT_DIR = r"/home/kota/ドキュメント/data_creator"  # なければ作ります
EXT = ".png"                  # 保存拡張子（.png 推奨）

# ====== 切り出し間隔（秒）======
INTERVAL_SEC = 0.5

# ====== 行番号とフォルダ名の対応 (1始まり) ======
mapping = {
    1: "x",
    2: "y",
    3: "z",
    5: "w_quat",
    6: "z_quat"
}

THRESHOLD = 300  # 300以上

def sanitize_folder_name(name: str, maxlen: int = 200) -> str:
    """フォルダ名に使いにくい文字を安全化。"""
    name = name.strip()
    # 許可: 英数, 空白, _, -, . のみ
    name = re.sub(r"[^0-9A-Za-z\-\._ ]+", "_", name)
    name = re.sub(r"\s+", "_", name).strip("._")
    if not name:
        name = "val"
    if len(name) > maxlen:
        name = name[:maxlen]
    return name

def format_value(v) -> str:
    """数値をフォルダ名文字列へ。整数は整数、そうでなければできるだけ短く。"""
    if pd.isna(v):
        return None
    try:
        num = float(v)
    except Exception:
        return None
    # 300以上だけ残す
    if not (num >= THRESHOLD):
        return None
    # ほぼ整数なら整数表記に
    if math.isclose(num, round(num), rel_tol=0, abs_tol=1e-9):
        s = str(int(round(num)))
    else:
        # 余計な0を避けつつ短めに（最大12桁相当）
        s = f"{num:.12g}"
    return sanitize_folder_name(s)

def create_folders():
    # 出力基準ディレクトリを作成
    os.makedirs(OUT_DIR, exist_ok=True)

    # CSVを読み込む（中身は今回使わないが存在確認のため）
    df = pd.read_csv(CSV_PATH)

    # マッピングに基づいてフォルダ作成
    for row_num, folder_name in mapping.items():
        if 1 <= row_num <= len(df):
            path = os.path.join(OUT_DIR, folder_name)
            os.makedirs(path, exist_ok=True)
            print(f"✅ 作成しました: {path}")
        else:
            print(f"⚠ 行 {row_num} はCSVに存在しません。スキップしました。")

def sanitize_filename(s: str, maxlen: int = 200) -> str:
    """
    ファイル名に使えない/危険な文字を安全化して返す。
    連続アンダースコアの整理と長さ制限も行う。
    """
    # 改行やタブの除去
    s = s.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    # 記号のうち許すのは [a-zA-Z0-9-_. ] のみ。その他は _ に。
    s = re.sub(r"[^0-9A-Za-z\-\._ ]+", "_", s)
    # 空白は _ に
    s = re.sub(r"\s+", "_", s)
    # 連続アンダースコアを1つに
    s = re.sub(r"_+", "_", s).strip("_")
    # Windows予約名の回避（念のため）
    reserved = {"CON","PRN","AUX","NUL","COM1","COM2","COM3","COM4","COM5","COM6","COM7","COM8","COM9",
                "LPT1","LPT2","LPT3","LPT4","LPT5","LPT6","LPT7","LPT8","LPT9"}
    if s.upper() in reserved:
        s = f"_{s}_"
    # 長すぎる場合は切る
    if len(s) > maxlen:
        s = s[:maxlen]
    # 空になったらプレースホルダ
    if not s:
        s = "row"
    return s

def row_to_name(row) -> str:
    """
    1行ぶんの値を連結して名前文字列に。
    列名付きCSVでも値だけを安全に拾います。
    """
    # 値を文字列に変換して連結（カンマ区切り）
    vals = [str(v) for v in row.tolist()]
    raw = ",".join(vals)
    return sanitize_filename(raw)

def main():
#     # 出力フォルダ用意
#     os.makedirs(OUT_DIR, exist_ok=True)

#     # CSV読み込み
#     df = pd.read_csv(CSV_PATH)
#     num_rows = len(df)

#     # 動画を開く
#     cap = cv2.VideoCapture(VIDEO_PATH)
#     if not cap.isOpened():
#         raise RuntimeError(f"動画を開けませんでした: {VIDEO_PATH}")

#     fps = cap.get(cv2.CAP_PROP_FPS)
#     frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#     duration_sec = frame_count / fps if fps > 0 else 0.0

#     # 0.0, 0.5, 1.0, ... の切り出し時刻配列
#     if duration_sec <= 0:
#         raise RuntimeError("動画の長さを取得できませんでした。")

#     times = []
#     t = 0.0
#     # 浮動小数の誤差を抑えるため丸め込み
#     while t <= duration_sec + 1e-6:
#         times.append(round(t, 3))
#         t += INTERVAL_SEC

#     # 実際に切り出す枚数は CSV 行数と times の小さい方
#     N = min(len(times), num_rows)

#     print(f"動画長: {duration_sec:.3f}s, FPS: {fps:.3f}, 総フレーム: {frame_count}")
#     print(f"切り出し間隔: {INTERVAL_SEC}s, 予定切り出し枚数: {len(times)}")
#     print(f"CSV行数: {num_rows}, 実際に保存する枚数: {N}")

#     saved = 0
#     for i in range(N):
#         t_sec = times[i]
#         # ミリ秒指定で位置を移動（より正確）
#         cap.set(cv2.CAP_PROP_POS_MSEC, t_sec * 1000.0)
#         ok, frame = cap.read()
#         if not ok or frame is None:
#             # 読めない場合は近いフレーム番号で再挑戦
#             target_frame_idx = int(round(t_sec * fps))
#             cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, target_frame_idx))
#             ok2, frame = cap.read()
#             if not ok2 or frame is None:
#                 print(f"[WARN] {t_sec:.3f}s のフレーム取得に失敗しました。スキップします。")
#                 continue

#         # 対応するCSV行からファイル名を作る
#         name_core = row_to_name(df.iloc[i])
#         # 重複回避：同名があれば _1, _2... を付ける
#         out_path = os.path.join(OUT_DIR, name_core + EXT)
#         if os.path.exists(out_path):
#             suffix = 1
#             while True:
#                 candidate = os.path.join(OUT_DIR, f"{name_core}_{suffix}{EXT}")
#                 if not os.path.exists(candidate):
#                     out_path = candidate
#                     break
#                 suffix += 1

#         # 画像保存（PNG）
#         ok_save = cv2.imwrite(out_path, frame)
#         if not ok_save:
#             print(f"[WARN] 保存失敗: {out_path}")
#             continue

#         saved += 1
#         # 進捗表示（任意）
#         if saved % 20 == 0 or i == N - 1:
#             print(f"Saved {saved}/{N}")

#     cap.release()
#     print(f"完了: {saved} 枚保存しました。出力先: {OUT_DIR}")
    create_folders()

if __name__ == "__main__":
    main()
