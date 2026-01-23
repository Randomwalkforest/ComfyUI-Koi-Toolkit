class StringContainsKeyword:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "string_input": ("STRING", {"multiline": False, "default": ""}),
                "keyword": ("STRING", {"multiline": False, "default": ""}),
            },
            "optional": {
                "case_sensitive": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("has_keyword",)
    FUNCTION = "check"
    CATEGORY = "🐟Koi-Toolkit"

    def check(self, string_input, keyword, case_sensitive=False):
        text = "" if string_input is None else str(string_input)
        key = "" if keyword is None else str(keyword)

        if key == "":
            return (False,)

        if not case_sensitive:
            text = text.lower()
            key = key.lower()

        return (key in text,)


NODE_CLASS_MAPPINGS = {
    "StringContainsKeyword": StringContainsKeyword
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StringContainsKeyword": "String Contains Keyword"
}
