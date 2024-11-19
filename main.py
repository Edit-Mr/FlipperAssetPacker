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
        self.root.title("PNG to BM Converter")
        
        # Preview size multiplier
        self.preview_size = 600  # Base size (200 * 3)
        
        # Store the list of PNG files
        self.png_files = list(pathlib.Path('.').glob("*.png"))
        if not self.png_files:
            tk.Label(root, text="No PNG files found in current directory!").pack(pady=20)
            return
            
        # Select random image for preview
        self.current_image_path = random.choice(self.png_files)
        
        # Create main frame with horizontal layout
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Preview frame (left side)
        preview_frame = ttk.Frame(main_frame)
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Original image preview
        self.original_label = ttk.Label(preview_frame, text="Original:", font=('Arial', 12, 'bold'))
        self.original_label.pack(pady=(0, 5))
        self.original_preview = ttk.Label(preview_frame)
        self.original_preview.pack()
        
        # Converted preview
        self.converted_label = ttk.Label(preview_frame, text="Preview:", font=('Arial', 12, 'bold'))
        self.converted_label.pack(pady=(20, 5))
        self.converted_preview = ttk.Label(preview_frame)
        self.converted_preview.pack()
        
        # Controls frame (right side)
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))
        
        # Controls group
        controls_group = ttk.LabelFrame(controls_frame, text="Settings", padding="10")
        controls_group.pack(fill=tk.X, pady=(0, 10))
        
        # Threshold slider
        ttk.Label(controls_group, text="Threshold:").pack()
        self.threshold_var = tk.IntVar(value=128)
        self.threshold_slider = ttk.Scale(
            controls_group,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            variable=self.threshold_var,
            command=self.update_preview
        )
        self.threshold_slider.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Dithering checkbox
        self.dither_var = tk.BooleanVar(value=False)
        self.dither_check = ttk.Checkbutton(
            controls_group,
            text="Use dithering",
            variable=self.dither_var,
            command=self.update_preview
        )
        self.dither_check.pack(pady=5)
        
        # Buttons group
        buttons_group = ttk.LabelFrame(controls_frame, text="Actions", padding="10")
        buttons_group.pack(fill=tk.X)
        
        # Random image button
        ttk.Button(
            buttons_group,
            text="Try Another Random Image",
            command=self.select_random_image
        ).pack(fill=tk.X, pady=(0, 5))
        
        # Convert all button
        ttk.Button(
            buttons_group,
            text="Convert All Files",
            command=self.convert_all_files
        ).pack(fill=tk.X, pady=(0, 5))
        
        # Status label
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(
            controls_frame, 
            textvariable=self.status_var,
            wraplength=200
        )
        self.status_label.pack(pady=10)
        
        # Initial preview
        self.update_preview()

    def convert_image(self, img_path, threshold, dither=False):
        """Convert image and return both BM data and preview image"""
        img = Image.open(img_path)
        # Convert to grayscale
        img = img.convert('L')
        
        # Convert to black and white
        if dither:
            preview = img.convert('1')
        else:
            preview = img.point(lambda x: 0 if x < threshold else 255, '1')
        
        # For BM format, we need to invert
        bm_image = ImageOps.invert(preview)
        
        # Convert to XBM format
        with io.BytesIO() as output:
            bm_image.save(output, format="XBM")
            xbm = output.getvalue()
        
        # Extract binary data
        data = xbm.decode().strip()
        data = data.replace("\n", "").replace(" ", "").split("=")[1][:-1]
        data_str = data[1:-1].replace(",", " ").replace("0x", "")
        data_bin = bytearray.fromhex(data_str)
        
        return b"\x00" + data_bin, preview

    def resize_with_aspect(self, image, max_size):
        """Resize image keeping aspect ratio"""
        ratio = min(max_size / image.width, max_size / image.height)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        return image.resize(new_size, Image.Resampling.LANCZOS)

    def update_preview(self, *args):
        """Update the preview images"""
        try:
            # Load original
            original = Image.open(self.current_image_path)
            # Resize keeping aspect ratio
            original = self.resize_with_aspect(original, self.preview_size)
            original_photo = ImageTk.PhotoImage(original)
            self.original_preview.configure(image=original_photo)
            self.original_preview.image = original_photo
            
            # Create and show preview
            _, preview = self.convert_image(
                self.current_image_path,
                self.threshold_var.get(),
                self.dither_var.get()
            )
            preview = self.resize_with_aspect(preview, self.preview_size)
            preview_photo = ImageTk.PhotoImage(preview)
            self.converted_preview.configure(image=preview_photo)
            self.converted_preview.image = preview_photo
            
            # Update status with image dimensions
            self.status_var.set(f"Image size: {original.width}x{original.height}")
            
        except Exception as e:
            self.status_var.set(f"Error updating preview: {e}")

    def select_random_image(self):
        """Select a new random image for preview"""
        if len(self.png_files) > 1:
            current_idx = self.png_files.index(self.current_image_path)
            available_files = self.png_files[:current_idx] + self.png_files[current_idx + 1:]
            self.current_image_path = random.choice(available_files)
        else:
            self.current_image_path = self.png_files[0]
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