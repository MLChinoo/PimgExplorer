from pathlib import Path

from PIL import Image

def has_transparency(png_path: Path) -> bool:
    img = Image.open(png_path)

    # 情况1：图片带 alpha 通道
    if img.mode in ("RGBA", "LA"):
        alpha = img.getchannel("A")
        # 如果有任何一个像素的 alpha < 255，就说明存在透明像素
        if any(pixel < 255 for pixel in alpha.getdata()):
            return True
        else:
            return False

    # 情况2：索引颜色模式 (P)，可能含透明信息
    elif img.mode == "P":
        # 获取调色板的透明信息
        if "transparency" in img.info:
            return True

    # 其他模式一般不带透明度
    return False

