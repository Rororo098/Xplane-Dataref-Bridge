from typing import List, Dict
from core.logic_engine import LogicBlock, LogicOutput
from core.input_mapper import ConditionRule

def get_templates() -> Dict[str, LogicBlock]:
    """Returns a dictionary of common logic templates."""
    templates = {}

    # 1. Gear Moving (Transit) Light
    # True if gear is between 0.01 and 0.99 (not fully up, not fully down)
    gear_transit = LogicBlock(
        name="GEAR_TRANSIT",
        description="Active when gear is moving (between locked positions)",
        logic_gate="AND",
        conditions=[
            ConditionRule(dataref="sim/cockpit2/controls/gear_handle_down", operator="==", value=1.0), # Example: check handle
            ConditionRule(dataref="sim/flightmodel2/gear/deploy_ratio[0]", operator=">", value=0.01),
            ConditionRule(dataref="sim/flightmodel2/gear/deploy_ratio[0]", operator="<", value=0.99)
        ],
        output_key="GEAR_TRANSIT_LED"
    )
    templates["Gear Transit Light"] = gear_transit

    # 2. Master Warning / Caution Blinker
    # Simplistic blinker logic usually requires time, but we can do static logic here
    # e.g. Warning is active
    master_warning = LogicBlock(
        name="MASTER_WARNING_ACTIVE",
        description="Active if any master warning is triggered",
        logic_gate="OR",
        conditions=[
            ConditionRule(dataref="sim/cockpit2/annunciators/master_warning", operator="==", value=1.0),
            ConditionRule(dataref="sim/cockpit2/annunciators/master_caution", operator="==", value=1.0)
        ],
        output_key="WARNING_LED"
    )
    templates["Master Warning/Caution"] = master_warning

    # 3. Flaps Transit
    flaps_transit = LogicBlock(
        name="FLAPS_TRANSIT",
        description="Active when flaps are moving between positions",
        logic_gate="AND",
        conditions=[
             ConditionRule(dataref="sim/flightmodel2/controls/flap_handle_deploy_ratio", operator="!=", value=0.0), # Not at target? 
             # Simpler: if actual ratio != handle ratio
        ]
    )
    # Flaps transit is hard because we need two drefs.
    # Let's do a simpler one: Park Brake Set
    park_brake = LogicBlock(
        name="PARK_BRAKE_ON",
        description="Active when parking brake is set",
        conditions=[
            ConditionRule(dataref="sim/flightmodel/controls/parkbrake", operator=">", value=0.5)
        ],
        output_key="PARK_BRAKE_LED"
    )
    templates["Parking Brake LED"] = park_brake

    return templates
