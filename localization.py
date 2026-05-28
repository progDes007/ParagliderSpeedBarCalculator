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
        "button.template": "Template...",
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
            " each level of bar is actually pulling.\n"
            "If your last step doesn't pull all of the line, set the percentage accordingly (example: 90%)"
        ),
        "label.step_with_number": "Step {step_number}",
        "button.calculate": "Calculate",
        "placeholder.polar_chart": "[Polar curve chart placeholder]",
        "placeholder.speedbar_glide_chart": "[Speedbar % for Glide placeholder]",
        "placeholder.conditions_matrix_chart": "[Best speedbar and glide chart (heat table) placeholder]",
        "placeholder.optimal_step_chart": "[Optimal speedbar step placeholder]",
        "tab.polar_curve": "Polar Curve",
        "tab.speedbar_glide": "Speedbar vs Glide",
        "tab.conditions_matrix": "Conditions Matrix",
        "tab.speedbar_speed": "Speedbar vs Speed",
        "tab.optimal_step": "Optimal Speedbar Step",
        "chart.polar.legend_curve": "Polar curve",
        "chart.polar.legend_trim_ld": "Trim L/D",
        "chart.polar.axis_x": "Speed (km/h)",
        "chart.polar.axis_y": "Sink (m/s)",
        "chart.polar.title": "Polar Curve",
        "chart.conditions.axis_x": "Headwind (km/h)",
        "chart.conditions.axis_y": "Air sink (m/s)",
        "chart.conditions.title": "Optimal speedbar for different conditions",
        "chart.conditions.colorbar": "Speedbar %",
        "chart.speedbar_glide.axis_x": "Glide",
        "chart.speedbar_glide.axis_y": "Speedbar % (0=trim, 1=max)",
        "chart.speedbar_glide.title": "Optimal Speedbar for Glide",
        "chart.optimal_step.axis_x": "Glide",
        "chart.optimal_step.axis_y": "Optimal step",
        "chart.optimal_step.title": "Optimal Speedbar Step",
        "chart.speedbar_speed.axis_x": "Speedbar % (0=trim, 1=max)",
        "chart.speedbar_speed.axis_y": "Speed (km/h)",
        "chart.speedbar_speed.title": "Speed for Speedbar %",
        "group.speed_system_wing": "Speed System (wing)",
        "label.speed_system_type": "Speed System Type:",
        "combo.speed_system_type_linear": "Whole range linear (?)",
        "combo.speed_system_type_lockout_end": "At the end one of the pulleys is locked (?)",
        "tooltip.speed_system_type_linear": "The line pulls pulleys of speed system at same rate over entire range.",
        "tooltip.speed_system_type_lockout_end": "In the end of the range one of the pulleys is locked out. This turns 3-pulley system into 2-pulley system. And makes further pull 50% harder and 50% faster.",
    },
    "russian": {
        "error.invalid_polar_params_html": "<span style='color:red'>Введите корректные значения поляры.</span>",
        "label.trim_glide_placeholder": "Глайд на балансировочной: --",
        "label.trim_glide_invalid_sink": "Глайд на балансировочной: -- (некорректная скорость снижения)",
        "label.trim_glide_value": "Глайд на балансировочной: {value:.2f} ",
        "label.max_glide_placeholder": "Глайд на максимальной: --",
        "label.max_glide_invalid_sink": "Глайд на максимальной: -- (invalid sink)",
        "label.max_glide_value": "Глайд на максимальной: {value:.2f} ",
        "group.polar_curve_params": "Параметры поляры",
        "button.template": "Шаблон...",
        "form.trim_speed": "Балансировочная скорость (км/ч):",
        "form.trim_sink": "Снижение при ней (м/с):",
        "checkbox.specify_mid_point": "Указать промежуточную точку",
        "form.middle_speed": "Промежуточная скорость (км/ч):",
        "form.middle_sink": "Снижение при ней (м/с):",
        "form.max_speed": "Максимальная скорость (км/ч):",
        "form.max_sink": "Снижение при ней (м/с):",
        "group.speedbar_steps": "Акселератор (подвеска)",
        "label.type": "Тип:",
        "combo.two_steps": "2 ступени",
        "combo.three_steps": "3 ступени",
        "label.note_hover": "Примечание: (наведите курсор)",
        "tooltip.speedbar_steps": (
            "Рекомендуется измерить, насколько каждая ступень системы скорости фактически тянет шнур акселя.\n"
            "Если последняя ступень не тянет весь шнур до конца, установите процент соответственно (например: 90%)"
        ),
        "label.step_with_number": "Ступень {step_number}",
        "button.calculate": "Расчитать",
        "tab.polar_curve": "Поляра",
        "tab.speedbar_glide": "Аксель и глайд",
        "tab.conditions_matrix": "Матрица условий",
        "tab.speedbar_speed": "Аксель и скорость",
        "tab.optimal_step": "Оптимальная ступень акселя",
        "chart.polar.legend_curve": "Поляра",
        "chart.polar.legend_trim_ld": "Глайд на балансировочной",
        "chart.polar.axis_x": "Скорость (км/ч)",
        "chart.polar.axis_y": "Снижение (м/с)",
        "chart.polar.title": "Поляра",
        "chart.conditions.axis_x": "Встречный ветер (км/ч)",
        "chart.conditions.axis_y": "Снижение воздуха (м/с)",
        "chart.conditions.title": "Оптимальный аксель для разных условий",
        "chart.conditions.colorbar": "Процент акселя %",
        "chart.speedbar_glide.axis_x": "Глайд",
        "chart.speedbar_glide.axis_y": "Процент акселя (0=балансировочная, 1=максимум)",
        "chart.speedbar_glide.title": "Оптимальный аксель и оптимальный глайд",
        "chart.optimal_step.axis_x": "Глайд",
        "chart.optimal_step.axis_y": "Оптимальная ступень акселя",
        "chart.optimal_step.title": "Оптимальная ступень акселя",
        "chart.speedbar_speed.axis_x": "Процент акселя (0=балансировочная, 1=максимум)",
        "chart.speedbar_speed.axis_y": "Скорость (км/ч)",
        "chart.speedbar_speed.title": "Скорость для акселя",
        "group.speed_system_wing": "Акселератор (крыло)",
        "label.speed_system_type": "Тип системы:",
        "combo.speed_system_type_linear": "Линейная во всем диапазоне (?)",
        "combo.speed_system_type_lockout_end": "В конце диапазона один из блочков блокируется (?)",
        "tooltip.speed_system_type_linear": "Шнур стягивает блочки с одинаковой скоростью во всем диапазоне.",
        "tooltip.speed_system_type_lockout_end": "В конце диапазона один из блочков блокируется. Это превращает систему из 3х блоков в систему из 2х блоков. Что делает дальнейшее стягивание на 50% тяжелее и на 50% быстрее.",
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