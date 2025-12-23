import torch
import numpy as np
from PIL import Image, ImageOps
import requests
import io
import json

class DownloadImagesFromUrls:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "urls_json": ("JSON", {"multiline": True, "default": "[]", "dynamicPrompts": False}),
            },
            "optional": {
                "keep_alpha_channel": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "download_images"
    CATEGORY = "🐟Koi-Toolkit"

    def download_images(self, urls_json, keep_alpha_channel=False):
        if isinstance(urls_json, (list, dict)):
            data = urls_json
        else:
            try:
                data = json.loads(urls_json)
            except json.JSONDecodeError:
                print(f"[DownloadImagesFromUrls] Error: Invalid JSON input.")
                # Return a blank image to avoid crashing the workflow completely, or maybe raise error?
                # Returning blank image is safer for continuity but might be confusing.
                # Let's return a 1x1 black pixel.
                return (torch.zeros((1, 64, 64, 3)),)

        urls = []
        if isinstance(data, list):
            urls = [str(item) for item in data]
        elif isinstance(data, dict):
            # Try to find a list in the dict
            for key, value in data.items():
                if isinstance(value, list):
                    urls.extend([str(item) for item in value])
            # If no list found, maybe the values are urls?
            if not urls:
                 urls = [str(v) for v in data.values() if isinstance(v, str)]
        
        if not urls:
            print(f"[DownloadImagesFromUrls] Warning: No URLs found in input.")
            return (torch.zeros((1, 64, 64, 3)),)

        images = []
        first_width = 0
        first_height = 0

        for url in urls:
            if not isinstance(url, str) or not url.startswith("http"):
                continue
            
            try:
                # Add headers to mimic a browser to avoid some 403s
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    i = Image.open(io.BytesIO(response.content))
                    i = ImageOps.exif_transpose(i) # Handle orientation

                    if not keep_alpha_channel:
                        i = i.convert("RGB")
                    else:
                        i = i.convert("RGBA")

                    # Handle resizing to match batch
                    if len(images) == 0:
                        first_width = i.width
                        first_height = i.height
                    else:
                        if i.width != first_width or i.height != first_height:
                            # Resize to match the first image
                            i = i.resize((first_width, first_height), Image.LANCZOS)

                    image = np.array(i).astype(np.float32) / 255.0
                    image = torch.from_numpy(image)[None,]
                    images.append(image)
                else:
                    print(f"[DownloadImagesFromUrls] Failed to download {url}: Status {response.status_code}")
            except Exception as e:
                print(f"[DownloadImagesFromUrls] Error downloading {url}: {e}")

        if not images:
             print(f"[DownloadImagesFromUrls] No images downloaded successfully.")
             return (torch.zeros((1, 64, 64, 3)),)

        if len(images) > 1:
            output_image = torch.cat(images, dim=0)
        else:
            output_image = images[0]

        return (output_image,)

NODE_CLASS_MAPPINGS = {
    "DownloadImagesFromUrls": DownloadImagesFromUrls
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DownloadImagesFromUrls": "Download Images From URLs"
}
