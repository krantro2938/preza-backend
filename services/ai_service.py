import os
import json
import httpx
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()


class AIService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "google/gemini-2.5-flash-lite"
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY не установлен")
    
    async def generate_presentation_structure(self, topic: str, slides_count: int, style: str) -> Dict[str, Any]:
        """Генерация структуры презентации с помощью ИИ"""
        
        prompt = f"""
        Создай структуру презентации на тему "{topic}" из {slides_count} слайдов в стиле "{style}".
        
        Требования:
        - Все тексты должны быть на русском языке
        - Стиль должен быть минималистичным и профессиональным
        - Каждый слайд должен иметь заголовок и содержание
        - Содержание должно быть информативным, но кратким (максимум 3-4 пункта)
        - Первый слайд должен быть титульным с layout "title-slide"
        - Остальные слайды используют layout "title-content"
        - Последний слайд должен быть заключительным
        - Используй markdown форматирование для списков (- пункт)
        - ОБЯЗАТЕЛЬНО: После маркированных пунктов каждого слайда добавь пустую строку, затем 1-2 предложения с ключевыми выводами на русском
        - Для каждого слайда создай релевантный запрос для поиска изображения на английском
        
        Верни результат строго в формате JSON:
        {{
            "title": "Заголовок презентации",
            "slides": [
                {{
                    "slide_number": 1,
                    "title": "Название презентации",
                    "content": "Краткое описание темы презентации",
                    "layout": "title-slide",
                    "image_query": "business presentation professional"
                }},
                {{
                    "slide_number": 2,
                    "title": "Заголовок слайда",
                    "content": "- Первый пункт\n- Второй пункт\n- Третий пункт\n\nКлючевые выводы: этот раздел показывает важность комплексного подхода к решению проблем.",
                    "layout": "title-content",
                    "image_query": "запрос для изображения на английском"
                }}
            ]
        }}
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
        
        if response.status_code != 200:
            raise Exception(f"Ошибка API OpenRouter: {response.status_code} - {response.text}")
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Парсим JSON из ответа
        try:
            # Находим JSON в ответе
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            structure = json.loads(json_str)
            return structure
        except (json.JSONDecodeError, ValueError) as e:
            raise Exception(f"Ошибка парсинга ответа ИИ: {str(e)}")
    
    async def improve_slide_content(self, title: str, content: str) -> str:
        """Улучшение содержимого слайда"""
        
        prompt = f"""
        Улучши содержимое этого слайда для презентации:
        
        Заголовок: {title}
        Текущее содержимое: {content}
        
        Требования:
        - Текст должен быть на русском языке
        - Стиль минималистичный и профессиональный
        - Используй markdown форматирование
        - Содержимое должно быть кратким, но информативным
        - Максимум 3-4 основных пункта
        
        Верни только улучшенное содержимое в формате markdown.
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 1000
                }
            )
        
        if response.status_code != 200:
            raise Exception(f"Ошибка API OpenRouter: {response.status_code}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()