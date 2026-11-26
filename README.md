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

Błędy mają postać `{"error":"Opis błędu"}`. Kody: `400` — niepoprawne dane lub JSON, `404` — brak zasobu, `405` — nieobsługiwana metoda, `413` — żądanie większe niż 16 KiB, `415` — niepoprawny typ treści. Backend odrzuca również puste obiekty i nieznane pola. Odpowiedzi `204` nie mają treści.

## Przypadki testowe dla testera manualnego (TestCase)

Pełny zestaw co najmniej 10 przypadków testowych zostanie opracowany w etapie dokumentacji. Podstawowy scenariusz sprawdzenia aktualnej aplikacji:

1. Utwórz listę „Zakupy na weekend”. Jej kafelek powinien pojawić się w sekcji „Moje listy”.
2. Dodaj „Mleko” w ilości 2 i „Chleb” w ilości 1. Powinny pojawić się dwa produkty.
3. Oznacz mleko jako kupione. Postęp powinien wynosić 50%, a filtr „Do kupienia” pokazywać wyłącznie chleb.
4. W filtrze „Kupione” cofnij zakup mleka. Produkt powinien wrócić do „Do kupienia”.
5. Zmień nazwę listy i ilość mleka na 3. Odśwież stronę i sprawdź zapis zmian.
6. Naciśnij „+” na karcie mleka. Ilość powinna wzrosnąć z 3 do 4. Naciśnij „−” i sprawdź powrót do 3.
7. Usuń produkt, a następnie całą listę, potwierdzając każdą operację. Kafelek listy powinien zniknąć z sekcji „Moje listy”.

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
