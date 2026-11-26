# Listownik

## Nazwa kursu

Testowanie i Jakość Oprogramowania.

## Autor

Kamil Kawa.

## Temat projektu

Listownik — aplikacja webowa do zarządzania listami zakupów.

## Opis projektu

Aplikacja umożliwia tworzenie, zmianę nazwy i usuwanie list zakupów. Do każdej listy można dodawać produkty z określoną liczbą sztuk, edytować je, usuwać oraz oznaczać jako kupione. Interfejs pozwala filtrować produkty według statusu i pokazuje postęp zakupów.

Listy wybiera się z kafelków w sekcji „Moje listy”. Produkty mają osobne karty z oznaczeniem zakupu, edycją, usuwaniem oraz przyciskami „−” i „+” do zmiany ilości. Przy granicach 1 i 999 odpowiedni przycisk jest wyłączony. Postęp zakupów jest liczony według liczby pozycji na liście.

Backend i frontend działają jako dwa osobne procesy. Dane zapisują się w pliku `backend/listownik.db`, tworzonym automatycznie przy pierwszym uruchomieniu. Nazwy mają od 1 do 80 znaków po usunięciu skrajnych spacji i nie mogą zawierać znaków sterujących. Ilości są liczbami całkowitymi od 1 do 999. Usunięcie listy usuwa także należące do niej produkty.

### Struktura projektu

```text
backend/
├── app.py                 # endpointy REST API (Blueprint Flask), obsługa błędów, fabryka aplikacji
├── database.py            # połączenie z SQLite i tworzenie tabel
├── validation.py          # walidacja danych wejściowych
├── requirements.txt       # zależności aplikacji
├── requirements-dev.txt   # zależności testowe
└── tests/
    ├── conftest.py        # wspólne fixture'y: tymczasowa baza i klient testowy
    ├── unit/              # testy jednostkowe
    └── integration/       # testy integracyjne API
frontend/
├── index.html             # struktura interfejsu
├── styles.css             # wygląd
├── app.js                 # logika interfejsu i komunikacja z API
└── assets/                # czcionka i grafiki
pytest.ini                 # konfiguracja pytest
```

Backend korzysta ze wzorca fabryki aplikacji: funkcja `create_app` w [backend/app.py](backend/app.py) tworzy aplikację z podaną konfiguracją, dzięki czemu testy uruchamiają ją z osobną, tymczasową bazą danych. Endpointy są zgrupowane w Blueprincie `api`, a walidacja danych i obsługa bazy są wydzielone do osobnych modułów.

## Uruchomienie projektu

Wymagany jest Python 3.10 lub nowszy. Poniższe polecenia są przeznaczone dla PowerShell w Windows. Oba terminale należy otworzyć w głównym katalogu projektu.

Pierwszy terminal — przygotowanie backendu, jednorazowo:

```powershell
python -m venv backend/.venv
./backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
```

Uruchomienie backendu:

```powershell
./backend/.venv/Scripts/python.exe backend/app.py
```

API jest dostępne pod adresem <http://127.0.0.1:5000/api/lists>.

Drugi terminal — uruchomienie frontendu:

```powershell
python -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

Otwórz <http://127.0.0.1:5500>. Oba procesy muszą działać jednocześnie; `Ctrl+C` zatrzymuje proces w danym terminalu. Frontend korzysta z API na porcie 5000, a backend dopuszcza połączenia przeglądarki z `http://127.0.0.1:5500` oraz `http://localhost:5500`.

Aby zacząć od pustej bazy danych (np. przed testami manualnymi), zatrzymaj backend i usuń plik bazy. Przy następnym uruchomieniu backend utworzy go ponownie:

```powershell
Remove-Item backend/listownik.db
```

## Testy

Testy automatyczne backendu są napisane w [pytest](https://docs.pytest.org/). Każdy test ma budowę **AAA (Arrange–Act–Assert)**, oznaczoną komentarzami `# Arrange`, `# Act` i `# Assert`. Wspólne fixture'y znajdują się w [backend/tests/conftest.py](backend/tests/conftest.py): każdy test dostaje nową, tymczasową bazę SQLite, więc testy są od siebie niezależne i nie zmieniają danych w `backend/listownik.db`.

| Rodzaj | Plik | Liczba testów | Zakres |
| --- | --- | --- | --- |
| Jednostkowe | [test_validation.py](backend/tests/unit/test_validation.py) | 12 | Walidacja pól JSON (brakujące i nieznane pola, pusty obiekt), nazw (limit 80 znaków, pusta nazwa, nazwa niebędąca tekstem, znaki sterujące), ilości (wartości graniczne 1 i 999, wartości spoza zakresu i niecałkowite) oraz statusu zakupu. |
| Integracyjne | [test_lists_api.py](backend/tests/integration/test_lists_api.py) | 6 | Endpointy list: tworzenie z przycięciem spacji, pobieranie od najnowszej z licznikami produktów, zmiana nazwy, usuwanie razem z produktami, błąd 400 dla pustej nazwy, zachowanie danych po ponownym uruchomieniu aplikacji. |
| Integracyjne | [test_items_api.py](backend/tests/integration/test_items_api.py) | 6 | Endpointy produktów: dodawanie, błąd 404 dla nieistniejącej listy, edycja tylko przesłanych pól, oznaczanie zakupu, próba zmiany produktu przez adres innej listy, usuwanie wybranego produktu. |

Razem jest 12 testów jednostkowych i 12 integracyjnych; po rozwinięciu parametryzacji (`pytest.mark.parametrize`) pytest wykonuje 35 przypadków. Testy jednostkowe sprawdzają pojedyncze funkcje bez bazy danych i serwera. Testy integracyjne wysyłają żądania HTTP przez klienta testowego Flask i przechodzą przez całą ścieżkę: routing, walidację i zapis w SQLite.

Polecenia uruchamia się w głównym katalogu projektu. Jednorazowa instalacja zależności testowych:

```powershell
./backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
```

Wszystkie testy:

```powershell
./backend/.venv/Scripts/python.exe -m pytest
```

Tylko testy jednostkowe albo tylko integracyjne:

```powershell
./backend/.venv/Scripts/python.exe -m pytest backend/tests/unit
./backend/.venv/Scripts/python.exe -m pytest backend/tests/integration
```

Pokrycie kodu backendu testami (97%; moduły `validation.py` i `database.py` są pokryte w 100%):

```powershell
./backend/.venv/Scripts/python.exe -m pytest --cov=app --cov=database --cov=validation --cov-report=term-missing
```

## Dokumentacja API

Adres bazowy: `http://127.0.0.1:5000/api`. Żądania z danymi wymagają nagłówka `Content-Type: application/json`.

| Metoda | Ścieżka | Dane JSON | Wynik |
| --- | --- | --- | --- |
| GET | `/lists` | — | 200: tablica list z polami `id`, `name`, `total_count`, `purchased_count` |
| POST | `/lists` | `{"name":"Zakupy na weekend"}` | 201: utworzona lista z polami `id` i `name` |
| GET | `/lists/{list_id}` | — | 200: lista z polami `id`, `name` i tablicą `items` |
| PATCH | `/lists/{list_id}` | `{"name":"Zakupy na poniedziałek"}` | 200: lista ze zmienioną nazwą |
| DELETE | `/lists/{list_id}` | — | 204: usunięcie listy wraz z produktami |
| POST | `/lists/{list_id}/items` | `{"name":"Mleko","quantity":2}` | 201: utworzony produkt |
| PATCH | `/lists/{list_id}/items/{item_id}` | Co najmniej jedno z pól: `name`, `quantity`, `is_purchased` | 200: zaktualizowany produkt |
| DELETE | `/lists/{list_id}/items/{item_id}` | — | 204: usunięcie produktu |

Produkt w odpowiedzi ma postać:

```json
{
  "id": 1,
  "name": "Mleko",
  "quantity": 2,
  "is_purchased": false
}
```

Zmiana statusu zakupu: `{"is_purchased":true}`. Cofnięcie zakupu: `{"is_purchased":false}`. Pola pominięte w aktualizacji produktu zachowują dotychczasowe wartości. Nowy produkt zawsze ma status `false`. Filtrowanie odbywa się po stronie frontendu. Nazwy list i produktów mogą się powtarzać.

Błędy mają postać `{"error":"Opis błędu"}`, a odpowiedzi `204` nie mają treści. Możliwe błędy:

| Kod | Sytuacja | Komunikat w polu `error` |
| --- | --- | --- |
| 400 | Niepoprawna składnia JSON | Prześlij poprawne dane JSON. |
| 400 | Treść nie jest niepustym obiektem JSON | Prześlij niepusty obiekt JSON. |
| 400 | Brak wymaganego pola | Brakuje wymaganych pól. |
| 400 | Pole spoza dozwolonych | Przesłano nieobsługiwane pola. |
| 400 | Nazwa nie jest tekstem | Nazwa musi być tekstem. |
| 400 | Nazwa pusta lub złożona z samych spacji | Nazwa nie może być pusta. |
| 400 | Nazwa dłuższa niż 80 znaków | Nazwa może mieć maksymalnie 80 znaków. |
| 400 | Nazwa ze znakiem sterującym, np. tabulatorem | Nazwa nie może zawierać znaków sterujących. |
| 400 | Ilość spoza zakresu 1–999 lub niebędąca liczbą całkowitą | Ilość musi być liczbą całkowitą od 1 do 999. |
| 400 | Status zakupu inny niż `true` lub `false` | Status zakupu musi mieć wartość true lub false. |
| 404 | Brak listy, produktu lub adresu | Nie znaleziono wskazanej listy, produktu lub adresu. |
| 405 | Nieobsługiwana metoda HTTP | Ta metoda HTTP nie jest obsługiwana. |
| 413 | Treść większa niż 16 KiB | Przesłane dane są zbyt duże. |
| 415 | Brak nagłówka `Content-Type: application/json` | Prześlij dane w formacie JSON. |
| 500 | Nieoczekiwany błąd serwera | Wystąpił błąd serwera. |

## Przypadki testowe dla testera manualnego (TestCase)

Każdy przypadek ma własne warunki wstępne, więc można je wykonywać niezależnie i w dowolnej kolejności. We wszystkich przypadkach backend i frontend są uruchomione zgodnie z sekcją „Uruchomienie projektu”, a aplikacja jest otwarta pod adresem <http://127.0.0.1:5500>. Komunikaty potwierdzające pojawiają się na dole ekranu i znikają po około 3,5 s. Po odświeżeniu strony aplikacja wybiera najnowszą listę.

### TC-01: Wyświetlenie aplikacji bez list

- **Warunki wstępne:** baza danych jest pusta (plik `backend/listownik.db` usunięty przed uruchomieniem backendu).
- **Kroki:**
  1. Otwórz <http://127.0.0.1:5500>.
- **Oczekiwany rezultat:** sekcja „Moje listy” ma licznik 0 i tekst „Jeszcze nie masz żadnej listy.”. Widoczna jest sekcja „Co dziś trzeba kupić?” z przyciskiem „Utwórz listę”. Nagłówek pokazuje „0 do kupienia”.

### TC-02: Utworzenie listy zakupów

- **Warunki wstępne:** aplikacja jest otwarta.
- **Kroki:**
  1. Kliknij „Nowa lista” w nagłówku.
  2. W polu „Nazwa listy” wpisz „Zakupy na weekend”.
  3. Kliknij „Utwórz listę”.
- **Oczekiwany rezultat:** okno się zamyka i pojawia się komunikat „Lista została utworzona.”. W sekcji „Moje listy” jest kafelek „Zakupy na weekend” z opisem „Pusta lista”. Nowa lista jest wybrana i pokazuje komunikat „Dodaj pierwszy produkt”.

### TC-03: Walidacja nazwy listy

- **Warunki wstępne:** otwarte jest okno „Nowa lista zakupów” (przycisk „Nowa lista”).
- **Kroki:**
  1. Przy pustym polu kliknij „Utwórz listę”.
  2. Wpisz trzy spacje i kliknij „Utwórz listę”.
  3. Wklej do pola tekst dłuższy niż 80 znaków.
  4. Kliknij „Anuluj”.
- **Oczekiwany rezultat:** w kroku 1 przeglądarka zgłasza wymagane pole, a w kroku 2 pojawia się komunikat „Wpisz nazwę. Sama spacja nie wystarczy.”. Pole przyjmuje najwyżej 80 znaków. Po kroku 4 okno jest zamknięte i nie powstała żadna lista.

### TC-04: Dodanie produktu do listy

- **Warunki wstępne:** istnieje i jest wybrana pusta lista „Zakupy na weekend”.
- **Kroki:**
  1. W polu „Co dopisać do listy?” wpisz „Mleko”.
  2. W polu „Ilość (szt.)” wpisz 2.
  3. Kliknij „Dodaj produkt”.
- **Oczekiwany rezultat:** pojawia się komunikat „Produkt został dodany.” i karta „Mleko” z ilością „2 szt.”, statusem „Do kupienia” i ilustracją butelki mleka. Formularz jest wyczyszczony, a ilość wraca do 1. Filtr „Wszystkie” pokazuje 1, a kafelek listy „1 do kupienia”.

### TC-05: Walidacja danych produktu

- **Warunki wstępne:** wybrana jest dowolna lista.
- **Kroki:**
  1. W polu nazwy wpisz trzy spacje i kliknij „Dodaj produkt”.
  2. Wpisz nazwę „Chleb”, ilość 0 i kliknij „Dodaj produkt”.
  3. Powtórz krok 2 z ilością 1000, 2,5 oraz z pustym polem ilości.
- **Oczekiwany rezultat:** w kroku 1 pojawia się komunikat „Wpisz nazwę. Sama spacja nie wystarczy.”. W krokach 2 i 3 przeglądarka zgłasza niepoprawną wartość ilości (dozwolone są liczby całkowite od 1 do 999). Żaden produkt nie zostaje dodany.

### TC-06: Oznaczenie produktu jako kupionego

- **Warunki wstępne:** wybrana lista zawiera produkty „Mleko” (2 szt.) i „Chleb” (1 szt.), oba do kupienia.
- **Kroki:**
  1. Zaznacz pole wyboru na karcie „Mleko”.
- **Oczekiwany rezultat:** pojawia się komunikat „Produkt oznaczony jako kupiony.”. Karta „Mleko” ma status „Kupione”, przekreśloną nazwę i przesuwa się na koniec listy. Postęp pokazuje „Kupione: 1 z 2” i 50%, a kafelek listy „1 do kupienia”.

### TC-07: Filtrowanie produktów według statusu

- **Warunki wstępne:** wybrana lista zawiera kupione „Mleko” i niekupiony „Chleb”.
- **Kroki:**
  1. Kliknij filtr „Do kupienia”.
  2. Kliknij filtr „Kupione”.
  3. Kliknij filtr „Wszystkie”.
- **Oczekiwany rezultat:** w kroku 1 widać tylko „Chleb”, w kroku 2 tylko „Mleko”, a w kroku 3 oba produkty. Liczniki przy filtrach to: Wszystkie 2, Do kupienia 1, Kupione 1. Aktywny filtr jest podświetlony.

### TC-08: Cofnięcie zakupu

- **Warunki wstępne:** jak w TC-07; wybrany jest filtr „Kupione”.
- **Kroki:**
  1. Odznacz pole wyboru na karcie „Mleko”.
- **Oczekiwany rezultat:** pojawia się komunikat „Produkt wrócił do kupienia.”. Karta znika z widoku, który pokazuje „Jeszcze nic nie jest kupione”. Postęp spada do 0%.

### TC-09: Zmiana ilości przyciskami „+” i „−”

- **Warunki wstępne:** istnieje jedna lista, zawierająca „Mleko” (2 szt.) i „Chleb” (1 szt.).
- **Kroki:**
  1. Na karcie „Mleko” kliknij „+”.
  2. Na tej samej karcie kliknij „−”.
  3. Sprawdź przycisk „−” na karcie „Chleb”.
  4. Odśwież stronę.
- **Oczekiwany rezultat:** po kroku 1 ilość wynosi „3 szt.”, a po kroku 2 „2 szt.”. Przycisk „−” na karcie „Chleb” (1 szt.) jest nieaktywny. Po odświeżeniu ilości się nie zmieniają.

### TC-10: Edycja produktu i górny limit ilości

- **Warunki wstępne:** wybrana lista zawiera „Mleko” (2 szt.).
- **Kroki:**
  1. Kliknij ikonę ołówka na karcie „Mleko”.
  2. Zmień nazwę na „Mleko 2%”, a ilość na 999.
  3. Kliknij „Zapisz zmiany”.
- **Oczekiwany rezultat:** pojawia się komunikat „Produkt został zmieniony.”. Karta pokazuje „Mleko 2%” i „999 szt.”, a przycisk „+” jest nieaktywny.

### TC-11: Zmiana nazwy listy

- **Warunki wstępne:** istnieje i jest wybrana lista „Zakupy na weekend”.
- **Kroki:**
  1. Kliknij ikonę ołówka obok nazwy listy.
  2. Wpisz „Zakupy na poniedziałek”.
  3. Kliknij „Zapisz zmiany”.
- **Oczekiwany rezultat:** pojawia się komunikat „Nazwa listy została zmieniona.”. Nowa nazwa jest widoczna w nagłówku listy i na kafelku w sekcji „Moje listy”.

### TC-12: Zachowanie danych po odświeżeniu i ponownym uruchomieniu backendu

- **Warunki wstępne:** istnieje jedna lista z co najmniej dwoma produktami, z których jeden jest kupiony.
- **Kroki:**
  1. Odśwież stronę (F5).
  2. Zatrzymaj backend (`Ctrl+C`) i uruchom go ponownie.
  3. Odśwież stronę.
- **Oczekiwany rezultat:** po każdym odświeżeniu lista, produkty, ilości i statusy zakupu są takie same jak przed rozpoczęciem testu.

### TC-13: Praca z kilkoma listami

- **Warunki wstępne:** istnieje tylko lista „Zakupy na weekend” z dwoma produktami do kupienia.
- **Kroki:**
  1. Utwórz listę „Drogeria” i dodaj do niej „Proszek do prania” (1 szt.).
  2. Kliknij kafelek „Zakupy na weekend”.
  3. Kliknij kafelek „Drogeria”.
- **Oczekiwany rezultat:** po kliknięciu kafelka widać tylko produkty tej listy, a wybrany kafelek jest podświetlony. Licznik „Moje listy” pokazuje 2, a nagłówek „3 do kupienia” (suma ze wszystkich list). „Proszek do prania” ma ilustrację torby z zakupami.

### TC-14: Usunięcie produktu z potwierdzeniem

- **Warunki wstępne:** wybrana lista zawiera produkty „Mleko” i „Chleb”.
- **Kroki:**
  1. Kliknij ikonę kosza na karcie „Chleb”.
  2. W oknie „Usunąć produkt?” kliknij „Anuluj”.
  3. Ponownie kliknij kosz na karcie „Chleb” i wybierz „Usuń”.
- **Oczekiwany rezultat:** po kroku 2 okno jest zamknięte, a „Chleb” nadal jest na liście. Po kroku 3 pojawia się komunikat „Produkt został usunięty.” i na liście zostaje tylko „Mleko”.

### TC-15: Usunięcie listy razem z produktami

- **Warunki wstępne:** istnieją tylko listy „Zakupy na weekend” i „Drogeria”; wybrana jest „Drogeria” z co najmniej jednym produktem.
- **Kroki:**
  1. Kliknij ikonę kosza obok nazwy listy.
  2. Kliknij „Usuń”.
  3. W ten sam sposób usuń listę „Zakupy na weekend”.
- **Oczekiwany rezultat:** okno z kroku 1 ostrzega, że lista „Drogeria” zostanie usunięta razem ze wszystkimi produktami. Po kroku 2 pojawia się komunikat „Lista została usunięta.”, kafelek znika i wybrana zostaje lista „Zakupy na weekend”. Po kroku 3 aplikacja wygląda jak w TC-01.

### TC-16: Brak połączenia z backendem

- **Warunki wstępne:** frontend jest uruchomiony, backend jest zatrzymany.
- **Kroki:**
  1. Odśwież stronę.
  2. Uruchom backend.
  3. Kliknij „Spróbuj ponownie”.
- **Oczekiwany rezultat:** po kroku 1 widać komunikat „Nie można połączyć się z backendem. Sprawdź, czy jest uruchomiony, i spróbuj ponownie.” z przyciskiem „Spróbuj ponownie”. Po kroku 3 komunikat znika i listy się wczytują.

### TC-17: Widok na ekranie telefonu

- **Warunki wstępne:** wybrana lista zawiera co najmniej cztery produkty.
- **Kroki:**
  1. Otwórz narzędzia deweloperskie przeglądarki (F12) i włącz tryb urządzenia (`Ctrl+Shift+M`).
  2. Ustaw szerokość ekranu 375 px (np. iPhone).
- **Oczekiwany rezultat:** karty produktów układają się w dwóch kolumnach, a przycisk „Nowa lista” jest dostępny w nagłówku. Strona nie przewija się w poziomie.

## Technologie użyte w projekcie

- Python, [Flask](https://flask.palletsprojects.com/en/stable/) i [Flask-CORS](https://flask-cors.readthedocs.io/en/latest/) — REST API i komunikacja z osobno uruchamianym frontendem.
- SQLite i moduł `sqlite3` — zapis danych.
- HTML, CSS i JavaScript — interfejs użytkownika.
- [pytest](https://docs.pytest.org/) i [pytest-cov](https://pytest-cov.readthedocs.io/) — testy jednostkowe i integracyjne oraz pomiar pokrycia kodu.
- Git — kontrola wersji.

## Wygląd i zasoby graficzne

Interfejs jest inspirowany dostarczoną makietą w filmie `web design.mp4`: ciemny turkus, limonkowe akcenty, jasne tło i karty produktów z zaokrągloną dolną krawędzią. Wszystkie zasoby są przechowywane lokalnie w [frontend/assets](frontend/assets).

- [Manrope](frontend/assets/manrope.ttf) — czcionka z repozytorium Google Fonts, dołączona wraz z [licencją SIL Open Font License](frontend/assets/manrope-license.txt).
- [grocery-bag.png](frontend/assets/grocery-bag.png) — grafika torby z zakupami na banerze i ilustracja pozostałych produktów.
- [products.png](frontend/assets/products.png) — arkusz ośmiu ilustracji produktów: mleka, pieczywa, jabłek, bananów, marchwi, pomidorów, jajek i sera. Ilustracja jest dobierana na podstawie nazwy produktu.

Obie grafiki zostały wygenerowane wbudowanym narzędziem imagegen. Ikony interfejsu są zapisane jako SVG w pliku HTML.

<details>
<summary>Prompty użyte do wygenerowania grafik</summary>

`grocery-bag.png`, z włączoną przezroczystością:

```text
Use case: product-mockup. Asset type: transparent cutout photograph for a Polish shopping-list web app named Listownik. Create a professional grocery-store campaign photograph of one deep emerald green reusable cotton shopping tote filled naturally with a crusty baguette, leafy lettuce, a bottle of milk with a plain white cap, red tomatoes, a yellow pepper, carrots, and long spring onions. The whole bag and groceries are visible, nothing cropped. Three-quarter front view, grounded realistic composition, crisp natural textures, soft directional studio light, appetizing real produce, ordinary European groceries. The bag has a plain fabric front with no logo or text. Compact composition centered in a portrait image with generous clear transparent padding around the silhouette. This cutout will be placed against dark teal #084c4f on the right of a wide banner. Transparent background with clean edges and actual alpha. No typography, no brands, no floating items, no decorative graphics, no border, no gradients, no people. Photographic realism, not a cartoon or illustration.
```

`products.png`, z włączoną przezroczystością:

```text
Use case: product-mockup. Asset type: CSS sprite sheet of grocery product photographs for a shopping-list interface. Create a wide 2:1 image, ideally 2048 by 1024 pixels, with exactly 4 equal columns and 2 equal rows. Every cell is a square, each subject centered entirely inside its cell with ample empty transparent margin. All eight cells share realistic grocery catalogue photography, soft neutral studio lighting and clean cutout edges. Top row from left to right: (1) a simple clear glass bottle of white milk with a plain white cap, no label; (2) a small crusty golden sourdough loaf with two bread slices; (3) two natural red apples with a green leaf; (4) a small bunch of ripe yellow bananas. Bottom row from left to right: (5) three orange carrots with short green leaves; (6) three red tomatoes on a green vine; (7) an open small kraft carton with six brown eggs; (8) a wedge of yellow cheese with a couple of small holes. Accurate natural textures and realistic proportions, appetizing but ordinary groceries. Completely transparent background and transparent gutters, actual alpha, no white rectangles. No labels, text, brands, borders, numbers, grid lines, props, or additional objects. No subject may cross into an adjacent cell. This is a uniform sprite grid, NOT an assortment clustered together.
```

</details>
