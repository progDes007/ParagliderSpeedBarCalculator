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
import sys
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

def fit_quadratic_curve(p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float]) -> Callable[[float], float]:
    """
    Fit a quadratic curve y = ax^2 + bx + c through three points.
    Returns a function y(x).
    """
    import numpy as np
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    A = np.array([
        [x1**2, x1, 1],
        [x2**2, x2, 1],
        [x3**2, x3, 1],
    ])
    b = np.array([y1, y2, y3])
    a, b_, c = np.linalg.solve(A, b)
    return lambda x: a * x**2 + b_ * x + c


from PySide6.QtCore import QTimer

class MainWindow(QWidget):


    def __init__(self):
        super().__init__()
        self.setWindowTitle("Paraglider Speedbar Calculator")
        self.init_ui()

        self.calc_btn.clicked.connect(self.on_calculate)
        self.auto_middle_checkbox.stateChanged.connect(self.on_auto_middle_changed)
        # Connect boundary fields to recalculate middle point if Auto is checked
        self.trim_speed.textChanged.connect(self.on_boundary_changed)
        self.trim_sink.textChanged.connect(self.on_boundary_changed)
        self.max_speed.textChanged.connect(self.on_boundary_changed)
        self.max_sink.textChanged.connect(self.on_boundary_changed)
    
    def on_boundary_changed(self):
            if self.auto_middle_checkbox.isChecked():
                try:
                    trim_speed = float(self.trim_speed.text())
                    trim_sink = -abs(float(self.trim_sink.text()))
                    max_speed = float(self.max_speed.text())
                    max_sink = -abs(float(self.max_sink.text()))
                    middle_speed, middle_sink = self.calculate_middle_point(trim_speed, trim_sink, max_speed, max_sink)
                    self.middle_speed.setText(f"{middle_speed:.3f}")
                    self.middle_sink.setText(f"{abs(middle_sink):.3f}")
                except ValueError:
                    self.middle_speed.setText("")
                    self.middle_sink.setText("")

    def on_auto_middle_changed(self, state):
        if self.auto_middle_checkbox.isChecked():
            try:
                trim_speed = float(self.trim_speed.text())
                trim_sink = -abs(float(self.trim_sink.text()))
                max_speed = float(self.max_speed.text())
                max_sink = -abs(float(self.max_sink.text()))
                middle_speed, middle_sink = self.calculate_middle_point(trim_speed, trim_sink, max_speed, max_sink)
                self.middle_speed.setText(f"{middle_speed:.3f}")
                self.middle_sink.setText(f"{abs(middle_sink):.3f}")
                self.middle_speed.setDisabled(True)
                self.middle_sink.setDisabled(True)
            except ValueError:
                self.middle_speed.setText("")
                self.middle_sink.setText("")
                self.middle_speed.setDisabled(True)
                self.middle_sink.setDisabled(True)
        else:
            self.middle_speed.setDisabled(False)
            self.middle_sink.setDisabled(False)

    def calculate_middle_point(self, trim_speed, trim_sink, max_speed, max_sink):
        trim_glide = (trim_speed / 3.6) / trim_sink
        max_speed_glide = (max_speed / 3.6) / max_sink
        middle_glide = (trim_glide + max_speed_glide) / 2

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
        polar_fn = fit_quadratic_curve(
            (trim_speed, trim_sink),
            (middle_speed, middle_sink),
            (max_speed, max_sink)
        )

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
        for i in range(len(sink_vals) ):
            for j in range(len(wind_vals ) ):
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

    # No need to redraw on resize; pixmap will scale with label

    def init_ui(self):
        from PySide6.QtWidgets import QComboBox, QMenu, QToolButton, QHBoxLayout
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
        self.preset_names = ["EN-B", "EN-B+", "EN-C", "EN D", "EN CCC"]
        for name in self.preset_names:
            self.set_menu.addAction(name)
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
        # --- Auto checkbox with '?' icon and tooltip ---
        auto_row = QHBoxLayout()
        self.auto_middle_checkbox = QCheckBox("Auto")
        auto_row.addWidget(self.auto_middle_checkbox)
        self.auto_help_label = QLabel("<span style='color:#007acc; font-weight:bold; cursor:pointer;'>?</span>")
        self.auto_help_label.setToolTip("Assumes that glide is degrading linearly between trim and max speed.")
        self.auto_help_label.setStyleSheet("QLabel { padding-left: 4px; }")
        auto_row.addWidget(self.auto_help_label)
        auto_row.addStretch(1)
        polar_layout.addRow(auto_row)
        polar_layout.addRow("Middle speed (km/h):", self.middle_speed)
        polar_layout.addRow("Middle sink (m/s):", self.middle_sink)
        polar_layout.addRow("Max speed (km/h):", self.max_speed)
        polar_layout.addRow("Max sink (m/s):", self.max_sink)

        polar_group.setLayout(polar_layout)
        left_col.addWidget(polar_group)

        self.calc_btn = QPushButton("Calculate")
        left_col.addWidget(self.calc_btn)
        left_col.addStretch(1)

        # --- Right column: Outputs ---
        right_col = QVBoxLayout()

        # Glide row: Trim Glide and Max Speed Glide side by side
        glide_row = QHBoxLayout()
        self.trim_glide_label = QLabel("Trim glide: --")
        glide_row.addWidget(self.trim_glide_label)
        self.max_glide_label = QLabel("Max speed glide: --")
        glide_row.addWidget(self.max_glide_label)
        glide_row.addStretch(1)
        right_col.addLayout(glide_row)

        from PySide6.QtWidgets import QSizePolicy

        self.polar_chart_label = QLabel("[Polar curve chart placeholder]")
        self.polar_chart_label.setStyleSheet("background: #eee; border: 1px dashed #aaa;")
        self.polar_chart_label.setFixedSize(640, 480)
        right_col.addWidget(self.polar_chart_label)

        self.heat_table_label = QLabel("[Best speedbar and glide chart (heat table) placeholder]")
        self.heat_table_label.setStyleSheet("background: #eee; border: 1px dashed #aaa;")
        self.heat_table_label.setFixedSize(640, 480)
        right_col.addWidget(self.heat_table_label)

        # Add columns to main layout
        main_layout.addLayout(left_col, 1)
        main_layout.addLayout(right_col, 2)
        self.setLayout(main_layout)

        # --- Connect preset actions ---
        for i, action in enumerate(self.set_menu.actions()):
            action.triggered.connect(lambda checked, idx=i: self.apply_preset(idx))

    def apply_preset(self, idx):
        """
        Set polar curve fields to preset values by index.
        Values to be filled in next step.
        """
        # Example stub values, replace with real ones in next step
        presets = [
            # EN-B
            {"trim_speed": "36", "trim_sink": "1.11", "max_speed": "48", "max_sink": "1.90"},
            # EN-B+
            {"trim_speed": "36", "trim_sink": "1.05", "max_speed": "50", "max_sink": "1.85"},
            # EN-C
            {"trim_speed": "37", "trim_sink": "1.03", "max_speed": "53", "max_sink": "1.84"},
            # EN D
            {"trim_speed": "37", "trim_sink": "0.98", "max_speed": "56", "max_sink": "1.83"},
            # EN CCC
            {"trim_speed": "37", "trim_sink": "0.93", "max_speed": "62", "max_sink": "1.91"},
        ]
        preset = presets[idx]
        self.trim_speed.setText(preset["trim_speed"])
        self.trim_sink.setText(preset["trim_sink"])
        self.auto_middle_checkbox.setChecked(True)  # Auto middle point for presets
        self.max_speed.setText(preset["max_speed"])
        self.max_sink.setText(preset["max_sink"])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
