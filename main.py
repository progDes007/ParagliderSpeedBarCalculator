import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLineEdit, QGroupBox
)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Paraglider Speedbar Calculator")
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Polar parameters group
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
        main_layout.addWidget(polar_group)

        # Calculate button
        self.calc_btn = QPushButton("Calculate")
        main_layout.addWidget(self.calc_btn)

        # Output: Best glide
        self.best_glide_label = QLabel("Best glide: --")
        main_layout.addWidget(self.best_glide_label)

        # Output: Polar curve chart placeholder
        self.polar_chart_label = QLabel("[Polar curve chart placeholder]")
        self.polar_chart_label.setStyleSheet("background: #eee; border: 1px dashed #aaa; min-height: 100px;")
        main_layout.addWidget(self.polar_chart_label)

        # Output: Heat table placeholder
        self.heat_table_label = QLabel("[Best speedbar and glide chart (heat table) placeholder]")
        self.heat_table_label.setStyleSheet("background: #eee; border: 1px dashed #aaa; min-height: 100px;")
        main_layout.addWidget(self.heat_table_label)

        self.setLayout(main_layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
