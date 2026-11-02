import pytest

from app.privacidad import tapar_datos_personales


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("Cédula de Identidad: V-12.345.678", "Cédula de Identidad: [Cédula de identidad]"),
        ("Cédula: [V-12.345.678]", "Cédula: [Cédula de identidad]"),
        ("C.I. 12.345.678", "C.I. [Cédula de identidad]"),
        ("cédula E-81234567", "cédula [Cédula de identidad]"),
        ("RIF: J-12345678-9", "RIF: [RIF o registro]"),
        ("RIF J123456789", "RIF [RIF o registro]"),
        ("Teléfono: 0414-5555555", "Teléfono: [Teléfono]"),
        ("Tlf. (0251) 555.55.55", "Tlf. [Teléfono]"),
        ("+58 414 555 5555", "[Teléfono]"),
        ("Correo: pedro.perez@gmail.com", "Correo: [Correo]"),
    ],
)
def test_tapa_datos_personales(texto: str, esperado: str) -> None:
    assert tapar_datos_personales(texto) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "Gaceta Oficial N° 5.453 Extraordinario del 24 de marzo de 2000",
        "Artículo 56, numeral 2, de la LOPPM",
        "Decreto N° 1.409, artículo 49",
        "Una densidad de 300 hab/ha y una altura de PB+4 (15 m)",
        "Folio IRI-2026-0012",
        "Sentencia N° 1632, exp. 00-1362",
        "Resolución N° 139 de 2003",
        "[Cédula de identidad]",
    ],
)
def test_no_toca_referencias_normativas(texto: str) -> None:
    assert tapar_datos_personales(texto) == texto
