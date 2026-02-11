import requests
from django.conf import settings
import json
# Берём API ключ из settings.py
API_KEY = getattr(settings, "OPENAI_API_KEY", None)
if not API_KEY:
    raise ValueError("Не найден OPENAI_API_KEY в settings.py")

def call_api(prompt, history=None):
    """
    Общая функция для вызова AI через OpenRouter / OpenAI API.
    history: список кортежей (role, message), role = 'user' или 'assistant'
    """
    if history is None:
        history = []

    # Формируем сообщения для API
    messages = [{"role": role, "content": msg} for role, msg in history]
    messages.append({"role": "user", "content": prompt})

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": messages,
            },
            timeout=30  # таймаут на случай долгого ответа
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        # Возвращаем ошибку как текст (можно логировать)
        return f"Ошибка AI: {str(e)}"

# Конкретные функции для LegalMind
def analyze_case(case_text, history=None):
    prompt = f"""
Ты — профессиональный ИИ-юрист. 
Твоя задача — автоматически определить юрисдикцию дела и провести точный анализ.

1) Сначала определи страну спора по признакам: валюта, имена, места, названия организаций, суды.
2) Применяй ТОЛЬКО законодательство той страны, которая логически относится к делу.
   Если валюта — рубли → РФ (ГК РФ, АПК РФ).
   Если валюта — сум → Узбекистан (ГК РУз, ЭПК РУз).
   Если тенге → Казахстан и т.д.
3) Не создавай документы. Только анализ.

Сделай:

1) Краткое содержание (2–3 строки).
2) Правовая квалификация: Укачи статьи ТОЛЬКО той страны, которую ты определил.
3) Анализ позиций истца и ответчика.
4) Оценка доказательств.
5) Вероятный исход дела.
6) Риски сторон.
7) Что нужно усилить истцу и ответчику.

Текст дела:
«««
{case_text}
»»»
"""

    return call_api(prompt, history)





import json
import re

def search_similar_cases(prompt, history=None):
    """
    Ищет похожие дела через AI и возвращает список словарей с 'title' и 'date'.
    """
    structured_prompt = f"""
    Найди похожие юридические дела на текст ниже и верни JSON в формате:
    [
        {{"title": "Название дела", "date": "Дата"}},
        ...
    ]
    Текст: {prompt}
    """

    response = call_api(structured_prompt, history)

    try:
        # Пытаемся найти JSON в ответе AI
        json_match = re.search(r"(\[.*\])", response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        else:
            # Если JSON не найден, возвращаем просто текст как одно дело
            return [{"title": response, "date": ""}]
    except json.JSONDecodeError:
        return [{"title": response, "date": ""}]



def generate_document(prompt, history=None):
    smart_prompt = f"""
Ты — помощник-юрист. На основе текста пользователя **определи тип юридического документа** 
и создай грамотно оформленный документ.

ТИПЫ: 
- Исковое заявление
- Ходатайство
- Жалоба
- Претензия
- Объяснительная
- Договор (черновик)
- Акт / протокол
- Заявление общего характера

ТРЕБОВАНИЯ К РЕЗУЛЬТАТУ:
1. Определи тип документа.
2. Скажи в начале: «Тип документа: …»
3. Составь реальный юридический документ в официальном стиле.
4. Используй структуру, реквизиты, вводную часть, описание обстоятельств, правовое обоснование, просительную часть.
5. Не придумывай данные: используй шаблонные фразы и [] для реквизитов.

ТЕКСТ ПОЛЬЗОВАТЕЛЯ:
«{prompt}»
"""
    return call_api(smart_prompt, history)

