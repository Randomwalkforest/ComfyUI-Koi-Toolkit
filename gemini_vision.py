from google import genai
from google.genai import types
import torch
import numpy as np
from PIL import Image
import io

class GeminiVision:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "text": ("STRING", {"multiline": True, "default": "What is in this image?"}),
                "api_key": ("STRING", {"default": "", "multiline": False}),
                "model": ("STRING", {"default": "gemini-3-flash-preview"}),
            },
            "optional": {
                "proxy": ("STRING", {"default": "", "multiline": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "generate_content"
    CATEGORY = "Koi/Chat"

    def generate_content(self, image, text, api_key, model, proxy=None):
        # Handle image conversion (Tensor to Base64)
        # Take the first image in the batch
        img_tensor = image[0]
        i = 255. * img_tensor.cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        image_bytes = buffered.getvalue()
        
        # Handle Proxy
        if proxy:
            import os
            proxy = proxy.strip()
            if not proxy.startswith("http"):
                proxy = f"http://{proxy}"
            os.environ['HTTP_PROXY'] = proxy
            os.environ['HTTPS_PROXY'] = proxy
            os.environ['ALL_PROXY'] = proxy
            print(f"GeminiVision: Using proxy {proxy}")

        # Initialize client
        # The media_resolution parameter is currently only available in the v1alpha API version.
        if not api_key:
            return ("Error: API Key is required.",)

        try:
            client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
            
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Content(
                        parts=[
                            types.Part(text=text),
                            types.Part(
                                inline_data=types.Blob(
                                    mime_type="image/jpeg",
                                    data=image_bytes,
                                ),
                                # media_resolution={"level": "media_resolution_high"}
                            )
                        ]
                    )
                ]
            )
            return (response.text,)
        except Exception as e:
            return (f"Error: {str(e)}",)

NODE_CLASS_MAPPINGS = {
    "GeminiVision": GeminiVision
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GeminiVision": "Gemini Vision API"
}
