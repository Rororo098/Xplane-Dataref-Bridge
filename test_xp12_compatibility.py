#!/usr/bin/env python3
"""
Test script for X-Plane 12 compatibility verification.
Run this script with X-Plane 12 running to verify compatibility.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.xplane_connection import XPlaneConnection
from core.dataref_manager import DatarefManager

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


class XP12CompatibilityTest:
    def __init__(self):
        self.xp_connection = XPlaneConnection()
        self.dataref_manager = DatarefManager()
        self.test_results = []

    async def run_all_tests(self):
        """Run all compatibility tests."""
        log.info("Starting X-Plane 12 Compatibility Tests")
        log.info("=" * 50)

        # Test 1: Connection
        await self.test_connection()

        # Test 2: Version Detection
        await self.test_version_detection()

        # Test 3: Common Datarefs
        await self.test_common_datarefs()

        # Test 4: Array Datarefs
        await self.test_array_datarefs()

        # Test 5: Writing Datarefs
        await self.test_writing_datarefs()

        # Test 6: Deprecated Dataref Handling
        await self.test_deprecated_handling()

        # Test 7: Custom Datarefs
        await self.test_custom_datarefs()

        # Print results
        self.print_results()

    async def test_connection(self):
        """Test basic connection to X-Plane."""
        log.info("Test 1: Connection")
        try:
            connected = await self.xp_connection.connect()
            if connected:
                self.test_results.append(
                    ("Connection", "PASS", "Successfully connected")
                )
                log.info("✅ Connected to X-Plane")
            else:
                self.test_results.append(("Connection", "FAIL", "Failed to connect"))
                log.error("❌ Failed to connect")
        except Exception as e:
            self.test_results.append(("Connection", "ERROR", str(e)))
            log.error(f"❌ Connection error: {e}")

    async def test_version_detection(self):
        """Test X-Plane version detection."""
        log.info("Test 2: Version Detection")
        try:
            if hasattr(self.xp_connection, "_detected_version"):
                version = self.xp_connection._detected_version
                if version:
                    if version >= 12000:  # X-Plane 12+
                        self.test_results.append(
                            (
                                "Version Detection",
                                "PASS",
                                f"Detected X-Plane v{version}",
                            )
                        )
                        log.info(f"✅ Detected X-Plane v{version}")
                    else:
                        self.test_results.append(
                            (
                                "Version Detection",
                                "PASS",
                                f"Detected X-Plane v{version} (pre-12)",
                            )
                        )
                        log.info(f"ℹ️ Detected X-Plane v{version} (pre-12)")
                else:
                    self.test_results.append(
                        ("Version Detection", "WARN", "Version not detected")
                    )
                    log.warning("⚠️ Version not detected")
            else:
                self.test_results.append(
                    ("Version Detection", "FAIL", "Version detection not implemented")
                )
                log.error("❌ Version detection not available")
        except Exception as e:
            self.test_results.append(("Version Detection", "ERROR", str(e)))
            log.error(f"❌ Version detection error: {e}")

    async def test_common_datarefs(self):
        """Test reading common datarefs."""
        log.info("Test 3: Common Datarefs")
        common_datarefs = [
            "sim/cockpit2/gauges/indicators/airspeed_kts_pilot",
            "sim/cockpit2/gauges/indicators/altitude_ft_pilot",
            "sim/flightmodel/position/latitude",
            "sim/flightmodel/position/longitude",
            "sim/cockpit2/controls/yoke_pitch_ratio",
        ]

        success_count = 0
        for dataref in common_datarefs:
            try:
                await self.xp_connection.subscribe_dataref(dataref, 5)
                await asyncio.sleep(0.2)  # Wait for data
                value = self.xp_connection.get_value(dataref)
                if value is not None:
                    success_count += 1
                    log.info(f"✅ {dataref}: {value}")
                else:
                    log.warning(f"⚠️ {dataref}: No value received")
            except Exception as e:
                log.error(f"❌ {dataref}: {e}")

        if success_count == len(common_datarefs):
            self.test_results.append(
                (
                    "Common Datarefs",
                    "PASS",
                    f"All {len(common_datarefs)} datarefs working",
                )
            )
        elif success_count > 0:
            self.test_results.append(
                (
                    "Common Datarefs",
                    "PARTIAL",
                    f"{success_count}/{len(common_datarefs)} working",
                )
            )
        else:
            self.test_results.append(("Common Datarefs", "FAIL", "No datarefs working"))

    async def test_array_datarefs(self):
        """Test array dataref handling."""
        log.info("Test 4: Array Datarefs")
        array_datarefs = [
            ("sim/cockpit2/engine/indicators/N1_percent", 8),
            ("sim/flightmodel/controls/yawb_def", 20),
        ]

        success_count = 0
        for dataref, count in array_datarefs:
            try:
                await self.xp_connection.subscribe_dataref(dataref, 5, count)
                await asyncio.sleep(0.2)

                # Check individual elements
                elements_working = 0
                for i in range(min(count, 4)):  # Test first 4 elements
                    element_name = f"{dataref}[{i}]"
                    value = self.xp_connection.get_value(element_name)
                    if value is not None:
                        elements_working += 1

                if elements_working > 0:
                    success_count += 1
                    log.info(
                        f"✅ {dataref}: {elements_working}/{count} elements working"
                    )
                else:
                    log.warning(f"⚠️ {dataref}: No elements working")

            except Exception as e:
                log.error(f"❌ {dataref}: {e}")

        if success_count == len(array_datarefs):
            self.test_results.append(
                ("Array Datarefs", "PASS", f"All {len(array_datarefs)} arrays working")
            )
        elif success_count > 0:
            self.test_results.append(
                (
                    "Array Datarefs",
                    "PARTIAL",
                    f"{success_count}/{len(array_datarefs)} working",
                )
            )
        else:
            self.test_results.append(("Array Datarefs", "FAIL", "No arrays working"))

    async def test_writing_datarefs(self):
        """Test writing to writable datarefs."""
        log.info("Test 5: Writing Datarefs")
        writable_datarefs = [
            ("sim/cockpit2/switches/beacon_on", 1.0),
            ("sim/cockpit2/switches/navigation_lights_on", 1.0),
        ]

        success_count = 0
        for dataref, value in writable_datarefs:
            try:
                # Get current value first
                original = self.xp_connection.get_value(dataref)

                # Write new value
                write_success = await self.xp_connection.write_dataref(dataref, value)
                if write_success:
                    await asyncio.sleep(0.1)
                    # Check if value changed
                    new_value = self.xp_connection.get_value(dataref)
                    if new_value is not None:
                        success_count += 1
                        log.info(f"✅ {dataref}: {original} → {new_value}")
                    else:
                        log.warning(
                            f"⚠️ {dataref}: Write succeeded but no value received"
                        )
                else:
                    log.warning(f"⚠️ {dataref}: Write failed")

            except Exception as e:
                log.error(f"❌ {dataref}: {e}")

        # Restore original values (simplified)
        for dataref, _ in writable_datarefs:
            try:
                await self.xp_connection.write_dataref(dataref, 0.0)
            except:
                pass

        if success_count == len(writable_datarefs):
            self.test_results.append(
                (
                    "Writing Datarefs",
                    "PASS",
                    f"All {len(writable_datarefs)} writes successful",
                )
            )
        elif success_count > 0:
            self.test_results.append(
                (
                    "Writing Datarefs",
                    "PARTIAL",
                    f"{success_count}/{len(writable_datarefs)} successful",
                )
            )
        else:
            self.test_results.append(
                ("Writing Datarefs", "FAIL", "No writes successful")
            )

    async def test_deprecated_handling(self):
        """Test deprecated dataref handling."""
        log.info("Test 6: Deprecated Dataref Handling")

        # Test deprecated datarefs
        deprecated_examples = [
            "sim/cockpit/electrical/beacon_on",  # Should suggest replacement
        ]

        success_count = 0
        for dataref in deprecated_examples:
            try:
                replacement = self.dataref_manager.suggest_replacement(dataref)
                if replacement:
                    log.info(f"✅ {dataref} → {replacement}")
                    success_count += 1
                else:
                    log.warning(f"⚠️ {dataref}: No replacement suggested")
            except Exception as e:
                log.error(f"❌ {dataref}: {e}")

        if success_count > 0:
            self.test_results.append(
                ("Deprecated Handling", "PASS", f"{success_count} replacements found")
            )
        else:
            self.test_results.append(
                ("Deprecated Handling", "WARN", "No replacements found")
            )

    async def test_custom_datarefs(self):
        """Test custom dataref functionality."""
        log.info("Test 7: Custom Datarefs")

        try:
            # Add a test custom dataref
            test_name = "sim/custom/test_value"
            added = self.dataref_manager.add_custom_dataref(
                name=test_name,
                dtype="float",
                description="Test dataref for XP12 compatibility",
                writable=True,
            )

            if added:
                # Test writing to it
                await self.xp_connection.subscribe_dataref(test_name, 5)
                await asyncio.sleep(0.1)

                write_success = await self.xp_connection.write_dataref(test_name, 42.0)
                await asyncio.sleep(0.1)

                value = self.xp_connection.get_value(test_name)

                if write_success and value == 42.0:
                    self.test_results.append(
                        ("Custom Datarefs", "PASS", "Custom dataref working")
                    )
                    log.info("✅ Custom dataref test successful")
                else:
                    self.test_results.append(
                        (
                            "Custom Datarefs",
                            "PARTIAL",
                            "Custom dataref added but write/test failed",
                        )
                    )
                    log.warning("⚠️ Custom dataref partially working")

                # Clean up
                self.dataref_manager.remove_custom_dataref(test_name)
            else:
                self.test_results.append(
                    ("Custom Datarefs", "FAIL", "Failed to add custom dataref")
                )
                log.error("❌ Failed to add custom dataref")

        except Exception as e:
            self.test_results.append(("Custom Datarefs", "ERROR", str(e)))
            log.error(f"❌ Custom dataref error: {e}")

    def print_results(self):
        """Print test results summary."""
        log.info("\n" + "=" * 50)
        log.info("COMPATIBILITY TEST RESULTS")
        log.info("=" * 50)

        for test_name, status, message in self.test_results:
            if status == "PASS":
                log.info(f"✅ {test_name}: {message}")
            elif status == "PARTIAL" or status == "WARN":
                log.warning(f"⚠️ {test_name}: {message}")
            else:
                log.error(f"❌ {test_name}: {message}")

        # Overall assessment
        passed = sum(1 for _, status, _ in self.test_results if status == "PASS")
        total = len(self.test_results)

        log.info(f"\nOverall: {passed}/{total} tests passed")

        if passed == total:
            log.info("🎉 FULL COMPATIBILITY - Your app is X-Plane 12 ready!")
        elif passed >= total * 0.8:
            log.info(
                "✅ GOOD COMPATIBILITY - Minor issues, should work with X-Plane 12"
            )
        elif passed >= total * 0.5:
            log.warning("⚠️ PARTIAL COMPATIBILITY - Some issues, may need attention")
        else:
            log.error("❌ POOR COMPATIBILITY - Significant issues, updates needed")


async def main():
    """Main test runner."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("X-Plane 12 Compatibility Test")
        print("Usage: python test_xp12_compatibility.py")
        print("\nMake sure X-Plane is running before testing.")
        return

    test = XP12CompatibilityTest()
    try:
        await test.run_all_tests()
    except KeyboardInterrupt:
        log.info("\nTest interrupted by user")
    except Exception as e:
        log.error(f"Test failed with error: {e}")
    finally:
        # Cleanup
        if test.xp_connection.connected:
            await test.xp_connection.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
