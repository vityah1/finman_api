# Erste Bank Österreich - Імпорт PDF виписок

## Опис

Модуль для парсингу та імпорту банківських виписок з PDF файлів Erste Bank Австрії.

## Особливості

- Підтримка PDF формату виписок
- Автоматичне конвертування EUR в UAH за курсом НБУ
- Розпізнавання типів транзакцій (George-Überweisung, E-COMM)
- Обробка багаторядкової структури PDF

## Типи транзакцій

### George-Überweisung
Перекази через George Banking:
- **Формат**: George-Überweisung ДДММ сума- отримувач
- **Приклад**: George-Überweisung 0305 12,00- Uliana Holoshivska

### E-COMM
Електронна комерція:
- **Формат**: E-COMM сума AT K1 ДД.ММ. ЧЧ:ХХ ДДММ сума- торговець
- **Приклад**: E-COMM 10,00 AT K1 27.05. 23:11 2905 10,00- HOT TELEKOM

## Структура даних

- **Дата** - у форматі ДДММ (додається поточний рік)
- **Опис операції** - назва отримувача або торговця
- **Тип транзакції** - Transfer або Purchase
- **Сума** - в EUR з автоконвертацією в UAH
- **Валюта** - EUR

## API Endpoint

```http
POST /api/import
Content-Type: multipart/form-data

file: <PDF файл виписки Erste Bank>
mode: "erste"
action: "show" | "import"
```
