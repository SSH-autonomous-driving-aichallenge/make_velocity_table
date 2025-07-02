import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Button
from matplotlib import colors, cm
import os

# --- 設定 ---
CSV_FILE_PATH = '/home/yuki/aichallenge-2025/aichallenge/workspace/src/aichallenge_submit/simple_trajectory_generator/data/raceline_awsim_30km.csv'
# 色分けに使用する速度の最小値と最大値
SPEED_MIN = 5.0
SPEED_MAX = 15.0

# --- データの準備 ---
if not os.path.exists(CSV_FILE_PATH):
    print(f"'{CSV_FILE_PATH}' が見つかりません。サンプルデータで新しいファイルを作成します。")
    csv_data_content = """x,y,z,x_quat,y_quat,z_quat,w_quat,speed
89630.0674883,43130.6945594,0.0,0.0,0.0,0.8908735393706145,0.4542514026937883,5.0
89628.3148229,43133.1098699,0.0,0.0,0.0,0.8876786755288125,0.4604634285276228,6.0
89626.5962446,43135.5491846,0.0,0.0,0.0,0.8865758413551225,0.4625832655052025,7.0
89624.8893618,43137.9966586,0.0,0.0,0.0,0.8866177348157583,0.46250296465014545,8.0
89623.1819638,43140.4439264,0.0,0.0,0.0,0.886022717946053,0.4636418265034863,9.0
89621.4806511,43142.8958758,0.0,0.0,0.0,0.8858404744325861,0.4639899286159677,10.0
89620.0,43145.0,0.0,0.0,0.0,0.885,0.464,11.0
89618.0,43148.0,0.0,0.0,0.0,0.884,0.465,12.0
89615.0,43150.0,0.0,0.0,0.0,0.883,0.466,13.0
89612.0,43152.0,0.0,0.0,0.0,0.882,0.467,14.0
89610.0,43150.0,0.0,0.0,0.0,0.881,0.468,15.0
89612.0,43148.0,0.0,0.0,0.0,0.880,0.469,14.0
89615.0,43145.0,0.0,0.0,0.0,0.879,0.470,13.0
89620.0,43140.0,0.0,0.0,0.0,0.878,0.471,12.0
89625.0,43135.0,0.0,0.0,0.0,0.877,0.472,11.0
"""
    with open(CSV_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(csv_data_content)

df = pd.read_csv(CSV_FILE_PATH)

# グローバル変数
selected_indices = []
indices_to_update = []
highlight_plot = None
scatter_plot = None # scatterオブジェクトをグローバルで保持

# --- Matplotlibのセットアップ ---
fig, ax = plt.subplots(figsize=(12, 8))
plt.subplots_adjust(bottom=0.25, right=0.85) # カラーバー用のスペースを確保

# 色と速度のマッピングを設定
cmap = plt.get_cmap('viridis') # 青 -> 緑 -> 黄色 のカラースキーム
normalizer = colors.Normalize(vmin=SPEED_MIN, vmax=SPEED_MAX)

# --- プロットの描画 ---
# 軌跡の線を描画
ax.plot(df['x'], df['y'], '-', color='lightgray', zorder=1)
# 速度に応じて色分けされたウェイポイントを描画
scatter_plot = ax.scatter(
    df['x'], df['y'], 
    c=df['speed'], 
    cmap=cmap, 
    norm=normalizer,
    s=50, # マーカーのサイズ
    zorder=2, # 線より手前に表示
    picker=True, 
    pickradius=5
)

ax.set_xlabel("X-coordinate")
ax.set_ylabel("Y-coordinate")
ax.set_title("Click a waypoint to start selection")
ax.grid(True)
ax.axis('equal')

# カラーバーを追加
cbar = fig.colorbar(cm.ScalarMappable(norm=normalizer, cmap=cmap), ax=ax, fraction=0.046, pad=0.04)
cbar.set_label('Speed (m/s)')

def get_shorter_path_indices(idx1, idx2, n_points):
    i, j = min(idx1, idx2), max(idx1, idx2)
    path_forward = list(range(i, j + 1))
    path_wrap = list(range(j, n_points)) + list(range(0, i + 1))
    return path_forward if len(path_forward) <= len(path_wrap) else path_wrap

def on_pick(event):
    global selected_indices, indices_to_update, highlight_plot

    # scatter_plot以外でのイベントは無視
    if event.artist != scatter_plot:
        return

    ind = event.ind[0]
    
    if len(selected_indices) >= 2:
        selected_indices.clear()
        indices_to_update.clear()

    selected_indices.append(ind)
    
    if highlight_plot:
        highlight_plot.remove()
        highlight_plot = None

    if len(selected_indices) == 1:
        idx1 = selected_indices[0]
        highlight_plot, = ax.plot(df.at[idx1, 'x'], df.at[idx1, 'y'], 'o', markersize=12, mfc='none', mec='red', mew=2)
        ax.set_title(f"Waypoint {idx1} selected. Click a second waypoint.")
        indices_to_update.clear()

    elif len(selected_indices) == 2:
        idx1, idx2 = selected_indices[0], selected_indices[1]
        indices_to_update = get_shorter_path_indices(idx1, idx2, len(df))
        
        highlight_x = df.loc[indices_to_update, 'x']
        highlight_y = df.loc[indices_to_update, 'y']
        highlight_plot, = ax.plot(highlight_x, highlight_y, 'o', markersize=12, mfc='none', mec='red', mew=2)
        ax.set_title(f"Selected {len(indices_to_update)} waypoints. Enter new speed.")

    fig.canvas.draw_idle()

def update_speed(text):
    if not indices_to_update:
        ax.set_title("Please select a range of waypoints first!")
        fig.canvas.draw_idle()
        return

    try:
        new_speed = float(text)
        df.loc[indices_to_update, 'speed'] = new_speed
        
        # ★ プロットの色を更新
        scatter_plot.set_array(df['speed'])
        
        ax.set_title(f"{len(indices_to_update)} waypoints' speed updated to: {new_speed:.2f} m/s")
        print(f"Indices {indices_to_update} speed updated to: {new_speed}")
        fig.canvas.draw_idle()
    except ValueError:
        ax.set_title("Invalid input. Please enter a number for speed.")
        fig.canvas.draw_idle()

def save_to_csv(event):
    try:
        df.to_csv(CSV_FILE_PATH, index=False, float_format='%.15g')
        ax.set_title(f"Changes saved successfully to '{CSV_FILE_PATH}'!")
        print(f"\n--- Changes saved successfully to '{CSV_FILE_PATH}' ---")
        fig.canvas.draw_idle()
    except Exception as e:
        ax.set_title(f"Error saving file: {e}")
        print(f"Error saving file: {e}")
        fig.canvas.draw_idle()

def reset_selection(event):
    global selected_indices, indices_to_update, highlight_plot
    selected_indices.clear()
    indices_to_update.clear()
    if highlight_plot:
        highlight_plot.remove()
        highlight_plot = None
    ax.set_title("Selection reset. Click a waypoint to start.")
    fig.canvas.draw_idle()

# --- GUIウィジェットの作成 ---
ax_box = plt.axes([0.25, 0.08, 0.2, 0.075])
speed_text_box = TextBox(ax_box, 'Speed (m/s)', initial="")
speed_text_box.on_submit(update_speed)

ax_button_save = plt.axes([0.48, 0.08, 0.15, 0.075])
button_save = Button(ax_button_save, 'Save to CSV')
button_save.on_clicked(save_to_csv)

ax_button_reset = plt.axes([0.65, 0.08, 0.15, 0.075])
button_reset = Button(ax_button_reset, 'Reset Selection')
button_reset.on_clicked(reset_selection)

# イベントハンドラを接続
fig.canvas.mpl_connect('pick_event', on_pick)

plt.show()