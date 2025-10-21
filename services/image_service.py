import os
import httpx
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class ImageService:
    def __init__(self):
        self.access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        self.base_url = "https://api.unsplash.com"
        
        if not self.access_key:
            raise ValueError("UNSPLASH_ACCESS_KEY не установлен")
    
    async def search_image(self, query: str, orientation: str = "landscape") -> Optional[Dict]:
        """Поиск изображения в Unsplash"""
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search/photos",
                params={
                    "query": query,
                    "per_page": 1,
                    "orientation": orientation,
                    "content_filter": "high",
                },
                headers={
                    "Authorization": f"Client-ID {self.access_key}",
                }
            )
        
        if response.status_code != 200:
            print(f"Ошибка поиска изображения: {response.status_code} - {response.text}")
            return None
        
        data = response.json()
        
        if not data["results"]:
            return None
        
        photo = data["results"][0]
        
        return {
            "url": photo["urls"]["regular"],
            "url_small": photo["urls"]["small"],
            "url_thumb": photo["urls"]["thumb"],
            "alt_description": photo["alt_description"] or query,
            "author": photo["user"]["name"],
            "author_url": photo["user"]["links"]["html"],
            "download_location": photo["links"]["download_location"]
        }
    
    async def get_images_for_slides(self, slides: List[Dict]) -> Dict[int, Dict]:
        """Получение изображений для всех слайдов"""
        images = {}
        
        for slide in slides:
            slide_number = slide["slide_number"]
            image_query = slide.get("image_query", slide["title"])
            
            # Пропускаем титульный слайд
            if slide.get("layout") == "title-slide":
                continue
                
            image = await self.search_image(image_query)
            
            if image:
                images[slide_number] = image
                # Уведомляем Unsplash о загрузке для аналитики
                await self._trigger_download(image["download_location"])
        
        return images
    
    async def _trigger_download(self, download_location: str):
        """Уведомление Unsplash о загрузке изображения для аналитики"""
        async with httpx.AsyncClient() as client:
            try:
                await client.get(
                    download_location,
                    headers={
                        "Authorization": f"Client-ID {self.access_key}",
                    }
                )
            except Exception as e:
                print(f"Ошибка уведомления о загрузке: {e}")
    
    async def get_random_image(self, query: Optional[str] = None) -> Optional[Dict]:
        """Получение случайного изображения"""
        
        params = {
            "orientation": "landscape",
            "content_filter": "high",
        }
        
        if query:
            params["query"] = query
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/photos/random",
                params=params,
                headers={
                    "Authorization": f"Client-ID {self.access_key}",
                }
            )
        
        if response.status_code != 200:
            print(f"Ошибка получения случайного изображения: {response.status_code}")
            return None
        
        photo = response.json()
        
        return {
            "url": photo["urls"]["regular"],
            "url_small": photo["urls"]["small"],
            "url_thumb": photo["urls"]["thumb"],
            "alt_description": photo["alt_description"] or query or "Изображение",
            "author": photo["user"]["name"],
            "author_url": photo["user"]["links"]["html"],
            "download_location": photo["links"]["download_location"]
        }