import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os

class BboxCoordinatesPicker:
    def __init__(self, root):
        self.root = root
        self.root.title("Bbox Coordinate Picker")
        self.root.geometry("800x600")  # Start with a default size

        # Frames for layout
        top_frame = tk.Frame(self.root)
        top_frame.pack(side="top", fill="x", pady=5)

        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(fill="both", expand=True)
        # Bind the configure event to the resize_image method
        self.canvas_frame.bind("<Configure>", self.on_resize)

        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(side="bottom", fill="x", pady=5)

        self.upload_button = tk.Button(top_frame, text="Upload Image", command=self.upload_image)
        self.upload_button.pack(side="left", padx=5)

        self.multiple_bboxes_var = tk.BooleanVar()
        self.multiple_bboxes_check = tk.Checkbutton(top_frame, text="Multiple Bounding Boxes", variable=self.multiple_bboxes_var)
        self.multiple_bboxes_check.pack(side="left", padx=5)

        self.canvas = tk.Canvas(self.canvas_frame, cursor="cross", bg="black")
        self.canvas.pack(fill="both", expand=True)

        # Label Entry
        label_frame = tk.Frame(bottom_frame)
        label_frame.pack(side="top")
        tk.Label(label_frame, text="Label:").pack(side="left", padx=5)
        self.label_text = tk.StringVar()
        self.label_entry = tk.Entry(label_frame, textvariable=self.label_text)
        self.label_entry.pack(side="left", padx=5)

        self.coordinates_label = tk.Label(bottom_frame, text="Coordinates: (x1, y1), (x2, y2)")
        self.coordinates_label.pack(side="top")

        button_container = tk.Frame(bottom_frame)
        button_container.pack(side="bottom", pady=5)

        self.copy_button = tk.Button(button_container, text="Copy Coordinates", command=self.copy_coordinates)
        self.copy_button.pack(side="left", padx=5)

        self.save_button = tk.Button(button_container, text="Save Cropped", command=self.save_cropped_image)
        self.save_button.pack(side="left", padx=5)

        self.save_annotation_button = tk.Button(button_container, text="Save Annotation", command=self.save_annotation)
        self.save_annotation_button.pack(side="left", padx=5)

        self.original_image = None
        self.image_path = None
        self.resized_image = None
        self.tk_image = None
        self.scale_factor = 1.0
        self.bboxes = []
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.resize_job = None

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def on_resize(self, event=None):
        if self.original_image:
            if self.resize_job:
                self.root.after_cancel(self.resize_job)
            self.resize_job = self.root.after(100, self.display_image)

    def upload_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                self.image_path = file_path
                self.original_image = Image.open(file_path)
                self.clear_bboxes()
                self.update_coordinates_label()
                self.display_image()
            except Image.UnidentifiedImageError:
                messagebox.showerror("Error", "Cannot identify image file. Please select a valid image file.")

    def display_image(self):
        if not self.original_image:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width == 1 or canvas_height == 1: # Canvas not yet realized
            self.root.after(20, self.display_image)
            return

        img_width, img_height = self.original_image.size

        # Calculate scaling factor
        width_ratio = canvas_width / img_width
        height_ratio = canvas_height / img_height
        self.scale_factor = min(width_ratio, height_ratio)

        new_width = int(img_width * self.scale_factor)
        new_height = int(img_height * self.scale_factor)

        self.resized_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(self.resized_image)

        # Clear canvas and display image
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        self.redraw_bboxes()

    def clear_bboxes(self):
        for bbox in self.bboxes:
            self.canvas.delete(bbox["rect_id"])
            if bbox.get("text_id"):
                self.canvas.delete(bbox["text_id"])
        self.bboxes = []

    def redraw_bboxes(self):
        for bbox_data in self.bboxes:
            x1, y1, x2, y2 = bbox_data["bbox"]
            # scale back to canvas coordinates
            cx1 = x1 * self.scale_factor
            cy1 = y1 * self.scale_factor
            cx2 = x2 * self.scale_factor
            cy2 = y2 * self.scale_factor
            
            rect_id = self.canvas.create_rectangle(cx1, cy1, cx2, cy2, outline='red', width=2)
            bbox_data["rect_id"] = rect_id
            self.draw_label(rect_id, bbox_data["label"])

    def draw_label(self, rect_id, label):
        x1, y1, _, _ = self.canvas.coords(rect_id)
        text_id = self.canvas.create_text(x1, y1 - 10, text=label, fill="white", anchor="sw")
        # find the bbox data and update the text_id
        for bbox in self.bboxes:
            if bbox["rect_id"] == rect_id:
                bbox["text_id"] = text_id
                break

    def update_coordinates_label(self):
        if self.bboxes:
            last_bbox = self.bboxes[-1]
            label = last_bbox["label"]
            x1, y1, x2, y2 = last_bbox["bbox"]
            self.coordinates_label.config(text=f'{repr(label)}, [({x1}, {y1}), ({x2}, {y2})]')
        else:
            self.coordinates_label.config(text="Coordinates: (x1, y1), (x2, y2)")

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y

        if not self.multiple_bboxes_var.get():
            self.clear_bboxes()

        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)

    def on_mouse_drag(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)

        # Convert coordinates to original image scale
        x1 = int(min(self.start_x, end_x) / self.scale_factor)
        y1 = int(min(self.start_y, end_y) / self.scale_factor)
        x2 = int(max(self.start_x, end_x) / self.scale_factor)
        y2 = int(max(self.start_y, end_y) / self.scale_factor)

        label = self.label_text.get()
        
        bbox_data = {
            "bbox": (x1, y1, x2, y2),
            "label": label,
            "rect_id": self.rect,
            "text_id": None
        }

        if not self.multiple_bboxes_var.get():
            self.bboxes = [bbox_data]
        else:
            self.bboxes.append(bbox_data)

        self.draw_label(self.rect, label)
        self.update_coordinates_label()

    def copy_coordinates(self):
        if self.bboxes:
            last_bbox = self.bboxes[-1]
            label = last_bbox["label"]
            x1, y1, x2, y2 = last_bbox["bbox"]
            formatted_coords = f'{repr(label)}, [({x1}, {y1}), ({x2}, {y2})]' 
            self.root.clipboard_clear()
            self.root.clipboard_append(formatted_coords)

    def save_cropped_image(self):
        if not self.bboxes or not self.original_image:
            return

        last_bbox = self.bboxes[-1]
        cropped_image = self.original_image.crop(last_bbox["bbox"])
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg;*.jpeg"),
                ("All files", "*.*"),
            ],
        )

        if file_path:
            cropped_image.save(file_path)

    def save_annotation(self):
        if not self.bboxes or not self.original_image or not self.image_path:
            return

        annotation = ET.Element("annotation")

        ET.SubElement(annotation, "folder").text = os.path.dirname(self.image_path)
        ET.SubElement(annotation, "filename").text = os.path.basename(self.image_path)
        ET.SubElement(annotation, "path").text = self.image_path

        source = ET.SubElement(annotation, "source")
        ET.SubElement(source, "database").text = "Unknown"

        size = ET.SubElement(annotation, "size")
        width, height = self.original_image.size
        ET.SubElement(size, "width").text = str(width)
        ET.SubElement(size, "height").text = str(height)
        ET.SubElement(size, "depth").text = str(self.original_image.mode == 'RGB' and 3 or 1)

        ET.SubElement(annotation, "segmented").text = "0"

        for bbox_data in self.bboxes:
            obj = ET.SubElement(annotation, "object")
            ET.SubElement(obj, "name").text = bbox_data["label"]
            ET.SubElement(obj, "pose").text = "Unspecified"
            ET.SubElement(obj, "truncated").text = "0"
            ET.SubElement(obj, "difficult").text = "0"
            bndbox = ET.SubElement(obj, "bndbox")
            xmin, ymin, xmax, ymax = bbox_data["bbox"]
            ET.SubElement(bndbox, "xmin").text = str(xmin)
            ET.SubElement(bndbox, "ymin").text = str(ymin)
            ET.SubElement(bndbox, "xmax").text = str(xmax)
            ET.SubElement(bndbox, "ymax").text = str(ymax)

        xml_str = ET.tostring(annotation)
        pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="   ")

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xml",
            filetypes=[("XML files", "*.xml")],
            initialfile=os.path.splitext(os.path.basename(self.image_path))[0] + ".xml"
        )

        if file_path:
            with open(file_path, "w") as f:
                f.write(pretty_xml_str)

if __name__ == "__main__":
    root = tk.Tk()
    app = BboxCoordinatesPicker(root)
    root.mainloop()
