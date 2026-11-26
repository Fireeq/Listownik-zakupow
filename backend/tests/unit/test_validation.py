import pytest

from validation import (
    ValidationError,
    validate_fields,
    validate_name,
    validate_purchased,
    validate_quantity,
)


def test_validate_fields_returns_payload_with_required_fields():
    # Arrange
    payload = {"name": "Mleko", "quantity": 2}

    # Act
    result = validate_fields(payload, {"name", "quantity"})

    # Assert
    assert result == payload


@pytest.mark.parametrize("payload", [{}, [], None], ids=["empty-object", "array", "null"])
def test_validate_fields_rejects_empty_or_non_object_payload(payload):
    # Arrange
    expected_message = "Prześlij niepusty obiekt JSON."

    # Act
    with pytest.raises(ValidationError) as error:
        validate_fields(payload, {"name"})

    # Assert
    assert str(error.value) == expected_message


def test_validate_fields_rejects_missing_required_field():
    # Arrange
    payload = {"name": "Mleko"}

    # Act
    with pytest.raises(ValidationError) as error:
        validate_fields(payload, {"name", "quantity"})

    # Assert
    assert str(error.value) == "Brakuje wymaganych pól."


def test_validate_fields_rejects_unknown_field():
    # Arrange
    payload = {"name": "Mleko", "price": 5}

    # Act
    with pytest.raises(ValidationError) as error:
        validate_fields(payload, {"name"})

    # Assert
    assert str(error.value) == "Przesłano nieobsługiwane pola."


def test_validate_name_accepts_exactly_80_characters():
    # Arrange
    raw_name = "x" * 80

    # Act
    name = validate_name(raw_name)

    # Assert
    assert name == raw_name


def test_validate_name_rejects_more_than_80_characters():
    # Arrange
    raw_name = "x" * 81

    # Act
    with pytest.raises(ValidationError) as error:
        validate_name(raw_name)

    # Assert
    assert str(error.value) == "Nazwa może mieć maksymalnie 80 znaków."


@pytest.mark.parametrize("raw_name", ["", "   "], ids=["empty", "spaces-only"])
def test_validate_name_rejects_blank_text(raw_name):
    # Arrange
    expected_message = "Nazwa nie może być pusta."

    # Act
    with pytest.raises(ValidationError) as error:
        validate_name(raw_name)

    # Assert
    assert str(error.value) == expected_message


def test_validate_name_rejects_value_that_is_not_text():
    # Arrange
    raw_name = 123

    # Act
    with pytest.raises(ValidationError) as error:
        validate_name(raw_name)

    # Assert
    assert str(error.value) == "Nazwa musi być tekstem."


@pytest.mark.parametrize(
    "raw_name", ["Mle\x07ko", "Mle\x85ko", "Mle\tko"], ids=["bell", "next-line", "tab"]
)
def test_validate_name_rejects_control_characters(raw_name):
    # Arrange
    expected_message = "Nazwa nie może zawierać znaków sterujących."

    # Act
    with pytest.raises(ValidationError) as error:
        validate_name(raw_name)

    # Assert
    assert str(error.value) == expected_message


@pytest.mark.parametrize("raw_quantity", [1, 999])
def test_validate_quantity_accepts_boundary_values(raw_quantity):
    # Arrange
    expected_quantity = raw_quantity

    # Act
    quantity = validate_quantity(raw_quantity)

    # Assert
    assert quantity == expected_quantity


@pytest.mark.parametrize("raw_quantity", [0, 1000, 2.5, "2", True])
def test_validate_quantity_rejects_invalid_values(raw_quantity):
    # Arrange
    expected_message = "Ilość musi być liczbą całkowitą od 1 do 999."

    # Act
    with pytest.raises(ValidationError) as error:
        validate_quantity(raw_quantity)

    # Assert
    assert str(error.value) == expected_message


@pytest.mark.parametrize("raw_status", ["true", 1])
def test_validate_purchased_rejects_value_that_is_not_boolean(raw_status):
    # Arrange
    expected_message = "Status zakupu musi mieć wartość true lub false."

    # Act
    with pytest.raises(ValidationError) as error:
        validate_purchased(raw_status)

    # Assert
    assert str(error.value) == expected_message
