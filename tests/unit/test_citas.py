import pytest

from app.citas import quitar_rutas_internas


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        (
            "declaró improcedente la aclaratoria [sentencias] sentencia_tsj_sc_847_2017_exp_16-0660_aclaratoria_1080.",
            "declaró improcedente la aclaratoria.",
        ),
        (
            "Según la Ordenanza (fuente: [ordenanzas] ordenanza_pdul_ciudad_barquisimeto_gm_1407_1999), el ámbito es…",
            "Según la Ordenanza, el ámbito es…",
        ),
        ("La ley nunca rigió [legislacion].", "La ley nunca rigió."),
        (
            "Ver `legislacion_ley_organica_planificacion_gestion_ordenacion_territorio_2006` para más detalle.",
            "Ver para más detalle.",
        ),
        (
            "Fuentes: [doctrina] urbanismo_propiedad_privada_allan_brewer_carias; [sentencias] sentencia_n208_exp20160659_sc_1_",
            "Fuentes:",
        ),
        (
            "* **[legislacion] legislacion_ley_organica_planificacion_gestion_2006** Ley de 2006.",
            "* Ley de 2006.",
        ),
    ],
)
def test_quita_etiquetas_y_archivos(texto: str, esperado: str) -> None:
    assert quitar_rutas_internas(texto) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "La Sentencia N° 847 del 27 de octubre de 2017 de la Sala Constitucional.",
        "El artículo 87 de la LOOU y la Ordenanza del PDUL de Barquisimeto (1999).",
        "[Cédula de identidad] [Fundamento normativo, opcional] [nombre de la avenida]",
        "Variables urbanas: PB+4, 300 hab/ha, retiro de frente 5 m.",
        "El folio IRI-2026-0012 y la Gaceta Oficial N° 5.820 Extraordinario.",
        "zona R1 y R4; vivienda multifamiliar_comercial",
    ],
)
def test_no_toca_texto_normal(texto: str) -> None:
    assert quitar_rutas_internas(texto) == texto
