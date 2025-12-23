import json
import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageColor

# 定义颜色列表
additional_colors = [colorname for (colorname, colorcode) in ImageColor.colormap.items()]
COLORS = [
    'red', 'green', 'blue', 'yellow', 'orange', 'pink', 'purple', 'brown', 'gray',
    'beige', 'turquoise', 'cyan', 'magenta', 'lime', 'navy', 'maroon', 'teal',
    'olive', 'coral', 'lavender', 'violet', 'gold', 'silver',
] + additional_colors


def get_font(size):
    """获取字体，尝试设置大小"""
    try:
        return ImageFont.load_default(size=size)
    except:
        return ImageFont.load_default()


def tensor2pil(image):
    """将 ComfyUI 的 tensor 图像转换为 PIL 图像"""
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))


def pil2tensor(image):
    """将 PIL 图像转换为 ComfyUI 的 tensor 格式"""
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


class QwenVLBboxVisualizer:
    """
    Qwen VL 边界框可视化节点
    将大模型返回的 JSON 格式边界框绘制到图像上
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "json_string": ("STRING", {
                    "forceInput": True,
                    "tooltip": "大模型返回的JSON格式边界框数据"
                }),
                "line_width": ("INT", {
                    "default": 3,
                    "min": 1,
                    "max": 20,
                    "tooltip": "边界框线条宽度"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "JSON")
    RETURN_NAMES = ("image", "bboxes_data")
    FUNCTION = "draw_bboxes"
    CATEGORY = "Koi/Visualization"

    def parse_json(self, json_text):
        """解析JSON文本，移除markdown标记"""
        # 清理markdown标记
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0]
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0]
        
        json_text = json_text.strip()
        
        try:
            data = json.loads(json_text)
            if not isinstance(data, list):
                data = [data]
            return data
        except Exception as e:
            print(f"JSON解析错误: {e}")
            return []

    def draw_bboxes(self, image, json_string, line_width=3):
        """在图像上绘制边界框"""
        # 转换为 PIL 图像
        pil_image = tensor2pil(image)
        width, height = pil_image.size
        
        draw = ImageDraw.Draw(pil_image)
        
        # 计算字体大小：图片短边的 2%
        font_size = max(int(min(width, height) * 0.02), 12)
        font = get_font(font_size)
        
        # 解析JSON数据
        bboxes = self.parse_json(json_string)
        
        if not bboxes:
            print("未找到有效的边界框数据")
            return (image, [])
        
        output_bboxes = []
        
        # 绘制每个边界框
        for i, bbox_item in enumerate(bboxes):
            if "bbox_2d" not in bbox_item:
                continue
            
            color = COLORS[i % len(COLORS)]
            bbox = bbox_item["bbox_2d"]
            
            # 将标准化坐标 [x1, y1, x2, y2] (0-1000) 转换为绝对坐标
            x1 = int(bbox[0] / 1000 * width)
            y1 = int(bbox[1] / 1000 * height)
            x2 = int(bbox[2] / 1000 * width)
            y2 = int(bbox[3] / 1000 * height)
            
            # 确保坐标顺序正确
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
            
            # 绘制矩形框
            draw.rectangle([(x1, y1), (x2, y2)], outline=color, width=line_width)
            
            # 添加标签
            if "label" in bbox_item:
                draw.text((x1 + 8, y1 + 6), bbox_item["label"], fill=color, font=font)
            
            output_bboxes.append({"bbox_2d": [x1, y1, x2, y2]})
        
        # 转换回 tensor
        result = pil2tensor(pil_image)
        return (result, output_bboxes)


class QwenVLPointVisualizer:
    """
    Qwen VL 点坐标可视化节点
    将大模型返回的 JSON 格式点坐标绘制到图像上
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "json_string": ("STRING", {
                    "forceInput": True,
                    "tooltip": "大模型返回的JSON格式点坐标数据"
                }),
                "point_radius": ("INT", {
                    "default": 5,
                    "min": 1,
                    "max": 20,
                    "tooltip": "点的半径大小"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "JSON")
    RETURN_NAMES = ("image", "points_data")
    FUNCTION = "draw_points"
    CATEGORY = "Koi/Visualization"

    def parse_json_points(self, json_text):
        """解析JSON格式的点坐标"""
        # 清理markdown标记
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0]
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0]
        
        json_text = json_text.strip()
        
        try:
            data = json.loads(json_text)
            points = []
            labels = []
            
            for item in data:
                if "point_2d" in item:
                    x, y = item["point_2d"]
                    points.append([x, y])
                    label = item.get("label", f"point_{len(points)}")
                    labels.append(label)
            
            return points, labels
        except Exception as e:
            print(f"JSON解析错误: {e}")
            return [], []

    def draw_points(self, image, json_string, point_radius=5):
        """在图像上绘制点"""
        # 转换为 PIL 图像
        pil_image = tensor2pil(image)
        width, height = pil_image.size
        
        draw = ImageDraw.Draw(pil_image)
        
        # 计算字体大小：图片短边的 2%
        font_size = max(int(min(width, height) * 0.02), 12)
        font = get_font(font_size)
        
        # 解析JSON数据
        points, labels = self.parse_json_points(json_string)
        
        if not points:
            print("未找到有效的点坐标数据")
            return (image, [])
        
        # 绘制每个点
        for i, point in enumerate(points):
            color = COLORS[i % len(COLORS)]
            
            # 将标准化坐标 (0-1000) 转换为绝对坐标
            x = int(point[0] / 1000 * width)
            y = int(point[1] / 1000 * height)
            
            # 绘制圆点
            draw.ellipse(
                [(x - point_radius, y - point_radius), 
                 (x + point_radius, y + point_radius)], 
                fill=color
            )
            
            # 添加标签
            if i < len(labels):
                draw.text((x + point_radius + 2, y + point_radius + 2), 
                         labels[i], fill=color, font=font)
        
        # 构造返回数据
        points_data = []
        for p, l in zip(points, labels):
            points_data.append({
                "point_2d": p,
                "label": l
            })
        
        # 转换回 tensor
        result = pil2tensor(pil_image)
        return (result, points_data)


# 注册节点
NODE_CLASS_MAPPINGS = {
    "QwenVLBboxVisualizer": QwenVLBboxVisualizer,
    "QwenVLPointVisualizer": QwenVLPointVisualizer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "QwenVLBboxVisualizer": "Qwen VL Bbox Visualizer",
    "QwenVLPointVisualizer": "Qwen VL Point Visualizer",
}
