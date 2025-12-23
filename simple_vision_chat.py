import httpx
import torch
import numpy as np
from PIL import Image
import io
import base64

class SimpleVisionChat:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "text": ("STRING", {"multiline": True, "default": "Briefly describe this icon to facilitate the diffusion model to reconstruct it."}),
                "api_url": ("STRING", {"default": "http://47.89.234.33:8861/api/v1"}),
                "api_key": ("STRING", {"default": "bHViYW5haTp4MTMyMXNkZjExMjM="}),
                "model": ("STRING", {"default": "gpt-4o"}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "chat_with_image"
    CATEGORY = "Koi/Chat"

    def chat_with_image(self, image, text, api_url, api_key, model):
        # Handle API URL - append /chat/completions if not present
        if not api_url.endswith("/chat/completions"):
            api_url = f"{api_url.rstrip('/')}/chat/completions"

        # Handle image conversion (Tensor to Base64)
        # Take the first image in the batch
        img_tensor = image[0]
        i = 255. * img_tensor.cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        image_data_url = f"data:image/jpeg;base64,{img_str}"

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Prepare payload
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text},
                        {"type": "image_url", "image_url": {"url": image_data_url}}
                    ]
                }
            ]
        }

        try:
            # Make the API call
            # Using a longer timeout as vision models can be slow
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    api_url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()['choices'][0]['message']['content']
                return (result,)
        except Exception as e:
            return (f"Error: {str(e)}",)

# Node class mappings
NODE_CLASS_MAPPINGS = {
    "SimpleVisionChat": SimpleVisionChat
}

# Node display name mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "SimpleVisionChat": "Simple Vision Chat API"
}
