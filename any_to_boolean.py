import torch
import json

class AnyToBoolean:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "any_input": ("*",),
            },
        }

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("boolean",)
    FUNCTION = "convert"
    CATEGORY = "Koi/Logic"

    def convert(self, any_input):
        ret = False
        
        # Handle None
        if any_input is None:
            ret = False
            return (ret,)

        # Handle Boolean
        if isinstance(any_input, bool):
            ret = any_input
            return (ret,)

        # Handle Tensor (Image/Mask)
        if isinstance(any_input, torch.Tensor):
            # Check if tensor is not empty
            ret = any_input.numel() > 0
            return (ret,)

        # Handle String
        if isinstance(any_input, str):
            s = any_input.strip().lower()
            if s in ["1", "true", "on", "yes"]:
                ret = True
            elif s in ["0", "false", "off", "no", ""]:
                ret = False
            else:
                # Try parsing as JSON if it looks like one
                if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
                    try:
                        parsed = json.loads(any_input)
                        ret = bool(parsed)
                    except:
                        ret = bool(any_input)
                else:
                    ret = bool(any_input)
            return (ret,)

        # Handle List/Dict/Tuple (JSON objects)
        if isinstance(any_input, (list, dict, tuple)):
            ret = bool(any_input)
            return (ret,)
            
        # Handle Numbers
        if isinstance(any_input, (int, float)):
            ret = bool(any_input)
            return (ret,)

        # Fallback
        ret = bool(any_input)
        return (ret,)

NODE_CLASS_MAPPINGS = {
    "AnyToBoolean": AnyToBoolean
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AnyToBoolean": "Any To Boolean"
}
