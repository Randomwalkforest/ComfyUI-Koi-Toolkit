import json
import re
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

    RETURN_TYPES = ("IMAGE", "MASK", "JSON")
    RETURN_NAMES = ("image", "mask", "bboxes_data")
    FUNCTION = "draw_bboxes"
    CATEGORY = "🐟Koi-Toolkit"

    def find_bboxes_recursive(self, data):
        """递归查找包含 bbox_2d 或 bbox 的对象"""
        bboxes = []
        if isinstance(data, dict):
            # 直接在该对象上提取bbox
            if "bbox_2d" in data and isinstance(data["bbox_2d"], list) and len(data["bbox_2d"]) == 4:
                bboxes.append(dict(data))
            elif "bbox" in data and isinstance(data["bbox"], list) and len(data["bbox"]) == 4:
                bboxes.append(dict(data))

            # 继续递归查找子项
            for value in data.values():
                bboxes.extend(self.find_bboxes_recursive(value))
        elif isinstance(data, list):
            for item in data:
                bboxes.extend(self.find_bboxes_recursive(item))
        return bboxes

    def extract_bboxes_regex(self, text):
        """正则提取 fallback"""
        bboxes = []
        
        # 直接匹配任意 [x, y, x, y] 格式，不关心键名
        pattern = re.compile(r'\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]')
        
        for i, match in enumerate(pattern.finditer(text)):
            x1, y1, x2, y2 = match.groups()
            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
            
            # 不再尝试根据特定键名查找标签，直接使用序号
            label = f"bbox_{i+1}"

            bboxes.append({
                "bbox_2d": [x1, y1, x2, y2],
                "label": label
            })
            
        return bboxes

    def parse_json(self, json_text):
        """解析JSON文本，移除markdown标记，支持容错"""
        # 清理markdown标记
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0]
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0]
        
        json_text = json_text.strip()
        
        # 尝试修复常见的 JSON 格式错误
        # 修复双重花括号 {{...}} -> {...}
        json_text = re.sub(r'\{\s*\{', '{', json_text)
        json_text = re.sub(r'\}\s*\}', '}', json_text)
        
        data = []
        try:
            parsed = json.loads(json_text)
            # 递归查找所有符合格式的 bbox 对象
            data = self.find_bboxes_recursive(parsed)
        except Exception as e:
            print(f"JSON解析失败，尝试正则提取: {e}")
            pass
            
        if not data:
             print(f"未找到标准格式数据，尝试正则提取...")
             data = self.extract_bboxes_regex(json_text)
             
        if not data:
             print(f"未找到有效数据，原始文本片段: {json_text[:100]}...")
             
        return data

    def draw_bboxes(self, image, json_string, line_width=3):
        """在图像上绘制边界框"""
        # 转换为 PIL 图像
        pil_image = tensor2pil(image)
        width, height = pil_image.size
        
        draw = ImageDraw.Draw(pil_image)
        
        # 创建 mask 图像
        mask_img = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask_img)
        
        # 计算字体大小：图片短边的 2%
        font_size = max(int(min(width, height) * 0.02), 12)
        font = get_font(font_size)
        
        # 解析JSON数据
        bboxes = self.parse_json(json_string)
        
        if not bboxes:
            print("未找到有效的边界框数据")
            return (image, torch.zeros((1, height, width), dtype=torch.float32), [])
        
        output_bboxes = []
        
        # 绘制每个边界框
        for i, bbox_item in enumerate(bboxes):
            bbox = bbox_item.get("bbox_2d", bbox_item.get("bbox"))
            if not bbox:
                continue
            
            color = COLORS[i % len(COLORS)]
            
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
            
            # 绘制 mask
            mask_draw.rectangle([(x1, y1), (x2, y2)], fill=255)
            
            # 添加标签
            label = bbox_item.get("label", bbox_item.get("text_content", bbox_item.get("name")))
            if label:
                draw.text((x1 + 8, y1 + 6), str(label), fill=color, font=font)
            
            abs_bbox = {"bbox_2d": [x1, y1, x2, y2]}
            output_bboxes.append(abs_bbox)
        
        # 转换回 tensor
        result = pil2tensor(pil_image)
        
        # Convert mask to tensor
        mask_np = np.array(mask_img).astype(np.float32) / 255.0
        mask_tensor = torch.from_numpy(mask_np).unsqueeze(0)
        
        return (result, mask_tensor, output_bboxes)


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
    CATEGORY = "🐟Koi-Toolkit"

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
