# anicli-ru

___
Скрипт для поиска и просмотра аниме из терминала с русской озвучкой или субтитрами для linux систем, 
написанный на python.

> Этот dev проект в стадии разработки, стабильность не гарантируется

---
Какие будут отличия от старой версии:

- Проект полностью переписан
- Api интерфейс парсера и Cli клиента разделены в отдельные репозитории
- парсеры работают в связке `httpx`, `parsel`, `chompjs`, умеет работать в sync и async, 
использует экспериментальную обёртку `scrape-schema` для повышения ремонтопригодности, консинстентности, 
читабельности и переиспользуемости кода
- Клиент написан на `eggella` - обёртка над prompt-toolkit для реализации prompt-line приложений 
(архитектура схожа с flask и актуальными фреймворк чат ботами (aiogram, discord.py, ...))


## Roadmap
-[x] минимальная реализация
-[ ] выбор источника
-[ ] http сервер-прослойка для передачи видео в плееры отличные от mpv (обход дополнительных аргументов 
headers для vlc плеера и других, например)
-[ ] поиск по нескольким источникам в одной сессии
-[ ] конфигурация приложения
-[ ] конфигурация http клиента (прокси, таймаут)
-[ ] кеширование
-[ ] синхронизация с shikimori
-[ ] система плагинов, частичная кастомизация
