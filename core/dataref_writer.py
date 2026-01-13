
"""
Dataref Writer Module
Handles writing different dataref types (byte, int, float, bool, arrays, commands) via OUTPUT ID.
"""

import logging
import asyncio
import struct
from typing import Optional, Dict, Any

log = logging.getLogger(__name__)


class DatarefWriter:
    """Handles writing different dataref types to X-Plane."""

    def __init__(self, xplane_connection, dataref_manager):
        """
        Initialize the DatarefWriter.

        Args:
            xplane_connection: XPlaneConnection instance for communicating with X-Plane
            dataref_manager: DatarefManager for getting dataref information
        """
        self.xplane_conn = xplane_connection
        self.dataref_manager = dataref_manager

        # Cache for OUTPUT ID to dataref mappings
        self.output_id_mappings: Dict[str, str] = {}  # OUTPUT ID -> dataref name

    def register_output_id(self, output_id: str, dataref_name: str) -> None:
        """Register an OUTPUT ID mapping to a dataref."""
        self.output_id_mappings[output_id.upper()] = dataref_name
        log.info(f"Registered OUTPUT ID '{output_id}' -> '{dataref_name}'")

    def unregister_output_id(self, output_id: str) -> None:
        """Unregister an OUTPUT ID mapping."""
        if output_id.upper() in self.output_id_mappings:
            del self.output_id_mappings[output_id.upper()]
            log.info(f"Unregistered OUTPUT ID '{output_id}'")

    async def write_by_output_id(self, output_id: str, value: Any) -> bool:
        """
        Write to a dataref using its OUTPUT ID.

        Args:
            output_id: The OUTPUT ID assigned to the dataref
            value: The value to write (type depends on dataref type)

        Returns:
            True if successful, False otherwise
        """
        output_id = output_id.upper()
        if output_id not in self.output_id_mappings:
            log.warning(f"OUTPUT ID '{output_id}' not registered")
            return False

        dataref_name = self.output_id_mappings[output_id]
        info = self.dataref_manager.get_dataref_info(dataref_name)

        if not info:
            log.warning(f"No information available for dataref '{dataref_name}'")
            return False

        dataref_type = info.get("type", "float")

        # Handle different dataref types
        if dataref_type == "command":
            return await self._execute_command(dataref_name)
        elif "byte[" in dataref_type:
            return await self._write_byte_array(dataref_name, value)
        elif "int[" in dataref_type:
            return await self._write_int_array(dataref_name, value)
        elif "float[" in dataref_type:
            return await self._write_float_array(dataref_name, value)
        elif "string" in dataref_type or "byte" in dataref_type:
            return await self._write_string(dataref_name, value)
        elif dataref_type in ["int", "float", "bool"]:
            return await self._write_scalar(dataref_name, value, dataref_type)
        else:
            # Default to float
            return await self._write_scalar(dataref_name, float(value), "float")

    async def _execute_command(self, command_name: str) -> bool:
        """Execute a command dataref (has no value, just triggers function)."""
        if not self.xplane_conn:
            log.error("Not connected to X-Plane")
            return False

        try:
            result = await self.xplane_conn.send_command(command_name)
            if result:
                log.info(f"Executed command: {command_name}")
            return result
        except Exception as e:
            log.error(f"Failed to execute command '{command_name}': {e}")
            return False

    async def _write_scalar(self, dataref_name: str, value: float, dataref_type: str) -> bool:
        """Write a scalar value (int, float, bool) to a dataref."""
        if not self.xplane_conn:
            log.error("Not connected to X-Plane")
            return False

        try:
            # Convert bool to float if needed
            if dataref_type == "bool":
                value = 1.0 if value else 0.0
            elif dataref_type == "int":
                value = float(int(value))

            result = await self.xplane_conn.write_dataref(dataref_name, value)
            if result:
                log.info(f"Wrote {dataref_type} {dataref_name} = {value}")
            return result
        except Exception as e:
            log.error(f"Failed to write scalar dataref '{dataref_name}': {e}")
            return False

    async def _write_byte_array(self, dataref_name: str, value: Any) -> bool:
        """
        Write to a byte array dataref.

        Args:
            dataref_name: Name of the dataref (e.g., sim/aircraft/view/acf_ICAO)
            value: Can be:
                - String: Each character is converted to a byte
                - List of ints: Each int is written as a byte
                - Dict with 'indices' and 'values': Specific indices to write
        """
        if not self.xplane_conn:
            log.error("Not connected to X-Plane")
            return False

        try:
            # Parse array size from dataref name
            import re
            m = re.search(r'byte\[(\d+)\]', dataref_name)
            if not m:
                # Try to get from dataref info
                info = self.dataref_manager.get_dataref_info(dataref_name)
                dtype = info.get("type", "") if info else ""
                m = re.search(r'\[(\d+)\]', dtype)

            array_size = int(m.group(1)) if m else 260  # Default to 260 if not found

            base_name = dataref_name.split("[")[0]

            # Handle different input types
            if isinstance(value, str):
                # Convert string to bytes
                for i, char_code in enumerate(value):
                    if i >= array_size:
                        break
                    await self.xplane_conn.write_dataref(
                        f"{base_name}[{i}]", 
                        float(ord(char_code))
                    )

                # Null terminate
                if len(value) < array_size:
                    await self.xplane_conn.write_dataref(
                        f"{base_name}[{len(value)}]", 
                        0.0
                    )

            elif isinstance(value, dict) and "indices" in value and "values" in value:
                # Write specific indices
                indices = value["indices"]
                values = value["values"]

                for i, idx in enumerate(indices):
                    if idx >= array_size:
                        continue
                    await self.xplane_conn.write_dataref(
                        f"{base_name}[{idx}]", 
                        float(values[i])
                    )

            elif isinstance(value, list):
                # Write all values from list
                for i, val in enumerate(value):
                    if i >= array_size:
                        break
                    await self.xplane_conn.write_dataref(
                        f"{base_name}[{i}]", 
                        float(val)
                    )

            log.info(f"Wrote byte array {dataref_name}")
            return True

        except Exception as e:
            log.error(f"Failed to write byte array '{dataref_name}': {e}")
            return False

    async def _write_int_array(self, dataref_name: str, value: Any) -> bool:
        """
        Write to an int array dataref.

        Args:
            dataref_name: Name of the dataref
            value: Can be:
                - List of ints: Each int is written to its index
                - Dict with 'indices' and 'values': Specific indices to write
        """
        if not self.xplane_conn:
            log.error("Not connected to X-Plane")
            return False

        try:
            # Parse array size from dataref name
            import re
            m = re.search(r'int\[(\d+)\]', dataref_name)
            if not m:
                # Try to get from dataref info
                info = self.dataref_manager.get_dataref_info(dataref_name)
                dtype = info.get("type", "") if info else ""
                m = re.search(r'\[(\d+)\]', dtype)

            array_size = int(m.group(1)) if m else 10  # Default to 10 if not found

            base_name = dataref_name.split("[")[0]

            # Handle different input types
            if isinstance(value, dict) and "indices" in value and "values" in value:
                # Write specific indices
                indices = value["indices"]
                values = value["values"]

                for i, idx in enumerate(indices):
                    if idx >= array_size:
                        continue
                    await self.xplane_conn.write_dataref(
                        f"{base_name}[{idx}]", 
                        float(int(values[i]))
                    )

            elif isinstance(value, list):
                # Write all values from list
                for i, val in enumerate(value):
                    if i >= array_size:
                        break
                    await self.xplane_conn.write_dataref(
                        f"{base_name}[{i}]", 
                        float(int(val))
                    )

            log.info(f"Wrote int array {dataref_name}")
            return True

        except Exception as e:
            log.error(f"Failed to write int array '{dataref_name}': {e}")
            return False

    async def _write_float_array(self, dataref_name: str, value: Any) -> bool:
        """
        Write to a float array dataref.

        Args:
            dataref_name: Name of the dataref
            value: Can be:
                - List of floats: Each float is written to its index
                - Dict with 'indices' and 'values': Specific indices to write
        """
        if not self.xplane_conn:
            log.error("Not connected to X-Plane")
            return False

        try:
            # Parse array size from dataref name
            import re
            m = re.search(r'float\[(\d+)\]', dataref_name)
            if not m:
                # Try to get from dataref info
                info = self.dataref_manager.get_dataref_info(dataref_name)
                dtype = info.get("type", "") if info else ""
                m = re.search(r'\[(\d+)\]', dtype)

            array_size = int(m.group(1)) if m else 10  # Default to 10 if not found

            base_name = dataref_name.split("[")[0]

            # Handle different input types
            if isinstance(value, dict) and "indices" in value and "values" in value:
                # Write specific indices
                indices = value["indices"]
                values = value["values"]

                for i, idx in enumerate(indices):
                    if idx >= array_size:
                        continue
                    await self.xplane_conn.write_dataref(
                        f"{base_name}[{idx}]", 
                        float(values[i])
                    )

            elif isinstance(value, list):
                # Write all values from list
                for i, val in enumerate(value):
                    if i >= array_size:
                        break
                    await self.xplane_conn.write_dataref(
                        f"{base_name}[{i}]", 
                        float(val)
                    )

            log.info(f"Wrote float array {dataref_name}")
            return True

        except Exception as e:
            log.error(f"Failed to write float array '{dataref_name}': {e}")
            return False

    async def _write_string(self, dataref_name: str, value: str) -> bool:
        """
        Write a string to a byte[n] dataref.

        Args:
            dataref_name: Name of the dataref
            value: String value to write
        """
        if not self.xplane_conn:
            log.error("Not connected to X-Plane")
            return False

        try:
            # Parse array size from dataref name
            import re
            m = re.search(r'\[(\d+)\]', dataref_name)
            array_size = int(m.group(1)) if m else 260  # Default to 260 if not found

            # Use the existing write_dataref_string method
            result = await self.xplane_conn.write_dataref_string(
                dataref_name, 
                value, 
                max_len=array_size
            )

            if result:
                log.info(f"Wrote string to {dataref_name}: '{value}'")
            return result

        except Exception as e:
            log.error(f"Failed to write string to '{dataref_name}': {e}")
            return False
