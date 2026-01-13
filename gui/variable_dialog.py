from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QComboBox, QPushButton, QCheckBox, QGroupBox,
    QFormLayout, QDoubleSpinBox, QScrollArea, QWidget, QLabel,
    QCompleter
)
from PyQt6.QtCore import Qt

from core.logic_engine import LogicBlock, LogicOutput, ConditionRule
from .logic_schematic_widget import LogicSchematicWidget
from .dataref_search_dialog import DatarefSearchDialog


class VariableDialog(QDialog):
    def __init__(self, dataref_manager, block: LogicBlock = None, variable_store=None, parent=None):
        super().__init__(parent)
        self.dataref_manager = dataref_manager
        self.variable_store = variable_store
        self.block = block or LogicBlock(name="New Variable")
        self.setWindowTitle("Configure Logic Variable")
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)

        self._cond_widgets = []
        self._output_widgets = []

        self._setup_ui()
        if block:
            self._populate()

    def _import_template(self):
        from core.logic_library import get_templates
        from PyQt6.QtWidgets import QMenu
        templates = get_templates()
        menu = QMenu(self)
        for name in templates.keys():
            action = menu.addAction(name)
            action.triggered.connect(lambda _, n=name: self._load_template_data(templates[n]))
        menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))

    def _load_template_data(self, template_block: LogicBlock):
        self.block = template_block
        self._populate()
        self._update_schematic()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Template Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.template_btn = QPushButton("💡 Load Template...")
        self.template_btn.clicked.connect(self._import_template)
        btn_layout.addWidget(self.template_btn)
        layout.addLayout(btn_layout)
        
        # 1. Name & Desc
        info_group = QGroupBox("1. Variable Information")
        info_layout = QVBoxLayout(info_group)
        self.name_input = QLineEdit()
        self.desc_input = QLineEdit()
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(True)


        info_layout.addWidget(QLabel("Name (Unique ID):"))
        info_layout.addWidget(self.name_input)
        info_layout.addWidget(QLabel("Description:"))
        info_layout.addWidget(self.desc_input)
        
        # Output Key (sent to hardware)
        self.output_key_input = QLineEdit()
        self.output_key_input.setPlaceholderText("Output ID Key (e.g., GEAR_LED)")
        info_layout.addWidget(QLabel("Output ID Key (for Hardware):"))
        info_layout.addWidget(self.output_key_input)
        
        # Initial Value (Sent on connect)
        self.init_val_input = QDoubleSpinBox()
        self.init_val_input.setRange(-999999, 999999)
        self.init_val_input.setDecimals(4)
        self.init_val_input.setSpecialValueText("None (Follow Logic)")
        # We'll use -999999 or similar to represent None, or just a checkbox.
        # Minimalist approach: add a checkbox to enable initial value
        self.init_enabled = QCheckBox("Set Initial Value on Connection")
        info_layout.addWidget(self.init_enabled)
        info_layout.addWidget(self.init_val_input)
        
        info_layout.addWidget(self.enabled_check)
        layout.addWidget(info_group)
        
        # 2. Visual Schematic
        self.schematic_widget = LogicSchematicWidget([], "AND", [])
        layout.addWidget(self.schematic_widget)
        
        # 3. Conditions (Inputs)
        cond_group = QGroupBox("2. Inputs (Conditions)")
        cond_layout = QVBoxLayout(cond_group)
        
        # Logic Gate Selector
        gate_layout = QHBoxLayout()
        gate_layout.addWidget(QLabel("Combine inputs with:"))
        self.logic_combo = QComboBox()
        self.logic_combo.addItems(["AND", "OR", "XOR", "NAND", "NOR", "XNOR"])
        gate_layout.addWidget(self.logic_combo)
        self.logic_combo.currentTextChanged.connect(self._update_schematic)
        gate_layout.addStretch()
        cond_layout.addLayout(gate_layout)
        
        # Scroll area for conditions
        self.cond_scroll = QScrollArea()
        self.cond_scroll.setWidgetResizable(True)
        self.cond_container = QWidget()
        self.cond_container_layout = QVBoxLayout(self.cond_container)
        self.cond_container_layout.addStretch()
        self.cond_scroll.setWidget(self.cond_container)
        cond_layout.addWidget(self.cond_scroll)
        
        add_cond_btn = QPushButton("➕ Add Condition (Input Dataref)")
        add_cond_btn.clicked.connect(self._add_condition)
        cond_layout.addWidget(add_cond_btn)
        
        layout.addWidget(cond_group)
        
        # 4. Outputs (Actions)
        out_group = QGroupBox("3. Actions (Outputs)")
        out_layout = QVBoxLayout(out_group)
        
        self.out_scroll = QScrollArea()
        self.out_scroll.setWidgetResizable(True)
        self.out_container = QWidget()
        self.out_container_layout = QVBoxLayout(self.out_container)
        self.out_container_layout.addStretch()
        self.out_scroll.setWidget(self.out_container)
        out_layout.addWidget(self.out_scroll)
        
        add_out_btn = QPushButton("➕ Add Output (Write to Dataref)")
        add_out_btn.clicked.connect(self._add_output)
        out_layout.addWidget(add_out_btn)
        
        layout.addWidget(out_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("Save")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _add_condition(self):
        # Create a simplified condition widget
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0,0,0,0)
        
        # Enabled checkbox
        enabled_check = QCheckBox()
        enabled_check.setChecked(True)
        
        # Dataref input
        inp = QLineEdit()
        inp.setPlaceholderText("Dataref (e.g., sim/cockpit2/gauges/indicators/airspeed_kts_pilot)")
        if self.dataref_manager:
            all_names = self.dataref_manager.get_all_dataref_names()
            completer = QCompleter(all_names)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setMaxVisibleItems(20)
            inp.setCompleter(completer)
        
        # Operator combo
        op = QComboBox()
        op.addItems(["<", "<=", ">", ">=", "==", "!="])
        
        # Value input
        val = QDoubleSpinBox()
        val.setRange(-999999, 999999)
        val.setDecimals(2)
        
        # Browse button
        browse_btn = QPushButton("🔍")
        browse_btn.setFixedSize(28,28)
        browse_btn.clicked.connect(lambda: self._open_search(inp))
        
        # Delete button
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(24,24)
        
        # Add widgets to layout
        l.addWidget(enabled_check)
        l.addWidget(inp, 1)
        l.addWidget(op)
        l.addWidget(val)
        l.addWidget(browse_btn)
        l.addWidget(del_btn)
        
        def on_del():
            self.cond_container_layout.removeWidget(w)
            w.deleteLater()
            # Remove from list if it exists
            for item in self._cond_widgets[:]:
                if item[0] == w:
                    self._cond_widgets.remove(item)
                    break
            self._update_schematic()
            
        del_btn.clicked.connect(on_del)
        self.cond_container_layout.insertWidget(self.cond_container_layout.count()-1, w)
        self._cond_widgets.append((w, enabled_check, inp, op, val))
        self._update_schematic()

    def _add_output(self):
        # Simple Output Widget
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0,0,0,0)
        
        # Target dataref
        tgt = QLineEdit()
        tgt.setPlaceholderText("Target Dataref")
        if self.dataref_manager:
            all_names = self.dataref_manager.get_all_dataref_names()
            completer = QCompleter(all_names)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setMaxVisibleItems(20)
            tgt.setCompleter(completer)
        browse_btn = QPushButton("🔍")
        browse_btn.setFixedSize(28,28)
        browse_btn.clicked.connect(lambda: self._open_search(tgt))
        
        # Value
        val = QDoubleSpinBox()
        val.setRange(-999999, 999999)
        val.setDecimals(2)
        
        # Action type
        action_combo = QComboBox()
        action_combo.addItems(["set", "toggle"])
        
        # Delete button
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(24,24)
        
        # Add widgets to layout
        l.addWidget(QLabel("Set"))
        l.addWidget(tgt, 1)
        l.addWidget(browse_btn)
        l.addWidget(QLabel("to"))
        l.addWidget(val)
        l.addWidget(QLabel("Action:"))
        l.addWidget(action_combo)
        l.addWidget(del_btn)
        
        def on_del():
            self.out_container_layout.removeWidget(w)
            w.deleteLater()
            # Remove from list if it exists
            for item in self._output_widgets[:]:
                if item[0] == w:
                    self._output_widgets.remove(item)
                    break
            self._update_schematic()
            
        del_btn.clicked.connect(on_del)
        self.out_container_layout.insertWidget(self.out_container_layout.count()-1, w)
        self._output_widgets.append((w, tgt, val, action_combo))
        self._update_schematic()

    def _open_search(self, line_edit):
        if not self.dataref_manager: return
        dlg = DatarefSearchDialog(self.dataref_manager, self.variable_store, self)
        if dlg.exec():
            line_edit.setText(dlg.get_selected_dataref())
            self._update_schematic()

    def _update_schematic(self):
        # Collect current data
        conds = []
        for w, enabled_check, inp, op, val in self._cond_widgets:
            if inp.text():
                conds.append(ConditionRule(inp.text(), op.currentText(), val.value(), enabled=enabled_check.isChecked()))
        
        outs = []
        for w, tgt, val, action_combo in self._output_widgets:
            if tgt.text():
                outs.append(LogicOutput(tgt.text(), val.value(), action_combo.currentText()))
        
        gate = self.logic_combo.currentText()
        self.schematic_widget.update_data(conds, gate, outs)

    def _populate(self):
        # Clear existing
        for w, _, _, _, _ in self._cond_widgets:
            self.cond_container_layout.removeWidget(w)
            w.deleteLater()
        self._cond_widgets = []
        for w, _, _, _ in self._output_widgets:
            self.out_container_layout.removeWidget(w)
            w.deleteLater()
        self._output_widgets = []

        self.name_input.setText(self.block.name)
        self.desc_input.setText(self.block.description)
        self.output_key_input.setText(self.block.output_key or "")
        self.enabled_check.setChecked(self.block.enabled)
        
        if self.block.initial_value is not None:
            self.init_enabled.setChecked(True)
            self.init_val_input.setValue(self.block.initial_value)
        else:
            self.init_enabled.setChecked(False)
            self.init_val_input.setValue(0.0)
            
        self.logic_combo.setCurrentText(self.block.logic_gate)
        
        # Populate conditions
        for c in self.block.conditions:
            self._add_condition()
            if self._cond_widgets:
                w, enabled_check, inp, op, val = self._cond_widgets[-1]
                inp.setText(c.dataref)
                op.setCurrentText(c.operator)
                val.setValue(c.value)
                enabled_check.setChecked(c.enabled)
            
        # Populate outputs
        for o in self.block.outputs:
            self._add_output()
            if self._output_widgets:
                w, tgt, val, action_combo = self._output_widgets[-1]
                tgt.setText(o.target)
                val.setValue(o.value)
                action_combo.setCurrentText(o.action_type)
            
        self._update_schematic()

    def get_block(self) -> LogicBlock:
        conds = []
        for w, enabled_check, inp, op, val in self._cond_widgets:
            if inp.text():
                conds.append(ConditionRule(inp.text(), op.currentText(), val.value(), enabled=enabled_check.isChecked()))
        
        outs = []
        for w, tgt, val, action_combo in self._output_widgets:
            if tgt.text():
                outs.append(LogicOutput(tgt.text(), val.value(), action_combo.currentText()))
                
        return LogicBlock(
            name=self.name_input.text(),
            description=self.desc_input.text(),
            enabled=self.enabled_check.isChecked(),
            conditions=conds,
            logic_gate=self.logic_combo.currentText(),
            outputs=outs,
            initial_value=self.init_val_input.value() if self.init_enabled.isChecked() else None,
            output_key=self.output_key_input.text().strip()
        )