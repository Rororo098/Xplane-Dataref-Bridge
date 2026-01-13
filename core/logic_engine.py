from __future__ import annotations
import logging
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from core.input_mapper import ConditionRule, LogicGate
from core.variable_store import VariableType

log = logging.getLogger(__name__)


@dataclass
class LogicOutput:
    """An action to perform when logic is true."""
    target: str  # Dataref or Variable Name
    value: float
    action_type: str = "set"  # 'set', 'toggle', 'increment'

    def to_dict(self):
        return {"target": self.target, "value": self.value, "action_type": self.action_type}

    @classmethod
    def from_dict(cls, data):
        return cls(target=data.get("target", ""), value=data.get("value", 0.0), action_type=data.get("action_type", "set"))


@dataclass
class LogicBlock:
    """
    A Virtual Variable / Logic Rule.
    Evaluates inputs based on a logic gate and triggers outputs.
    """
    name: str
    description: str = ""
    enabled: bool = True
    
    # Inputs: The Datarefs/Variables to read
    conditions: List[ConditionRule] = field(default_factory=list)
    
    # Logic: How to combine conditions
    logic_gate: str = "AND"  # AND, OR, XOR, etc.
    
    # Outputs: What to write to
    outputs: List[LogicOutput] = field(default_factory=list)
    
    initial_value: Optional[float] = None
    output_key: str = ""  # Key for Arduino communication
    
    # Internal state tracking (for toggle/debounce)
    _last_state: bool = False

    def evaluate(self, current_datarefs: Dict[str, float]) -> bool:
        """
        Evaluate if conditions are met.
        Returns True if logic met and state changed (or met, depending on trigger type).
        """
        if not self.enabled:
            return False

        # 1. Evaluate individual conditions
        results = self._evaluate_conditions(current_datarefs)

        if not results:
            return True  # No conditions means always true

        # 2. Apply Logic Gate
        return self._apply_logic_gate(results)

    def _evaluate_conditions(self, current_datarefs: Dict[str, float]) -> List[bool]:
        """Evaluate all conditions and return results."""
        results = []
        for rule in self.conditions:
            if not rule.enabled:
                continue

            val = current_datarefs.get(rule.dataref)
            if val is None:
                log.debug("LogicBlock '%s': Missing dataref %s", self.name, rule.dataref)
                return []  # Treat missing dataref as False to be safe

            res = self._evaluate_single_condition(rule, val)
            results.append(res)

        return results

    def _evaluate_single_condition(self, rule: ConditionRule, val: float) -> bool:
        """Evaluate a single condition."""
        if rule.operator == "<":
            return val < rule.value
        elif rule.operator == "<=":
            return val <= rule.value
        elif rule.operator == ">":
            return val > rule.value
        elif rule.operator == ">=":
            return val >= rule.value
        elif rule.operator == "==":
            return abs(val - rule.value) < 0.001
        elif rule.operator == "!=":
            return abs(val - rule.value) >= 0.001
        return False  # Default fallback

    def _apply_logic_gate(self, results: List[bool]) -> bool:
        """Apply the logic gate to the results."""
        gate = self.logic_gate.upper()
        true_count = sum(results)

        if gate == "AND":
            return all(results)
        elif gate == "OR":
            return any(results)
        elif gate == "NAND":
            return not all(results)
        elif gate == "NOR":
            return not any(results)
        elif gate == "XOR":
            return (true_count % 2) == 1
        elif gate == "XNOR":
            return (true_count % 2) == 0

        return False  # Default fallback

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "conditions": [c.to_dict() for c in self.conditions],
            "logic_gate": self.logic_gate,
            "outputs": [o.to_dict() for o in self.outputs],
            "initial_value": self.initial_value,
            "output_key": self.output_key
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            conditions=[ConditionRule.from_dict(c) for c in data.get("conditions", [])],
            logic_gate=data.get("logic_gate", "AND"),
            outputs=[LogicOutput.from_dict(o) for o in data.get("outputs", [])],
            initial_value=data.get("initial_value"),
            output_key=data.get("output_key", "")
        )


class LogicEngine:
    """Manages all Logic Blocks (Virtual Variables)."""
    
    def __init__(self, xplane_conn, input_mapper, arduino_manager=None):
        self.xplane_conn = xplane_conn
        self.input_mapper = input_mapper # To get current dataref values
        self.arduino_manager = arduino_manager

        self._blocks: List[LogicBlock] = []
        self._values: Dict[str, float] = {}
        self.variable_store = None # Will be set by MainWindow
        self._initialized = False  # Flag to prevent re-initialization
        self._tasks = []  # Store tasks to prevent garbage collection

    def add_block(self, block: LogicBlock):
        # Check if block already exists, replace if it does
        existing_idx = None
        for i, existing_block in enumerate(self._blocks):
            if existing_block.name == block.name:
                existing_idx = i
                break

        if existing_idx is not None:
            # Replace existing block
            self._blocks[existing_idx] = block
        else:
            # Add new block
            self._blocks.append(block)

        # Register hardware mapping if set
        if block.output_key and self.arduino_manager:
            self.arduino_manager.set_universal_mapping(block.name, block.output_key)

    def remove_block(self, name: str):
        # 1. Clear hardware mapping if exists
        if self.arduino_manager:
            self.arduino_manager.set_universal_mapping(name, "")
            
        # 2. Remove from internal list
        self._blocks = [b for b in self._blocks if b.name != name]

    def get_blocks(self) -> List[LogicBlock]:
        return self._blocks

    def get_all_output_keys(self) -> List[str]:
        """Get list of all unique output keys (IDs) used in logic blocks."""
        keys = set()
        for b in self._blocks:
            if b.output_key:
                keys.add(b.output_key.strip())
        return sorted(keys)

    def clear_blocks(self):
        """Remove all logic blocks."""
        self._blocks = []
        self._values = {}

    async def sync_initial_values(self):
        """Send all initial values to X-Plane/VariableStore."""
        if not self.xplane_conn or not self.xplane_conn.connected:
            return

        log.info("Performing initial values synchronization for Logic Blocks...")
        for block in self._blocks:
            if block.enabled and block.initial_value is not None:
                # Update variable store
                if self.variable_store:
                    from core.variable_store import VariableType
                    self.variable_store.update_value(
                        block.name, 
                        block.initial_value, 
                        VariableType.VARIABLE_VIRTUAL,
                        "Initial value sync"
                    )
                
                # Force execute outputs with initial value
                await self._execute_outputs(block)
                log.info("Init sync logic: %s = %.2f", block.name, block.initial_value)

    def process_tick(self):
        """
        Called periodically (or on dataref update) to evaluate all logic blocks.
        """
        # Get current snapshot of state
        state = self._get_current_state()

        for block in self._blocks:
            if not block.enabled:
                continue

            self._process_single_block(block, state)

    def _get_current_state(self) -> Dict[str, float]:
        """Get current state from input mapper and variable store."""
        state = {}
        if hasattr(self.input_mapper, '_current_values'):
            state.update(self.input_mapper._current_values)
        if self.variable_store:
            for v_name, entry in self.variable_store.get_all().items():
                state[v_name] = entry.value
        return state

    def _process_single_block(self, block: LogicBlock, state: Dict[str, float]) -> None:
        """Process a single logic block."""
        is_met = block.evaluate(state)
        val = 1.0 if is_met else 0.0

        # Sync to VariableStore for live monitoring
        if block.name and self.variable_store:
            self.variable_store.update_value(block.name, val, VariableType.VARIABLE_VIRTUAL)

        if is_met:
            task = asyncio.create_task(self._execute_outputs(block))
            self._tasks.append(task)  # Store task to prevent garbage collection

        # 3. Notify Arduino if output key is set
        if block.output_key and self.arduino_manager:
            self._notify_arduino(block, val)

    def _notify_arduino(self, block: LogicBlock, val: float) -> None:
        """Notify Arduino about block state change."""
        if block.name:
            # Named block: use mapping system
            self.arduino_manager.on_dataref_update(block.name, val)
        else:
            # Headless block: broadcast directly by key
            # This allows identifying blocks by Output Key in the logs too
            self.arduino_manager.broadcast_by_key(block.output_key, val)

    async def trigger_block_manual(self, name: str):
        """
        Manually trigger a logic block's outputs from an external input.
        ONLY executes if the block's conditions are currently met.
        """
        block = self._find_block_by_name(name)
        if not block or not block.enabled:
            return

        state = self._get_current_state()
        is_met = block.evaluate(state)

        await self._handle_trigger_result(name, block, is_met)

    def _find_block_by_name(self, name: str) -> Optional[LogicBlock]:
        """Find a block by its name."""
        return next((b for b in self._blocks if b.name == name), None)

    async def _handle_trigger_result(self, name: str, block: LogicBlock, is_met: bool) -> None:
        """Handle the result of the trigger evaluation."""
        if is_met:
            log.info("Logic Block '%s' manual trigger: Conditions MET. Executing outputs.", name)
            await self._execute_outputs(block)
        else:
            log.info("Logic Block '%s' manual trigger: Conditions NOT MET. Ignoring.", name)

    async def _execute_outputs(self, block: LogicBlock):
        """Perform actions defined in the block outputs."""
        for out in block.outputs:
            await self._execute_single_output(out)

    async def _execute_single_output(self, out: LogicOutput):
        """Execute a single output action."""
        target = out.target
        val = out.value

        # 1. Try Variable Store
        if self.variable_store and target in self.variable_store.get_names():
            await self._handle_variable_store_update(target, val)
            return

        # 2. Try X-Plane
        await self._handle_xplane_update(out, target, val)

    def _handle_variable_store_update(self, target: str, val: float):
        """Handle updating the variable store."""
        existing = self.variable_store.get_all().get(target)
        from core.variable_store import VariableType
        self.variable_store.update_value(target, val, existing.type if existing else VariableType.VARIABLE_VIRTUAL)

        # Notify Arduino if it's monitoring this variable
        if self.arduino_manager:
            self.arduino_manager.on_dataref_update(target, val)

    async def _handle_xplane_update(self, out: LogicOutput, target: str, val: float):
        """Handle updating X-Plane."""
        if self.xplane_conn and self.xplane_conn.connected:
            if out.action_type == "set":
                await self.xplane_conn.write_dataref(target, val)
            elif out.action_type == "toggle":
                curr = self.input_mapper.get_current_value(target) or 0.0
                await self.xplane_conn.write_dataref(target, 0.0 if curr > 0.5 else 1.0)
            # Update internal tracker after successful write
            self.input_mapper.update_current_value(target, val)