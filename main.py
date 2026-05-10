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
        best_glide: best glide (L/D)
    """
    best_glide = -float('inf')
    best_percent = 0.0
    for i in range(10):
        percent = i / 9 if 9 > 0 else 0
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

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Paraglider Speedbar Calculator")
        self.init_ui()

        self.calc_btn.clicked.connect(self.on_calculate)

    def on_calculate(self):
        # Read and validate user input
        try:
            trim_speed = float(self.trim_speed.text())
            trim_sink = -float(self.trim_sink.text())
            middle_speed = float(self.middle_speed.text())
            middle_sink = -float(self.middle_sink.text())
            max_speed = float(self.max_speed.text())
            max_sink = -float(self.max_sink.text())
        except ValueError:
            self.polar_chart_label.setText("<span style='color:red'>Please enter valid numbers for all polar parameters.</span>")
            self.trim_glide_label.setText("Trim glide: --")
            return

        # Calculate and display trim glide
        # Convert speed from km/h to m/s for correct L/D calculation
        if trim_sink != 0:
            trim_speed_ms = trim_speed / 3.6
            trim_glide = trim_speed_ms / abs(trim_sink)
            self.trim_glide_label.setText(f"Trim glide: {trim_glide:.2f} (L/D)")
        else:
            self.trim_glide_label.setText("Trim glide: -- (invalid sink)")

        # Calculate and display max speed glide
        if max_sink != 0:
            max_speed_ms = max_speed / 3.6
            max_glide = max_speed_ms / abs(max_sink)
            self.max_glide_label.setText(f"Max speed glide: {max_glide:.2f} (L/D)")
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
        # Get label size in pixels
        label_width = max(self.polar_chart_label.width(), 100)
        label_height = max(self.polar_chart_label.height(), 100)
        dpi = 100
        fig_width = label_width / dpi
        fig_height = label_height / dpi
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

        # --- Heatmap of best speedbar % ---
        # Grid: sink in [0, 3], headwind in [-20, 30]
        sink_vals = np.linspace(0, 2.2, 11)
        wind_vals = np.linspace(-20, 20, 11)
        heat = np.zeros((len(sink_vals), len(wind_vals)))
        for i, air_sink in enumerate(sink_vals):
            for j, headwind in enumerate(wind_vals):
                best_percent, _ = find_best_speedbar_and_glide(
                    polar_fn,
                    trim_speed,
                    max_speed,
                    headwind / 3.6,
                    air_sink
                )
                heat[i, j] = best_percent

        label2_width = max(self.heat_table_label.width(), 100)
        label2_height = max(self.heat_table_label.height(), 100)
        fig2_width = label2_width / dpi
        fig2_height = label2_height / dpi
        fig2, ax2 = plt.subplots(figsize=(fig2_width, fig2_height), dpi=dpi)
        c = ax2.imshow(
            heat,
            origin='lower',
            aspect='auto',
            extent=[wind_vals[0], wind_vals[-1], sink_vals[0], sink_vals[-1]],
            cmap='viridis',
            vmin=0, vmax=1
        )
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

    def resizeEvent(self, event):
        # Redraw plots at new size to avoid pixelation
        self.on_calculate()
        super().resizeEvent(event)

    def init_ui(self):
        main_layout = QHBoxLayout()

        # --- Left column: Inputs ---
        left_col = QVBoxLayout()

        polar_group = QGroupBox("Polar Curve Parameters")
        polar_layout = QFormLayout()
        self.trim_speed = QLineEdit()
        self.max_speed = QLineEdit()
        self.middle_speed = QLineEdit()
        self.trim_sink = QLineEdit()
        self.max_sink = QLineEdit()
        self.middle_sink = QLineEdit()
        polar_layout.addRow("Trim speed (km/h):", self.trim_speed)
        polar_layout.addRow("Trim sink (m/s):", self.trim_sink)
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
        self.polar_chart_label.setStyleSheet("background: #eee; border: 1px dashed #aaa; min-height: 100px;")
        self.polar_chart_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_col.addWidget(self.polar_chart_label, stretch=2)

        self.heat_table_label = QLabel("[Best speedbar and glide chart (heat table) placeholder]")
        self.heat_table_label.setStyleSheet("background: #eee; border: 1px dashed #aaa; min-height: 100px;")
        self.heat_table_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_col.addWidget(self.heat_table_label, stretch=2)

        # Add columns to main layout
        main_layout.addLayout(left_col, 1)
        main_layout.addLayout(right_col, 2)
        self.setLayout(main_layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
