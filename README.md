# hillel_hw_14 — Django: книгарня (Class-Based Views, шаблони, статика)

Навчальний Django-проєкт (Hillel). Продовження ДЗ №10 (моделі, адмінка,
management-команди): тепер у книгарні є власний сайт.

- **Class-Based Views**: `ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`;
- **Django Templates з Bootstrap 5**: базовий шаблон, navbar, пагінація, фільтри;
- **статичні файли** і **URLconf з namespace**;
- понад завдання: **обкладинки книг** (завантаження файлів, media).

## Стек

- Python 3.13, Django 6.1
- SQLite
- Bootstrap 5.3 (через CDN, із перевіркою `integrity`)
- Pillow: перевірка зображень для `ImageField`
- python-dotenv: налаштування з `.env`

## Сторінки сайту

| URL | Ім'я маршруту | View | Що робить |
|---|---|---|---|
| `/` | `books:list` | `BookListView` | каталог: фільтри, сортування, пагінація по 10 книг |
| `/<pk>/` | `books:detail` | `BookDetailView` | сторінка книги |
| `/create/` | `books:create` | `BookCreateView` | додавання книги |
| `/<pk>/update/` | `books:update` | `BookUpdateView` | редагування книги |
| `/<pk>/delete/` | `books:delete` | `BookDeleteView` | підтвердження й видалення |
| `/authors/` | `books:author_list` | `AuthorListView` | автори з кількістю книг |
| `/authors/<pk>/` | `books:author_detail` | `AuthorDetailView` | автор, біографія та його книги |
| `/admin/` | `admin:index` | | адмінка |

Маршрути описані в `books/urls.py` з `app_name = "books"` (namespace) і
підключені в `config/urls.py` через `include()`. У шаблонах і коді адреси
будуються тільки за іменами: `{% url 'books:detail' book.pk %}`,
`reverse_lazy("books:list")`.

## Структура

```
config/
├── settings.py              # templates, static, media
└── urls.py                  # admin + include("books.urls") + media у DEBUG
books/
├── models.py                # Category, Author, Book (+ cover), BookCategory, BookQuerySet
├── forms.py                 # BookForm, BookFilterForm, CoverInput
├── views.py                 # Class-Based Views для книг і авторів
├── urls.py                  # app_name = "books"
├── admin.py                 # адмінка (+ мініатюри обкладинок)
├── apps.py                  # підключення сигналу для SQLite
├── sqlite_functions.py      # пошук без урахування регістру для кирилиці
├── templates/books/
│   ├── book_list.html
│   ├── book_detail.html
│   ├── book_form.html             # спільний для Create і Update
│   ├── book_confirm_delete.html
│   ├── author_list.html
│   ├── author_detail.html
│   ├── includes/stock_badge.html  # бейдж наявності
│   └── widgets/cover_input.html   # поле обкладинки з прев'ю
└── management/commands/
    ├── seed_books.py
    └── book_stats.py
templates/                   # спільні шаблони проєкту
├── base.html
└── includes/
    ├── navbar.html
    ├── messages.html
    └── pagination.html
static/                      # статика проєкту
├── css/styles.css
└── img/
    ├── no-cover.svg         # заглушка, коли обкладинки немає
    └── favicon.svg
media/                       # завантажені обкладинки (не в git)
```

## Class-Based Views

| View | Шаблон за замовчуванням | Особливості |
|---|---|---|
| `BookListView` | `books/book_list.html` | `paginate_by = 10`; фільтри з GET-параметрів через `BookFilterForm`; `prefetch_related("categories")` |
| `BookDetailView` | `books/book_detail.html` | `prefetch_related("categories")` |
| `BookCreateView` | `books/book_form.html` | `form_class = BookForm`; після збереження редирект на `get_absolute_url()` |
| `BookUpdateView` | `books/book_form.html` | той самий шаблон; заголовок і кнопки залежать від `object` |
| `BookDeleteView` | `books/book_confirm_delete.html` | видалення тільки через POST; редирект на каталог |
| `AuthorListView` | `books/author_list.html` | `annotate(Count("books"))`, `paginate_by = 20` |
| `AuthorDetailView` | `books/author_detail.html` | книги автора через `author.books` |

Сторінки авторів тільки для перегляду: авторів додають і редагують в адмінці.
Для staff-користувачів на сторінках авторів є посилання в адмінку.

Після створення, редагування й видалення `SuccessMessageMixin` показує
повідомлення (messages framework → Bootstrap alert).

## Шаблони

- `base.html`: каркас сторінки з блоками `title` і `content`. Сторінки
  наслідуються від нього через `{% extends "base.html" %}`.
- `navbar.html`: прилипає до верху під час прокручування (`sticky-top`),
  підсвічує активний пункт меню (`request.resolver_match.url_name`), має
  швидкий пошук і на вузькому екрані згортається в «бургер».
- `pagination.html`: універсальна пагінація для будь-якого `ListView`.
  Тег `{% querystring page=N %}` зберігає поточні фільтри при переході між
  сторінками; довгий список сторінок скорочується (`get_elided_page_range`).
- `messages.html`: flash-повідомлення.

### Фільтри каталогу

Форма `BookFilterForm`, метод GET (фільтри видно в адресі, сторінку можна
зберегти в закладки):

| Параметр | Що робить |
|---|---|
| `q` | пошук за назвою або іменем автора (без урахування регістру, зокрема для кирилиці) |
| `category` | категорія за `slug` |
| `author` | автор за `pk` |
| `stock` | наявність: `in_stock` / `low` (≤ 5) / `out` |
| `price_min`, `price_max` | діапазон ціни; якщо «від» більше за «до», форма покаже помилку |
| `sort` | `title`, `-title`, `author__name`, `price`, `-price`, `-created_at` |

Некоректні значення (`?price_min=abc`) не ламають сторінку: форма показує
помилку, а каталог виводить усі книги.

## Статичні файли і media

| | Static | Media |
|---|---|---|
| Що це | CSS, іконки, заглушка обкладинки | обкладинки, завантажені через форму |
| Де лежить | `static/` (у git) | `media/covers/<рік>/<місяць>/` (не в git) |
| Налаштування | `STATIC_URL`, `STATICFILES_DIRS`, `STATIC_ROOT` | `MEDIA_URL`, `MEDIA_ROOT` |
| Хто роздає в розробці | `runserver` сам | `static()` у `config/urls.py` (тільки при `DEBUG=True`) |

- У шаблонах статика підключається через `{% load static %}` і `{% static '...' %}`.
- Для продакшну: `python manage.py collectstatic` збирає всю статику в
  `staticfiles/` (теж не в git). При `DEBUG=False` статику й media має
  роздавати вебсервер (nginx) або сховище.

### Обкладинки книг

- Поле `Book.cover` (`ImageField`, необов'язкове).
- `Book.cover_url` повертає адресу обкладинки, а якщо її немає, то заглушки.
- Перевірки під час завантаження:
  - файл справді є зображенням (Pillow);
  - формат JPG, PNG або WebP (SVG і GIF заборонені);
  - розмір до 2 МБ.
- На сторінці редагування видно прев'ю поточної обкладинки й чекбокс
  «Remove cover» (власний віджет `CoverInput` на основі `ClearableFileInput`).
- Форма відправляється з `enctype="multipart/form-data"`, без нього файл не дійшов би на сервер.

## Моделі

| Модель | Поля | Примітки |
|---|---|---|
| `Category` | `name`, `slug` | обидва унікальні |
| `Author` | `name`, `bio` | `name` унікальне; `bio` необов'язкове |
| `Book` | `title`, `author`, `price`, `description`, `stock`, `cover`, `categories`, `created_at`, `updated_at` | `price ≥ 0`; `author` — ForeignKey на `Author` з `on_delete=PROTECT` (не можна видалити автора, у якого є книги); зв'язок ManyToMany з категоріями через `BookCategory`; `get_absolute_url()`, `cover_url`, `is_low_stock` |
| `BookCategory` | `book`, `category` | проміжна модель; `on_delete=PROTECT` не дає видалити категорію, у якій є книги; пара `book + category` унікальна |

`BookQuerySet.by_stock_status()` фільтрує книги за наявністю. Його
використовують і каталог, і адмінка; поріг «мало» задає `LOW_STOCK_THRESHOLD = 5`.

### Перенесення авторів в окрему модель

Раніше автор був текстовим полем `Book.author`. Перенесення зроблено
чотирма міграціями, щоб не втратити дані:

| Міграція | Що робить |
|---|---|
| `0003_rename_author_book_author_name` | перейменовує текстове поле на `author_name` |
| `0004_author_book_author` | створює `Author` і тимчасовий необов'язковий `Book.author` |
| `0005_move_authors_to_author_model` | data migration: для кожного імені створює `Author` (`get_or_create`) і пов'язує з книгами |
| `0006_remove_book_author_name_alter_book_author` | видаляє `author_name`, робить `author` обов'язковим |

Просто замінити `CharField` на `ForeignKey` під тим самим іменем не можна:
Django згенерував би `AlterField` і спробував би перетворити імена авторів на числові id.
Усі чотири міграції можна відкотити (`python manage.py migrate books 0002`).

## Адмінка

- **Книги:**
  - колонки: мініатюра обкладинки, автор, категорії, ознака наявності;
  - автор вибирається з пошуком під час введення (`autocomplete_fields`);
  - ціну й кількість можна редагувати прямо у списку;
  - фільтри: наявність (є / мало ≤ 5 / немає), категорії, дата;
  - пошук за назвою, іменем автора, описом і категорією;
  - `date_hierarchy`, `fieldsets` із секцією «Cover» (прев'ю обкладинки), inline для категорій.
- **Автори:** кількість книг (із сортуванням), пошук за іменем, біографія.
- **Категорії:** кількість книг (із сортуванням), автозаповнення `slug`,
  inline зі списком книг.
- Запити оптимізовано через `select_related` / `prefetch_related` та `annotate`.

## Встановлення та запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# згенерувати SECRET_KEY і вставити в .env:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

python manage.py migrate
python manage.py createsuperuser
python manage.py seed_books
python manage.py runserver
```

- Сайт: http://127.0.0.1:8000/
- Адмінка: http://127.0.0.1:8000/admin/

### Змінні оточення (`.env`)

| Змінна | Опис | Приклад |
|---|---|---|
| `DJANGO_SECRET_KEY` | секретний ключ (обов'язковий) | `change-me` |
| `DJANGO_DEBUG` | режим налагодження; при `False` runserver не роздає статику й media | `True` |
| `DJANGO_ALLOWED_HOSTS` | хости через кому | `127.0.0.1,localhost` |

## Management-команди

### `seed_books`

Створює 5 категорій, 10 авторів і 12 книг. Команду можна запускати повторно,
дублікати не створюються.

```bash
python manage.py seed_books
```

### `book_stats`

Виводить статистику книгарні та демонструє можливості ORM:

1. **filter**:
   - у наявності й дешевші за задану ціну;
   - мало на складі, немає на складі;
   - книги певної категорії, книги без категорії;
2. **Q-об'єкти**:
   - пошук за назвою / автором / категорією (OR);
   - «у наявності, але не в категорії» (AND + NOT);
   - складна умова для акції;
3. **annotate**:
   - статистика по категоріях;
   - топ-5 книг за вартістю запасу (`F("price") * F("stock")`);
   - категорії з понад 2 книгами (HAVING);
4. **aggregate**: підсумок по всьому магазину.

```bash
python manage.py book_stats
python manage.py book_stats --max-price 200 --search кінг --category fentezi
python manage.py book_stats --sql   # також показати згенерований SQL
```

| Параметр | За замовчуванням | Опис |
|---|---|---|
| `--max-price` | `300` | максимальна ціна для фільтра |
| `--search` | `Кінг` | рядок пошуку для Q-запиту |
| `--category` | `fentezi` | slug категорії |
| `--sql` | | друкувати SQL кожного запиту |

## Пошук кирилицею в SQLite

Вбудований оператор `LIKE` в SQLite ігнорує регістр тільки для латиниці,
тому стандартний `icontains` не знаходив «Вбивство» за запитом «вбив».

`books/sqlite_functions.py` замінює функцію, що стоїть за `LIKE`, на
Python-версію з `str.casefold()`. Реєструє її сигнал `connection_created`
(підключається в `BooksConfig.ready()`) для кожного нового з'єднання з базою.
Тепер без урахування регістру шукають каталог, адмінка й `book_stats --search`.

Компроміси:
- `LIKE` виконується в Python і працює трохи повільніше;
- як і вбудований `LIKE` в SQLite, `contains` (без `i`) теж не враховує регістр;
- на PostgreSQL / MySQL модуль нічого не робить, вони коректно працюють з Unicode самі.

## Відомі обмеження

- **Старі файли обкладинок не видаляються.** Django не прибирає файл з
  диска, коли книгу видалено, обкладинку замінено або позначено «Remove».
  Такі файли лишаються в `media/`.
- **Сортування кирилиці в SQLite.** SQLite порівнює рядки за кодами
  символів Unicode, тому українська «І» стоїть перед «А» («Іван Багряний»
  опиняється першим у списку авторів). Стосується сортування авторів і книг за назвою.
- **Валюта одна.** Ціни показуються з `₴`; підтримку кількох валют
  (UAH, USD) заплановано на наступні домашки.

## Плани

- i18n: українська та англійська мови інтерфейсу;
- валюти: модель `Currency` (UAH, USD);
- тести для views, форм і фільтрів.
