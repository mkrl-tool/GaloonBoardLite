from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon():
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img_large = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img_large)

    # 背景角丸四角形（鮮やかなブルー/シアンのグラデーション風）
    # メイン背景
    draw.rounded_rectangle([(16, 16), (240, 240)], radius=48, fill=(30, 41, 59))
    
    # ガルーン風カレンダー上部バー（ヘッダーアクセント）
    draw.rounded_rectangle([(16, 16), (240, 80)], radius=48, fill=(14, 116, 144))
    draw.rectangle([(16, 50), (240, 80)], fill=(14, 116, 144))

    # カレンダーのバインダーリング（2つ）
    draw.rounded_rectangle([(60, 6), (76, 32)], radius=6, fill=(226, 232, 240))
    draw.rounded_rectangle([(180, 6), (196, 32)], radius=6, fill=(226, 232, 240))

    # 行動予定の行（ホワイトボード風のスケジュールバー）
    # メンバー1（在席：緑）
    draw.ellipse([(44, 112), (58, 126)], fill=(34, 197, 94))
    draw.rounded_rectangle([(70, 114), (212, 124)], radius=5, fill=(71, 85, 105))

    # メンバー2（外出：オレンジ）
    draw.ellipse([(44, 152), (58, 166)], fill=(249, 115, 22))
    draw.rounded_rectangle([(70, 154), (180, 164)], radius=5, fill=(71, 85, 105))

    # メンバー3（会議：ブルー）
    draw.ellipse([(44, 192), (58, 206)], fill=(59, 130, 246))
    draw.rounded_rectangle([(70, 194), (196, 204)], radius=5, fill=(71, 85, 105))

    os.makedirs("assets", exist_ok=True)
    img_large.save("assets/app_icon.png")

    # ICOファイル作成（複数解像度）
    images = []
    for s in sizes:
        images.append(img_large.resize(s, Image.Resampling.LANCZOS))
    images[0].save("assets/icon.ico", format="ICO", sizes=[(s[0], s[1]) for s in sizes])
    print("Icons generated successfully!")

if __name__ == "__main__":
    create_app_icon()
