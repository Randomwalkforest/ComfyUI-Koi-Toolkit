import json
import re
from typing import Any, List, Union


def _strip_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        # Remove starting ``` or ```json
        t = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n?", "", t)
        # Remove ending ```
        t = re.sub(r"\n?```\s*$", "", t)
    return t.strip()


_TOKEN_RE = re.compile(
    r"""
    (?:\.(?P<dotkey>[A-Za-z_][A-Za-z0-9_\-]*))
    |(?:\[(?P<index>\d+)\])
    |(?:\[\s*(?P<q>['\"])(?P<strkey>(?:\\.|(?!\3).)*)\3\s*\])
    """,
    re.VERBOSE,
)


def _parse_path(path: str) -> List[Union[str, int]]:
    """Parse a simple dotted/bracket path like: a.b[0]['c-d']"""
    p = (path or "").strip()
    if not p or p == "$":
        return []
    if p.startswith("$"):
        p = p[1:]
    if p.startswith("."):
        p = p[1:]

    tokens: List[Union[str, int]] = []

    # Allow first segment without leading dot: foo.bar
    first, *rest = p.split(".")
    if first:
        # first might still contain brackets, so handle by prefixing dot and parsing uniformly
        p2 = "." + p
    else:
        p2 = "." + ".".join(rest)

    for m in _TOKEN_RE.finditer(p2):
        if m.group("dotkey") is not None:
            tokens.append(m.group("dotkey"))
        elif m.group("index") is not None:
            tokens.append(int(m.group("index")))
        else:
            raw = m.group("strkey") or ""
            # Unescape basic sequences inside quoted key
            try:
                tokens.append(bytes(raw, "utf-8").decode("unicode_escape"))
            except Exception:
                tokens.append(raw)

    return tokens


def _get_by_path(data: Any, tokens: List[Union[str, int]]) -> Any:
    cur = data
    for tok in tokens:
        if isinstance(tok, int):
            if not isinstance(cur, list) or tok < 0 or tok >= len(cur):
                return None
            cur = cur[tok]
        else:
            if not isinstance(cur, dict) or tok not in cur:
                return None
            cur = cur[tok]
    return cur


def _collect_texts(obj: Any) -> List[str]:
    """Recursively collect primitive values as plain strings, ignoring JSON structural symbols."""
    if obj is None:
        return []
    if isinstance(obj, str):
        s = obj.strip()
        return [s] if s != "" else []
    if isinstance(obj, (int, float, bool)):
        return [str(obj)]
    if isinstance(obj, list):
        out: List[str] = []
        for item in obj:
            out.extend(_collect_texts(item))
        return out
    if isinstance(obj, dict):
        out: List[str] = []
        for v in obj.values():
            out.extend(_collect_texts(v))
        return out
    return [str(obj)]


class JsonExtractTextList:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_input": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "JSON字符串（例如: [\"Light Bulb\", \"Paint Palette\"] 或 { ... }）",
                }),
                "path": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "取值路径：支持 a.b[0].c 或 ['a-b']；留空表示根对象",
                }),
            },
            "optional": {
                "leaf_key": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "当取到的是对象数组时，可指定每项要取的字段名（例如 name/text/label）；留空则递归提取所有文本",
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "extract"
    CATEGORY = "Koi/Utils"

    def extract(self, json_input: str, path: str = "", leaf_key: str = ""):
        raw = _strip_code_fences(str(json_input))
        if raw == "":
            return ([],)

        try:
            data = json.loads(raw)
        except Exception:
            # If it's not valid JSON, treat as a single string value
            data = raw

        tokens = _parse_path(path)
        value = _get_by_path(data, tokens) if tokens else data
        if value is None:
            return ([],)

        lk = (leaf_key or "").strip()
        if lk and isinstance(value, list):
            out: List[str] = []
            for item in value:
                if isinstance(item, dict) and lk in item:
                    out.extend(_collect_texts(item.get(lk)))
                else:
                    out.extend(_collect_texts(item))
            return (out,)

        return (_collect_texts(value),)


NODE_CLASS_MAPPINGS = {
    "JsonExtractTextList": JsonExtractTextList,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "JsonExtractTextList": "JSON Extract Text List",
}
