import torch

class MaskThresholdToWhite:
    """
    检查mask中白色部分的比例，如果超过指定阈值则返回全白mask，否则返回原mask
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK",),
                "threshold": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "slider"
                }),
            }
        }
    
    CATEGORY = "🐟Koi-Toolkit"
    DESCRIPTION = "如果mask中白色部分超过阈值比例，则返回全白mask，否则返回原mask"
    
    RETURN_TYPES = ("MASK", "FLOAT", "BOOLEAN")
    RETURN_NAMES = ("mask", "white_ratio", "is_converted")
    
    FUNCTION = "process"
    
    def process(self, mask, threshold):
        # 处理输入mask的维度
        if mask.dim() == 2:
            mask = mask.unsqueeze(0)
        
        batch_size = mask.shape[0]
        result_masks = []
        ratios = []
        converted_flags = []
        
        for i in range(batch_size):
            current_mask = mask[i]
            
            # 计算白色像素比例（值>0.5视为白色）
            total_pixels = current_mask.numel()
            white_pixels = (current_mask > 0.5).sum().item()
            white_ratio = white_pixels / total_pixels if total_pixels > 0 else 0.0
            
            ratios.append(white_ratio)
            
            # 判断是否超过阈值
            if white_ratio >= threshold:
                # 超过阈值，返回全白mask
                result_mask = torch.ones_like(current_mask)
                converted_flags.append(True)
            else:
                # 未超过阈值，返回原mask
                result_mask = current_mask
                converted_flags.append(False)
            
            result_masks.append(result_mask)
        
        # 合并结果
        result = torch.stack(result_masks, dim=0)
        
        # 返回第一个batch的比例和转换标志（用于单张mask场景）
        avg_ratio = sum(ratios) / len(ratios) if ratios else 0.0
        any_converted = any(converted_flags)
        
        return (result, avg_ratio, any_converted)


NODE_CLASS_MAPPINGS = {
    "MaskThresholdToWhite": MaskThresholdToWhite,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MaskThresholdToWhite": "Mask Threshold to White 🐟",
}
