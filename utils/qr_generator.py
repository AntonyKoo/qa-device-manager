import os, qrcode
from PIL import Image, ImageDraw, ImageFont

QR_DIR = os.path.join("static", "qr_codes")
os.makedirs(QR_DIR, exist_ok=True)

def generate_qr_images(devices, ip):
    base_url = f"http://{ip}:5000/rent?device="

    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()

    for device in devices:
        url = f"{base_url}{device}"
        qr_img = qrcode.make(url).convert("RGB")

        text_height = 30
        new_img = Image.new("RGB", (qr_img.width, qr_img.height + text_height), "white")
        new_img.paste(qr_img, (0, 0))

        draw = ImageDraw.Draw(new_img)
        bbox = draw.textbbox((0, 0), device, font=font)
        text_x = (qr_img.width - (bbox[2] - bbox[0])) // 2
        # draw.text((text_x, qr_img.height + 5), device, font=font, fill="black")

        new_img.save(os.path.join(QR_DIR, f"{device}.png"))
