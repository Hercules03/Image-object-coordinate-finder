
# Advanced Image Annotation Tool

A versatile desktop application for creating object detection and segmentation annotations. Supports bounding boxes, polygons, and multiple export formats including COCO, PASCAL VOC, YOLO, and Python Dictionary.

This tool is built with Python and Tkinter, providing a simple and cross-platform interface for your image annotation needs.

## Screenshots
![Main interface of the annotation tool](placeholder.png)

## Features

- **Multiple Annotation Modes**: Create both rectangular **Bounding Boxes** and precise **Polygon** segmentation masks.
- **Modern UI**: A clean interface with a dedicated control panel and a spacious canvas for annotation.
- **Interactive Annotation List**: View all annotations for an image in a clear list. Select any annotation to highlight it on the canvas.
- **Full Zoom & Pan Control**: 
  - Zoom in and out smoothly with the mouse wheel.
  - Pan around the image by clicking and dragging the middle mouse button.
  - Automatically or manually fit the image to the window size.
- **Flexible Labeling**: A free-text entry field allows for any custom labels for your objects.
- **Multiple Export Formats**: Save your annotations in a variety of popular formats:
  - **COCO JSON** (`.json`): For object detection and segmentation.
  - **PASCAL VOC** (`.xml`): A standard format for object detection.
  - **YOLO** (`.txt`): For use with the YOLO family of models.
  - **Python Dict** (`.py`): A simple, human-readable Python file.
- **Edit and Delete**: Easily delete any annotation by selecting it in the list or on the canvas and pressing the `Delete` or `Backspace` key.

## Requirements

- Python 3.x
- Pillow (the Python Imaging Library)

## How to Run

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Hercules03/Image-object-coordinate-finder.git
   cd Image-object-coordinate-finder
   ```

2. **Set up a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   ```

3. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

## How to Use

1.  **Load an Image**: Click the **"Upload Image"** button to open an image file.
2.  **Fit the Image**: The image will automatically fit the window. You can also click **"Fit to Window"** or resize the window itself.
3.  **Select a Mode**: Choose between **"BBox"** or **"Polygon"** mode at the top.
4.  **Enter a Label**: Type the desired label for your object in the text box at the bottom.
5.  **Draw an Annotation**:
    - **BBox Mode**: Click and drag to draw a rectangle.
    - **Polygon Mode**: Left-click to place points. Right-click or press `Enter` to finish the polygon.
6.  **Save Annotations**: Click the **"Save Annotations"** button and choose your desired format from the dropdown in the save dialog.

## Controls

| Action | Control |
| :--- | :--- |
| **Drawing (BBox)** | `Left-click` + `Drag` |
| **Drawing (Polygon)** | `Left-click` to place points |
| **Finish Polygon** | `Right-click` or `Enter` key |
| **Cancel Current Drawing** | `Escape` key |
| **Select Annotation** | `Left-click` on the annotation on the canvas or in the list |
| **Delete Selected** | `Delete` or `Backspace` key |
| **Pan Image** | `Middle-click` + `Drag` |
| **Zoom Image** | `Mouse Wheel` (Scroll up/down) |
| **Fit Image to Window** | Click the "Fit to Window" button or resize the window |
