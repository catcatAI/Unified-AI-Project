import asyncio
import uuid
import logging
import base64
import io
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from apps.backend.src.agents.base_agent import BaseAgent
from apps.backend.src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

class VisionProcessingAgent(BaseAgent):
    """
    A specialized agent for computer vision tasks like image classification,
    object detection, and image enhancement.
    """
    def __init__(self, agent_id: str):
        capabilities = [
            {
                "capability_id": f"{agent_id}_image_classification_v1.0",
                "name": "image_classification",
                "description": "Classifies images into predefined categories.",
                "version": "1.0",
                "parameters": [
                    {"name": "image_data", "type": "string", "required": True, "description": "Base64 encoded image data"},
                    {"name": "categories", "type": "array", "required": False, "description": "List of possible categories for classification"}
                ],
                "returns": {"type": "object", "description": "Classification results including predicted category and confidence."}
            },
            {
                "capability_id": f"{agent_id}_object_detection_v1.0",
                "name": "object_detection",
                "description": "Detects and localizes objects within an image.",
                "version": "1.0",
                "parameters": [
                    {"name": "image_data", "type": "string", "required": True, "description": "Base64 encoded image data"}
                ],
                "returns": {"type": "object", "description": "Detected objects with bounding boxes and labels."}
            },
            {
                "capability_id": f"{agent_id}_image_enhancement_v1.0",
                "name": "image_enhancement",
                "description": "Enhances image quality through noise reduction and sharpening.",
                "version": "1.0",
                "parameters": [
                    {"name": "image_data", "type": "string", "required": True, "description": "Base64 encoded image data"},
                    {"name": "enhancement_type", "type": "string", "required": False, "description": "Type of enhancement (sharpen, denoise, brighten)"}
                ],
                "returns": {"type": "string", "description": "Base64 encoded enhanced image data."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities)
        logging.info(f"[{self.agent_id}] VisionProcessingAgent initialized with capabilities: {[cap['name'] for cap in capabilities]}")

    async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        request_id = task_payload.get("request_id")
        capability_id = task_payload.get("capability_id_filter", "")
        params = task_payload.get("parameters", {})

        logging.info(f"[{self.agent_id}] Handling task {request_id} for capability '{capability_id}'")

        try:
            if "image_classification" in capability_id:
                result = self._classify_image(params)
                result_payload = self._create_success_payload(request_id, result)
            elif "object_detection" in capability_id:
                result = self._detect_objects(params)
                result_payload = self._create_success_payload(request_id, result)
            elif "image_enhancement" in capability_id:
                result = self._enhance_image(params)
                result_payload = self._create_success_payload(request_id, result)
            else:
                result_payload = self._create_failure_payload(request_id, "CAPABILITY_NOT_SUPPORTED", f"Capability '{capability_id}' is not supported by this agent.")
        except Exception as e:
            logging.error(f"[{self.agent_id}] Error processing task {request_id}: {e}")
            result_payload = self._create_failure_payload(request_id, "EXECUTION_ERROR", str(e))

        if self.hsp_connector and task_payload.get("callback_address"):
            callback_topic = task_payload["callback_address"]
            await self.hsp_connector.send_task_result(result_payload, callback_topic)
            logging.info(f"[{self.agent_id}] Sent task result for {request_id} to {callback_topic}")

    def _classify_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Classifies an image into predefined categories."""
        image_data = params.get('image_data', '')
        
        if not image_data:
            raise ValueError("No image data provided for classification")
        
        # In a real implementation, this would use a proper image classification model
        # For this example, we'll simulate classification with random results
        categories = params.get('categories', ['animal', 'vehicle', 'person', 'object', 'scene'])
        if not categories:
            categories = ['animal', 'vehicle', 'person', 'object', 'scene']
            
        # Simulate classification result
        import random
        predicted_category = random.choice(categories)
        confidence = random.uniform(0.7, 0.95)
        
        # Decode image to get basic info
        try:
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            image_info = {
                "width": image.width,
                "height": image.height,
                "mode": image.mode
            }
        except Exception as e:
            image_info = {"error": f"Could not decode image: {str(e)}"}
        
        return {
            "predicted_category": predicted_category,
            "confidence": round(confidence, 3),
            "categories": categories,
            "image_info": image_info
        }

    def _detect_objects(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detects objects in an image."""
        image_data = params.get('image_data', '')
        
        if not image_data:
            raise ValueError("No image data provided for object detection")
        
        # In a real implementation, this would use a proper object detection model
        # For this example, we'll simulate detection with random results
        common_objects = ['person', 'car', 'dog', 'cat', 'tree', 'building', 'chair', 'table', 'phone', 'book']
        
        # Simulate object detection results
        import random
        num_objects = random.randint(0, 5)
        detected_objects = []
        
        for i in range(num_objects):
            obj = {
                "label": random.choice(common_objects),
                "confidence": round(random.uniform(0.5, 0.95), 3),
                "bounding_box": {
                    "x": random.randint(0, 100),
                    "y": random.randint(0, 100),
                    "width": random.randint(10, 50),
                    "height": random.randint(10, 50)
                }
            }
            detected_objects.append(obj)
        
        # Decode image to get basic info
        try:
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            image_info = {
                "width": image.width,
                "height": image.height
            }
        except Exception as e:
            image_info = {"error": f"Could not decode image: {str(e)}"}
        
        return {
            "objects": detected_objects,
            "object_count": len(detected_objects),
            "image_info": image_info
        }

    def _enhance_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enhances an image."""
        image_data = params.get('image_data', '')
        enhancement_type = params.get('enhancement_type', 'sharpen')
        
        if not image_data:
            raise ValueError("No image data provided for enhancement")
        
        try:
            # Decode the image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Apply enhancement based on type
            if enhancement_type == 'sharpen':
                # Simple sharpening using PIL
                from PIL import ImageFilter
                enhanced_image = image.filter(ImageFilter.SHARPEN)
            elif enhancement_type == 'denoise':
                # Simple denoising simulation
                from PIL import ImageFilter
                enhanced_image = image.filter(ImageFilter.SMOOTH)
            elif enhancement_type == 'brighten':
                # Brighten the image
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Brightness(image)
                enhanced_image = enhancer.enhance(1.2)  # Increase brightness by 20%
            else:
                # Default to sharpening
                from PIL import ImageFilter
                enhanced_image = image.filter(ImageFilter.SHARPEN)
            
            # Encode the enhanced image back to base64
            buffered = io.BytesIO()
            enhanced_image.save(buffered, format=image.format or 'PNG')
            enhanced_image_data = base64.b64encode(buffered.getvalue()).decode()
            
            return {
                "enhanced_image_data": enhanced_image_data,
                "original_size": len(image_data),
                "enhanced_size": len(enhanced_image_data),
                "enhancement_type": enhancement_type,
                "image_info": {
                    "width": enhanced_image.width,
                    "height": enhanced_image.height,
                    "mode": enhanced_image.mode
                }
            }
        except Exception as e:
            raise ValueError(f"Error enhancing image: {str(e)}")

    def _create_success_payload(self, request_id: str, result: Any) -> HSPTaskResultPayload:
        return HSPTaskResultPayload(
            request_id=request_id,
            status="success",
            payload=result
        )

    def _create_failure_payload(self, request_id: str, error_code: str, error_message: str) -> HSPTaskResultPayload:
        return HSPTaskResultPayload(
            request_id=request_id,
            status="failure",
            error_details={"error_code": error_code, "error_message": error_message}
        )


if __name__ == '__main__':
    async def main():
        agent_id = f"did:hsp:vision_processing_agent_{uuid.uuid4().hex[:6]}"
        agent = VisionProcessingAgent(agent_id=agent_id)
        await agent.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nVisionProcessingAgent manually stopped.")