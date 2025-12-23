class string_to_boolean:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "string_input": ("STRING", {"multiline": False, "default": "false"}),
            }
        }

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("boolean",)
    FUNCTION = "convert"
    CATEGORY = "Koi/Utils"

    def convert(self, string_input):
        s = str(string_input).strip().lower()
        if s in ["true", "1", "yes", "on"]:
            return (True,)
        
        # 默认返回False，包括 "false", "0", "no", "off" 以及其他无法识别的情况
        return (False,)

NODE_CLASS_MAPPINGS = {
    "string_to_boolean": string_to_boolean
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "string_to_boolean": "String to Boolean"
}
