import importlib
import traceback

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# 定义需要加载的模块列表
modules = [
    "inpaint_stitch_simple",
    "mask_external_rectangle",
    "image_stitch_improved",
    "image_subtraction",
    "florence2_json_display",
    "aliyun_chat",
    "text_split_lines",
    "svg_converter",
    "image_desaturate_edge_binarize",
    "icon_search_freepik",
    "string_to_boolean",
    "simple_vision_chat",
    "json_extract_text_list",
    "string_contains_keyword",
    "download_url",
    "any_to_boolean",
    "qwen_vl_visualizer",
    "crop_by_json",
    "gemini_vision",
]

for module_name in modules:
    try:
        # 动态导入模块
        module = importlib.import_module(f".{module_name}", package=__name__)
        
        # 更新节点映射
        if hasattr(module, "NODE_CLASS_MAPPINGS"):
            NODE_CLASS_MAPPINGS.update(module.NODE_CLASS_MAPPINGS)
            
        if hasattr(module, "NODE_DISPLAY_NAME_MAPPINGS"):
            NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)
            
    except ImportError as e:
        # 捕获导入错误（通常是缺少依赖），打印警告但不中断
        print(f"[ComfyUI-Koi-Toolkit] Warning: Failed to import module '{module_name}'. Dependency missing? Error: {e}")
    except Exception as e:
        # 捕获其他异常
        print(f"[ComfyUI-Koi-Toolkit] Error: Failed to load module '{module_name}'.")
        traceback.print_exc()

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]