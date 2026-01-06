import torch

class MaskBatchCombine:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "mask": ("MASK",),
            }
        }

    RETURN_TYPES = ("MASK",)
    FUNCTION = "combine"
    CATEGORY = "Koi/Mask"

    def combine(self, mask):
        # mask shape: [B, H, W]
        # Sum along batch dimension (dim 0)
        # keepdim=True to maintain [1, H, W] shape which is compatible with single mask
        result = torch.sum(mask, dim=0, keepdim=True)
        # Clamp to ensure values are between 0 and 1
        result = torch.clamp(result, 0.0, 1.0)
        return (result,)

NODE_CLASS_MAPPINGS = {
    "MaskBatchCombine": MaskBatchCombine
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MaskBatchCombine": "Mask Batch Combine"
}
