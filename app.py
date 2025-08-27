import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Scrollbar, Toplevel
from PIL import Image, ImageTk
import os
from utils import save_annotations

class BboxCoordinatesPicker:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Annotation Tool")
        self.root.geometry("1200x800")

        # Main layout frames
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        self.left_frame = tk.Frame(self.main_frame, width=250, relief="sunken", borderwidth=1)
        self.left_frame.pack(side="left", fill="y", padx=5, pady=5)
        self.left_frame.pack_propagate(False)

        self.canvas_frame = tk.Frame(self.main_frame, relief="sunken", borderwidth=1)
        self.canvas_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # --- Top bar for controls ---
        top_frame = tk.Frame(self.canvas_frame)
        top_frame.pack(side="top", fill="x", pady=2)

        self.upload_button = tk.Button(top_frame, text="Upload Image", command=self.upload_image)
        self.upload_button.pack(side="left", padx=5)

        # --- Drawing Mode Selection ---
        self.draw_mode = tk.StringVar(value="BBox")
        tk.Label(top_frame, text="Mode:").pack(side="left", padx=(10,2))
        tk.Radiobutton(top_frame, text="BBox", variable=self.draw_mode, value="BBox", command=self.cancel_drawing).pack(side="left")
        tk.Radiobutton(top_frame, text="Polygon", variable=self.draw_mode, value="Polygon", command=self.cancel_drawing).pack(side="left")

        # Canvas for image display
        self.canvas = tk.Canvas(self.canvas_frame, cursor="cross", bg="black")
        self.canvas.pack(fill="both", expand=True)

        # --- Bottom bar for controls ---
        bottom_frame = tk.Frame(self.canvas_frame)
        bottom_frame.pack(side="bottom", fill="x", pady=2)

        # --- Left Panel Widgets ---
        tk.Label(self.left_frame, text="Annotations", font=("Helvetica", 12, "bold")).pack(pady=5)
        
        self.annotation_list_frame = tk.Frame(self.left_frame)
        self.annotation_list_frame.pack(fill="both", expand=True, padx=5)
        
        self.annotation_listbox = Listbox(self.annotation_list_frame, selectmode=tk.SINGLE)
        self.annotation_listbox.pack(side="left", fill="both", expand=True)
        
        self.annotation_scrollbar = Scrollbar(self.annotation_list_frame, orient="vertical", command=self.annotation_listbox.yview)
        self.annotation_scrollbar.pack(side="right", fill="y")
        self.annotation_listbox.config(yscrollcommand=self.annotation_scrollbar.set)
        self.annotation_listbox.bind("<<ListboxSelect>>", self.on_annotation_select)

        self.delete_button = tk.Button(self.left_frame, text="Delete Selected", command=self.delete_selected_annotation)
        self.delete_button.pack(pady=5)

        # --- Bottom Bar Widgets ---
        # Label Entry
        tk.Label(bottom_frame, text="Label:").pack(side="left", padx=(10, 0))
        self.label_text = tk.StringVar(value="object") # Default label
        self.label_entry = tk.Entry(bottom_frame, textvariable=self.label_text)
        self.label_entry.pack(side="left", padx=5)

        self.coordinates_label = tk.Label(bottom_frame, text="Status: Load an image to begin.")
        self.coordinates_label.pack(side="left", padx=10)

        self.save_annotation_button = tk.Button(bottom_frame, text="Save Annotations", command=self.save_annotation_dialog)
        self.save_annotation_button.pack(side="right", padx=5)

        # --- Class attributes ---
        self.original_image = None
        self.image_path = None
        self.tk_image = None
        self.annotations = []
        self.selected_annotation_index = -1
        
        # Drawing state
        self.drawing = False
        self.start_x, self.start_y = None, None
        self.current_rect_id = None
        self.current_polygon_points = []
        self.current_polygon_id = None

        # Pan and Zoom state
        self.pan_start_x, self.pan_start_y = 0, 0
        self.canvas_x, self.canvas_y = 0, 0
        self.zoom_level = 1.0
        self.resize_job = None

        # --- Bindings ---
        self.canvas_frame.bind("<Configure>", self.on_window_resize)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.canvas.bind("<ButtonPress-2>", self.on_pan_start)
        self.canvas.bind("<B2-Motion>", self.on_pan_move)
        self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.root.bind("<KeyPress-Return>", self.finish_polygon) # Enter key
        self.root.bind("<ButtonPress-3>", self.finish_polygon) # Right-click
        self.root.bind("<Escape>", self.cancel_drawing)
        self.root.bind("<KeyPress-Delete>", self.delete_selected_annotation)
        self.root.bind("<KeyPress-BackSpace>", self.delete_selected_annotation)

    def on_window_resize(self, event=None):
        if self.resize_job:
            self.root.after_cancel(self.resize_job)
        self.resize_job = self.root.after(300, self.fit_image_to_canvas)

    def fit_image_to_canvas(self):
        if not self.original_image: return
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_width, img_height = self.original_image.size

        if img_width > 0 and img_height > 0 and canvas_width > 1 and canvas_height > 1:
            width_ratio = canvas_width / img_width
            height_ratio = canvas_height / img_height
            self.zoom_level = min(width_ratio, height_ratio)
            
            # Center the image
            self.canvas_x = (canvas_width - (img_width * self.zoom_level)) / 2
            self.canvas_y = (canvas_height - (img_height * self.zoom_level)) / 2
            
            self.display_image()

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif")])
        if file_path:
            try:
                self.image_path = file_path
                self.original_image = Image.open(file_path)
                self.reset_view()
                self.fit_image_to_canvas()
                self.update_status("Image loaded. Ready to annotate.")
            except (Image.UnidentifiedImageError, IOError) as e:
                messagebox.showerror("Error", f"Cannot identify image file: {e}")

    def display_image(self):
        if not self.original_image: return
        self.canvas.delete("all")
        img_w, img_h = self.original_image.size
        scaled_w, scaled_h = int(img_w * self.zoom_level), int(img_h * self.zoom_level)
        
        # Only resize if scaled dimensions are > 0
        if scaled_w > 0 and scaled_h > 0:
            self.resized_image = self.original_image.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
            self.tk_image = ImageTk.PhotoImage(self.resized_image)
            self.canvas.create_image(self.canvas_x, self.canvas_y, anchor="nw", image=self.tk_image, tags="image")
        
        self.redraw_annotations()

    def reset_view(self):
        self.canvas_x, self.canvas_y = 0, 0
        self.zoom_level = 1.0
        self.annotations = []
        self.selected_annotation_index = -1
        self.annotation_listbox.delete(0, tk.END)
        self.cancel_drawing()

    def redraw_annotations(self):
        for i, ann in enumerate(self.annotations):
            points = ann["points"]
            color = "cyan" if i == self.selected_annotation_index else "red"
            if ann["type"] == "BBox":
                x1, y1, x2, y2 = points[0][0], points[0][1], points[1][0], points[1][1]
                cx1, cy1 = self.img_to_canvas(x1, y1)
                cx2, cy2 = self.img_to_canvas(x2, y2)
                self.canvas.create_rectangle(cx1, cy1, cx2, cy2, outline=color, width=2, tags=f"ann_{i}")
                self.canvas.create_text(cx1, cy1 - 10, text=ann["label"], fill="white", anchor="sw", tags=f"label_{i}")
            elif ann["type"] == "Polygon":
                canvas_points = [self.img_to_canvas(p[0], p[1]) for p in points]
                if len(canvas_points) > 1:
                    self.canvas.create_polygon(canvas_points, outline=color, fill="", width=2, tags=f"ann_{i}")
                    self.canvas.create_text(canvas_points[0][0], canvas_points[0][1] - 10, text=ann["label"], fill="white", anchor="sw", tags=f"label_{i}")

    def on_button_press(self, event):
        clicked_item_ids = self.canvas.find_withtag(tk.CURRENT)
        if clicked_item_ids:
            item_id = clicked_item_ids[0]
            item_tags = self.canvas.gettags(item_id)
            ann_tags = [tag for tag in item_tags if tag.startswith("ann_")]
            if ann_tags:
                ann_index = int(ann_tags[0].split("_")[1])
                self.select_annotation(ann_index)
                return

        if self.draw_mode.get() == "BBox":
            self.drawing = True
            self.start_x, self.start_y = event.x, event.y
            self.current_rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)
        elif self.draw_mode.get() == "Polygon":
            self.drawing = True
            self.current_polygon_points.append((event.x, event.y))
            if len(self.current_polygon_points) == 1:
                self.update_status("Click to add points. Right-click or press Enter to finish.")
            if self.current_polygon_id:
                self.canvas.delete(self.current_polygon_id)
            self.current_polygon_id = self.canvas.create_polygon(self.current_polygon_points, outline="red", fill="", width=2)

    def on_mouse_drag(self, event):
        if self.draw_mode.get() == "BBox" and self.drawing:
            self.canvas.coords(self.current_rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_button_release(self, event):
        if self.draw_mode.get() == "BBox" and self.drawing:
            self.drawing = False
            x1_c, y1_c = self.start_x, self.start_y
            x2_c, y2_c = event.x, event.y
            x1, y1 = self.canvas_to_img(x1_c, y1_c)
            x2, y2 = self.canvas_to_img(x2_c, y2_c)
            if abs(x1 - x2) < 1 or abs(y1 - y2) < 1:
                self.canvas.delete(self.current_rect_id)
            else:
                points = [(min(x1, x2), min(y1, y2)), (max(x1, x2), max(y1, y2))]
                self.add_annotation("BBox", points)
            self.current_rect_id = None

    def on_mouse_move(self, event):
        if self.draw_mode.get() == "Polygon" and self.drawing and self.current_polygon_points:
            if self.current_polygon_id:
                self.canvas.delete(self.current_polygon_id)
            self.current_polygon_id = self.canvas.create_polygon(self.current_polygon_points + [(event.x, event.y)], outline="red", fill="", width=2)

    def finish_polygon(self, event=None):
        if self.draw_mode.get() == "Polygon" and self.drawing and len(self.current_polygon_points) >= 3:
            img_points = [self.canvas_to_img(p[0], p[1]) for p in self.current_polygon_points]
            self.add_annotation("Polygon", img_points)
        self.cancel_drawing()
        return "break"

    def cancel_drawing(self, event=None):
        self.drawing = False
        if self.current_rect_id: self.canvas.delete(self.current_rect_id)
        if self.current_polygon_id: self.canvas.delete(self.current_polygon_id)
        self.current_rect_id = None
        self.current_polygon_id = None
        self.current_polygon_points = []
        self.update_status("Ready.")

    def add_annotation(self, ann_type, points):
        label = self.label_text.get()
        ann_data = {"type": ann_type, "label": label, "points": points}
        self.annotations.append(ann_data)
        self.annotation_listbox.insert(tk.END, f"{label}: {ann_type}")
        self.select_annotation(len(self.annotations) - 1)

    def select_annotation(self, index):
        if 0 <= index < len(self.annotations):
            self.selected_annotation_index = index
            self.annotation_listbox.selection_clear(0, tk.END)
            self.annotation_listbox.selection_set(index)
            self.annotation_listbox.activate(index)
            self.display_image()
            self.update_status(f"Selected annotation {index+1}")

    def on_annotation_select(self, event):
        selected_indices = self.annotation_listbox.curselection()
        if selected_indices: self.select_annotation(selected_indices[0])

    def delete_selected_annotation(self, event=None):
        if self.selected_annotation_index != -1:
            self.annotations.pop(self.selected_annotation_index)
            self.annotation_listbox.delete(self.selected_annotation_index)
            self.selected_annotation_index = -1
            self.display_image()
            self.update_status("Annotation deleted.")

    def on_pan_start(self, event): self.pan_start_x, self.pan_start_y = event.x, event.y
    def on_pan_move(self, event):
        dx, dy = event.x - self.pan_start_x, event.y - self.pan_start_y
        self.canvas_x += dx
        self.canvas_y += dy
        self.pan_start_x, self.pan_start_y = event.x, event.y
        self.display_image()

    def on_zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        cx, cy = event.x, event.y
        ix, iy = self.canvas_to_img(cx, cy, zoom_independent=True)
        self.zoom_level *= factor
        self.canvas_x = cx - ix * self.zoom_level
        self.canvas_y = cy - iy * self.zoom_level
        self.display_image()

    def canvas_to_img(self, x, y, zoom_independent=False):
        zoom = 1.0 if zoom_independent else self.zoom_level
        img_x = (x - self.canvas_x) / zoom
        img_y = (y - self.canvas_y) / zoom
        return int(img_x), int(img_y)

    def img_to_canvas(self, x, y):
        can_x = self.canvas_x + x * self.zoom_level
        can_y = self.canvas_y + y * self.zoom_level
        return can_x, can_y

    def update_status(self, text):
        self.coordinates_label.config(text=f"Status: {text}")

    def save_annotation_dialog(self):
        if not self.annotations: messagebox.showinfo("Info", "No annotations to save."); return
        file_path = filedialog.asksaveasfilename(
            filetypes=[
                ("Python Dict", "*.py"),
                ("COCO JSON", "*.json"), 
                ("PASCAL VOC XML", "*.xml"), 
                ("YOLO TXT", "*.txt")
            ],
            initialfile=os.path.splitext(os.path.basename(self.image_path))[0])
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            fmt = {".py": "python_dict", ".json": "coco", ".xml": "pascal_voc", ".txt": "yolo"}.get(ext)
            if not fmt: messagebox.showerror("Error", "Unsupported format."); return
            class_list = sorted(list(set(ann['label'] for ann in self.annotations)))
            save_annotations(fmt, file_path, self.annotations, self.image_path, self.original_image.size, class_list)
            messagebox.showinfo("Success", f"Annotations saved to {file_path}")