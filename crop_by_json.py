import torch
import json

class CropImageByJson:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "bboxes_data": ("JSON", {}),
            },
            "optional": {
                "padding_ratio": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 10.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "crop"
    CATEGORY = "🐟Koi-Toolkit"

    def crop(self, image, bboxes_data, padding_ratio=0.0):
        import re
        try:
            if not isinstance(bboxes_data, str):
                data = bboxes_data
            else:
                # 尝试提取 JSON 部分 (兼容 markdown 和 冗余文本)
                match = re.search(r'(\[.*\]|\{.*\})', bboxes_data, re.DOTALL)
                if match:
                    bboxes_data = match.group(0)
                data = json.loads(bboxes_data)
        except Exception as e:
            print(f"[CropImageByJson] JSON Parse Error: {e}")
            return ([],)

        # 确保 data 是列表
        if not isinstance(data, list):
            data = [data]

        results = []
        # image is [B, H, W, C]
        for i in range(image.shape[0]):
            img = image[i] # [H, W, C]
            h, w, c = img.shape
            
            for item in data:
                if "bbox_2d" in item:
                    bbox = item["bbox_2d"]
                    # bbox format: [x_min, y_min, x_max, y_max]
                    # Ensure coordinates are within bounds and integers
                    try:
                        x1_org = int(bbox[0])
                        y1_org = int(bbox[1])
                        x2_org = int(bbox[2])
                        y2_org = int(bbox[3])
                        
                        # Calculate padding based on current crop size
                        w_crop = x2_org - x1_org
                        h_crop = y2_org - y1_org
                        pad_w = int(w_crop * padding_ratio)
                        pad_h = int(h_crop * padding_ratio)
                        
                        x1 = max(0, x1_org - pad_w)
                        y1 = max(0, y1_org - pad_h)
                        x2 = min(w, x2_org + pad_w)
                        y2 = min(h, y2_org + pad_h)
                    except (ValueError, TypeError, IndexError):
                        continue
                    
                    if x2 > x1 and y2 > y1:
                        cropped = img[y1:y2, x1:x2, :]
                        # Add batch dimension back: [1, H', W', C]
                        cropped = cropped.unsqueeze(0)
                        results.append(cropped)
        
        return (results,)

NODE_CLASS_MAPPINGS = {
    "CropImageByJson": CropImageByJson
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CropImageByJson": "Crop Image By JSON"
}
