# ODCV Analytics Dashboard - Backlog

## Future Enhancements

### 🔄 **Sensor-Zone Mapping Uploader**
**Priority**: Medium
**Description**: Add functionality to upload custom sensor-zone mapping CSV files instead of relying on automatic alphabetical pairing.

**Requirements**:
- CSV upload interface for mapping files
- Expected format: `sensor_name,zone_name` (e.g., "115-4-01 presence,BV200")
- Validation to ensure all sensors and zones exist in loaded data
- Override automatic mapping when custom mapping is provided
- API endpoint: `/api/upload-mapping`
- Error handling for invalid mappings

**Use Cases**:
- Buildings with non-sequential sensor/zone relationships
- Custom commissioning requirements
- Multi-building deployments with different naming schemes
- Validation of specific sensor-zone correlations

**Technical Notes**:
- Should integrate with existing dataset selection interface
- Validate mapping against currently loaded sensor data
- Store mapping state with dataset selection
- Provide mapping export functionality for documentation

---

## Completed Features
- ✅ Dataset selection interface with preset options
- ✅ Automatic sensor-zone mapping generation
- ✅ Real-time metric calculation and time period switching
- ✅ Critical data loading bug fixes