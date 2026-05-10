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
            trim_sink = float(self.trim_sink.text())
            middle_speed = float(self.middle_speed.text())
            middle_sink = float(self.middle_sink.text())
            max_speed = float(self.max_speed.text())
            max_sink = float(self.max_sink.text())
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

        # Sample the curve
        speeds = np.linspace(trim_speed, max_speed, 100)
        sinks = [polar_fn(v) for v in speeds]

        # Plot
        fig, ax = plt.subplots(figsize=(4, 2.5), dpi=100)
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

        self.polar_chart_label = QLabel("[Polar curve chart placeholder]")
        self.polar_chart_label.setStyleSheet("background: #eee; border: 1px dashed #aaa; min-height: 100px;")
        right_col.addWidget(self.polar_chart_label)

        self.heat_table_label = QLabel("[Best speedbar and glide chart (heat table) placeholder]")
        self.heat_table_label.setStyleSheet("background: #eee; border: 1px dashed #aaa; min-height: 100px;")
        right_col.addWidget(self.heat_table_label)

        right_col.addStretch(1)

        # Add columns to main layout
        main_layout.addLayout(left_col, 1)
        main_layout.addLayout(right_col, 2)
        self.setLayout(main_layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
