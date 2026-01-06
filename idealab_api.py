import requests
import json
import torch
import numpy as np
from PIL import Image
import io
import base64
import re

class IdealabAPINode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("STRING", {"default": "gemini-3-flash-preview"}),
                "api_key": ("STRING", {"default": "", "multiline": False}),
                "system_prompt": ("STRING", {"default": "", "multiline": True}),
                "user_prompt": ("STRING", {"default": "", "multiline": True}),
            },
            "optional": {
                "image": ("IMAGE",),
                "image2": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("STRING", "IMAGE")
    RETURN_NAMES = ("response", "image")
    FUNCTION = "chat"
    CATEGORY = "🐟Koi-Toolkit"

    def chat(self, api_key, system_prompt, user_prompt, model, image=None, image2=None):
        url = "https://idealab.alibaba-inc.com/api/openai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Construct messages
        user_content = user_prompt

        images = []
        if image is not None:
            images.append(image)
        if image2 is not None:
            images.append(image2)

        if len(images) > 0:
            user_content = [
                {
                    "type": "text",
                    "text": user_prompt
                }
            ]
            
            for img_batch in images:
                try:
                    # Take the first image in the batch
                    img_tensor = img_batch[0]
                    i = 255. * img_tensor.cpu().numpy()
                    img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
                    
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    base64_image = f"data:image/jpeg;base64,{img_str}"
                    
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": base64_image
                        }
                    })
                except Exception as e:
                    raise RuntimeError(f"Error processing image: {str(e)}")

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_content
            }
        ]

        # Construct payload
        payload = {
            "messages": messages,
            "model": model,
            "extendParams": {}
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Try to extract content from standard OpenAI format
            # Usually: choices[0].message.content
            try:
                raw_content = result["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                # If structure is different, return full JSON string
                raw_content = json.dumps(result, ensure_ascii=False, indent=2)
            
            # Ensure content is string for return and regex
            if isinstance(raw_content, str):
                content = raw_content
            else:
                content = json.dumps(raw_content, ensure_ascii=False, indent=2)
            
            # Process image output
            output_image = torch.zeros((1, 64, 64, 3), dtype=torch.float32) # Dummy image
            
            try:
                # Check for markdown image
                img_match = re.search(r"!\[.*?\]\((.*?)\)", content)
                img_url = None
                if img_match:
                    img_url = img_match.group(1)
                else:
                    # Check for raw URL that looks like an image
                    url_match = re.search(r"(https?://\S+\.(?:png|jpg|jpeg|webp|gif))", content, re.IGNORECASE)
                    if url_match:
                        img_url = url_match.group(1)
                
                # If no URL found in string, and raw_content was a list, try to find image_url in the structure
                if not img_url and isinstance(raw_content, list):
                    for part in raw_content:
                        if isinstance(part, dict):
                            # Check for standard OpenAI image_url format or just image_url key
                            if part.get("type") == "image_url" or "image_url" in part:
                                url_obj = part.get("image_url")
                                if isinstance(url_obj, dict):
                                    img_url = url_obj.get("url")
                                elif isinstance(url_obj, str):
                                    img_url = url_obj
                            # Check for other formats
                            elif "url" in part and isinstance(part["url"], str):
                                if any(part["url"].lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif']):
                                    img_url = part["url"]

                if img_url:
                    print(f"Found image URL/Data: {img_url[:50]}...")
                    
                    img = None
                    if img_url.startswith("http"):
                        img_response = requests.get(img_url, timeout=30)
                        img_response.raise_for_status()
                        img = Image.open(io.BytesIO(img_response.content))
                    elif img_url.startswith("data:image/"):
                        # Handle data URI
                        base64_data = img_url.split(",")[1]
                        img_data = base64.b64decode(base64_data)
                        img = Image.open(io.BytesIO(img_data))
                    else:
                        # Assume raw base64
                        try:
                            img_data = base64.b64decode(img_url)
                            img = Image.open(io.BytesIO(img_data))
                        except Exception:
                            print("Failed to decode base64 image")
                    
                    if img:
                        img = img.convert("RGB")
                        img_np = np.array(img).astype(np.float32) / 255.0
                        output_image = torch.from_numpy(img_np).unsqueeze(0)
            except Exception as e:
                print(f"Error processing output image: {str(e)}")
                
            return (content, output_image)

        except requests.exceptions.RequestException as e:
            error_msg = f"API Request Failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f"\nStatus Code: {e.response.status_code}"
                error_msg += f"\nResponse: {e.response.text}"
            raise RuntimeError(error_msg)
        except Exception as e:
            raise RuntimeError(f"An error occurred: {str(e)}")

NODE_CLASS_MAPPINGS = {
    "IdealabAPINode": IdealabAPINode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IdealabAPINode": "Idealab API Chat"
}
