import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import json
import pprint

def save_annotations(format_type, file_path, annotations, image_path, image_size, class_list):
    """Dispatcher function to save annotations in the specified format."""
    dispatch = {
        "pascal_voc": _save_pascal_voc,
        "coco": _save_coco,
        "yolo": _save_yolo,
        "python_dict": _save_python_dict
    }
    if format_type in dispatch:
        dispatch[format_type](file_path, annotations, image_path, image_size, class_list)

def _get_bbox_from_polygon(points):
    """Calculate the bounding box coordinates for a given polygon."""
    x_coords = [p[0] for p in points]
    y_coords = [p[1] for p in points]
    xmin = min(x_coords)
    ymin = min(y_coords)
    xmax = max(x_coords)
    ymax = max(y_coords)
    return xmin, ymin, xmax, ymax

def _save_pascal_voc(file_path, annotations, image_path, image_size, class_list):
    annotation_el = ET.Element("annotation")
    ET.SubElement(annotation_el, "folder").text = os.path.dirname(image_path)
    ET.SubElement(annotation_el, "filename").text = os.path.basename(image_path)
    ET.SubElement(annotation_el, "path").text = image_path
    source = ET.SubElement(annotation_el, "source")
    ET.SubElement(source, "database").text = "Unknown"
    size_el = ET.SubElement(annotation_el, "size")
    width, height = image_size
    ET.SubElement(size_el, "width").text = str(width)
    ET.SubElement(size_el, "height").text = str(height)
    ET.SubElement(size_el, "depth").text = "3"
    ET.SubElement(annotation_el, "segmented").text = str(int(any(ann["type"] == "Polygon" for ann in annotations)))

    for ann_data in annotations:
        if ann_data["type"] == "BBox":
            xmin, ymin = ann_data["points"][0]
            xmax, ymax = ann_data["points"][1]
        else: # Polygon
            xmin, ymin, xmax, ymax = _get_bbox_from_polygon(ann_data["points"])

        obj_el = ET.SubElement(annotation_el, "object")
        ET.SubElement(obj_el, "name").text = ann_data["label"]
        ET.SubElement(obj_el, "pose").text = "Unspecified"
        ET.SubElement(obj_el, "truncated").text = "0"
        ET.SubElement(obj_el, "difficult").text = "0"
        bndbox_el = ET.SubElement(obj_el, "bndbox")
        ET.SubElement(bndbox_el, "xmin").text = str(xmin)
        ET.SubElement(bndbox_el, "ymin").text = str(ymin)
        ET.SubElement(bndbox_el, "xmax").text = str(xmax)
        ET.SubElement(bndbox_el, "ymax").text = str(ymax)

    xml_str = ET.tostring(annotation_el)
    pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="   ")
    with open(file_path, "w") as f:
        f.write(pretty_xml_str)

def _save_coco(file_path, annotations, image_path, image_size, class_list):
    width, height = image_size
    cat_map = {name: i for i, name in enumerate(class_list)}
    categories = [{"id": i, "name": name, "supercategory": "none"} for i, name in enumerate(class_list)]
    images = [{"id": 0, "file_name": os.path.basename(image_path), "height": height, "width": width}]
    
    coco_annotations = []
    for i, ann_data in enumerate(annotations):
        label = ann_data["label"]
        points = ann_data["points"]
        
        if ann_data["type"] == "BBox":
            xmin, ymin = points[0]
            xmax, ymax = points[1]
            segmentation = [[xmin, ymin, xmax, ymin, xmax, ymax, xmin, ymax]]
        else: # Polygon
            segmentation = [[coord for point in points for coord in point]]

        xmin, ymin, xmax, ymax = _get_bbox_from_polygon(points if ann_data["type"] == "Polygon" else [points[0], points[1]])
        coco_bbox = [xmin, ymin, xmax - xmin, ymax - ymin]
        area = coco_bbox[2] * coco_bbox[3]

        coco_annotations.append({
            "id": i,
            "image_id": 0,
            "category_id": cat_map.get(label, -1),
            "bbox": coco_bbox,
            "area": area,
            "iscrowd": 0,
            "segmentation": segmentation
        })

    with open(file_path, 'w') as f:
        json.dump({"images": images, "annotations": coco_annotations, "categories": categories}, f, indent=4)

def _save_yolo(file_path, annotations, image_size, class_list):
    img_w, img_h = image_size
    cat_map = {name: i for i, name in enumerate(class_list)}
    lines = []
    for ann_data in annotations:
        class_id = cat_map.get(ann_data["label"])
        if class_id is None: continue

        if ann_data["type"] == "BBox":
            xmin, ymin = ann_data["points"][0]
            xmax, ymax = ann_data["points"][1]
        else: # Polygon
            xmin, ymin, xmax, ymax = _get_bbox_from_polygon(ann_data["points"])

        box_w, box_h = xmax - xmin, ymax - ymin
        center_x, center_y = xmin + box_w / 2, ymin + box_h / 2
        
        lines.append(f"{class_id} {center_x/img_w:.6f} {center_y/img_h:.6f} {box_w/img_w:.6f} {box_h/img_h:.6f}")

    with open(file_path, 'w') as f:
        f.write('\n'.join(lines))

def _save_python_dict(file_path, annotations, image_path, image_size, class_list):
    output_dict = {}
    for ann in annotations:
        label = ann['label']
        points = ann['points']
        if label not in output_dict:
            output_dict[label] = []
        output_dict[label].append(points)

    with open(file_path, 'w') as f:
        f.write(f"annotations = {pprint.pformat(output_dict)}")