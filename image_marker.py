import torch
import numpy as np
from PIL import Image
import io
import base64
from server import PromptServer
from aiohttp import web
import traceback
from threading import Event

# Store node state
marker_node_data = {}

class KoiImageMarker:
    """
    A node that pops up a dialog for the user to mark bounding boxes on an image.
    Returns the image with the marked boxes.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "mark_image"
    CATEGORY = "Koi/Image"

    def mark_image(self, image, unique_id):
        try:
            node_id = unique_id
            event = Event()
            
            # Initialize node data
            marker_node_data[node_id] = {
                "event": event,
                "result": None,
            }
            
            # Prepare image for preview (take the first batch item)
            # Logic copied from ImageCropper for consistency
            preview_image = (torch.clamp(image.clone(), 0, 1) * 255).cpu().numpy().astype(np.uint8)[0]
            pil_image = Image.fromarray(preview_image)
            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG")
            base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            try:
                # Send event to frontend
                PromptServer.instance.send_sync("koi_marker_update", {
                    "node_id": node_id,
                    "image_data": f"data:image/png;base64,{base64_image}"
                })
                
                # Wait for user response (timeout 300s to give user time)
                print(f"[KoiImageMarker] Waiting for user input on node {node_id}...")
                if not event.wait(timeout=300):
                    print(f"[KoiImageMarker] Timeout waiting for node {node_id}")
                    if node_id in marker_node_data:
                        del marker_node_data[node_id]
                    return (image,)

                # Get result
                result_data = None
                if node_id in marker_node_data:
                    result_data = marker_node_data[node_id]["result"]
                    del marker_node_data[node_id]
                
                if result_data:
                    # Convert base64 back to tensor
                    try:
                        if result_data.startswith('data:image'):
                            base64_data = result_data.split(',')[1]
                        else:
                            base64_data = result_data
                            
                        image_data = base64.b64decode(base64_data)
                        buffer = io.BytesIO(image_data)
                        pil_image = Image.open(buffer)
                        
                        if pil_image.mode == 'RGBA':
                            pil_image = pil_image.convert('RGB')
                        
                        np_image = np.array(pil_image)
                        
                        # Convert to tensor (1, H, W, C)
                        tensor_image = torch.from_numpy(np_image / 255.0).float().unsqueeze(0)
                        return (tensor_image,)
                        
                    except Exception as e:
                        print(f"[KoiImageMarker] Error processing result image: {e}")
                        traceback.print_exc()
                        return (image,)
                
                return (image,)
                
            except Exception as e:
                print(f"[KoiImageMarker] Error in processing loop: {str(e)}")
                traceback.print_exc()
                if node_id in marker_node_data:
                    del marker_node_data[node_id]
                return (image,)
            
        except Exception as e:
            print(f"[KoiImageMarker] Error: {str(e)}")
            traceback.print_exc()
            return (image,)

# API Routes
@PromptServer.instance.routes.post("/koi/image_marker/apply")
async def apply_marker(request):
    try:
        data = await request.json()
        node_id = data.get("node_id")
        image_data = data.get("image_data")
        
        if node_id in marker_node_data:
            marker_node_data[node_id]["result"] = image_data
            marker_node_data[node_id]["event"].set()
            return web.json_response({"success": True})
            
        return web.json_response({"success": False, "error": "Node session not found"})
        
    except Exception as e:
        print(f"[KoiImageMarker] API Error: {str(e)}")
        traceback.print_exc()
        return web.json_response({"success": False, "error": str(e)})

@PromptServer.instance.routes.post("/koi/image_marker/cancel")
async def cancel_marker(request):
    try:
        data = await request.json()
        node_id = data.get("node_id")
        
        if node_id in marker_node_data:
            # Just set event to continue execution with default values
            marker_node_data[node_id]["event"].set()
            print(f"[KoiImageMarker] Cancelled node {node_id}")
            return web.json_response({"success": True})
        
        return web.json_response({"success": False, "error": "Node session not found"})
        
    except Exception as e:
        print(f"[KoiImageMarker] API Error: {str(e)}")
        traceback.print_exc()
        return web.json_response({"success": False, "error": str(e)})

NODE_CLASS_MAPPINGS = {
    "KoiImageMarker": KoiImageMarker,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "KoiImageMarker": "Koi Image Marker",
}
