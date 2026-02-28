import logging
import asyncio
from typing import List, Optional
from volcenginesdkarkruntime import AsyncArk
from interfaces.image_output import ImageOutput

class ImageGeneratorSeedArkAPI:
    def __init__(
        self,
        api_key: str,
        image_model_endpoint: str = "ep-20260228143218-zwr4g",
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
        **kwargs
    ):
        self.api_key = api_key
        self.endpoint = image_model_endpoint
        self.base_url = base_url
        self.client = AsyncArk(base_url=self.base_url, api_key=self.api_key)

    async def generate_single_image(
        self,
        prompt: str,
        reference_image_paths: List[str] = [],
        size: Optional[str] = None,
        **kwargs,
    ) -> ImageOutput:
        
        logging.info(f"Calling Ark API ({self.endpoint}) to generate image...")
        
        # Volcengine Ark implementation for standard image generation
        try:
            # Seedream 5.0 model has strict size limits (must be at least 3,686,400 pixels).
            # Ignore ViMax's default '1024x1024' size request and use '2K'.
            final_size = "2K"
            
            response = await self.client.images.generate(
                model=self.endpoint,
                prompt=prompt,
                size=final_size,
                response_format="url",
                extra_body={
                    "watermark": False,
                },
            )
            image_url = response.data[0].url
            logging.info(f"Image generation succeeded. URL: {image_url}")
            return ImageOutput(fmt="url", ext="png", data=image_url)
        except Exception as e:
            logging.error(f"Error occurred while generating image: {e}")
            raise e
