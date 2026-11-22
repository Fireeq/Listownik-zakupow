import unicodedata


class ValidationError(ValueError):
    pass


def validate_fields(
    data: object, required: set[str], optional: set[str] | None = None
) -> dict:
    if not isinstance(data, dict) or not data:
        raise ValidationError("Prześlij niepusty obiekt JSON.")
    if not required.issubset(data):
        raise ValidationError("Brakuje wymaganych pól.")
    if data.keys() - required - (optional or set()):
        raise ValidationError("Przesłano nieobsługiwane pola.")
    return data


def validate_name(value: object) -> str:
    if not isinstance(value, str):
        raise ValidationError("Nazwa musi być tekstem.")
    name = value.strip()
    if not name:
        raise ValidationError("Nazwa nie może być pusta.")
    if len(name) > 80:
        raise ValidationError("Nazwa może mieć maksymalnie 80 znaków.")
    if any(unicodedata.category(character) == "Cc" for character in name):
        raise ValidationError("Nazwa nie może zawierać znaków sterujących.")
    return name


def validate_quantity(value: object) -> int:
    if type(value) is not int or not 1 <= value <= 999:
        raise ValidationError("Ilość musi być liczbą całkowitą od 1 do 999.")
    return value


def validate_purchased(value: object) -> bool:
    if type(value) is not bool:
        raise ValidationError("Status zakupu musi mieć wartość true lub false.")
    return value
