import sys
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLineEdit, QGroupBox
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

from typing import Tuple, Callable

def find_best_speedbar_and_glide(
    polar_fn: Callable[[float], float],
    min_speed: float,
    max_speed: float,
    headwind: float,
    air_sink: float,
) -> Tuple[float, float, float]:
    """
    Finds the best speedbar position (as percent, 0=trim, 1=max) and glide for given conditions.
    Inputs:
        polar_fn: function mapping speed (km/h) to sink (m/s)
        min_speed: trim speed (km/h)
        max_speed: max speed (km/h)
        headwind: headwind (m/s, positive)
        air_sink: surrounding air sink (m/s)
    Returns:
        (best_percent, best_speed, best_glide)
        best_percent: float in [0, 1] (0=trim, 1=max)
        best_speed: speed (km/h)
        best_glide: best glide 
    """
    best_glide = -float('inf')
    best_percent = 0.0
    n_steps = 50
    for i in range(n_steps + 1):
        percent = i / n_steps
        speed = min_speed + percent * (max_speed - min_speed)
        sink = polar_fn(speed)
        speed_ms = speed / 3.6
        real_speed = speed_ms - headwind
        real_sink = sink - air_sink
        if real_sink >= 0.0 or real_speed <= 0.0:
            glide = 0.0
        else:
            glide = real_speed / abs(real_sink)
        if glide > best_glide:
            best_glide = glide
            best_percent = percent
    return best_percent, best_glide


def fit_polynomial2(p1: Tuple[float, float], p2: Tuple[float, float]) -> Callable[[float], float]:
    # it is assumed that glider is trimed so that that glide is optimal at trim speed.
    # that means that derivative of glide at trim speed is 0,
    # so constraints are:
    # 1. Pass through p1 and p2
    # 2. f'(p1[0]) = trim glide = m
    # 3. given g(x) = f(x) / x, then g'(x0) = 0.  Meaning that glide is peaked at trim speed.

    m = p1[1] / p1[0]  # glide at trim speed
    # this curve satisfies above constraints
    a = (p2[1] - m * p2[0]) / (p2[0] - p1[0])**2
    return lambda x: a * (x - p1[0])**2 + m * (x - p1[0]) + p1[1]

def fit_polynomial3(p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float]) -> Callable[[float], float]:
    #same as fit_polynomial2 but with additional constraint that it also passes through p3
    x0 = p1[0]
    x1 = p2[0]
    x2 = p3[0]
    y0 = p1[1]  
    y1 = p2[1]
    y2 = p3[1]

    z0 = x0
    z1 = x0
    z2 = x1
    z3 = x2

    m = y0 / z0

    c0 = y0
    c1 = z0z1 = m
    z1z2 = (y1-y0)/(x1-x0)
    z2z3 = (y2-y1)/(x2-x1)
    c2 = z0z1z2 = (z1z2-m) / (x1 - x0)
    z0z1z2 = (z1z2-m) / (x1-x0)
    z1z2z3 = (z2z3-z1z2) / (x2 - x0)
    c3 = z0z1z2z3 = (z1z2z3-z0z1z2) / (x2-x0)

    return lambda x: c0 + c1*(x-x0) + c2*(x-x0)**2 + c3*(x-x0)**2 * (x-x1)



from PySide6.QtCore import QTimer

presets = [
    {"name": "EN-B",   "trim_speed": "36", "trim_sink": "1.11", "max_speed": "48", "max_sink": "1.90"},
    {"name": "EN-B+",  "trim_speed": "36", "trim_sink": "1.05", "max_speed": "50", "max_sink": "1.85"},
    {"name": "EN-C",   "trim_speed": "37", "trim_sink": "1.03", "max_speed": "53", "max_sink": "1.84"},
    {"name": "EN D",   "trim_speed": "37", "trim_sink": "0.98", "max_speed": "56", "max_sink": "1.83"},
    {"name": "EN CCC", "trim_speed": "37", "trim_sink": "0.93", "max_speed": "62", "max_sink": "1.91"},
    {"name": "Advance-Alpha (A)", 
     "trim_speed": "38", "trim_sink": "1.26",
      "middle_speed" : "44.0", "middle_sink": "1.50", 
      "max_speed": "48", "max_sink": "1.8"},
    {"name": "Advance-Epsilon (Mid B)", 
     "trim_speed": "38", "trim_sink": "1.17",
      "middle_speed" : "44.0", "middle_sink": "1.40", 
      "max_speed": "53", "max_sink": "2.0"},
    {"name": "Advance-Sigma (C)", 
     "trim_speed": "39", "trim_sink": "1.17",
      "middle_speed" : "47.0", "middle_sink": "1.50", 
      "max_speed": "56.5", "max_sink": "2.2"},
    {"name": "Advance-Omega (D)", 
     "trim_speed": "41", "trim_sink": "1.14",
      "middle_speed" : "50.0", "middle_sink": "1.50", 
      "max_speed": "60.0", "max_sink": "2.2"}
]

class MainWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Paraglider Speedbar Calculator")
        self.init_ui()

        self.calc_btn.clicked.connect(self.on_calculate)
        self.specify_middle_checkbox.stateChanged.connect(self.on_specify_middle_changed)
     

    def on_specify_middle_changed(self, state):
        if self.specify_middle_checkbox.isChecked():
            # Enable editing, and if empty or zero, set to calculated values
            try:
                trim_speed = float(self.trim_speed.text())
                trim_sink = -abs(float(self.trim_sink.text()))
                max_speed = float(self.max_speed.text())
                max_sink = -abs(float(self.max_sink.text()))
                middle_speed, middle_sink = self.calculate_middle_point(trim_speed, trim_sink, max_speed, max_sink)
                # Only set if empty or zero
                ms = self.middle_speed.text()
                msi = self.middle_sink.text()
                if ms.strip() == "" or float(ms) == 0.0:
                    self.middle_speed.setText(f"{middle_speed:.3f}")
                if msi.strip() == "" or float(msi) == 0.0:
                    self.middle_sink.setText(f"{abs(middle_sink):.3f}")
            except Exception:
                pass
            self.middle_speed.setDisabled(False)
            self.middle_sink.setDisabled(False)

    def lerp(self, a, b, t):
        return a + (b - a) * t
    
    def calculate_middle_point(self, trim_speed, trim_sink, max_speed, max_sink):
        trim_glide = (trim_speed / 3.6) / trim_sink
        max_speed_glide = (max_speed / 3.6) / max_sink
        middle_glide = self.lerp(trim_glide, max_speed_glide, 0.5**1.7)

        middle_speed = (trim_speed + max_speed) / 2
        middle_sink = -(middle_speed / 3.6) / middle_glide

        return middle_speed, middle_sink


    def on_calculate(self):
        # Read and validate user input
        try:
            trim_speed = float(self.trim_speed.text())
            trim_sink = -abs(float(self.trim_sink.text()))
            max_speed = float(self.max_speed.text())
            max_sink = -abs(float(self.max_sink.text()))
            middle_speed = float(self.middle_speed.text())
            middle_sink = -abs(float(self.middle_sink.text()))
        except ValueError:
            self.polar_chart_label.setText("<span style='color:red'>Please enter valid numbers for all polar parameters.</span>")
            self.trim_glide_label.setText("Trim glide: --")
            return

        # Calculate and display trim glide
        # Convert speed from km/h to m/s for correct L/D calculation
        if trim_sink != 0:
            trim_speed_ms = trim_speed / 3.6
            trim_glide = trim_speed_ms / abs(trim_sink)
            self.trim_glide_label.setText(f"Trim glide: {trim_glide:.2f} ")
        else:
            self.trim_glide_label.setText("Trim glide: -- (invalid sink)")

        # Calculate and display max speed glide
        if max_sink != 0:
            max_speed_ms = max_speed / 3.6
            max_glide = max_speed_ms / abs(max_sink)
            self.max_glide_label.setText(f"Max speed glide: {max_glide:.2f} ")
        else:
            self.max_glide_label.setText("Max speed glide: -- (invalid sink)")

        # Fit the quadratic curve
        if self.specify_middle_checkbox.isChecked():
            polar_fn = fit_polynomial3(
                (trim_speed, trim_sink),
                (middle_speed, middle_sink),
                (max_speed, max_sink))
        else:
            polar_fn = fit_polynomial2(
                (trim_speed, trim_sink),
                (max_speed, max_sink))

        # --- Polar curve plot ---
        speeds = np.linspace(trim_speed, max_speed, 100)
        sinks = [polar_fn(v) for v in speeds]
        chart_width, chart_height = 630, 480
        dpi = 100
        fig_width = chart_width / dpi
        fig_height = chart_height / dpi
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
        ax.plot(speeds, sinks, label="Polar curve", color="blue")
        ax.scatter([trim_speed, middle_speed, max_speed], [trim_sink, middle_sink, max_sink], color="red", zorder=5)
        # Add dotted line representing the glide slope at trim speed
        ax.plot([trim_speed*0.7, trim_speed], [trim_sink*0.7, trim_sink], linestyle=':', color='black', linewidth=2, label="Trim L/D")
        ax.set_xlabel("Speed (km/h)")
        ax.set_ylabel("Sink (m/s)")
        ax.set_title("Polar Curve")
        ax.grid(True)
        ax.legend()
        fig.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue(), 'PNG')
        self.polar_chart_label.setPixmap(pixmap)
        self.polar_chart_label.setAlignment(Qt.AlignCenter)

        # --- Heatmap of best speedbar % and glide values ---
        range_sink = (-2.5, 0)  # m/s
        range_wind = (-25, 25)   # km/h
        steps_sink = 21
        steps_wind = 17
        sink_vals = np.linspace(range_sink[0], range_sink[1], steps_sink, endpoint=True)
        wind_vals = np.linspace(range_wind[0], range_wind[1], steps_wind, endpoint=True)
        hstep_sink = (range_sink[1] - range_sink[0]) / steps_sink * 0.5 
        hstep_wind = (range_wind[1] - range_wind[0]) / steps_wind * 0.5

        heat = np.zeros((len(sink_vals), len(wind_vals)))
        glide_vals = np.zeros((len(sink_vals), len(wind_vals)))
        for i, air_sink in enumerate(sink_vals):
            for j, headwind in enumerate(wind_vals):
                best_percent, best_glide = find_best_speedbar_and_glide(
                    polar_fn,
                    trim_speed,
                    max_speed,
                    headwind / 3.6,
                    -air_sink
                )
                heat[i, j] = best_percent
                glide_vals[i, j] = best_glide

        # --- Heatmap plot ---
        heatmap_width, heatmap_height = 640, 480
        fig2_width = heatmap_width / dpi
        fig2_height = heatmap_height / dpi
        fig2, ax2 = plt.subplots(figsize=(fig2_width, fig2_height), dpi=dpi)
        c = ax2.imshow(
            heat,
            origin='lower',
            aspect='auto',
            extent=[wind_vals[0] - hstep_wind, wind_vals[-1] + hstep_wind, sink_vals[0] - hstep_sink, sink_vals[-1] + hstep_sink],
            cmap='gray',
            vmin=0, vmax=1
        )
        # Add glide values as text inside each cell
        for i in range(len(sink_vals)):
            for j in range(len(wind_vals)):
                x = wind_vals[j]
                y = sink_vals[i]
                val = glide_vals[i, j]
                ax2.text(x, y, f"{val:.1f}", ha='center', va='center', color='red', fontsize=8)

        ax2.set_xlabel('Headwind (km/h)')
        ax2.set_ylabel('Air sink (m/s)')
        ax2.set_title('Best Speedbar % (0=trim, 1=max)')
        fig2.colorbar(c, ax=ax2, label='Speedbar %')
        fig2.tight_layout()
        buf2 = BytesIO()
        plt.savefig(buf2, format='png')
        plt.close(fig2)
        buf2.seek(0)
        pixmap2 = QPixmap()
        pixmap2.loadFromData(buf2.getvalue(), 'PNG')
        self.heat_table_label.setPixmap(pixmap2)
        self.heat_table_label.setAlignment(Qt.AlignCenter)

        # --- Speedbar % for Glide chart (X: glide, Y: speedbar) ---
        wind_range = np.linspace(-trim_speed, trim_speed, 100)
        glide_x = []
        speedbar_y = []
        for wind in wind_range:
            best_percent, best_glide = find_best_speedbar_and_glide(
                polar_fn,
                trim_speed,
                max_speed,
                wind / 3.6,
                0.0
            )
            glide_x.append(best_glide)
            speedbar_y.append(best_percent)

        fig3, ax3 = plt.subplots(figsize=(6.4, 4.8), dpi=100)
        ax3.plot(glide_x, speedbar_y, color='green', lw=2)
        ax3.set_xlabel('Glide')
        ax3.set_ylabel('Speedbar % (0=trim, 1=max)')
        ax3.set_title('Speedbar % for Glide')
        ax3.grid(True)
        fig3.tight_layout()
        buf3 = BytesIO()
        plt.savefig(buf3, format='png')
        plt.close(fig3)
        buf3.seek(0)
        pixmap3 = QPixmap()
        pixmap3.loadFromData(buf3.getvalue(), 'PNG')
        self.speedbar_glide_label.setPixmap(pixmap3)
        self.speedbar_glide_label.setAlignment(Qt.AlignCenter)

    # No need to redraw on resize; pixmap will scale with label

    def init_ui(self):
        from PySide6.QtWidgets import QComboBox, QMenu, QToolButton, QHBoxLayout, QGridLayout, QSizePolicy

        main_layout = QHBoxLayout()

        # --- Left column: Inputs ---
        left_col = QVBoxLayout()

        polar_group = QGroupBox("Polar Curve Parameters")
        polar_layout = QFormLayout()

        # --- Set... button and dropdown (moved above entries) ---
        set_layout = QHBoxLayout()
        self.set_btn = QToolButton()
        self.set_btn.setText("Set...")
        self.set_menu = QMenu()
        for preset in presets:
            self.set_menu.addAction(preset["name"])
        self.set_btn.setMenu(self.set_menu)
        self.set_btn.setPopupMode(QToolButton.InstantPopup)
        set_layout.addWidget(self.set_btn)
        set_layout.addStretch(1)
        polar_layout.addRow(set_layout)

        # --- Polar curve entries ---
        from PySide6.QtWidgets import QCheckBox, QLabel, QHBoxLayout
        self.trim_speed = QLineEdit()
        self.max_speed = QLineEdit()
        self.middle_speed = QLineEdit()
        self.trim_sink = QLineEdit()
        self.max_sink = QLineEdit()
        self.middle_sink = QLineEdit()
        polar_layout.addRow("Trim speed (km/h):", self.trim_speed)
        polar_layout.addRow("Trim sink (m/s):", self.trim_sink)
        # --- Specify Mid Point checkbox with '?' icon and tooltip ---
        specify_row = QHBoxLayout()
        self.specify_middle_checkbox = QCheckBox("Specify Mid Point")
        specify_row.addWidget(self.specify_middle_checkbox)
        specify_row.addStretch(1)
        polar_layout.addRow(specify_row)
        polar_layout.addRow("Middle speed (km/h):", self.middle_speed)
        polar_layout.addRow("Middle sink (m/s):", self.middle_sink)
        polar_layout.addRow("Max speed (km/h):", self.max_speed)
        polar_layout.addRow("Max sink (m/s):", self.max_sink)

        polar_group.setLayout(polar_layout)
        left_col.addWidget(polar_group)

        self.calc_btn = QPushButton("Calculate")
        left_col.addWidget(self.calc_btn)
        # Add glide labels under Calculate button
        self.trim_glide_label = QLabel("Trim glide: --")
        self.max_glide_label = QLabel("Max speed glide: --")
        left_col.addWidget(self.trim_glide_label)
        left_col.addWidget(self.max_glide_label)
        left_col.addStretch(1)

        # --- Right column: Outputs as 2x2 grid ---
        right_grid = QGridLayout()

        self.polar_chart_label = QLabel("[Polar curve chart placeholder]")
        self.polar_chart_label.setStyleSheet("background: #eee; border: 1px dashed #aaa;")
        self.polar_chart_label.setFixedSize(640, 480)
        right_grid.addWidget(self.polar_chart_label, 0, 0)

        self.heat_table_label = QLabel("[Best speedbar and glide chart (heat table) placeholder]")
        self.heat_table_label.setStyleSheet("background: #eee; border: 1px dashed #aaa;")
        self.heat_table_label.setFixedSize(640, 480)
        right_grid.addWidget(self.heat_table_label, 1, 0)

        # --- Add new empty chart: Speedbar % for Glide ---
        self.speedbar_glide_label = QLabel("[Speedbar % for Glide placeholder]")
        self.speedbar_glide_label.setStyleSheet("background: #eee; border: 1px dashed #aaa;")
        self.speedbar_glide_label.setFixedSize(640, 480)
        right_grid.addWidget(self.speedbar_glide_label, 0, 1)

        # --- Optionally, add a placeholder for future chart or leave empty ---
        self.empty_label = QLabel("")
        self.empty_label.setStyleSheet("background: #eee; border: 1px dashed #aaa;")
        self.empty_label.setFixedSize(640, 480)
        right_grid.addWidget(self.empty_label, 1, 1)

        # --- Wrap left_col in a QWidget with fixed/minimum width ---
        left_widget = QWidget()
        left_widget.setLayout(left_col)
        left_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        left_widget.setMinimumWidth(260)

        # --- Wrap right_grid in a QWidget that expands ---
        right_widget = QWidget()
        right_widget.setLayout(right_grid)
        right_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add widgets to main layout (left fixed, right expands)
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget, stretch=1)
        self.setLayout(main_layout)

        # --- Connect preset actions ---
        for i, action in enumerate(self.set_menu.actions()):
            action.triggered.connect(lambda checked, idx=i: self.apply_preset(idx))

    def apply_preset(self, idx):
        """
        Set polar curve fields to preset values by index.
        If middle_speed and middle_sink are present, enable Specify Mid Point; otherwise, auto-calculate.
        """
        preset = presets[idx]
        self.trim_speed.setText(preset["trim_speed"])
        self.trim_sink.setText(preset["trim_sink"])
        self.max_speed.setText(preset["max_speed"])
        self.max_sink.setText(preset["max_sink"])
        if "middle_speed" in preset and "middle_sink" in preset:
            self.middle_speed.setText(preset["middle_speed"])
            self.middle_sink.setText(preset["middle_sink"])
            self.specify_middle_checkbox.setChecked(True)
            self.middle_speed.setDisabled(False)
            self.middle_sink.setDisabled(False)
        else:
            self.specify_middle_checkbox.setChecked(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
