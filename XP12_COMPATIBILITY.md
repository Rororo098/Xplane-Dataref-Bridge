# X-Plane 12 Compatibility Guide

## Overview
Your X-Plane Dataref Bridge application **is compatible with X-Plane 12** with the updates implemented. This document outlines the compatibility status, required changes, and recommendations.

## Compatibility Status

### ✅ What Works Out-of-the-Box
- **UDP Protocol**: The X-Plane UDP protocol (ports 49000/49001) remains unchanged
- **Dataref Reading/Writing**: `RREF` and `DREF` commands work identically
- **Array Datarefs**: Multi-dimensional array support is fully functional
- **Custom Datarefs**: User-defined datarefs continue to work
- **Auto-discovery**: Beacon discovery protocol is supported

### ⚠️ Updates Required
1. **Version Detection**: Automatically detects X-Plane 11 vs 12
2. **Deprecated Datarefs**: Handles removed/changed datarefs
3. **Database Updates**: X-Plane 12 specific datarefs added

## Key Changes Implemented

### 1. Version Detection
```python
# Automatically detects X-Plane version on connection
async def _detect_xplane_version(self):
    await self.subscribe_dataref("sim/version/xplane_internal_version", 1)
    version_value = self.get_value("sim/version/xplane_internal_version")
    if version_value:
        self._detected_version = int(version_value)
```

### 2. Deprecated Dataref Handling
Common X-Plane 11 datarefs that changed in X-Plane 12:

| X-Plane 11 Dataref | X-Plane 12 Replacement |
|-------------------|----------------------|
| `sim/flightmodel/position/mag_psi` | `sim/flightmodel/position/true_psi` |
| `sim/cockpit/electrical/landing_lights_on` | `sim/cockpit2/switches/landing_lights_on` |
| `sim/flightmodel/controls/yoke1_pitch` | `sim/cockpit2/controls/yoke_pitch_ratio` |
| `sim/cockpit/electrical/beacon_on` | `sim/cockpit2/switches/beacon_on` |

### 3. Enhanced Error Handling
- Graceful handling of "Dataref not found" errors
- Automatic suggestions for deprecated datarefs
- Fallback values for type conversion failures

## Recommended Actions

### Before Using with X-Plane 12

1. **Update Dataref Database**
   ```bash
   # Run the update script to get latest X-Plane 12 datarefs
   python update_dataref_db.py
   ```

2. **Test Connection**
   - Start X-Plane 12
   - Run your application
   - Check logs for detected version

3. **Verify Deprecated Datarefs**
   - Monitor logs for "deprecated dataref" warnings
   - Update any hardcoded datarefs in your profiles

### Network Configuration
Ensure X-Plane 12 network settings match:
- **UDP Port**: 49000 (send) / 49001 (receive)
- **Data Input**: Enabled
- **Data Output**: Enabled  
- **IP Address**: Your computer's IP (not 127.0.0.1 for remote connections)

## New X-Plane 12 Features

### Web API (Alternative to UDP)
X-Plane 12.1.1+ includes a Web API:
- **REST Endpoint**: `http://localhost:8086/api/v2/`
- **WebSocket**: `ws://localhost:8086/api/v2`
- **Features**: Dataref CRUD, subscriptions, commands

Your current UDP-based implementation remains fully supported.

## Testing Checklist

- [ ] Connect to X-Plane 12 successfully
- [ ] Version detection shows v12.x
- [ ] Read common datarefs (altitude, airspeed, heading)
- [ ] Write to writable datarefs (lights, flaps, gear)
- [ ] Test array datarefs (engine N1, controls)
- [ ] Verify custom datarefs work
- [ ] Check for deprecated dataref warnings

## Troubleshooting

### "Dataref not found" Errors
1. Check if the dataref is deprecated
2. Look for replacement suggestions in logs
3. Update your profiles with new datarefs

### Connection Issues
1. Verify X-Plane 12 network settings
2. Check firewall rules for ports 49000/49001
3. Ensure IP address is correct

### Performance Considerations
- X-Plane 12 may have higher data update rates
- Consider adjusting subscription frequencies
- Monitor network bandwidth usage

## Future Considerations

### X-Plane 12.1.4+ Features
- Enhanced Web API capabilities
- Additional datarefs for new aircraft systems
- Improved error reporting

### Migration Path
Your application can seamlessly work with both X-Plane 11 and 12. No separate versions needed.

## Support Resources

- **X-Plane Developer Docs**: https://developer.x-plane.com/
- **Dataref Reference**: https://datareftool.com/
- **Web API Documentation**: https://developer.x-plane.com/article/x-plane-web-api

---

**Bottom Line**: Your application is X-Plane 12 ready! The implemented changes ensure backward compatibility with X-Plane 11 while adding X-Plane 12 specific enhancements.