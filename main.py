import sys
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLineEdit, QGroupBox
)
from PySide6.QtCore import Qt

from charts import (
    build_conditions_matrix_chart_pixmap,
    build_polar_curve_chart_pixmap,
    build_speedbar_vs_glide_chart_pixmap,
    build_speedbar_vs_speed_chart_pixmap,
    build_optimal_speedbar_pedal_chart_pixmap,
)
from localization import t, set_language, detect_language, get_language

from typing import Tuple, Callable


def glide_for_speedbar_and_conditions(
    polar_fn: Callable[[float], float],
    speedbar_to_speed_fn: Callable[[float], float],
    speedbar_percent: float,
    headwind: float,
    air_sink: float,
) -> float:
    speed = speedbar_to_speed_fn(speedbar_percent)
    sink = polar_fn(speed)
    speed_ms = speed / 3.6
    real_speed = speed_ms - headwind
    real_sink = sink - air_sink
    if real_sink >= 0.0 or real_speed <= 0.0:
        return 0.0
    return real_speed / abs(real_sink)

def find_best_speedbar_and_glide(
    polar_fn: Callable[[float], float],
    speedbar_to_speed_fn: Callable[[float], float],
    headwind: float,
    air_sink: float,
) -> Tuple[float, float]:
    """
    Finds the best speedbar position (as percent, 0=trim, 1=max) and glide for given conditions.
    Inputs:
        polar_fn: function mapping speed (km/h) to sink (m/s)
        speedbar_to_speed_fn: function mapping speedbar position (0=trim, 1=max) to speed (km/h)
        headwind: headwind (m/s, positive)
        air_sink: surrounding air sink (m/s)
    Returns:
        (best_percent, best_glide)
        best_percent: float in [0, 1] (0=trim, 1=max)
        best_glide: best glide 
    """
    best_glide = -float('inf')
    best_percent = 0.0
    n_steps = 50
    for i in range(n_steps + 1):
        percent = i / n_steps
        glide = glide_for_speedbar_and_conditions(
            polar_fn=polar_fn,
            speedbar_to_speed_fn=speedbar_to_speed_fn,
            speedbar_percent=percent,
            headwind=headwind,
            air_sink=air_sink,
        )
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

def speedbar_to_speed_fn_full(speedbar: float, trim_speed: float, max_speed: float) -> float:
    # Assumes that speedbar is only rotating the profile (not deformning it)
    # given the dimensions of paraglider, it can be assumed that AoA is linearly related to speedbar pos
    # at normal AoA the lift is roughly linearly proportional to speed.
    # Pushing speedbar also reduces the glide slope, this effects AoA. But my tests show that this
    # effect is absolutely negligble, so it is not take into account

    # Knowing that lift is proportional to square of the speed we can:

    max_speed_pct = max_speed / trim_speed
    max_speed_lift_pct = 1 / max_speed_pct**2

    lift_pct = 1 + speedbar * (max_speed_lift_pct - 1)
    speed = max_speed * (lift_pct/max_speed_lift_pct)**(-0.5)
    return speed    


from PySide6.QtCore import QTimer

presets = [
    {"name": "EN-B",   "trim_speed": "39", "trim_sink": "1.20", "max_speed": "51.8", "max_sink": "2.07"},
    {"name": "EN-B+",  "trim_speed": "39", "trim_sink": "1.134", "max_speed": "54", "max_sink": "2.05"},
    {"name": "EN-C",   "trim_speed": "40", "trim_sink": "1.1124", "max_speed": "57.24", "max_sink": "2.02"},
    {"name": "EN D",   "trim_speed": "40", "trim_sink": "1.0584", "max_speed": "60.48", "max_sink": "1.9764"},
    {"name": "EN CCC", "trim_speed": "40", "trim_sink": "1.004", "max_speed": "66.96", "max_sink": "2.0628"},
    {"name": "Advance-Alpha (A)", 
     "trim_speed": "38", "trim_sink": "1.26",
      "middle_speed" : "44.0", "middle_sink": "1.50", 
      "max_speed": "48", "max_sink": "1.8"},
    {"name": "Advance-Epsilon (Mid B)", 
     "trim_speed": "38", "trim_sink": "1.17",
      "middle_speed" : "43.5", "middle_sink": "1.40", 
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
        set_language(detect_language())
        self.t = t
        self.language = get_language()
        self.setWindowTitle(self.t("app.title"))
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
        else:
            self.middle_speed.setDisabled(True)
            self.middle_sink.setDisabled(True)

    def lerp(self, a, b, t):
        return a + (b - a) * t
    
    def calculate_middle_point(self, trim_speed, trim_sink, max_speed, max_sink):
        trim_glide = (trim_speed / 3.6) / trim_sink
        max_speed_glide = (max_speed / 3.6) / max_sink
        middle_speed = (trim_speed + max_speed) / 2
        #glide changes according to quadratic law.
        ratio = (middle_speed - max_speed) / (max_speed - trim_speed)
        ratio = ratio**2
        middle_glide = self.lerp(trim_glide, max_speed_glide, ratio)

        
        middle_sink = -(middle_speed / 3.6) / middle_glide

        return middle_speed, middle_sink

    def on_speedbar_steps_mode_changed(self):
        is_three_step = self.speedbar_steps_mode.currentIndex() == 1
        self.step_rows[2].setVisible(is_three_step)

        # Apply recommended defaults for active mode.
        defaults = [50.0, 100.0] if not is_three_step else [33.0, 66.0, 100.0]
        active_count = 3 if is_three_step else 2
        for i in range(active_count):
            self.step_inputs[i].setValue(defaults[i])

    def on_speed_system_type_changed(self):
        is_linear = self.speed_system_type_combo.currentIndex() == 0
        self.pulley_block_row_widget.setVisible(not is_linear)
        self.pulley_block_note_label.setVisible(not is_linear)


    def on_calculate(self):
        # Read and validate user input
        try:
            trim_speed = float(self.trim_speed.text())
            trim_sink = -abs(float(self.trim_sink.text()))
            max_speed = float(self.max_speed.text())
            max_sink = -abs(float(self.max_sink.text()))
            if self.specify_middle_checkbox.isChecked():
                middle_speed = float(self.middle_speed.text())
                middle_sink = -abs(float(self.middle_sink.text()))
        except ValueError:
            self.polar_chart_label.setText(self.t("error.invalid_polar_params_html"))
            self.trim_glide_label.setText(self.t("label.trim_glide_placeholder"))
            return

        active_steps = 3 if self.speedbar_steps_mode.currentIndex() == 1 else 2
        step_values = [self.step_inputs[i].value() for i in range(active_steps)]

        # Pedal map uses numeric keys and normalized percentages (0..1).
        # Pedal 0 is trim and should always map to 0% speedbar.
        pedal_map = {0: 0.0}
        for i in range(active_steps):
            pedal_map[i + 1] = step_values[i] / 100.0

        # Calculate and display trim glide
        # Convert speed from km/h to m/s for correct L/D calculation
        if trim_sink != 0:
            trim_speed_ms = trim_speed / 3.6
            trim_glide = trim_speed_ms / abs(trim_sink)
            self.trim_glide_label.setText(self.t("label.trim_glide_value", value=trim_glide))
        else:
            self.trim_glide_label.setText(self.t("label.trim_glide_invalid_sink"))

        # Calculate and display max speed glide
        if max_sink != 0:
            max_speed_ms = max_speed / 3.6
            max_glide = max_speed_ms / abs(max_sink)
            self.max_glide_label.setText(self.t("label.max_glide_value", value=max_glide))
        else:
            self.max_glide_label.setText(self.t("label.max_glide_invalid_sink"))

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
        
        # How speedbar converts ot speed
        speedbar_to_speed_fn = lambda percent: speedbar_to_speed_fn_full(percent, trim_speed, max_speed)

        chart_width, chart_height = 800, 600
        dpi = 100

        pixmap = build_polar_curve_chart_pixmap(
            polar_fn=polar_fn,
            trim_speed=trim_speed,
            trim_sink=trim_sink,
            max_speed=max_speed,
            max_sink=max_sink,
            include_middle_point=self.specify_middle_checkbox.isChecked(),
            middle_speed=middle_speed if self.specify_middle_checkbox.isChecked() else 0.0,
            middle_sink=middle_sink if self.specify_middle_checkbox.isChecked() else 0.0,
            chart_width=chart_width,
            chart_height=chart_height,
            dpi=dpi,
        )
        self.polar_chart_label.setPixmap(pixmap)
        self.polar_chart_label.setAlignment(Qt.AlignCenter)

        range_sink = (1.5*max_sink, 0)  # m/s
        range_wind = (-0.9 * trim_speed, +0.9*trim_speed)   # km/h
        steps_sink = 21
        steps_wind = 17
        pixmap2 = build_conditions_matrix_chart_pixmap(
            polar_fn=polar_fn,
            speedbar_to_speed_fn=speedbar_to_speed_fn,
            find_best_speedbar_and_glide_fn=find_best_speedbar_and_glide,
            sink_range=range_sink,
            wind_range=range_wind,
            sink_steps=steps_sink,
            wind_steps=steps_wind,
            chart_width=chart_width,
            chart_height=chart_height,
            dpi=dpi,
        )
        self.heat_table_label.setPixmap(pixmap2)
        self.heat_table_label.setAlignment(Qt.AlignCenter)

        pixmap3 = build_speedbar_vs_glide_chart_pixmap(
            polar_fn=polar_fn,
            speedbar_to_speed_fn=speedbar_to_speed_fn,
            find_best_speedbar_and_glide_fn=find_best_speedbar_and_glide,
            trim_speed=trim_speed,
            chart_width=chart_width,
            chart_height=chart_height,
            dpi=dpi,
        )
        self.speedbar_glide_label.setPixmap(pixmap3)
        self.speedbar_glide_label.setAlignment(Qt.AlignCenter)

        pixmap4 = build_speedbar_vs_speed_chart_pixmap(
            speedbar_to_speed_fn=speedbar_to_speed_fn,
            chart_width=chart_width,
            chart_height=chart_height,
            dpi=dpi,
        )
        self.empty_label.setPixmap(pixmap4)
        self.empty_label.setAlignment(Qt.AlignCenter)

        pixmap5 = build_optimal_speedbar_pedal_chart_pixmap(
            polar_fn=polar_fn,
            speedbar_to_speed_fn=speedbar_to_speed_fn,
            glide_for_speedbar_and_conditions_fn=glide_for_speedbar_and_conditions,
            trim_speed=trim_speed,
            pedal_map=pedal_map,
            chart_width=chart_width,
            chart_height=chart_height,
            dpi=dpi,
        )
        self.optimal_pedal_label.setPixmap(pixmap5)
        self.optimal_pedal_label.setAlignment(Qt.AlignCenter)

    # No need to redraw on resize; pixmap will scale with label

    def init_ui(self):
        from PySide6.QtWidgets import QComboBox, QMenu, QToolButton, QHBoxLayout, QSizePolicy, QTabWidget, QDoubleSpinBox

        main_layout = QHBoxLayout()

        # --- Left column: Inputs ---
        left_col = QVBoxLayout()

        polar_group = QGroupBox(self.t("group.polar_curve_params"))
        polar_layout = QFormLayout()

        # --- Set... button and dropdown (moved above entries) ---
        set_layout = QHBoxLayout()
        self.set_btn = QToolButton()
        self.set_btn.setText(self.t("button.template"))
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
        self.middle_speed.setDisabled(True)
        self.trim_sink = QLineEdit()
        self.max_sink = QLineEdit()
        self.middle_sink = QLineEdit()
        self.middle_sink.setDisabled(True)
        polar_layout.addRow(self.t("form.trim_speed"), self.trim_speed)
        polar_layout.addRow(self.t("form.trim_sink"), self.trim_sink)
        specify_row = QHBoxLayout()
        self.specify_middle_checkbox = QCheckBox(self.t("checkbox.specify_mid_point"))
        specify_row.addWidget(self.specify_middle_checkbox)
        specify_row.addStretch(1)
        polar_layout.addRow(specify_row)
        polar_layout.addRow(self.t("form.middle_speed"), self.middle_speed)
        polar_layout.addRow(self.t("form.middle_sink"), self.middle_sink)
        polar_layout.addRow(self.t("form.max_speed"), self.max_speed)
        polar_layout.addRow(self.t("form.max_sink"), self.max_sink)

        polar_group.setLayout(polar_layout)
        left_col.addWidget(polar_group)

        #Speed system (in the wing) settings
        # speed_system_group = QGroupBox(self.t("group.speed_system_wing"))
        # speed_system_layout = QVBoxLayout()

        # speed_system_type_layout = QVBoxLayout()
        # speed_system_type_label = QLabel(self.t("label.speed_system_type"))
        # self.speed_system_type_combo = QComboBox()
        # self.speed_system_type_combo.addItems([
        #     self.t("combo.speed_system_type_1_stage"),
        #     self.t("combo.speed_system_type_2_stage"),
        # ])
        # self.speed_system_type_combo.setItemData(
        #     0,
        #     self.t("tooltip.speed_system_type_1_stage"),
        #     Qt.ToolTipRole,
        # )
        # self.speed_system_type_combo.setItemData(
        #     1,
        #     self.t("tooltip.speed_system_type_2_stage"),
        #     Qt.ToolTipRole,
        # )

        # self.pulley_block_row_widget = QWidget()
        # pulley_block_row = QHBoxLayout()
        # pulley_block_row.setContentsMargins(0, 0, 0, 0)
        # pulley_block_label = QLabel(self.t("label.pulley_blocked_at"))
        # self.pulley_blocked_at_input = QDoubleSpinBox()
        # self.pulley_blocked_at_input.setRange(0.0, 100.0)
        # self.pulley_blocked_at_input.setDecimals(1)
        # self.pulley_blocked_at_input.setSingleStep(1.0)
        # self.pulley_blocked_at_input.setValue(80.0)
        # self.pulley_blocked_at_input.setSuffix(" %")
        # self.pulley_blocked_at_input.setFixedWidth(110)
        # pulley_block_row.addWidget(pulley_block_label)
        # pulley_block_row.addStretch(1)
        # pulley_block_row.addWidget(self.pulley_blocked_at_input)
        # self.pulley_block_row_widget.setLayout(pulley_block_row)

        # self.pulley_block_note_label = QLabel(self.t("label.pulley_blocked_note"))
        # self.pulley_block_note_label.setWordWrap(True)

        # speed_system_type_layout.addWidget(speed_system_type_label)
        # speed_system_type_layout.addWidget(self.speed_system_type_combo)
        # speed_system_type_layout.addWidget(self.pulley_block_row_widget)
        # speed_system_type_layout.addWidget(self.pulley_block_note_label)
        # speed_system_layout.addLayout(speed_system_type_layout)

        # speed_system_group.setLayout(speed_system_layout)
        # left_col.addWidget(speed_system_group)

        #Speedbar step settings
        speedbar_steps_group = QGroupBox(self.t("group.speedbar_steps"))
        speedbar_steps_layout = QVBoxLayout()

        speedbar_mode_row = QHBoxLayout()
        speedbar_mode_label = QLabel(self.t("label.type"))
        self.speedbar_steps_mode = QComboBox()
        self.speedbar_steps_mode.addItems([self.t("combo.two_steps"), self.t("combo.three_steps")])
        speedbar_mode_row.addWidget(speedbar_mode_label)
        speedbar_mode_row.addWidget(self.speedbar_steps_mode)
        speedbar_mode_row.addStretch(1)
        speedbar_steps_layout.addLayout(speedbar_mode_row)

        note_label = QLabel(self.t("label.note_hover"))
        note_label.setToolTip(self.t("tooltip.speedbar_steps"))
        note_label.setStyleSheet("color: #1565c0; font-weight: 700;")
        speedbar_steps_layout.addWidget(note_label)

        self.step_rows = []
        self.step_inputs = []
        for step_number in range(1, 4):
            row = QWidget()
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addWidget(QLabel(self.t("label.step_with_number", step_number=step_number)))
            row_layout.addStretch(1)
            amount_input = QDoubleSpinBox()
            amount_input.setRange(0.0, 100.0)
            amount_input.setDecimals(1)
            amount_input.setSingleStep(1.0)
            amount_input.setSuffix(" %")
            amount_input.setFixedWidth(110)
            row_layout.addWidget(amount_input)
            row.setLayout(row_layout)
            self.step_rows.append(row)
            self.step_inputs.append(amount_input)
            speedbar_steps_layout.addWidget(row)

        speedbar_steps_group.setLayout(speedbar_steps_layout)
        left_col.addWidget(speedbar_steps_group)

        self.speedbar_steps_mode.currentIndexChanged.connect(self.on_speedbar_steps_mode_changed)
        #self.speed_system_type_combo.currentIndexChanged.connect(self.on_speed_system_type_changed)
        self.on_speedbar_steps_mode_changed()
        #self.on_speed_system_type_changed()

        self.calc_btn = QPushButton(self.t("button.calculate"))
        left_col.addWidget(self.calc_btn)
        # Add glide labels under Calculate button
        self.trim_glide_label = QLabel(self.t("label.trim_glide_placeholder"))
        self.max_glide_label = QLabel(self.t("label.max_glide_placeholder"))
        left_col.addWidget(self.trim_glide_label)
        left_col.addWidget(self.max_glide_label)
        left_col.addStretch(1)

        # --- Right column: outputs in tabs ---
        right_tabs = QTabWidget()

        def create_chart_tab(label: QLabel) -> QWidget:
            tab = QWidget()
            tab_layout = QVBoxLayout()
            tab_layout.setContentsMargins(8, 8, 8, 8)
            tab_layout.addWidget(label, alignment=Qt.AlignCenter)
            tab.setLayout(tab_layout)
            return tab

        self.polar_chart_label = QLabel(self.t("placeholder.polar_chart"))
        self.polar_chart_label.setStyleSheet("background: #eee; border: 1px dashed #aaa;")
        self.polar_chart_label.setFixedSize(800, 600)
        right_tabs.addTab(create_chart_tab(self.polar_chart_label), self.t("tab.polar_curve"))

        self.speedbar_glide_label = QLabel(self.t("placeholder.speedbar_glide_chart"))
        self.speedbar_glide_label.setStyleSheet("background: #eee; border: 1px dashed #aaa;")
        self.speedbar_glide_label.setFixedSize(800, 600)
        right_tabs.addTab(create_chart_tab(self.speedbar_glide_label), self.t("tab.speedbar_glide"))

        self.heat_table_label = QLabel(self.t("placeholder.conditions_matrix_chart"))
        self.heat_table_label.setStyleSheet("background: #eee; border: 1px dashed #aaa;")
        self.heat_table_label.setFixedSize(800, 600)
        right_tabs.addTab(create_chart_tab(self.heat_table_label), self.t("tab.conditions_matrix"))

        self.empty_label = QLabel("")
        self.empty_label.setStyleSheet("background: #eee; border: 1px dashed #aaa;")
        self.empty_label.setFixedSize(800, 600)
        right_tabs.addTab(create_chart_tab(self.empty_label), self.t("tab.speedbar_speed"))

        self.optimal_pedal_label = QLabel(self.t("placeholder.optimal_step_chart"))
        self.optimal_pedal_label.setStyleSheet("background: #eee; border: 1px dashed #aaa;")
        self.optimal_pedal_label.setFixedSize(800, 600)
        right_tabs.addTab(create_chart_tab(self.optimal_pedal_label), self.t("tab.optimal_step"))

        # --- Wrap left_col in a QWidget with fixed/minimum width ---
        left_widget = QWidget()
        left_widget.setLayout(left_col)
        left_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        left_widget.setMinimumWidth(260)

        # --- Wrap right tabs in a QWidget that expands ---
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(right_tabs)
        right_widget.setLayout(right_layout)
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
            self.middle_speed.setText("")
            self.middle_sink.setText("")
            self.middle_speed.setDisabled(True)
            self.middle_sink.setDisabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
