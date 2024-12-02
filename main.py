#!/usr/bin/env python
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageOps, ImageTk
import pathlib
import io
import random


class ImageConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Momentum Image Converter")

        # Store the list of PNG files
        self.png_files = list(pathlib.Path('.').glob("*.png"))
        if not self.png_files:
            tk.Label(root, text="No PNG files found in current directory!").pack(pady=20)
            return

        # Select random image for preview
        self.current_image_index = random.randint(0, len(self.png_files) - 1)

        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Preview frame
        preview_frame = ttk.Frame(main_frame)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Original image preview
        self.original_label = ttk.Label(preview_frame, text="Original:")
        self.original_label.grid(row=0, column=0, padx=10)
        self.original_preview = ttk.Label(preview_frame)
        self.original_preview.grid(row=1, column=0)

        # Converted preview
        self.converted_label = ttk.Label(preview_frame, text="Preview:")
        self.converted_label.grid(row=0, column=1, padx=10)
        self.converted_preview = ttk.Label(preview_frame)
        self.converted_preview.grid(row=1, column=1)

        # Controls
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=10)

        # Threshold slider
        ttk.Label(controls_frame, text="Threshold:").pack()
        self.threshold_var = tk.IntVar(value=128)
        self.threshold_slider = ttk.Scale(
            controls_frame,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            variable=self.threshold_var,
            command=self.update_preview
        )
        self.threshold_slider.pack(fill=tk.X, padx=10)

        # Dithering checkbox
        self.dither_var = tk.BooleanVar(value=False)
        self.dither_check = ttk.Checkbutton(
            controls_frame,
            text="Use dithering",
            variable=self.dither_var,
            command=self.update_preview
        )
        self.dither_check.pack(pady=5)

        # Background color toggle checkbox
        self.bg_color_var = tk.BooleanVar(value=False)
        self.bg_color_check = ttk.Checkbutton(
            controls_frame,
            text="Orange Background Preview",
            variable=self.bg_color_var,
            command=self.update_preview
        )
        self.bg_color_check.pack(pady=5)

        # Navigation buttons
        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(fill=tk.X, pady=10)

        self.prev_button = ttk.Button(nav_frame, text="Previous", command=self.show_previous_image)
        self.prev_button.pack(side=tk.LEFT, padx=10)

        self.next_button = ttk.Button(nav_frame, text="Next", command=self.show_next_image)
        self.next_button.pack(side=tk.LEFT)

        # Status label
        self.status_var = tk.StringVar()
        ttk.Label(main_frame, textvariable=self.status_var).pack(pady=5)

        # Initial preview update after window is drawn
        self.root.bind("<Configure>", self.on_resize)

        # Initial preview update
        self.update_preview()

    def on_resize(self, event):
        """Handle window resize events and update preview"""
        self.update_preview()

    def convert_image(self, img_path, threshold, dither=False):
        """Convert image and return both BM data and preview image"""
        img = Image.open(img_path)

        # Resize to 128x64 while maintaining aspect ratio, then crop from center
        img = img.resize((128, int(img.height * 128 / img.width)), Image.Resampling.LANCZOS)
        img = img.crop(((img.width - 128) // 2, (img.height - 64) // 2, (img.width + 128) // 2, (img.height + 64) // 2))

        # Convert to grayscale
        img = img.convert('L')

        # Convert to black and white
        if dither:
            bw_img = img.convert('1')
        else:
            bw_img = img.point(lambda x: 0 if x < threshold else 255, '1')

        # Create preview image with optional orange background
        preview = bw_img.convert('RGB')
        if self.bg_color_var.get():
            preview_data = preview.load()
            for y in range(preview.height):
                for x in range(preview.width):
                    if preview_data[x, y] == (255, 255, 255):
                        preview_data[x, y] = (255, 130, 0)  # Orange background

        # Convert to XBM format
        bm_image = ImageOps.invert(bw_img)
        with io.BytesIO() as output:
            bm_image.save(output, format="XBM")
            xbm = output.getvalue()

        # Extract binary data
        data = xbm.decode().strip()
        data = data.replace("\n", "").replace(" ", "").split("=")[1][:-1]
        data_str = data[1:-1].replace(",", " ").replace("0x", "")
        data_bin = bytearray.fromhex(data_str)

        return b"\x00" + data_bin, preview

    def update_preview(self, *args):
        """Update the preview images"""
        try:
            # Ensure the preview size is at least a reasonable value
            width = self.root.winfo_width() // 2 or 128
            height = self.root.winfo_height() // 2 or 64

            # Load and resize original
            original = Image.open(self.png_files[self.current_image_index])
            original.thumbnail((width, height))
            original_photo = ImageTk.PhotoImage(original)
            self.original_preview.configure(image=original_photo)
            self.original_preview.image = original_photo

            # Create and show preview
            _, preview = self.convert_image(
                self.png_files[self.current_image_index],
                self.threshold_var.get(),
                self.dither_var.get()
            )
            preview.thumbnail((width, height))
            preview_photo = ImageTk.PhotoImage(preview)
            self.converted_preview.configure(image=preview_photo)
            self.converted_preview.image = preview_photo

            # Update status with image dimensions
            self.status_var.set(f"Image size: {original.width}x{original.height}")

        except Exception as e:
            self.status_var.set(f"Error updating preview: {e}")

    def show_previous_image(self):
        """Show the previous image in the list"""
        self.current_image_index = (self.current_image_index - 1) % len(self.png_files)
        self.update_preview()

    def show_next_image(self):
        """Show the next image in the list"""
        self.current_image_index = (self.current_image_index + 1) % len(self.png_files)
        self.update_preview()

    def convert_all_files(self):
        """Convert all PNG files in the directory"""
        threshold = self.threshold_var.get()
        dither = self.dither_var.get()
        count = 0

        for png_file in self.png_files:
            try:
                bm_data, _ = self.convert_image(png_file, threshold, dither)
                output_file = png_file.parent / png_file.stem
                output_file.write_bytes(bm_data)
                count += 1
            except Exception as e:
                self.status_var.set(f"Error converting {png_file.name}: {e}")
                return

        self.status_var.set(f"Successfully converted {count} files!")


def main():
    root = tk.Tk()
    app = ImageConverterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
