import requests
import json
import time
import random

class FreepikIconSearch:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"default": "FPSX402fe058c923beb81ccb2e6cf0bda1cf", "multiline": False}),
                "accept_language": ("STRING", {"default": "zh", "multiline": False}),
                "term": ("STRING", {"default": "材质", "multiline": False}),
                "page": ("INT", {"default": 1, "min": 0, "max": 100}),
                "per_page": ("INT", {"default": 2, "min": 0, "max": 100}),
                "thumbnail_size": ("INT", {"default": 256, "min": 0, "max": 512}),
                "icon_type": (["none","standard", "animated", "sticker", "uicon"],),
                "color": (["none", "gradient", "solid-black", "multicolor", "azure", "black", "blue", "chartreuse", "cyan", "gray", "green", "orange", "red", "rose", "spring-green", "violet", "white", "yellow"],),
                "shape": (["none", "outline", "fill", "lineal-color", "hand-drawn"],),
                "period": (["none","all", "three-months", "six-months", "one-year"],),
                "order": (["none","relevance", "recent"],),
                "enable_random_selection": ("BOOLEAN", {"default": False}),
                "selection_count": ("INT", {"default": 1, "min": 1, "max": 100}),
            },
        }

    RETURN_TYPES = ("JSON", "JSON")
    RETURN_NAMES = ("icon_urls", "raw_json")
    FUNCTION = "search_icons"
    CATEGORY = "Koi/Network"

    def search_icons(self, api_key, accept_language, term, page, per_page, thumbnail_size, icon_type, color, shape, period, order, enable_random_selection, selection_count):
        base_url = "https://api.freepik.com/v1/icons"
        
        headers = {
            "Accept-Language": accept_language,
            "x-freepik-api-key": api_key
        }
        
        # Construct variable parameters
        param_mapping = {
            "term": term,
            "order": order,
            "filters[icon_type][]": icon_type,
            "filters[color]": color,
            "filters[shape]": shape,
            "filters[period]": period
        }
        
        current_params = {k: v for k, v in param_mapping.items() if v and v != "none"}
            
        # Construct constant parameters
        base_params = {}
        if page > 0:
            base_params["page"] = page
        if per_page > 0:
            base_params["per_page"] = per_page
        if thumbnail_size > 0:
            base_params["thumbnail_size"] = thumbnail_size
            
        # Priority of relaxation (drop order)
        keys_to_drop_priority = [
            "order",
            "filters[period]",
            "filters[color]",
            "filters[shape]",
            "filters[icon_type][]"
        ]
        
        last_data = {}
        
        while True:
            # Merge current variable params with base params
            request_params = {**current_params, **base_params}
            
            try:
                response = requests.get(base_url, headers=headers, params=request_params)
                
                extracted_icons = []
                data = {}

                if response.status_code == 200:
                    data = response.json()
                    last_data = data
                    if "data" in data:
                        for item in data["data"]:
                            if "thumbnails" in item and len(item["thumbnails"]) > 0:
                                extracted_icons.append(item["thumbnails"][0]["url"])
                elif response.status_code == 404:
                    # Freepik API returns 404 when no icons are found, handle this gracefully
                    try:
                        error_data = response.json()
                        if error_data.get("message") == "No icons found":
                            # Treat as empty results and continue to relaxation logic
                            pass
                        else:
                            # Real 404 error
                            response.raise_for_status()
                    except:
                        response.raise_for_status()
                elif response.status_code == 400:
                    # Handle 400 Bad Request (often invalid parameter combinations)
                    try:
                        error_data = response.json()
                        print(f"Freepik Icon Search: API returned 400 Bad Request. Message: {error_data.get('message')}")
                        # Treat as failure and continue to relaxation logic
                        pass
                    except:
                        response.raise_for_status()
                else:
                    response.raise_for_status()
                
                if extracted_icons:
                    print(f"Freepik Icon Search: Found {len(extracted_icons)} icons. Params: {current_params}")
                    
                    if enable_random_selection and len(extracted_icons) > selection_count:
                        extracted_icons = random.sample(extracted_icons, selection_count)
                        print(f"Freepik Icon Search: Randomly selected {len(extracted_icons)} icons.")

                    return (extracted_icons, data)
                
                # If return value is empty (no icons found), automatically execute relaxation steps
                print(f"Freepik Icon Search: No icons found with params {current_params}. Starting relaxation process...")
                
                key_dropped = False
                for key in keys_to_drop_priority:
                    # If the parameter exists in current_params, drop it and retry.
                    if key in current_params:
                        del current_params[key]
                        print(f"Freepik Icon Search: Dropped parameter '{key}'. Retrying search...")
                        key_dropped = True
                        break
                    else:
                        # Debug log to show we are skipping keys that don't exist
                        # print(f"Freepik Icon Search: Parameter '{key}' not active, skipping.")
                        pass
                
                if not key_dropped:
                    # No more keys to drop, and still no results
                    print("Freepik Icon Search: No icons found even after relaxing all conditions.")
                    return ([], last_data)
                
                if not key_dropped:
                    # No more keys to drop, and still no results
                    print("Freepik Icon Search: No icons found even after relaxing all conditions.")
                    return ([], last_data)
                    
            except Exception as e:
                print(f"Error searching icons: {e}")
                if 'response' in locals():
                    print(f"Response content: {response.text}")
                return ([], {})

NODE_CLASS_MAPPINGS = {
    "FreepikIconSearch": FreepikIconSearch
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FreepikIconSearch": "Freepik Icon Search"
}
