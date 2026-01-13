from __future__ import annotations
import logging
import asyncio
import math
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum, auto
import json
from pathlib import Path

log = logging.getLogger(__name__)


class InputAction(Enum):
    """Type of action to perform when input is received."""
    COMMAND = auto()        # Send X-Plane command
    DATAREF_SET = auto()    # Set dataref to specific value
    DATAREF_TOGGLE = auto() # Toggle dataref between 0 and 1
    DATAREF_INC = auto()    # Increment dataref
    DATAREF_DEC = auto()    # Decrement dataref
    AXIS = auto()           # Map axis value to dataref
    SEQUENCE = auto()       # Execute multiple actions in sequence
    CUSTOM = auto()         # Custom callback


class DeadzonePosition(Enum):
    """Where the deadzone is applied on the axis."""
    CENTER = "center"       # Deadzone around center (for joysticks/yokes)
    LEFT = "left"           # Deadzone at minimum (for throttle idle cutoff)
    RIGHT = "right"         # Deadzone at maximum (for throttle max detent)
    ENDS = "ends"           # Deadzone at both ends (for worn potentiometers)


class ResponseCurve(Enum):
    """Response curve type for axis mapping."""
    LINEAR = "linear"       # Direct 1:1 response
    SMOOTH = "smooth"       # Gentle acceleration (x^1.5)
    AGGRESSIVE = "aggressive"  # Quick response, fine center control (√x)
    SOFT = "soft"           # Precise center, fast at extremes (x²)
    ULTRA_FINE = "ultra_fine"  # Maximum precision center (x³)
    S_CURVE = "s_curve"     # Smooth start and end (smoothstep)
    EXPONENTIAL = "exponential"  # Slow start, fast finish


@dataclass
class SequenceAction:
    """A single action within a sequence."""
    action_type: str        # "command" or "dataref"
    target: str             # Command or dataref name
    value: float = 0.0      # Value to set (for dataref)
    delay_ms: int = 0       # Delay after this action (milliseconds)
    
    def to_dict(self) -> Dict:
        return {
            "action_type": self.action_type,
            "target": self.target,
            "value": self.value,
            "delay_ms": self.delay_ms,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SequenceAction":
        return cls(
            action_type=data.get("action_type", "command"),
            target=data.get("target", ""),
            value=data.get("value", 0.0),
            delay_ms=data.get("delay_ms", 0),
        )


@dataclass
class Condition:
    """A single logical condition."""
    dataref: str
    operator: str  # <, <=, >, >=, ==, !=
    value: float
    enabled: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "dataref": self.dataref, 
            "operator": self.operator, 
            "value": self.value,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Condition":
        return cls(
            data["dataref"], 
            data["operator"], 
            data["value"],
            enabled=data.get("enabled", True)
        )

# Aliases for backward compatibility
ConditionRule = Condition

class LogicGate(Enum):
    AND = "AND"
    OR = "OR"
    NAND = "NAND"
    NOR = "NOR"
    XOR = "XOR"
    XNOR = "XNOR"

@dataclass
class TargetAction:
    """A single target dataref action."""
    target: str
    value_on: float = 1.0
    value_off: float = 0.0
    
    def to_dict(self) -> Dict:
        return {"target": self.target, "value_on": self.value_on, "value_off": self.value_off}
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TargetAction":
        return cls(data["target"], data.get("value_on", 1.0), data.get("value_off", 0.0))

@dataclass
class InputMapping:
    """Defines how an input maps to one or more X-Plane actions."""
    
    input_key: str
    device_port: str
    action: InputAction
    
    # Legacy target (for simple mappings)
    target: str = ""
    value_on: float = 1.0
    value_off: float = 0.0
    
    # NEW: Multiple targets support
    targets: List[TargetAction] = field(default_factory=list)
    
    # NEW: Multi-condition support
    condition_enabled: bool = False
    conditions: List[Condition] = field(default_factory=list)
    condition_logic: str = "AND"  # AND, OR
    
    # NEW: Initialization Sync
    sync_on_connect: bool = True
    
    # Existing fields...
    increment: float = 1.0
    min_value: float = 0.0
    max_value: float = 360.0
    wrap: bool = False
    axis_min: float = -1.0
    axis_max: float = 1.0
    axis_deadzone: float = 0.0
    axis_deadzone_pos: str = "center"
    axis_curve: str = "linear"
    axis_invert: bool = False
    multiplier: float = 1.0
    sequence_actions: List[SequenceAction] = field(default_factory=list)
    sequence_stop_on_error: bool = False
    sequence_repeat_while_held: bool = False
    sequence_reverse_on_release: bool = False
    description: str = ""
    enabled: bool = True
    init_value: Optional[float] = None  # NEW: Value to set on startup
    command_delay_ms: int = 20  # Delay between command executions when multiplier > 1
    
    def to_dict(self) -> Dict:
        return {
            "input_key": self.input_key,
            "device_port": self.device_port,
            "action": self.action.name,
            "target": self.target,
            "value_on": self.value_on,
            "value_off": self.value_off,
            "targets": [t.to_dict() for t in self.targets],
            "condition_enabled": self.condition_enabled,
            "conditions": [c.to_dict() for c in self.conditions],
            "condition_logic": self.condition_logic,
            "sync_on_connect": self.sync_on_connect,
            "increment": self.increment,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "wrap": self.wrap,
            "axis_min": self.axis_min,
            "axis_max": self.axis_max,
            "axis_deadzone": self.axis_deadzone,
            "axis_deadzone_pos": self.axis_deadzone_pos,
            "axis_curve": self.axis_curve,
            "axis_invert": self.axis_invert,
            "multiplier": self.multiplier,
            "sequence_actions": [a.to_dict() for a in self.sequence_actions],
            "sequence_stop_on_error": self.sequence_stop_on_error,
            "sequence_repeat_while_held": self.sequence_repeat_while_held,
            "sequence_reverse_on_release": self.sequence_reverse_on_release,
            "description": self.description,
            "enabled": self.enabled,
            "init_value": self.init_value,
            "command_delay_ms": self.command_delay_ms,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "InputMapping":
        seq_actions = [SequenceAction.from_dict(a) for a in data.get("sequence_actions", [])]
        conds = [Condition.from_dict(c) for c in data.get("conditions", [])]
        
        trgs = [TargetAction.from_dict(t) for t in data.get("targets", [])]
        # Backward compatibility for old "multi_targets"
        if not trgs and "multi_targets" in data:
            for mt in data["multi_targets"]:
                # Old format: {"dataref": "...", "value": 1.0, "delay": 0}
                t_name = mt.get("dataref") or mt.get("target") or ""
                t_val = mt.get("value", 0.0)
                t_delay = mt.get("delay", 0)
                # Map old single-value to value_on, and assume 0 for off? 
                # Or simply use it as Set Value logic.
                trgs.append(TargetAction(t_name, t_val, 0.0, delay_ms=int(t_delay*1000) if t_delay < 10 else t_delay))
        
        return cls(
            input_key=data["input_key"],
            device_port=data.get("device_port", "*"),
            action=InputAction[data["action"]],
            target=data.get("target", ""),
            value_on=data.get("value_on", 1.0),
            value_off=data.get("value_off", 0.0),
            targets=trgs,
            condition_enabled=data.get("condition_enabled", False),
            conditions=conds,
            condition_logic=data.get("condition_logic", "AND"),
            sync_on_connect=data.get("sync_on_connect", True),
            increment=data.get("increment", 1.0),
            min_value=data.get("min_value", 0.0),
            max_value=data.get("max_value", 360.0),
            wrap=data.get("wrap", False),
            axis_min=data.get("axis_min", -1.0),
            axis_max=data.get("axis_max", 1.0),
            axis_deadzone=data.get("axis_deadzone", 0.0),
            axis_deadzone_pos=data.get("axis_deadzone_pos", "center"),
            axis_curve=data.get("axis_curve", "linear"),
            axis_invert=data.get("axis_invert", False),
            multiplier=data.get("multiplier", 1.0),
            sequence_actions=seq_actions,
            sequence_stop_on_error=data.get("sequence_stop_on_error", False),
            sequence_repeat_while_held=data.get("sequence_repeat_while_held", False),
            sequence_reverse_on_release=data.get("sequence_reverse_on_release", False),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            init_value=data.get("init_value"),
            command_delay_ms=data.get("command_delay_ms", 20),
        )


class InputMapper:
    """
    Maps device inputs to X-Plane actions.
    
    Supports:
    - Conditional execution (check dataref before acting)
    - Axis calibration with deadzone and response curves
    - Sequence macros (multiple actions per input)
    """
    
    MAPPINGS_FILE = Path(__file__).parent.parent / "config" / "input_mappings.json"
    
    def __init__(self, xplane_connection, dataref_manager=None, hid_manager=None, arduino_manager=None, variable_store=None, logic_engine=None) -> None:
        self.xplane_conn = xplane_connection
        self.dataref_manager = dataref_manager
        self.hid_manager = hid_manager
        self.arduino_manager = arduino_manager
        self.variable_store = variable_store
        self.logic_engine = logic_engine

        self._mappings: List[InputMapping] = []
        self._current_values: Dict[str, float] = {}  # dataref -> current value
        
        # Track active sequences for repeat-while-held
        self._active_sequences: Dict[str, asyncio.Task] = {}

        # Callbacks
        self.on_mapping_triggered: Optional[Callable[[InputMapping, float], None]] = None
        self.on_condition_failed: Optional[Callable[[InputMapping, str], None]] = None

        self._load_mappings()
        self._create_default_mappings()
    
    def _load_mappings(self) -> None:
        """Load mappings from file."""
        # Legacy loading disabled in favor of ProfileManager
        pass
    
    def _create_default_mappings(self) -> None:
        """Create default mappings if none exist."""
        # Default creation disabled in favor of ProfileManager
        pass
    
    def save_mappings(self) -> bool:
        """Save mappings to file."""
        # Legacy saving disabled in favor of ProfileManager
        return True
    
    def add_mapping(self, mapping: InputMapping) -> None:
        """Add a new mapping."""
        self._mappings.append(mapping)
    
    def remove_mapping(self, index: int) -> None:
        """Remove a mapping by index."""
        if 0 <= index < len(self._mappings):
            del self._mappings[index]
    
    def get_mappings(self) -> List[InputMapping]:
        """Get all mappings."""
        return self._mappings.copy()
    
    def get_mappings_for_input(self, input_key: str, device_port: str = None) -> List[InputMapping]:
        """Get all mappings for a specific input."""
        result = []
        for m in self._mappings:
            if not m.enabled:
                continue
            if m.input_key != input_key:
                continue
            if m.device_port != "*" and device_port and m.device_port != device_port:
                continue
            result.append(m)
        return result

    def remove_mappings_for_input(self, input_key: str, device_port: str) -> None:
        """Remove all mappings matching key and device."""
        initial_len = len(self._mappings)
        self._mappings = [m for m in self._mappings
                          if not (m.input_key == input_key and m.device_port == device_port)]

        if len(self._mappings) < initial_len:
            log.info("Removed %d old mapping(s) for %s on %s", 
                     initial_len - len(self._mappings), input_key, device_port)

    def update_current_value(self, dataref: str, value: float) -> None:
        """Update tracked current value for a dataref."""
        self._current_values[dataref] = value
    
    def get_current_value(self, dataref: str) -> Optional[float]:
        """Get the current tracked value for a dataref."""
        return self._current_values.get(dataref)
    
    async def sync_hardware_to_xplane(self) -> None:
        """
        Synchronize current hardware switch states to X-Plane.
        This is called upon connection to ensure X-Plane matches physical switches.
        """
        if not self.xplane_conn or not self.xplane_conn.connected:
            return

        log.info("Performing hardware to X-Plane synchronization...")

        # 1. Sync HID Devices (Joysticks/Yokes)
        await self._sync_hid_devices()

        # 2. Sync Arduino Devices
        await self._sync_arduino_devices()

        # 3. Sync Initial Values (pre-written values)
        await self._sync_initial_values()

        log.info("Hardware synchronization complete.")

    async def _sync_hid_devices(self) -> None:
        """Sync HID devices (joysticks, yokes) to X-Plane."""
        if not self.hid_manager:
            return

        devices = self.hid_manager.devices_snapshot()
        for dev_id, device in devices.items():
            if not device.connected:
                continue

            # Sync Buttons
            for i, pressed in enumerate(device.buttons):
                # We treat buttons as binary inputs
                await self.process_input(dev_id, f"BTN_{i}", 1.0 if pressed else 0.0)

            # Sync Axes
            for i, val in enumerate(device.axes):
                await self.process_input(dev_id, f"AXIS_{i}", val)

    async def _sync_arduino_devices(self) -> None:
        """Sync Arduino devices to X-Plane."""
        if not self.arduino_manager:
            return

        devices = self.arduino_manager.devices_snapshot()
        for port, device in devices.items():
            if not device.is_ready:
                continue

            inputs = device.get_all_inputs()
            for key, val in inputs.items():
                await self.process_input(port, key, val)

    async def _sync_initial_values(self) -> None:
        """Sync initial values for mappings."""
        for mapping in self._mappings:
            if not mapping.enabled or mapping.init_value is None:
                continue

            if mapping.action == InputAction.DATAREF_SET:
                trgs = mapping.targets if mapping.targets else [TargetAction(mapping.target, mapping.value_on, mapping.value_off)]
                for t in trgs:
                    await self._write_target(t.target, mapping.init_value)
                    log.info("Init sync: Set %s to %.2f", t.target, mapping.init_value)
            elif mapping.action == InputAction.AXIS:
                await self._write_target(mapping.target, mapping.init_value)
                log.info("Init sync: Set Axis %s to %.2f", mapping.target, mapping.init_value)
    
    # =========================================================================
    # Condition Evaluation
    # =========================================================================
    
    def _check_condition(self, mapping: InputMapping) -> tuple[bool, str]:
        """Evaluate multiple conditions with AND/OR logic."""
        if not mapping.condition_enabled or not mapping.conditions:
            return True, ""

        results = []
        operators = {
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "==": lambda a, b: abs(a - b) < 0.001,
            "!=": lambda a, b: abs(a - b) >= 0.001,
        }

        for cond in mapping.conditions:
            current = self._current_values.get(cond.dataref)
            if current is None:
                results.append(False)
                continue
            
            op_func = operators.get(cond.operator, lambda a, b: False)
            results.append(op_func(current, cond.value))

        if mapping.condition_logic == "AND":
            met = all(results)
        else:
            met = any(results)

        reason = f"Logic {mapping.condition_logic}: {results} -> {met}"
        return met, reason
    
    # =========================================================================
    # Axis Processing with Deadzone and Curves
    # =========================================================================
    
    def _apply_axis_processing(self, raw_value: float, mapping: InputMapping) -> float:
        """
        Apply deadzone, response curve, and output mapping to axis input.

        Args:
            raw_value: Raw normalized input (-1.0 to 1.0 from HID)
            mapping: The axis mapping configuration

        Returns:
            Processed output value mapped to target range
        """
        # 1. Clamp to configured input range
        clamped_value = self._clamp_input_range(raw_value, mapping)

        # 2. Normalize to -1.0 to 1.0 based on configured range
        normalized = self._normalize_input_range(clamped_value, mapping)

        # 3. Apply deadzone based on position
        normalized = self._apply_deadzone_if_needed(normalized, mapping)

        # 4. Apply response curve
        normalized = self._apply_curve(normalized, mapping.axis_curve)

        # 5. Invert if needed
        if mapping.axis_invert:
            normalized = -normalized

        # 6. Map to output range (min_value to max_value)
        output_value = self._map_to_output_range(normalized, mapping)

        return output_value

    def _clamp_input_range(self, raw_value: float, mapping: InputMapping) -> float:
        """Clamp the raw value to the configured input range."""
        return max(mapping.axis_min, min(mapping.axis_max, raw_value))

    def _normalize_input_range(self, value: float, mapping: InputMapping) -> float:
        """Normalize the value to -1.0 to 1.0 based on configured range."""
        if mapping.axis_max != mapping.axis_min:
            # For center-based: normalize to -1..1
            # For end-based: normalize to 0..1
            input_range = mapping.axis_max - mapping.axis_min
            return (value - mapping.axis_min) / input_range * 2.0 - 1.0
        else:
            return 0.0

    def _apply_deadzone_if_needed(self, value: float, mapping: InputMapping) -> float:
        """Apply deadzone if configured."""
        if mapping.axis_deadzone > 0:
            return self._apply_deadzone(value, mapping.axis_deadzone, mapping.axis_deadzone_pos)
        return value

    def _map_to_output_range(self, normalized: float, mapping: InputMapping) -> float:
        """Map the normalized value to the output range."""
        # Convert from -1..1 to 0..1 first
        output_normalized = (normalized + 1.0) / 2.0
        # Then map to output range
        return mapping.min_value + (output_normalized * (mapping.max_value - mapping.min_value))
    
    def _apply_deadzone(self, value: float, deadzone: float, position: str) -> float:
        """
        Apply deadzone based on position setting.

        Args:
            value: Normalized input (-1.0 to 1.0)
            deadzone: Deadzone size (0.0 to 0.5)
            position: 'center', 'left', 'right', or 'ends'

        Returns:
            Value with deadzone applied
        """
        if position == "center":
            return self._apply_center_deadzone(value, deadzone)
        elif position == "left":
            return self._apply_left_deadzone(value, deadzone)
        elif position == "right":
            return self._apply_right_deadzone(value, deadzone)
        elif position == "ends":
            return self._apply_ends_deadzone(value, deadzone)
        else:
            return value  # Fallback

    def _apply_center_deadzone(self, value: float, deadzone: float) -> float:
        """Apply deadzone around center."""
        if abs(value) < deadzone:
            return 0.0
        else:
            # Scale remaining range to full output
            sign = 1.0 if value > 0 else -1.0
            return sign * (abs(value) - deadzone) / (1.0 - deadzone)

    def _apply_left_deadzone(self, value: float, deadzone: float) -> float:
        """Apply deadzone at minimum (left/bottom)."""
        # Convert to 0..1 range for easier processing
        val_01 = (value + 1.0) / 2.0  # -1..1 -> 0..1
        dz_01 = deadzone  # Deadzone as fraction of full range

        if val_01 < dz_01:
            return -1.0  # Output minimum
        else:
            # Scale remaining range
            scaled = (val_01 - dz_01) / (1.0 - dz_01)
            return scaled * 2.0 - 1.0  # Back to -1..1

    def _apply_right_deadzone(self, value: float, deadzone: float) -> float:
        """Apply deadzone at maximum (right/top)."""
        val_01 = (value + 1.0) / 2.0  # -1..1 -> 0..1
        dz_01 = deadzone

        if val_01 > (1.0 - dz_01):
            return 1.0  # Output maximum
        else:
            # Scale remaining range
            scaled = val_01 / (1.0 - dz_01)
            return scaled * 2.0 - 1.0  # Back to -1..1

    def _apply_ends_deadzone(self, value: float, deadzone: float) -> float:
        """Apply deadzone at both ends."""
        val_01 = (value + 1.0) / 2.0  # -1..1 -> 0..1
        dz_half = deadzone / 2.0  # Split deadzone between both ends

        if val_01 < dz_half:
            return -1.0  # Output minimum
        elif val_01 > (1.0 - dz_half):
            return 1.0  # Output maximum
        else:
            # Scale middle range to full output
            scaled = (val_01 - dz_half) / (1.0 - deadzone)
            return scaled * 2.0 - 1.0  # Back to -1..1
    
    def _apply_curve(self, value: float, curve: str) -> float:
        """
        Apply response curve to normalized value.
        
        Args:
            value: Normalized input (-1.0 to 1.0)
            curve: Curve type ('linear', 'smooth', 'aggressive', 'soft', 'ultra_fine', 's_curve', 'exponential')
            
        Returns:
            Curved value (-1.0 to 1.0)
        """
        sign = 1.0 if value >= 0 else -1.0
        abs_val = abs(value)
        
        if curve == "linear":
            return value
        
        elif curve == "aggressive":
            # Square root - more sensitive near center, less at extremes
            # Good for precise control with quick authority
            return sign * math.pow(abs_val, 0.5)
        
        elif curve == "soft":
            # Squared - less sensitive near center, more at extremes
            # Good for large aircraft needing fine adjustments
            return sign * math.pow(abs_val, 2.0)
        
        elif curve == "smooth":
            # x^1.5 - gentle acceleration
            # Good balance for general use
            return sign * math.pow(abs_val, 1.5)
        
        elif curve == "ultra_fine":
            # Cubic - maximum precision near center
            # For when you need very fine adjustments
            return sign * math.pow(abs_val, 3.0)
        
        elif curve == "s_curve":
            # Smoothstep function - eases in and out
            # Natural feeling movement
            t = abs_val
            return sign * (t * t * (3.0 - 2.0 * t))
        
        elif curve == "exponential":
            # Exponential - slow start, fast finish
            # Good for throttle/brake feel
            return sign * ((math.exp(abs_val) - 1) / (math.e - 1))
        
        return value  # Fallback
    def on_dataref_update(self, dataref: str, value: float) -> None:
        """Called when a dataref value changes (from X-Plane or manual write)."""
        # Strip prefixes for internal logic state
        raw_dataref = dataref
        if ":" in dataref:
            raw_dataref = dataref.split(":", 1)[1]
            
        self._current_values[raw_dataref] = value
        log.debug("InputMapper state update: %s = %.4f", raw_dataref, value)

    # =========================================================================
    # Input Processing
    # =========================================================================
    
    async def process_input(self, device_port: str, input_key: str, value: float) -> None:
        """
        Process an input from a device.
        
        Args:
            device_port: The device ID (e.g., "COM3", "WINMM_0")
            input_key: The input identifier (e.g., "BTN_3", "AXIS_0")
            value: The input value (1/0 for buttons, -1..1 for axes)
        """
        mappings = self.get_mappings_for_input(input_key, device_port)
        
        if not mappings:
            log.debug("No mapping for input: %s from %s", input_key, device_port)
            return
        
        for mapping in mappings:
            await self._execute_mapping(mapping, value)
    
    async def _write_target(self, target: str, value: float):
        """Helper to write to X-Plane, LogicEngine, Virtual Variables, or Arduino Keys."""
        # 1. Resolve prefix
        raw_target = self._resolve_prefix(target)

        # 2. Try Logic Engine (Conditional Execution)
        if await self._try_logic_engine(raw_target, value):
            return

        # 3. Try Variable Store
        if self._try_variable_store(raw_target, value):
            return

        # 4. Handle ID: prefixed targets
        if self._handle_id_prefixed_target(target, value):
            return

        # 5. Try Arduino Output IDs
        if self._try_arduino_output_ids(raw_target, value):
            return

        # 6. Default to X-Plane
        await self._write_to_xplane(target, raw_target, value)

    def _resolve_prefix(self, target: str) -> str:
        """Resolve prefix from target string."""
        raw_target = target
        if ":" in target and not target.startswith("ID:"):  # ID: is handled separately below
            parts = target.split(":", 1)
            if len(parts) == 2:
                _, raw_target = parts
        return raw_target

    async def _try_logic_engine(self, raw_target: str, value: float) -> bool:
        """Try to write to the logic engine."""
        if self.logic_engine:
            block = next((b for b in self.logic_engine.get_blocks() if b.name == raw_target), None)
            if block:
                await self.logic_engine.trigger_block_manual(raw_target, value)
                return True
        return False

    def _try_variable_store(self, raw_target: str, value: float) -> bool:
        """Try to write to the variable store."""
        if self.variable_store and raw_target in self.variable_store.get_names():
            # Get existing entry to preserve type
            existing = self.variable_store.get_all().get(raw_target)
            v_type = existing.type if existing else None
            from core.variable_store import VariableType
            self.variable_store.update_value(raw_target, value, v_type or VariableType.VARIABLE_VIRTUAL)

            # Update internal tracker
            self._current_values[raw_target] = value
            return True
        return False

    def _handle_id_prefixed_target(self, target: str, value: float) -> bool:
        """Handle ID: prefixed targets."""
        if target.startswith("ID:"):
            # Target is a universal output ID key
            id_key = target[3:]
            if self.arduino_manager:
                self.arduino_manager.broadcast_by_key(id_key, value)
            return True
        return False

    def _try_arduino_output_ids(self, raw_target: str, value: float) -> bool:
        """Try to write to Arduino output IDs."""
        if self.arduino_manager:
            output_keys = self.arduino_manager.get_all_output_keys()
            if raw_target in output_keys:
                # Direct broadcast to hardware
                self.arduino_manager.on_dataref_update(raw_target, value)
                # Update internal tracker
                self._current_values[raw_target] = value
                return True
        return False

    async def _write_to_xplane(self, target: str, raw_target: str, value: float):
        """Write to X-Plane as default."""
        if self.xplane_conn and self.xplane_conn.connected:
            # For XP: prefixed targets, send the original target (with prefix) to xplane_conn
            # xplane_conn will handle the prefix appropriately
            # For non-prefixed targets, send as-is (they are assumed to be datarefs)
            await self.xplane_conn.write_dataref(target, value)
            # Update internal tracker with the raw target name (without XP: prefix if present)
            self._current_values[raw_target] = value

    async def _execute_mapping(self, mapping: InputMapping, value: float) -> None:
        """Execute a mapping action with multiple targets."""
        if not self.xplane_conn:
            return

        if mapping.action != InputAction.AXIS:
            met, _ = self._check_condition(mapping)
            if not met:
                return

        # Multi-target support
        targets_to_process = mapping.targets if mapping.targets else [TargetAction(mapping.target, mapping.value_on, mapping.value_off)]

        for target_obj in targets_to_process:
            await self._execute_single_target_action(mapping, target_obj, value)

        # Existing logic for Axis, Inc, Dec, Sequence...
        await self._execute_special_actions(mapping, targets_to_process[0].target, value)

        if self.on_mapping_triggered:
            self.on_mapping_triggered(mapping, value)

    async def _execute_single_target_action(self, mapping: InputMapping, target_obj: TargetAction, value: float) -> None:
        """Execute action for a single target."""
        try:
            if mapping.action == InputAction.COMMAND:
                await self._execute_command_action(target_obj, value)
            elif mapping.action == InputAction.DATAREF_SET:
                await self._execute_dataref_set_action(target_obj, value)
            elif mapping.action == InputAction.DATAREF_TOGGLE:
                await self._execute_dataref_toggle_action(target_obj, value)
            # ... other actions use target_obj.target instead of mapping.target
        except Exception as e:
            log.error("Action error on target %s: %s", target_obj.target, e)

    async def _execute_command_action(self, target_obj: TargetAction, value: float) -> None:
        """Execute a command action."""
        if value > 0:
            # Commands should be sent to X-Plane without XP: prefix
            command_target = target_obj.target
            if command_target.startswith("XP:"):
                command_target = command_target[3:]  # Remove "XP:" prefix
            # Also handle case where user might have selected a command from search
            # that doesn't have XP: prefix but is still in the dataref database as a command
            await self.xplane_conn.send_command(command_target)

    async def _execute_dataref_set_action(self, target_obj: TargetAction, value: float) -> None:
        """Execute a dataref set action."""
        new_val = target_obj.value_on if value > 0 else target_obj.value_off
        await self._write_target(target_obj.target, new_val)

    async def _execute_dataref_toggle_action(self, target_obj: TargetAction, value: float) -> None:
        """Execute a dataref toggle action."""
        if value > 0:
            # Get current from internal tracker or variable store
            curr = self._current_values.get(target_obj.target)
            if curr is None and self.variable_store:
                curr = self.variable_store.get_value(target_obj.target)

            curr = curr or 0.0
            new_val = 0.0 if curr > 0.5 else 1.0
            await self._write_target(target_obj.target, new_val)

    async def _execute_special_actions(self, mapping: InputMapping, main_target: str, value: float) -> None:
        """Execute special action types like axis, sequence, inc/dec."""
        if mapping.action == InputAction.AXIS:
            await self._execute_axis(mapping, value)
        elif mapping.action == InputAction.SEQUENCE:
            await self._execute_sequence(mapping, value)
        elif mapping.action in (InputAction.DATAREF_INC, InputAction.DATAREF_DEC):
            # INC/DEC still uses the first target in targets list for now
            await self._execute_dataref_inc_internal(mapping, main_target, value, 1 if mapping.action == InputAction.DATAREF_INC else -1)
    
    async def _execute_command(self, mapping: InputMapping, value: float) -> None:
        """Execute a command action."""
        # Only send command on button press (value > 0)
        if value > 0:
            await self.xplane_conn.send_command(mapping.target)
            log.info("Sent command: %s", mapping.target)
    
    async def _execute_dataref_set(self, mapping: InputMapping, value: float) -> None:
        """Execute a set-value action."""
        # Set to value_on on press, value_off on release
        new_value = mapping.value_on if value > 0 else mapping.value_off
        await self._write_target(mapping.target, new_value)
        # _write_target updates the internal tracker appropriately
        log.info("Set dataref: %s = %.2f", mapping.target, new_value)
    
    async def _execute_dataref_toggle(self, mapping: InputMapping, value: float) -> None:
        """Execute a toggle action."""
        # Toggle between 0 and 1 on press only
        if value > 0:
            current = self._current_values.get(mapping.target, 0)
            new_value = 0.0 if current > 0.5 else 1.0
            await self._write_target(mapping.target, new_value)
            # _write_target updates the internal tracker appropriately
            log.info("Toggled dataref: %s = %.2f", mapping.target, new_value)
    
    async def _execute_dataref_inc_internal(self, mapping: InputMapping, target: str, value: float, direction: int) -> None:
        """Execute an increment/decrement action on a specific target."""
        
        # Check if target is a command type
        is_command = False
        if self.dataref_manager:
            target_info = self.dataref_manager.get_dataref_info(target)
            is_command = target_info and target_info.get("type") == "command"
        
        # For commands, execute the command instead of incrementing/decrementing
        if is_command:
            await self._execute_command_for_encoder(target, direction, mapping)
            return
        
        # Regular dataref increment/decrement behavior
        current = self._current_values.get(target, 0)
        delta = 1.0 * mapping.increment * mapping.multiplier * direction # Use 1.0 typically for encoder tick
        # Note: mapping.increment logic might need value scaling if axis is used, but typically encoders send 1/0

        new_value = current + delta

        # Apply limits
        new_value = self._apply_value_limits(new_value, mapping)

        await self._write_target(target, new_value)
        # _write_target updates the internal tracker appropriately
        log.info("Incremented dataref: %s = %.2f (delta: %.2f)",
                target, new_value, delta)
    
    async def _execute_command_for_encoder(self, target: str, direction: int, mapping: InputMapping) -> None:
        """Execute a command for encoder input."""
        # Remove XP: prefix if present
        command_target = target
        if command_target.startswith("XP:"):
            command_target = command_target[3:]
        
        # Calculate execution count based on multiplier (rounded up, minimum 1)
        execution_count = max(1, math.ceil(mapping.multiplier))
        
        # Execute command multiple times with delays
        for i in range(execution_count):
            await self.xplane_conn.send_command(command_target)
            if i < execution_count - 1:
                await asyncio.sleep(mapping.command_delay_ms / 1000.0)
        
        log.info("Sent encoder command: %s %d times (multiplier: %.1f, delay: %dms, direction: %s)",
                 command_target, execution_count, mapping.multiplier,
                 mapping.command_delay_ms, "CW" if direction > 0 else "CCW")

    def _apply_value_limits(self, new_value: float, mapping: InputMapping) -> float:
        """Apply limits to the new value based on mapping configuration."""
        if mapping.wrap:
            return self._apply_wrapping_limits(new_value, mapping)
        else:
            return max(mapping.min_value, min(mapping.max_value, new_value))

    def _apply_wrapping_limits(self, new_value: float, mapping: InputMapping) -> float:
        """Apply wrapping limits to the new value."""
        value_range = mapping.max_value - mapping.min_value
        if new_value > mapping.max_value:
            return mapping.min_value + (new_value - mapping.max_value) % value_range
        elif new_value < mapping.min_value:
            return mapping.max_value - (mapping.min_value - new_value) % value_range
        return new_value

    async def _execute_dataref_inc(self, mapping: InputMapping, value: float, direction: int) -> None:
        """Stub for old method signature if needed."""
        await self._execute_dataref_inc_internal(mapping, mapping.target, value, direction)

    async def _execute_axis(self, mapping: InputMapping, value: float) -> None:
        """Execute an axis mapping."""
        # Process the axis value through calibration, deadzone, and curve
        output_value = self._apply_axis_processing(value, mapping)

        # Only send if changed significantly to avoid spam
        current = self._current_values.get(mapping.target, -999999)
        if abs(output_value - current) > 0.001:
            await self._write_target(mapping.target, output_value)
            # _write_target updates the internal tracker appropriately
            # log.debug("Axis %s -> %s = %.3f", mapping.input_key, mapping.target, output_value)
    
    async def _execute_sequence(self, mapping: InputMapping, value: float) -> None:
        """Execute a sequence of actions."""
        seq_key = f"{mapping.device_port}:{mapping.input_key}"
        
        if value > 0:
            # Button pressed - start sequence
            if seq_key in self._active_sequences:
                # Cancel any existing sequence for this input
                self._active_sequences[seq_key].cancel()
            
            # Start new sequence
            task = asyncio.create_task(
                self._run_sequence(mapping, seq_key)
            )
            self._active_sequences[seq_key] = task
        
        else:
            # Button released
            if seq_key in self._active_sequences:
                # Cancel repeat-while-held if active
                if mapping.sequence_repeat_while_held:
                    self._active_sequences[seq_key].cancel()
                    del self._active_sequences[seq_key]
                
                # Execute reverse sequence if enabled
                if mapping.sequence_reverse_on_release:
                    await self._run_sequence_reverse(mapping)
    
    async def _run_sequence(self, mapping: InputMapping, seq_key: str) -> None:
        """Run a sequence of actions."""
        try:
            while True:  # Loop for repeat-while-held
                should_break = await self._execute_sequence_steps(mapping)
                if should_break:
                    break

                # Small delay between repeats
                await asyncio.sleep(0.05)

        except asyncio.CancelledError:
            log.debug("Sequence cancelled")
            raise

        finally:
            # Clean up
            if seq_key in self._active_sequences:
                del self._active_sequences[seq_key]

    async def _execute_sequence_steps(self, mapping: InputMapping) -> bool:
        """Execute all steps in the sequence and return whether to break the loop."""
        for i, action in enumerate(mapping.sequence_actions):
            # Check condition before each step if stop-on-error is enabled
            if mapping.sequence_stop_on_error:
                condition_met, reason = self._check_condition(mapping)
                if not condition_met:
                    log.info("Sequence aborted at step %d: %s", i + 1, reason)
                    return True  # Should break

            # Execute the action
            await self._execute_sequence_action(action, i + 1)

            # Wait for delay before next action
            if action.delay_ms > 0:
                await asyncio.sleep(action.delay_ms / 1000.0)

        log.info("Sequence completed: %d actions", len(mapping.sequence_actions))

        # Only repeat if configured
        if not mapping.sequence_repeat_while_held:
            return True  # Should break

        return False  # Should continue
    
    async def _run_sequence_reverse(self, mapping: InputMapping) -> None:
        """Run sequence in reverse order with opposite values."""
        for i, action in enumerate(reversed(mapping.sequence_actions)):
            # Create reversed action (invert value for datarefs)
            if action.action_type == "dataref":
                # Simple toggle logic: 1 -> 0, 0 -> 1
                reversed_value = 0.0 if action.value > 0.5 else 1.0
                reversed_action = SequenceAction(
                    action_type=action.action_type,
                    target=action.target,
                    value=reversed_value,
                    delay_ms=action.delay_ms
                )
            else:
                # Commands don't have a reverse
                reversed_action = action
            
            await self._execute_sequence_action(reversed_action, i + 1)
            
            if reversed_action.delay_ms > 0:
                await asyncio.sleep(reversed_action.delay_ms / 1000.0)
    
    async def _execute_sequence_action(self, action: SequenceAction, step_num: int) -> None:
        """Execute a single sequence action."""
        try:
            # Handle prefix for commands
            if action.action_type == "command":
                # Commands should be sent to X-Plane without XP: prefix
                command_target = action.target
                if command_target.startswith("XP:"):
                    command_target = command_target[3:]  # Remove "XP:" prefix

                await self.xplane_conn.send_command(command_target)
                log.info("Sequence step %d: CMD %s", step_num, command_target)
            else:
                await self._write_target(action.target, action.value)
                log.info("Sequence step %d: DREF %s = %.2f", step_num, action.target, action.value)

        except Exception as e:
            log.error("Sequence step %d failed: %s", step_num, e)
