import locale
import os
from typing import Dict


TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "app.title": "Paraglider Speedbar Calculator",
        "error.invalid_polar_params_html": "<span style='color:red'>Please enter valid numbers for all polar parameters.</span>",
        "label.trim_glide_placeholder": "Trim glide: --",
        "label.trim_glide_invalid_sink": "Trim glide: -- (invalid sink)",
        "label.trim_glide_value": "Trim glide: {value:.2f} ",
        "label.max_glide_placeholder": "Max speed glide: --",
        "label.max_glide_invalid_sink": "Max speed glide: -- (invalid sink)",
        "label.max_glide_value": "Max speed glide: {value:.2f} ",
        "group.polar_curve_params": "Polar Curve Parameters",
        "button.set": "Set...",
        "form.trim_speed": "Trim speed (km/h):",
        "form.trim_sink": "Trim sink (m/s):",
        "checkbox.specify_mid_point": "Specify Mid Point",
        "form.middle_speed": "Middle speed (km/h):",
        "form.middle_sink": "Middle sink (m/s):",
        "form.max_speed": "Max speed (km/h):",
        "form.max_sink": "Max sink (m/s):",
        "group.speedbar_steps": "Speedbar Steps",
        "label.type": "Type:",
        "combo.two_steps": "2 steps",
        "combo.three_steps": "3 steps",
        "label.note_hover": "Note: (hover me)",
        "tooltip.speedbar_steps": (
            "It is recommended that you measure how much speed system line the"
            " each level of bar is actually pulling.\nThere are some geometric non-linearities"
            " and harness deformations. You may be surprised.\n"
            "Some gliders have markings on the line. These allow to eyeball it in the flight.\n"
            "If your last pedal doesn't pull all of the line, set the percentage accordingly (example: 90%%)"
        ),
        "label.step_with_number": "Step {step_number}",
        "button.calculate": "Calculate",
        "placeholder.polar_chart": "[Polar curve chart placeholder]",
        "placeholder.speedbar_glide_chart": "[Speedbar % for Glide placeholder]",
        "placeholder.conditions_matrix_chart": "[Best speedbar and glide chart (heat table) placeholder]",
        "placeholder.optimal_pedal_chart": "[Optimal speedbar pedal placeholder]",
        "tab.polar_curve": "Polar Curve",
        "tab.speedbar_glide": "Speedbar vs Glide",
        "tab.conditions_matrix": "Conditions Matrix",
        "tab.speedbar_speed": "Speedbar vs Speed",
        "tab.optimal_pedal": "Optimal Speedbar Pedal",
        "chart.polar.legend_curve": "Polar curve",
        "chart.polar.legend_trim_ld": "Trim L/D",
        "chart.polar.axis_x": "Speed (km/h)",
        "chart.polar.axis_y": "Sink (m/s)",
        "chart.polar.title": "Polar Curve",
        "chart.conditions.axis_x": "Headwind (km/h)",
        "chart.conditions.axis_y": "Air sink (m/s)",
        "chart.conditions.title": "Best Speedbar % (0=trim, 1=max)",
        "chart.conditions.colorbar": "Speedbar %",
        "chart.speedbar_glide.axis_x": "Glide",
        "chart.speedbar_glide.axis_y": "Speedbar % (0=trim, 1=max)",
        "chart.speedbar_glide.title": "Speedbar % for Glide",
        "chart.optimal_pedal.axis_x": "Glide",
        "chart.optimal_pedal.axis_y": "Optimal pedal",
        "chart.optimal_pedal.title": "Optimal Speedbar Pedal",
        "chart.speedbar_speed.axis_x": "Speedbar % (0=trim, 1=max)",
        "chart.speedbar_speed.axis_y": "Speed (km/h)",
        "chart.speedbar_speed.title": "Speed for Speedbar %",
    },
}


def _normalize_language_code(language_code: str) -> str:
    normalized = language_code.strip().lower().replace("-", "_")
    if normalized in TRANSLATIONS:
        return normalized
    base_language = normalized.split("_", 1)[0]
    if base_language in TRANSLATIONS:
        return base_language
    return "en"


def detect_language() -> str:
    override = os.getenv("PSBC_LANG")
    if override:
        return _normalize_language_code(override)

    locale_name = locale.getlocale()[0] or ""
    if not locale_name:
        locale_name = locale.getdefaultlocale()[0] or ""
    if not locale_name:
        return "en"

    return _normalize_language_code(locale_name)


_ACTIVE_LANGUAGE = detect_language()


def set_language(language: str) -> str:
    global _ACTIVE_LANGUAGE
    _ACTIVE_LANGUAGE = _normalize_language_code(language)
    return _ACTIVE_LANGUAGE


def get_language() -> str:
    return _ACTIVE_LANGUAGE


def t(key: str, **kwargs) -> str:
    selected_map = TRANSLATIONS.get(_ACTIVE_LANGUAGE, TRANSLATIONS["en"])
    english_map = TRANSLATIONS["en"]
    template = selected_map.get(key, english_map.get(key, key))
    if kwargs:
        return template.format(**kwargs)
    return template