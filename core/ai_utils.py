import requests
from django.conf import settings
import json
import re

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
            timeout=40
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Ошибка AI: {str(e)}"


def extract_json_block(response_text, fallback):
    """
    Пытается вытащить JSON-объект или массив из ответа AI.
    """
    try:
        return json.loads(response_text)
    except Exception:
        pass

    patterns = [
        r"(\{.*\})",
        r"(\[.*\])",
    ]

    for pattern in patterns:
        match = re.search(pattern, response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                continue

    return fallback


# ---------- АНАЛИЗ ДЕЛА ----------

def analyze_case_structured(case_text, history=None):
    prompt = f"""
Ты — профессиональный ИИ-юрист и legal analyst.

Проанализируй дело и верни СТРОГО JSON без markdown, комментариев и лишнего текста.

Формат ответа:
{{
  "summary": "краткое содержание 2-3 строки",
  "jurisdiction": "предполагаемая юрисдикция",
  "complexity": "Низкая / Средняя / Высокая",
  "plaintiff": "истец или 'Не указано'",
  "defendant": "ответчик или 'Не указано'",
  "claim": "суть требований",
  "facts": [
    "факт 1",
    "факт 2"
  ],
  "what_must_be_proven": [
    "что должен доказать истец 1",
    "что должен доказать истец 2"
  ],
  "missing_information": [
    "каких данных не хватает 1",
    "каких данных не хватает 2"
  ],
  "legal_basis": [
    "конкретная статья закона 1",
    "конкретная статья закона 2"
  ],
  "plaintiff_position": "позиция истца только по имеющимся данным",
  "defendant_position": "позиция ответчика только если она прямо есть в тексте; иначе: 'Не раскрыта в представленных материалах'",
  "evidence_assessment": "оценка достаточности доказательств",
  "risks": [
    "риск 1",
    "риск 2"
  ],
  "recommendations": [
    "рекомендация 1",
    "рекомендация 2"
  ],
  "predicted_outcome": "вероятный исход с учетом неполноты данных",
  "winning_probability": 0
}}

Правила:
1. Не выдумывай факты, которых нет в тексте.
2. Если позиция ответчика не дана в тексте, ОБЯЗАТЕЛЬНО пиши:
   "Не раскрыта в представленных материалах".
3. Если юрисдикция Узбекистан — указывай конкретные статьи, когда это возможно:
   - ГК РУз
   - КоАО РУз
   - ГПК РУз
4. Примеры legal_basis:
   - ГК РУз ст. 985 — возмещение вреда
   - ГК РУз ст. 1000 — ответственность за вред, причинённый источником повышенной опасности
   - КоАО РУз ст. 128 — нарушение правил дорожного движения
5. В legal_basis не ограничивайся только общими категориями, старайся указывать конкретные статьи и краткий смысл статьи.
6. complexity:
   - Низкая — простой спор, мало участников, мало эпизодов
   - Средняя — спор требует анализа доказательств
   - Высокая — экспертизы, несколько эпизодов, много участников, сложная доказательная база
7. В what_must_be_proven укажи минимум 2 пункта, если это возможно.
8. В missing_information укажи минимум 2 конкретных недостающих элемента, если данных недостаточно.
9. В risks укажи минимум 2 различных риска.
10. В recommendations укажи минимум 2 практических действия.
11. recommendations должны быть конкретными и прикладными: протокол ДТП, фото, видео, свидетели, экспертиза, оценка ущерба, переписка, договор, квитанции и т.п.
12. Не делай слишком уверенный вывод без доказательств.
13. winning_probability:
   - 40-55 если данных мало,
   - 55-70 если есть базовые факты, но мало доказательств,
   - 70-85 только если есть сильные доказательства,
   - выше 85 только при очень сильной доказательной базе.
14. Верни только JSON.

Текст дела:
{case_text}
"""

    response = call_api(prompt, history)

    fallback = {
        "summary": response,
        "jurisdiction": "Не определено",
        "complexity": "Средняя",
        "plaintiff": "Не указано",
        "defendant": "Не указано",
        "claim": "Не удалось определить",
        "facts": [],
        "what_must_be_proven": [],
        "missing_information": [],
        "legal_basis": [],
        "plaintiff_position": "Не удалось определить",
        "defendant_position": "Не раскрыта в представленных материалах",
        "evidence_assessment": "Недостаточно данных",
        "risks": [],
        "recommendations": [],
        "predicted_outcome": "Не удалось определить",
        "winning_probability": 0,
    }

    data = extract_json_block(response, fallback)

    if not isinstance(data, dict):
        return fallback

    data.setdefault("summary", "")
    data.setdefault("jurisdiction", "Не определено")
    data.setdefault("complexity", "Средняя")
    data.setdefault("plaintiff", "Не указано")
    data.setdefault("defendant", "Не указано")
    data.setdefault("claim", "Не удалось определить")
    data.setdefault("facts", [])
    data.setdefault("what_must_be_proven", [])
    data.setdefault("missing_information", [])
    data.setdefault("legal_basis", [])
    data.setdefault("plaintiff_position", "Не удалось определить")
    data.setdefault("defendant_position", "Не раскрыта в представленных материалах")
    data.setdefault("evidence_assessment", "Недостаточно данных")
    data.setdefault("risks", [])
    data.setdefault("recommendations", [])
    data.setdefault("predicted_outcome", "Не удалось определить")
    data.setdefault("winning_probability", 0)

    try:
        data["winning_probability"] = int(data["winning_probability"])
    except Exception:
        data["winning_probability"] = 0

    data["winning_probability"] = max(0, min(100, data["winning_probability"]))

    if not isinstance(data["facts"], list):
        data["facts"] = []
    if not isinstance(data["what_must_be_proven"], list):
        data["what_must_be_proven"] = []
    if not isinstance(data["missing_information"], list):
        data["missing_information"] = []
    if not isinstance(data["legal_basis"], list):
        data["legal_basis"] = []
    if not isinstance(data["risks"], list):
        data["risks"] = []
    if not isinstance(data["recommendations"], list):
        data["recommendations"] = []

    return data


def analyze_case(case_text, history=None):
    """
    Оставил совместимость, если где-то ещё используется старое имя.
    """
    return analyze_case_structured(case_text, history)


# ---------- ПОИСК ПОХОЖИХ ДЕЛ ----------

def search_similar_cases(prompt, history=None):
    structured_prompt = f"""
Ты — юридическая AI-система поиска прецедентов.

По описанию пользователя подбери похожие УЖЕ ЗАВЕРШЁННЫЕ или релевантные юридические дела и верни СТРОГО JSON-массив.
Без markdown, без пояснений, без текста до и после JSON.

Формат:
[
  {{
    "title": "Название дела",
    "date": "2025-01-10",
    "similarity": 87,
    "reason": "Краткая причина схожести",
    "outcome": "Иск удовлетворён частично"
  }},
  {{
    "title": "Название дела 2",
    "date": "2024-11-03",
    "similarity": 74,
    "reason": "Похожий спор о некачественном товаре",
    "outcome": "В иске отказано"
  }}
]

Правила:
1. similarity — это процент сходства, целое число от 0 до 100.
2. outcome — это ИСХОД похожего дела, а не прогноз.
3. Не указывай вероятность победы, шанс выигрыша, прогноз или risk score.
4. reason — коротко объясни, почему дело похоже.
5. Верни от 3 до 5 результатов.
6. Если точных совпадений нет, верни наиболее близкие юридические кейсы.
7. Никакого текста кроме JSON.

Текст для поиска:
{prompt}
"""

    response = call_api(structured_prompt, history)

    fallback = [
        {
            "title": response,
            "date": "",
            "similarity": 0,
            "reason": "Не удалось структурировать ответ AI",
            "outcome": "Не указано"
        }
    ]

    data = extract_json_block(response, fallback)

    if not isinstance(data, list):
        return fallback

    cleaned = []
    for item in data:
        if not isinstance(item, dict):
            continue

        title = item.get("title", "Без названия")
        date = item.get("date", "")
        reason = item.get("reason", "Причина не указана")
        outcome = item.get("outcome", "Не указано")

        try:
            similarity = int(item.get("similarity", 0))
        except Exception:
            similarity = 0

        similarity = max(0, min(100, similarity))

        cleaned.append({
            "title": title,
            "date": date,
            "similarity": similarity,
            "reason": reason,
            "outcome": outcome
        })

    return cleaned if cleaned else fallback


# ---------- ГЕНЕРАЦИЯ ДОКУМЕНТА ----------

def generate_document(prompt, history=None):
    smart_prompt = f"""
Ты — помощник-юрист. На основе текста пользователя определи тип юридического документа
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