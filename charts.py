from io import BytesIO
from typing import Callable, Mapping, Tuple
from localization import t

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PySide6.QtGui import QPixmap


def _figure_to_qpixmap(fig) -> QPixmap:
    buf = BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    pixmap = QPixmap()
    pixmap.loadFromData(buf.getvalue(), "PNG")
    return pixmap


def build_polar_curve_chart_pixmap(
    polar_fn: Callable[[float], float],
    trim_speed: float,
    trim_sink: float,
    max_speed: float,
    max_sink: float,
    include_middle_point: bool,
    middle_speed: float,
    middle_sink: float,
    chart_width: int,
    chart_height: int,
    dpi: int,
) -> QPixmap:
    speeds = np.linspace(trim_speed, max_speed, 100)
    sinks = [polar_fn(v) for v in speeds]

    fig_width = chart_width / dpi
    fig_height = chart_height / dpi
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)

    ax.plot(speeds, sinks, label=t("chart.polar.legend_curve"), color="blue")
    polar_speeds = [trim_speed, max_speed]
    polar_sinks = [trim_sink, max_sink]
    if include_middle_point:
        polar_speeds.insert(1, middle_speed)
        polar_sinks.insert(1, middle_sink)
    ax.scatter(polar_speeds, polar_sinks, color="red", zorder=5)

    ax.plot(
        [trim_speed * 0.7, trim_speed],
        [trim_sink * 0.7, trim_sink],
        linestyle=":",
        color="black",
        linewidth=2,
        label=t("chart.polar.legend_trim_ld"),
    )

    ax.set_xlabel(t("chart.polar.axis_x"))
    ax.set_ylabel(t("chart.polar.axis_y"))
    ax.set_title(t("chart.polar.title"))
    ax.grid(True)
    ax.legend()
    fig.tight_layout()

    return _figure_to_qpixmap(fig)


def build_conditions_matrix_chart_pixmap(
    polar_fn: Callable[[float], float],
    speedbar_to_speed_fn: Callable[[float], float],
    find_best_speedbar_and_glide_fn: Callable[[Callable[[float], float], Callable[[float], float], float, float], Tuple[float, float]],
    sink_range: Tuple[float, float],
    wind_range: Tuple[float, float],
    sink_steps: int,
    wind_steps: int,
    chart_width: int,
    chart_height: int,
    dpi: int,
) -> QPixmap:
    sink_vals = np.linspace(sink_range[0], sink_range[1], sink_steps, endpoint=True)
    wind_vals = np.linspace(wind_range[0], wind_range[1], wind_steps, endpoint=True)
    hstep_sink = (sink_range[1] - sink_range[0]) / sink_steps * 0.5
    hstep_wind = (wind_range[1] - wind_range[0]) / wind_steps * 0.5

    heat = np.zeros((len(sink_vals), len(wind_vals)))
    glide_vals = np.zeros((len(sink_vals), len(wind_vals)))
    for i, air_sink in enumerate(sink_vals):
        for j, headwind in enumerate(wind_vals):
            best_percent, best_glide = find_best_speedbar_and_glide_fn(
                polar_fn,
                speedbar_to_speed_fn,
                headwind / 3.6,
                -air_sink,
            )
            heat[i, j] = best_percent
            glide_vals[i, j] = best_glide

    cmap_name = "gray"
    text_color = "red"
    text_fontsize = 8
    vmin = 0
    vmax = 1
    fig_width = chart_width / dpi
    fig_height = chart_height / dpi
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)

    image = ax.imshow(
        heat,
        origin="lower",
        aspect="auto",
        extent=[
            wind_vals[0] - hstep_wind,
            wind_vals[-1] + hstep_wind,
            sink_vals[0] - hstep_sink,
            sink_vals[-1] + hstep_sink,
        ],
        cmap=cmap_name,
        vmin=vmin,
        vmax=vmax,
    )

    for i in range(len(sink_vals)):
        for j in range(len(wind_vals)):
            ax.text(
                wind_vals[j],
                sink_vals[i],
                f"{glide_vals[i, j]:.1f}",
                ha="center",
                va="center",
                color=text_color,
                fontsize=text_fontsize,
            )

    ax.set_xlabel(t("chart.conditions.axis_x"))
    ax.set_ylabel(t("chart.conditions.axis_y"))
    ax.set_title(t("chart.conditions.title"))
    fig.colorbar(image, ax=ax, label=t("chart.conditions.colorbar"))
    fig.tight_layout()

    return _figure_to_qpixmap(fig)


def build_speedbar_vs_glide_chart_pixmap(
    polar_fn: Callable[[float], float],
    speedbar_to_speed_fn: Callable[[float], float],
    find_best_speedbar_and_glide_fn: Callable[[Callable[[float], float], Callable[[float], float], float, float], Tuple[float, float]],
    trim_speed: float,
    chart_width: int,
    chart_height: int,
    dpi: int,
) -> QPixmap:
    wind_sample_count = 100
    line_color = "green"
    line_width = 2
    wind_range = np.linspace(0, trim_speed, wind_sample_count)
    glide_x = []
    speedbar_y = []

    for wind in wind_range:
        best_percent, best_glide = find_best_speedbar_and_glide_fn(
            polar_fn,
            speedbar_to_speed_fn,
            wind / 3.6,
            0.0,
        )
        glide_x.append(best_glide)
        speedbar_y.append(best_percent)

    fig_width = chart_width / dpi
    fig_height = chart_height / dpi
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
    ax.plot(glide_x, speedbar_y, color=line_color, lw=line_width)
    ax.set_xlabel(t("chart.speedbar_glide.axis_x"))
    ax.set_ylabel(t("chart.speedbar_glide.axis_y"))
    ax.set_title(t("chart.speedbar_glide.title"))
    ax.grid(True)
    fig.tight_layout()

    return _figure_to_qpixmap(fig)


def build_optimal_speedbar_pedal_chart_pixmap(
    polar_fn: Callable[[float], float],
    speedbar_to_speed_fn: Callable[[float], float],
    glide_for_speedbar_and_conditions_fn: Callable[[Callable[[float], float], Callable[[float], float], float, float, float], float],
    trim_speed: float,
    pedal_map: Mapping[int, float],
    chart_width: int,
    chart_height: int,
    dpi: int,
) -> QPixmap:
    wind_sample_count = 100
    wind_range = np.linspace(0, trim_speed, wind_sample_count)
    glide_x = []
    pedal_y = []

    sorted_pedals = sorted(pedal_map.items(), key=lambda item: item[0])
    for wind in wind_range:
        best_pedal = 0
        best_glide = -float("inf")
        headwind_ms = wind / 3.6
        for pedal_index, speedbar_percent in sorted_pedals:
            glide = glide_for_speedbar_and_conditions_fn(
                polar_fn=polar_fn,
                speedbar_to_speed_fn=speedbar_to_speed_fn,
                speedbar_percent=speedbar_percent,
                headwind=headwind_ms,
                air_sink=0.0,
            )
            if glide > best_glide:
                best_glide = glide
                best_pedal = pedal_index
        glide_x.append(best_glide)
        pedal_y.append(best_pedal)

    fig_width = chart_width / dpi
    fig_height = chart_height / dpi
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
    ax.scatter(glide_x, pedal_y, color="tab:orange", s=14)
    ax.plot(glide_x, pedal_y, color="tab:orange", lw=1)
    ax.set_xlabel(t("chart.optimal_pedal.axis_x"))
    ax.set_ylabel(t("chart.optimal_pedal.axis_y"))
    ax.set_title(t("chart.optimal_pedal.title"))
    if sorted_pedals:
        y_ticks = [pedal_index for pedal_index, _ in sorted_pedals]
        ax.set_yticks(y_ticks)
    ax.grid(True)
    fig.tight_layout()

    return _figure_to_qpixmap(fig)


def build_speedbar_vs_speed_chart_pixmap(
    speedbar_to_speed_fn: Callable[[float], float],
    chart_width: int,
    chart_height: int,
    dpi: int,
) -> QPixmap:
    sample_count = 10
    speedbar_min = 0.0
    speedbar_max = 1.0
    line_color = "blue"
    line_width = 2
    speedbar_samples = np.linspace(speedbar_min, speedbar_max, sample_count)
    speed_samples = [speedbar_to_speed_fn(percent) for percent in speedbar_samples]

    fig_width = chart_width / dpi
    fig_height = chart_height / dpi
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
    ax.plot(speedbar_samples, speed_samples, color=line_color, lw=line_width)
    ax.set_xlabel(t("chart.speedbar_speed.axis_x"))
    ax.set_ylabel(t("chart.speedbar_speed.axis_y"))
    ax.set_title(t("chart.speedbar_speed.title"))
    ax.grid(True)
    fig.tight_layout()

    return _figure_to_qpixmap(fig)
