import os
import csv
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageEnhance
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import datetime
import shutil  # For copying files

# Constants
RAW_FOLDER = 'raw'
RAW_SQUARED_FOLDER = 'raw_squared'
WATERMARKED_FOLDER = 'watermarked'
WATERMARKED_SQUARED_FOLDER = 'watermark_squared'
WATERMARK_IMAGE = 'watermark.png'  # Assuming watermark.png is in the same directory as the script

def generate_filename(base_name, extension):
    counter = 1
    filename = f"{base_name}.{extension}"

    while os.path.exists(filename):
        filename = f"{base_name}-{counter}.{extension}"
        counter += 1

    return filename
output_csv_path = generate_filename(f'imageprocessor_{datetime.date.today().strftime("%d%b%Y").lower()}', 'csv')

def square_image(image_path, save_path, suffix):
    image = Image.open(image_path)
    width, height = image.size
    new_filename = image_path.stem + suffix + '.jpg'
    new_file_path = save_path / new_filename

    if width != height:
        bigside = max(width, height)
        background = Image.new('RGB', (bigside, bigside), (255, 255, 255))
        offset = ((bigside - width) // 2, (bigside - height) // 2)
        background.paste(image, offset)
        image = background

    image = image.convert('RGB')  # Ensure image is in RGB mode
    image.save(new_file_path, "JPEG", quality=75)
    print(f"Processed {image_path.name} to {new_filename}")


def apply_watermark(image_stem, save_path, original_suffix, opacity=0.8):
    watermark = Image.open(WATERMARK_IMAGE).convert("RGBA")

    alpha = watermark.split()[-1]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)

    watermark.putalpha(alpha)

    raw_image_path = save_path.parent / RAW_FOLDER / (image_stem + '_r' + original_suffix)
    base_image = Image.open(raw_image_path).convert("RGBA")

    base_width, base_height = base_image.size
    watermark_width, watermark_height = watermark.size
    scaling_factor = min(base_width / watermark_width, base_height / watermark_height) * 0.8
    new_size = (int(watermark_width * scaling_factor), int(watermark_height * scaling_factor))
    position = (int((base_width - new_size[0]) / 2), int((base_height - new_size[1]) / 2))
    resized_watermark = watermark.resize(new_size, Image.LANCZOS)

    combined = Image.new("RGBA", base_image.size)
    combined.paste(base_image, (0, 0))
    combined.paste(resized_watermark, position, resized_watermark)
    combined = combined.convert("RGB")

    new_filename = image_stem + '_w.jpg'
    new_file_path = save_path / new_filename
    combined.save(new_file_path, "JPEG")
    print(f"Watermarked {new_filename}")

def process_image(image_path, folders):
    raw_image_name = image_path.stem + '_r' + image_path.suffix
    raw_image_path = folders['raw'] / raw_image_name
    shutil.copy(image_path, raw_image_path)

    square_image(raw_image_path, folders['raw_squared'], '_s')
    apply_watermark(image_path.stem, folders['watermarked'], image_path.suffix)
    watermarked_image_name = image_path.stem + '_w.jpg'
    watermarked_image_path = folders['watermarked'] / watermarked_image_name
    square_image(watermarked_image_path, folders['watermarked_squared'], '_s')

    return {
        "original": str(image_path),
        "raw": str(raw_image_path),
        "raw_squared": str(folders['raw_squared'] / (raw_image_name.replace(image_path.suffix, '_s.jpg'))),
        "watermarked": str(watermarked_image_path),
        "watermarked_squared": str(folders['watermarked_squared'] / watermarked_image_name.replace('.jpg', '_s.jpg'))
    }

def process_images_parallel(folder_path, folders):
    with open(output_csv_path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["original", "raw", "raw_squared", "watermarked", "watermarked_squared"])
        writer.writeheader()

        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = [executor.submit(process_image, image_path, folders)
                       for image_path in folder_path.glob("*.*")
                       if image_path.is_file() and image_path.suffix.lower() in (".jpg", ".png")]

            for future in futures:
                writer.writerow(future.result())

def main():
    root = tk.Tk()
    root.withdraw()
    folder_path = Path(filedialog.askdirectory(title="Choose folder of images you would like to process"))

    folders = {
        'raw': folder_path / RAW_FOLDER,
        'raw_squared': folder_path / RAW_SQUARED_FOLDER,
        'watermarked': folder_path / WATERMARKED_FOLDER,
        'watermarked_squared': folder_path / WATERMARKED_SQUARED_FOLDER
    }

    for folder in folders.values():
        folder.mkdir(exist_ok=True)

    process_images_parallel(folder_path, folders)

if __name__ == '__main__':
    main()
