import torch
import numpy as np
import cv2

class MaskFilterByInclusion:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "mask_to_filter": ("MASK",),
                "mask_reference": ("MASK",),
                "threshold": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("MASK",)
    FUNCTION = "process"
    CATEGORY = "Koi"

    def process(self, mask_to_filter, mask_reference, threshold):
        # mask inputs are torch tensors [B, H, W]
        
        result_masks = []
        
        # Handle batch size differences simply
        B1 = mask_to_filter.shape[0]
        B2 = mask_reference.shape[0]
        
        for i in range(B1):
            m1 = mask_to_filter[i].cpu().numpy()
            m2 = mask_reference[i % B2].cpu().numpy()
            
            # Convert to uint8 for cv2
            # Ensure binary 0/1
            m1_uint8 = (m1 > 0.5).astype(np.uint8)
            m2_uint8 = (m2 > 0.5).astype(np.uint8)
            
            # Connected components
            num_labels, labels = cv2.connectedComponents(m1_uint8)
            
            # Create a mask to subtract (initially empty)
            # Or just modify a copy of m1
            out_m = m1.copy()
            
            for label in range(1, num_labels): # 0 is background
                component_mask = (labels == label)
                component_area = np.sum(component_mask)
                
                if component_area == 0:
                    continue
                
                # Calculate overlap
                # m2_uint8[component_mask] gives values of m2 where component is present
                overlap_count = np.sum(m2_uint8[component_mask])
                
                ratio = overlap_count / component_area
                
                if ratio >= threshold:
                    out_m[component_mask] = 0.0
            
            result_masks.append(torch.from_numpy(out_m))
            
        return (torch.stack(result_masks),)

NODE_CLASS_MAPPINGS = {
    "MaskFilterByInclusion": MaskFilterByInclusion
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MaskFilterByInclusion": "Mask Filter By Inclusion (Koi)"
}
