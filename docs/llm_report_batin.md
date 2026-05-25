# Отчёт по онлайн-курсам: LLM
**Батин Николай, группа 251-372**

---

## Пройденные курсы

### Hugging Face NLP Course
https://huggingface.co/learn/nlp-course — онлайн, бесплатно, ~20 часов

Курс прошёл целиком. Основной упор делается на библиотеку `transformers` и работу с предобученными моделями. Прошёл все главы: от токенизаторов до fine-tuning и написания кастомных обучающих циклов.

Что конкретно изучил:
- Как устроен Transformer изнутри — механизм self-attention, позиционные энкодинги, нормализация
- Разница между энкодерными (BERT) и декодерными (GPT) моделями на практике
- Работа с `AutoTokenizer` и `AutoModelForSequenceClassification`
- Подготовка датасетов через `datasets`, батчинг, padding/truncation
- Fine-tuning на кастомных данных через `Trainer` API

### Stepik — Введение в LLM
https://stepik.org/catalog?query=LLM — русский язык, ~8 часов

Прошёл для понимания общей картины: как устроены современные большие модели, чем отличаются от классических нейросетей, как с ними правильно работать.

Что изучил:
- Принцип авторегрессионной генерации — как выбирается следующий токен
- Параметры генерации: `temperature`, `top_k`, `top_p`, `repetition_penalty`
- Промпт-инжиниринг: zero-shot, few-shot, chain-of-thought, system prompts
- Ограничения LLM: галлюцинации, устаревшие знания, зависимость от формулировки

---

## Как применил при разработке FitBot

Основная задача в вариативной части — написать Telegram-бота на GigaChat. Знания из курсов применил напрямую.

**Интеграция GigaChat API.** Библиотека `gigachat` работает похоже на `transformers` — передаёшь промпт, получаешь ответ. Реализовал асинхронные вызовы через `GigaChatAsyncClient`:

```python
async def _call_giga(prompt: str, temperature: float = 0.9) -> str:
    async with GigaChatAsyncClient(credentials=GIGACHAT_CREDENTIALS,
                                   verify_ssl_certs=False) as giga:
        response = await giga.achat(
            Chat(messages=[Messages(role=MessagesRole.USER, content=prompt)],
                 temperature=temperature)
        )
    return response.choices[0].message.content
```

**Подбор temperature.** Из курса знал, что при высокой temperature модель генерирует разнообразные, но менее предсказуемые ответы. Для основного рациона использую `0.8` — стабильный результат. Для альтернативного варианта поднимаю до `1.0` чтобы получать другие блюда.

**Обработка лимитов.** API возвращает 429 при превышении rate limit. Реализовал retry с нарастающими паузами (5 → 15 → 30 сек) — идею взял из практики fine-tuning, где тоже нужно обрабатывать прерывания обучения.

**Главный вывод:** промпт — это фактически программа для LLM. Чем точнее описаны роль, формат и ограничения, тем стабильнее результат. Добавление одной строки «Не используй markdown» полностью убрало проблему с отображением в Telegram.
