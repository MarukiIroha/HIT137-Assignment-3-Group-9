"""
Name: Group 9
Date started: 21/05
GitHub URL:https://github.com/MarukiIroha/HIT137-Assignment-3-Group-9
"""
from tkinter import *
from tkinter import filedialog, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk

class ImageEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Editor")
        self.root.geometry("1200x800")

        # Initialize variables
        self.original_image = None
        self.display_image = None
        self.cropped_image = None
        self.photo = None
        self.is_drawing = False
        self.start_x = 0
        self.start_y = 0
        self.rect = None
        self.scale_factor = 1.0
        self.display_ratio = 1.0
        self.is_grayscale = False
        self.brightness_factor = 1.0
        self.undo_stack = []
        self.redo_stack = []

        # Setup GUI
        self.setup_gui()

    def setup_gui(self):
        # Frames
        self.control_frame = ttk.Frame(self.root)
        self.control_frame.pack(side=TOP, fill=X, padx=10, pady=5)

        self.image_frame = ttk.Frame(self.root)
        self.image_frame.pack(side=TOP, fill=BOTH, expand=True)

        # Buttons
        ttk.Button(self.control_frame, text="Load Image", command=self.load_image).pack(side=LEFT, padx=5)
        ttk.Button(self.control_frame, text="Save Image", command=self.save_image).pack(side=LEFT, padx=5)
        ttk.Button(self.control_frame, text="Toggle Grayscale", command=self.toggle_grayscale).pack(side=LEFT, padx=5)
        ttk.Button(self.control_frame, text="Undo", command=self.undo).pack(side=LEFT, padx=5)
        ttk.Button(self.control_frame, text="Redo", command=self.redo).pack(side=LEFT, padx=5)

        # Sliders
        self.size_slider = ttk.Scale(self.control_frame, from_=0.1, to=2.0, orient=HORIZONTAL, 
                                   value=1.0, command=self.update_resize)
        self.size_slider.pack(side=LEFT, padx=5)
        ttk.Label(self.control_frame, text="Resize Scale").pack(side=LEFT, padx=5)

        self.brightness_slider = ttk.Scale(self.control_frame, from_=0.5, to=1.5, orient=HORIZONTAL, 
                                         value=1.0, command=self.update_brightness)
        self.brightness_slider.pack(side=LEFT, padx=5)
        ttk.Label(self.control_frame, text="Brightness").pack(side=LEFT, padx=5)

        # Canvas for image display and cropping
        self.canvas = Canvas(self.image_frame, bg='gray')
        self.canvas.pack(fill=BOTH, expand=True)

        # Bind mouse events for cropping
        self.canvas.bind("<Button-1>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.draw_crop)
        self.canvas.bind("<ButtonRelease-1>", self.end_crop)

        # Bind keyboard shortcuts
        self.root.bind("<Control-o>", lambda event: self.load_image())
        self.root.bind("<Control-s>", lambda event: self.save_image())
        self.root.bind("<Control-g>", lambda event: self.toggle_grayscale())
        self.root.bind("<Control-z>", lambda event: self.undo())
        self.root.bind("<Control-y>", lambda event: self.redo())

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
        if file_path:
            self.original_image = cv2.imread(file_path)
            if self.original_image is None:
                self.canvas.delete("all")
                self.canvas.create_text(100, 50, text="Error: Could not load image", fill="white", font=("Arial", 12))
                return
            self.original_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
            self.cropped_image = None
            self.scale_factor = 1.0
            self.brightness_factor = 1.0
            self.is_grayscale = False
            self.undo_stack = []
            self.redo_stack = []
            self.size_slider.set(1.0)
            self.brightness_slider.set(1.0)
            self.update_display()

    def toggle_grayscale(self):
        if self.cropped_image is None:
            return
        # Save state for undo
        self.undo_stack.append({
            'action': 'grayscale',
            'image': self.cropped_image.copy(),
            'scale_factor': self.scale_factor,
            'brightness_factor': self.brightness_factor,
            'is_grayscale': self.is_grayscale
        })
        self.redo_stack = []
        self.is_grayscale = not self.is_grayscale
        self.update_display()
    
    def undo(self):
        if not self.undo_stack:
            return
        # Save current state for redo
        self.redo_stack.append({
            'action': 'current',
            'image': self.cropped_image.copy() if self.cropped_image is not None else None,
            'scale_factor': self.scale_factor,
            'brightness_factor': self.brightness_factor,
            'is_grayscale': self.is_grayscale
        })
        state = self.undo_stack.pop()
        self.cropped_image = state['image'].copy() if state['image'] is not None else None
        self.scale_factor = state['scale_factor']
        self.brightness_factor = state['brightness_factor']
        self.is_grayscale = state['is_grayscale']
        self.size_slider.set(self.scale_factor)
        self.brightness_slider.set(self.brightness_factor)
        self.update_display()

    def redo(self):
        if not self.redo_stack:
            return
        # Save current state for undo
        self.undo_stack.append({
            'action': 'current',
            'image': self.cropped_image.copy() if self.cropped_image is not None else None,
            'scale_factor': self.scale_factor,
            'brightness_factor': self.brightness_factor,
            'is_grayscale': self.is_grayscale
        })
        state = self.redo_stack.pop()
        self.cropped_image = state['image'].copy() if state['image'] is not None else None
        self.scale_factor = state['scale_factor']
        self.brightness_factor = state['brightness_factor']
        self.is_grayscale = state['is_grayscale']
        self.size_slider.set(self.scale_factor)
        self.brightness_slider.set(self.brightness_factor)
        self.update_display()

    def update_display(self):
        if self.original_image is None:
            self.canvas.delete("all")
            self.canvas.create_text(100, 50, text="No image loaded", fill="white", font=("Arial", 12))
            return

        # Calculate display size while maintaining aspect ratio
        max_display_size = (800, 600)
        h, w = self.original_image.shape[:2]
        self.display_ratio = min(max_display_size[0]/w, max_display_size[1]/h)
        display_size = (int(w * self.display_ratio), int(h * self.display_ratio))

        # Resize image for display
        self.display_image = cv2.resize(self.original_image, display_size, interpolation=cv2.INTER_AREA)

        # Process cropped image if exists
        if self.cropped_image is not None:
            processed_image = self.cropped_image.copy()
            
            # Apply brightness
            processed_image = cv2.convertScaleAbs(processed_image, alpha=self.brightness_factor, beta=0)
            
            # Apply grayscale if enabled
            if self.is_grayscale:
                processed_image = cv2.cvtColor(processed_image, cv2.COLOR_RGB2GRAY)
                processed_image = cv2.cvtColor(processed_image, cv2.COLOR_GRAY2RGB)  # Convert back for display
            
            # Resize cropped image
            scaled_size = (max(1, int(processed_image.shape[1] * self.scale_factor)),
                          max(1, int(processed_image.shape[0] * self.scale_factor)))
            display_cropped = cv2.resize(processed_image, scaled_size, interpolation=cv2.INTER_AREA)
            
            # Combine original and cropped images side by side
            combined_width = self.display_image.shape[1] + display_cropped.shape[1]
            combined_height = self.display_image.shape[0]
            combined_image = np.zeros((combined_height, combined_width, 3), dtype=np.uint8)
            combined_image[:self.display_image.shape[0], :self.display_image.shape[1]] = self.display_image
            combined_image[:display_cropped.shape[0], self.display_image.shape[1]:] = display_cropped
        else:
            combined_image = self.display_image
            combined_width = self.display_image.shape[1]
            combined_height = self.display_image.shape[0]

        # Convert to PhotoImage
        self.photo = ImageTk.PhotoImage(image=Image.fromarray(combined_image))
        self.canvas.config(width=combined_width, height=combined_height)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.photo, anchor=NW)

    def start_crop(self, event):
        if self.original_image is None:
            return
        self.is_drawing = True
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = None

    def draw_crop(self, event):
        if self.is_drawing:
            if self.rect:
                self.canvas.delete(self.rect)
            self.rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline='red', width=2)

    def end_crop(self, event):
        if self.is_drawing:
            self.is_drawing = False
            if self.original_image is not None:
                # Convert canvas coordinates to image coordinates
                h, w = self.original_image.shape[:2]
                x1 = int(self.start_x / self.display_ratio)
                y1 = int(self.start_y / self.display_ratio)
                x2 = int(event.x / self.display_ratio)
                y2 = int(event.y / self.display_ratio)

                # Ensure coordinates are within bounds
                x1, x2 = sorted([x1, x2])
                y1, y2 = sorted([y1, y2])
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)

                # Debug output
                print(f"Cropping coordinates: x1={x1}, y1={y1}, x2={x2}, y2={y2}")

                # Crop image
                if x2 > x1 and y2 > y1:
                    # Save state for undo
                    self.undo_stack.append({
                        'action': 'crop',
                        'image': self.cropped_image.copy() if self.cropped_image is not None else None,
                        'scale_factor': self.scale_factor,
                        'brightness_factor': self.brightness_factor,
                        'is_grayscale': self.is_grayscale
                    })
                    self.redo_stack = []
                    self.cropped_image = self.original_image[y1:y2, x1:x2]
                    self.update_display()
                else:
                    print("Invalid crop area: Zero or negative dimensions")
    
    def update_resize(self, value):
        try:
            new_scale = float(value)
            if self.cropped_image is not None and new_scale != self.scale_factor:
                # Save state for undo
                self.undo_stack.append({
                    'action': 'resize',
                    'image': self.cropped_image.copy(),
                    'scale_factor': self.scale_factor,
                    'brightness_factor': self.brightness_factor,
                    'is_grayscale': self.is_grayscale
                })
                self.redo_stack = []
                self.scale_factor = new_scale
                self.update_display()
        except ValueError:
            print("Invalid slider value")

    def update_brightness(self, value):
        try:
            new_brightness = float(value)
            if self.cropped_image is not None and new_brightness != self.brightness_factor:
                # Save state for undo
                self.undo_stack.append({
                    'action': 'brightness',
                    'image': self.cropped_image.copy(),
                    'scale_factor': self.scale_factor,
                    'brightness_factor': self.brightness_factor,
                    'is_grayscale': self.is_grayscale
                })
                self.redo_stack = []
                self.brightness_factor = new_brightness
                self.update_display()
        except ValueError:
            print("Invalid brightness value")
    
    def save_image(self):
        if self.cropped_image is not None:
            file_path = filedialog.asksaveasfilename(defaultextension=".png",filetypes=[("PNG files", "*.png"),("JPEG files", "*.jpg")])
            if file_path:
                processed_image = self.cropped_image.copy()
                # Apply brightness
                processed_image = cv2.convertScaleAbs(processed_image, alpha=self.brightness_factor, beta=0)
                # Apply grayscale if enabled
                if self.is_grayscale:
                    processed_image = cv2.cvtColor(processed_image, cv2.COLOR_RGB2GRAY)
                    processed_image = cv2.cvtColor(processed_image, cv2.COLOR_GRAY2RGB)
                # Resize
                scaled_size = (max(1, int(processed_image.shape[1] * self.scale_factor)),
                             max(1, int(processed_image.shape[0] * self.scale_factor)))
                save_image = cv2.resize(processed_image, scaled_size, interpolation=cv2.INTER_AREA)
                save_image = cv2.cvtColor(save_image, cv2.COLOR_RGB2BGR)
                cv2.imwrite(file_path, save_image)


root = Tk()
app = ImageEditor(root)
root.mainloop()