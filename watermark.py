import os
import csv
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

RAW_FOLDER = 'raw'
WATERMARKED_FOLDER = 'watermarked'
WATERMARK_OPACITY = 0.8 #Transparency 0-1 - 0 means invisible, 1 means solid
WATERMARK_IMAGE = 'watermark.png'  # Assuming watermark.png is in the same directory as the script
IMAGE_QUALITY = 100 #Change as needed, 1-100 - smaller number means smaller file size
CSV_FILENAME = 'data.csv'
SUPPORTED_IMAGE_FORMATS = (".jpg", ".jpeg", ".png")

watermark = Image.open(WATERMARK_IMAGE).convert("RGBA")

def calculate_watermark_size_and_position(watermark, base_image):
    base_width, base_height = base_image.size
    watermark_width, watermark_height = watermark.size

    # Scaling factor for X % size relative to the base image
    scaling_factor = min(base_width / watermark_width, base_height / watermark_height) * WATERMARK_OPACITY

    new_size = (int(watermark_width * scaling_factor), int(watermark_height * scaling_factor))

    # Calculate the position to place the watermark, ensuring values are integers
    position = (
        int((base_width - new_size[0]) / 2),
        int((base_height - new_size[1]) / 2)
    )

    resized_watermark = watermark.resize(new_size, Image.LANCZOS)

    return resized_watermark, position

# Function to apply watermark to an image
def apply_watermark(image_path, save_path):
    base_image = Image.open(image_path).convert("RGBA")
    watermark_resized, position = calculate_watermark_size_and_position(watermark, base_image)
    combined = Image.new("RGBA", base_image.size)
    combined.paste(base_image, (0, 0))
    combined.paste(watermark_resized, position, watermark_resized)
    combined = combined.convert("RGB")  

    new_filename = image_path.stem + '.jpg'
    new_file_path = save_path / new_filename
    combined.save(new_file_path, "JPEG")
    print(f"Watermarked {image_path.stem}")
    return image_path.name, str(image_path), new_filename, str(new_file_path)

def process_images_in_folder(folder_path, save_path):
    script_directory = os.path.dirname(os.path.realpath(__file__))
    csv_file_path = os.path.join(script_directory, CSV_FILENAME)

    with open(csv_file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Original Filename', 'Original Filepath', 'New Filename', 'New Filepath'])

        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = []

            for image_path in Path(folder_path).rglob("*"):
                if image_path.is_file() and image_path.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
                    if not image_path.stem.endswith('_s') and not WATERMARKED_FOLDER in image_path: ## Needs new logic
                        futures.append(executor.submit(apply_watermark, image_path, save_path))

            for future in futures:
                try:
                    result = future.result()
                    writer.writerow(result)
                except Exception as e:
                    print(f"Error processing {image_path.name}: {e}")
                    writer.writerow([image_path.name, str(image_path), 'Error', str(e)])

    return csv_file_path

def main():
    root = tk.Tk()
    root.withdraw()  

    folder_path = filedialog.askdirectory(title="Choose the folder of images you would like to watermark")
    if not folder_path: 
        print("Folder selection was canceled. Exiting.")
        return

    images_folder_path = Path(folder_path)
    save_path = images_folder_path / 'watermarked'
    csv_file_path = process_images_in_folder(images_folder_path, save_path)
    print(f"Processing complete. Details logged to {csv_file_path}")

if __name__ == '__main__':
    main()
