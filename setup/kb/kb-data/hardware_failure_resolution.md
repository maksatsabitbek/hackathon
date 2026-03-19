# Hardware Failure Resolution Runbook

## Problem Description
Equipment hardware failure including RF units, baseband units, transport equipment, or ancillary systems causing service degradation or outage.

## Common Hardware Failures
1. **Radio Equipment**: RRU (Remote Radio Unit), BBU (Baseband Unit), Antenna
2. **Transport Equipment**: Router, Switch, Optical modules (SFP/SFP+)
3. **Power Equipment**: Rectifier, Battery, DC distribution
4. **Ancillary Systems**: GPS, Synchronization, Cooling/HVAC
5. **Passive Components**: Feeders, Jumpers, Connectors, Combiners

## Symptoms by Equipment Type

### RRU (Remote Radio Unit) Failure
- Sector down, no radio transmission
- High VSWR (Voltage Standing Wave Ratio >1.5)
- Transmit power degradation or unstable
- RRU communication lost alarm
- Temperature alarm (>65°C)

### BBU (Baseband Unit) Failure
- Multiple sectors down simultaneously
- eNodeB unreachable from EMS
- S1 interface down (connection to core network)
- High CPU/memory utilization (>90%)
- Frequent reboots or crashes

### Transport Equipment Failure
- Site isolated (cannot ping from NOC)
- Fiber link down alarms
- High packet loss (>1%) or latency (>50ms)
- SFP module failure (no light)
- Interface errors or CRC errors increasing

### GPS/Sync Failure
- Loss of synchronization alarm
- Timing accuracy degraded
- Holdover mode activated
- Impact: Handover failures, call drops

## Resolution Steps

### Immediate Actions (0-15 minutes)

1. **Identify Failed Component**
   ```
   Check: Equipment alarms and fault logs
   Check: Communication status (pingable? manageable?)
   Check: Physical layer (link up? optical power OK?)
   Check: Environmental status (temperature, voltage)
   Isolate: Single component vs multiple component failure
   ```

2. **Remote Diagnostics**
   - **For accessible equipment**:
   ```
   Command: show equipment-status
   Command: show alarms active
   Command: show interface statistics
   Command: show hardware inventory
   Command: show temperature sensors
   Command: show optical power levels (if fiber)
   ```

   - **For inaccessible equipment** (management down):
   ```
   Check: Ping response (IP layer)
   Check: SNMP polling response
   Check: Remote PDU status (if available)
   Check: Neighboring equipment for clues
   ```

3. **Quick Workarounds**
   - **Sector redundancy**:
   ```
   If: 3-sector site with 1 RRU failure
   Action: Increase power on working sectors by 3-6 dB
   Action: Adjust tilt to expand coverage
   Expected: Maintain 70-80% coverage
   ```

   - **Transport redundancy**:
   ```
   If: Dual transport links, one failed
   Action: Verify automatic failover to backup link
   Action: Monitor backup link capacity (may be reduced)
   Action: Implement QoS to prioritize critical traffic
   ```

### Short-term Mitigation (15-60 minutes)

4. **Component-Specific Troubleshooting**

   **RRU Failure:**
   ```
   Step 1: Power cycle RRU (remote command or via PDU)
   Step 2: Check fiber connection (RRU ↔ BBU)
   Step 3: Verify CPRI link status and optical power
   Step 4: Check antenna connection and VSWR
   Step 5: Review temperature and fan status
   Success rate: ~30% resolution via remote actions
   ```

   **BBU Failure:**
   ```
   Step 1: Collect crash logs and core dumps
   Step 2: Attempt software restart (warm reboot)
   Step 3: Check for hung processes (high CPU)
   Step 4: Verify license file integrity
   Step 5: Cold reboot if warm reboot fails
   Wait: 10-15 min for full initialization
   Success rate: ~50% resolution via reboot
   ```

   **Transport Equipment Failure:**
   ```
   Step 1: Check interface status (up/down)
   Step 2: Verify SFP module (clean, reseat, replace)
   Step 3: Check fiber patch panel for damage
   Step 4: Test with known-good SFP module
   Step 5: Check routing table and static routes
   Step 6: Verify VLAN configuration
   ```

   **GPS/Sync Failure:**
   ```
   Step 1: Check GPS antenna cable and connector
   Step 2: Verify GPS receiver status and satellite count
   Step 3: Check for GPS jamming or interference
   Step 4: Enable holdover mode (use local oscillator)
   Step 5: Switch to alternative sync source (SyncE, PTP)
   Note: Holdover acceptable for 24-72 hours
   ```

5. **Deploy Spare Equipment (If Available)**
   - Check on-site spare inventory:
     - RRU spares (same frequency band)
     - SFP modules (1G/10G, single/multi-mode)
     - Patch cables (fiber, ethernet)
     - Power supplies and fans

   - Hot-swap procedure:
   ```
   For redundant equipment (no service impact):
     1. Prepare replacement unit
     2. Disable faulty unit gracefully
     3. Physically replace component
     4. Power on and verify initialization
     5. Enable and integrate into service

   For non-redundant equipment (service impact):
     1. Schedule short maintenance window (if possible)
     2. Notify customers via SMS (if outage >30 min)
     3. Perform replacement
     4. Restore and validate service
   ```

### Long-term Resolution (1-8 hours)

6. **Field Technician Dispatch**
   - **Ticket Information Requirements**:
   ```
   Include: Site ID, GPS coordinates, access instructions
   Include: Failed equipment type, serial number, alarm details
   Include: Suspected root cause and troubleshooting done
   Include: Replacement part number (from inventory system)
   Include: Site access codes, lock combinations, contacts
   Include: Safety requirements (high voltage, tower climb, etc.)
   ```

   - **Priority Assignment**:
     - P1: Critical site, >5000 customers, revenue impact >$5k/hour
     - P2: Major site, 1000-5000 customers, redundancy lost
     - P3: Minor site, <1000 customers, degraded service
     - P4: Scheduled maintenance, no immediate impact

7. **On-Site Hardware Replacement**

   **RRU Replacement Procedure:**
   ```
   Step 1: Verify replacement RRU (same model, frequency)
   Step 2: Power down faulty RRU
   Step 3: Disconnect fiber (CPRI) and antenna feeders
   Step 4: Unmount RRU and mount replacement
   Step 5: Connect antenna feeders and verify VSWR <1.3
   Step 6: Connect fiber and verify optical power (-10 to -20 dBm)
   Step 7: Power on and wait for initialization (5-10 min)
   Step 8: Download configuration from BBU or EMS
   Step 9: Perform radio calibration
   Step 10: Verify transmit power and KPIs
   Duration: 1-2 hours including testing
   ```

   **BBU Replacement Procedure:**
   ```
   Step 1: Backup BBU configuration (critical!)
   Step 2: Gracefully shut down BBU (if possible)
   Step 3: Power down and disconnect all cables
   Step 4: Physically replace BBU
   Step 5: Power on and load operating system
   Step 6: Restore configuration from backup
   Step 7: Verify all RRUs recognized and operational
   Step 8: Verify S1 connection to core network
   Step 9: Test call setup and data sessions
   Duration: 2-4 hours including software load
   ```

   **Transport Equipment Replacement:**
   ```
   Step 1: Prepare replacement device with config
   Step 2: If redundant, hot-swap with no outage
   Step 3: If non-redundant, schedule brief outage
   Step 4: Physical replacement and cable connection
   Step 5: Power on and verify boot sequence
   Step 6: Validate routing, VLANs, and connectivity
   Step 7: Run ping and throughput tests
   Duration: 30 min - 2 hours depending on complexity
   ```

8. **Root Cause Analysis**
   - Collect evidence from failed equipment:
   ```
   Capture: Event logs, error counters, crash dumps
   Capture: Environmental data (temp, humidity, voltage)
   Photograph: Physical damage, burnt components, corrosion
   Document: Age of equipment, maintenance history
   Test: Failed component in lab (if feasible)
   ```

   - Common root causes:
     - Environmental: Overheating (40%), lightning (15%), moisture (10%)
     - Electrical: Power surge (10%), unstable power (5%)
     - Mechanical: Vibration (5%), connector wear (5%)
     - Software: Bug triggered hardware watchdog (5%)
     - End of life: Normal wear and tear (5%)

9. **Preventive Actions Post-Failure**
   ```
   If environmental: Improve HVAC, add heat shields, seal enclosures
   If electrical: Install surge protectors, stabilize power, improve grounding
   If mechanical: Improve cable management, dampen vibration, replace connectors
   If software: Apply patches, update firmware, report bug to vendor
   If EOL: Identify similar-age equipment, plan proactive replacement
   ```

### Validation and Testing

10. **Comprehensive Service Validation**
    ```
    Level 1 - Basic Functionality:
      ✓ Equipment powered on and communicating
      ✓ All interfaces up and passing traffic
      ✓ No active alarms
      ✓ Environmental parameters normal (temp <50°C, voltage stable)

    Level 2 - Radio Performance (if RF equipment):
      ✓ RSRP/RSRQ within expected range (-80 to -100 dBm)
      ✓ VSWR <1.3 on all antenna ports
      ✓ Transmit power matches configured value (±1 dB)
      ✓ CSSR >99%, HOSR >98%

    Level 3 - End-to-End Service:
      ✓ Voice call setup and quality (MOS >4.0)
      ✓ Data throughput test (>70% of theoretical max)
      ✓ Handover success from/to neighboring cells
      ✓ Customer complaints cleared

    Monitoring: Continuous monitoring for 24-48 hours post-repair
    ```

## Escalation Path
- **L1 NOC**: Initial detection, remote diagnostics, reboot attempts
- **L2 Technical Support**: Advanced troubleshooting, configuration changes
- **Field Technician**: On-site access, physical inspection, hardware replacement
- **L3 Engineering**: Complex issues, vendor coordination, design flaws
- **Vendor TAC (Technical Assistance Center)**: Equipment defects, RMA process
- **Site Operations Manager**: Multi-site failures, logistics coordination

## Prevention Measures

### Proactive Maintenance
- **Regular Inspections** (Quarterly):
  - Visual inspection of equipment (burns, corrosion, damage)
  - Connector cleaning and tightening
  - Temperature and fan status verification
  - Firmware and software updates

- **Predictive Maintenance** (Monthly):
  - Trend analysis: CPU, memory, temperature over time
  - Anomaly detection: Unusual error rates or behavior
  - Performance degradation monitoring
  - Plan replacement before failure (based on trends)

### Spare Parts Management
- **Critical Spares** (On-site):
  - RRUs for each frequency band (1 per 10 sites)
  - BBU or spare blade/card (1 per 20 sites)
  - SFP modules: 10G/1G, single/multi-mode (10 of each)
  - Patch cables: Fiber, ethernet (20 of each)
  - Power supplies and fan units (5 of each)

- **Vendor Stock** (2-4 hour delivery):
  - High-value equipment (BBU, routers)
  - Less common modules or cards
  - Emergency stock for vendor-supported equipment

### Equipment Lifecycle Management
- Track equipment age and plan replacement:
  - **0-3 years**: Low failure rate, reactive maintenance
  - **3-5 years**: Moderate failure rate, increase monitoring
  - **5-7 years**: High failure rate, proactive replacement planning
  - **>7 years**: End-of-life, plan technology refresh

## Related Issues
- See also: "Cell Tower Outage Resolution" for service impact mitigation
- See also: "Power Failure Resolution" for power-related hardware issues
- See also: "Environmental Alarm Resolution" for cooling and temperature issues

## Success Metrics
- **MTTR (Mean Time to Repair)**:
  - Remote fix: <30 min
  - On-site simple swap: <2 hours
  - On-site complex replacement: <4 hours
- **Hardware Reliability**: MTBF (Mean Time Between Failures) >50,000 hours
- **Spare Parts Availability**: >95% (critical parts available on-site/nearby)
- **First-Time Fix Rate**: >90% (no return visits needed)
- **Preventive Maintenance Effectiveness**: Reduce reactive failures by 30-50%

## Vendor Support and RMA Process
1. **TAC Case Opening** (within 30 min of failure confirmation):
   - Provide: Serial number, software version, alarm logs
   - Describe: Symptoms, troubleshooting done, suspected component
   - Request: Advanced replacement (if under warranty/contract)

2. **RMA (Return Material Authorization)**:
   - Advance replacement: New unit shipped before returning faulty unit
   - Turnaround: 2-5 days for standard, 4-24 hours for critical
   - Shipping: Overnight or same-day courier for P1 failures

3. **Warranty and Contracts**:
   - Standard warranty: 1-3 years (varies by vendor)
   - Extended warranty: 5+ years with premium support
   - 4-hour or 24-hour on-site service contracts (for critical sites)
