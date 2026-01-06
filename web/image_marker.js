import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// Create Modal HTML
function createMarkerModal() {
    const modal = document.createElement("dialog");
    modal.id = "koi-marker-modal";
    modal.innerHTML = `
        <div class="marker-container">
            <div class="marker-header">
                <h3>Image Marker</h3>
                <button class="close-button">×</button>
            </div>
            <div class="marker-content">
                <div class="marker-wrapper">
                    <canvas id="marker-canvas"></canvas>
                </div>
                <div class="marker-controls">
                    <button id="undo-marker">Undo</button>
                    <button id="clear-marker">Clear</button>
                    <div style="flex-grow: 1;"></div>
                    <button id="apply-marker">Apply</button>
                    <button id="cancel-marker">Cancel</button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    return modal;
}

// Styles
const style = document.createElement("style");
style.textContent = `
    #koi-marker-modal {
        border: none;
        border-radius: 8px;
        padding: 0;
        background: #2a2a2a;
        max-width: 90vw;
        max-height: 90vh;
        color: #fff;
    }
    
    #koi-marker-modal::backdrop {
        background: rgba(0, 0, 0, 0.5);
    }
    
    .marker-container {
        width: fit-content;
        height: fit-content;
        min-width: 400px;
        min-height: 300px;
        display: flex;
        flex-direction: column;
    }
    
    .marker-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 20px;
        background: #333;
        border-bottom: 1px solid #444;
    }
    
    .marker-header h3 {
        margin: 0;
    }
    
    .close-button {
        background: none;
        border: none;
        color: #fff;
        font-size: 24px;
        cursor: pointer;
    }
    
    .marker-content {
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: 15px;
        overflow: auto;
    }
    
    .marker-wrapper {
        position: relative;
        overflow: hidden;
        background: #1a1a1a;
        display: flex;
        justify-content: center;
        align-items: center;
        user-select: none;
    }
    
    #marker-canvas {
        max-width: 100%;
        max-height: 60vh;
        object-fit: contain;
        display: block;
        cursor: crosshair;
    }
    
    .marker-controls {
        display: flex;
        gap: 10px;
        justify-content: flex-end;
    }
    
    .marker-controls button {
        padding: 8px 16px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-weight: bold;
    }
    
    #apply-marker {
        background: #2a8af6;
        color: white;
    }
    
    #apply-marker:hover {
        background: #1a7ae6;
    }
    
    #cancel-marker {
        background: #666;
        color: white;
    }
    
    #cancel-marker:hover {
        background: #555;
    }

    #undo-marker, #clear-marker {
        background: #444;
        color: white;
    }
    
    #undo-marker:hover, #clear-marker:hover {
        background: #555;
    }
`;
document.head.appendChild(style);

class KoiImageMarker {
    constructor() {
        this.modal = createMarkerModal();
        this.canvas = this.modal.querySelector("#marker-canvas");
        this.ctx = this.canvas.getContext("2d");
        
        this.isDrawing = false;
        this.startX = 0;
        this.startY = 0;
        this.rects = []; // Store all drawn rectangles
        this.img = null; // Store original image
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Close/Cancel
        const closeBtn = this.modal.querySelector(".close-button");
        const cancelBtn = this.modal.querySelector("#cancel-marker");
        
        const handleClose = () => this.cleanupAndClose(true);
        
        closeBtn.addEventListener("click", handleClose);
        cancelBtn.addEventListener("click", handleClose);
        
        // Apply
        const applyBtn = this.modal.querySelector("#apply-marker");
        applyBtn.addEventListener("click", () => this.applyMarker());
        
        // Undo
        const undoBtn = this.modal.querySelector("#undo-marker");
        undoBtn.addEventListener("click", () => {
            this.rects.pop();
            this.redraw();
        });

        // Clear
        const clearBtn = this.modal.querySelector("#clear-marker");
        clearBtn.addEventListener("click", () => {
            this.rects = [];
            this.redraw();
        });

        // ESC key
        this.modal.addEventListener("keydown", (e) => {
            if (e.key === "Escape") handleClose();
        });
        
        // Drawing
        this.canvas.addEventListener("mousedown", (e) => this.startDrawing(e));
        window.addEventListener("mousemove", (e) => this.draw(e));
        window.addEventListener("mouseup", () => this.endDrawing());
    }
    
    async cleanupAndClose(cancelled = false) {
        if (cancelled && this.currentNodeId) {
            try {
                await api.fetchApi("/koi/image_marker/cancel", {
                    method: "POST",
                    body: JSON.stringify({ node_id: this.currentNodeId })
                });
            } catch (e) {
                console.error("Failed to cancel marker:", e);
            }
        }
        
        this.isDrawing = false;
        this.modal.close();
    }
    
    getCanvasCoordinates(e) {
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        
        return {
            x: (e.clientX - rect.left) * scaleX,
            y: (e.clientY - rect.top) * scaleY
        };
    }

    startDrawing(e) {
        const coords = this.getCanvasCoordinates(e);
        this.isDrawing = true;
        this.startX = coords.x;
        this.startY = coords.y;
        this.currentW = 0;
        this.currentH = 0;
    }
    
    draw(e) {
        if (!this.isDrawing) return;
        
        const coords = this.getCanvasCoordinates(e);
        // Constrain to canvas
        const currentX = Math.max(0, Math.min(coords.x, this.canvas.width));
        const currentY = Math.max(0, Math.min(coords.y, this.canvas.height));
        
        this.currentW = currentX - this.startX;
        this.currentH = currentY - this.startY;
        
        this.redraw();
        
        // Draw current selection
        this.ctx.strokeStyle = "red";
        this.ctx.lineWidth = 5; // Thicker line
        this.ctx.strokeRect(this.startX, this.startY, this.currentW, this.currentH);
    }
    
    endDrawing() {
        if (!this.isDrawing) return;
        this.isDrawing = false;
        
        if (Math.abs(this.currentW) > 5 && Math.abs(this.currentH) > 5) {
            this.rects.push({
                x: this.startX,
                y: this.startY,
                w: this.currentW,
                h: this.currentH
            });
        }
        this.redraw();
    }

    redraw() {
        // Clear
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw Image
        if (this.img) {
            this.ctx.drawImage(this.img, 0, 0);
        }
        
        // Draw all rects
        this.ctx.strokeStyle = "red";
        this.ctx.lineWidth = 5;
        
        for (const rect of this.rects) {
            this.ctx.strokeRect(rect.x, rect.y, rect.w, rect.h);
        }
    }
    
    async applyMarker() {
        try {
            // Get the full image with markings
            const imageData = this.canvas.toDataURL("image/png");
            
            await api.fetchApi("/koi/image_marker/apply", {
                method: "POST",
                body: JSON.stringify({
                    node_id: this.currentNodeId,
                    image_data: imageData
                })
            });
            this.cleanupAndClose(false);
        } catch (e) {
            console.error("Failed to apply marker:", e);
            alert("Error applying marker: " + e.message);
        }
    }
    
    show(nodeId, imageData, node) {
        this.currentNodeId = nodeId;
        this.currentNode = node;
        this.rects = []; // Reset rects
        
        this.img = new Image();
        this.img.onload = () => {
            this.canvas.width = this.img.width;
            this.canvas.height = this.img.height;
            this.redraw();
            this.modal.showModal();
        };
        this.img.src = imageData;
    }
}

// Register Extension
app.registerExtension({
    name: "Koi.ImageMarker",
    async setup() {
        const marker = new KoiImageMarker();
        
        api.addEventListener("koi_marker_update", ({ detail }) => {
            const { node_id, image_data } = detail;
            const node = app.graph.getNodeById(node_id);
            marker.show(node_id, image_data, node);
        });
    }
});
