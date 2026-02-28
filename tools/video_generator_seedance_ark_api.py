import logging
import asyncio
from typing import List, Literal, Optional
from volcenginesdkarkruntime import AsyncArk
from interfaces.video_output import VideoOutput
from utils.image import image_path_to_b64
from tenacity import retry, stop_after_attempt
from utils.retry import after_func

class VideoGeneratorSeedanceArkAPI:
    def __init__(
        self,
        api_key: str,
        video_model_endpoint: str = "ep-20260206152338-7vwzw",
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
        **kwargs
    ):
        self.api_key = api_key
        self.endpoint = video_model_endpoint
        self.base_url = base_url
        self.client = AsyncArk(base_url=self.base_url, api_key=self.api_key)

    async def generate_single_video(
        self,
        prompt: str,
        reference_image_paths: List[str] = [],
        resolution: Literal["480p", "720p", "1080p"] = "720p",
        aspect_ratio: str = "16:9",
        fps: Literal[16, 24] = 16,
        duration: Literal[5, 10] = 5,
    ) -> VideoOutput:
        
        logging.info(f"Calling Ark API ({self.endpoint}) to generate video...")
        
        content = [{"type": "text", "text": prompt}]
        
        if len(reference_image_paths) >= 1:
            image_b64 = image_path_to_b64(reference_image_paths[0], mime=True)
            content.append({
                "type": "image_url",
                "image_url": {"url": image_b64},
                "role": "first_frame"
            })
            
        if len(reference_image_paths) >= 2:
            image_b64 = image_path_to_b64(reference_image_paths[1], mime=True)
            content.append({
                "type": "image_url",
                "image_url": {"url": image_b64},
                "role": "last_frame"
            })

        try:
            create_result = await self.client.content_generation.tasks.create(
                model=self.endpoint,
                content=content,
                ratio=aspect_ratio,
                duration=duration,
            )
            task_id = create_result.id
            logging.info(f"Video task created successfully. Task ID: {task_id}")
        except Exception as e:
            logging.error(f"Error creating video task: {e}")
            raise e

        # Poll the task status
        while True:
            try:
                get_result = await self.client.content_generation.tasks.get(task_id=task_id)
            except Exception as e:
                logging.error(f"Error querying task status: {e}, retrying in 5 seconds...")
                await asyncio.sleep(5)
                continue

            status = get_result.status
            
            if status == "succeeded":
                # Extract video URL
                video_url = None
                if hasattr(get_result, 'content') and hasattr(get_result.content, 'video_url'):
                    video_url = get_result.content.video_url
                elif hasattr(get_result, 'video_url'):
                    video_url = get_result.video_url
                
                if video_url is None:
                    raise ValueError(f"Could not find video_url in response: {get_result}")

                logging.info(f"Video generation succeeded. URL: {video_url}")
                return VideoOutput(fmt="url", ext="mp4", data=video_url)
                
            elif status == "failed":
                error_msg = getattr(get_result, 'error', 'Unknown Error')
                logging.error(f"Video generation failed: {error_msg}")
                raise ValueError(f"Video generation failed: {error_msg}")
                
            else:
                logging.info(f"Task status: {status}, waiting 5 seconds...")
                await asyncio.sleep(5)
