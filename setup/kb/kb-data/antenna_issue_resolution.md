# Antenna and RF Path Issue Resolution Runbook

## Problem Description
Issues with antenna systems, feeders, or RF path causing coverage degradation, interference, or complete service loss.

## Common Antenna/RF Path Issues
1. **Antenna Misalignment**: Azimuth or tilt deviation from design
2. **High VSWR**: Impedance mismatch indicating RF path problems
3. **Feeder Damage**: Cable cuts, water ingress, connector corrosion
4. **Antenna Hardware**: Broken elements, radome damage, mounting issues
5. **PIM (Passive Intermodulation)**: Non-linear distortion in passive components

## Symptoms by Issue Type

### Antenna Misalignment
- Coverage gap or overlap in unexpected areas
- Increased handover failures in specific direction
- Customer complaints from specific geographic area
- Interference with neighboring cells
- Asymmetric cell performance (one side strong, other weak)

### High VSWR (Voltage Standing Wave Ratio)
- Reduced transmit power (protection mechanism activated)
- RRU power alarms or derating
- Reflected power >5% of forward power
- VSWR measurement >1.5:1 (normal <1.3:1)
- Overheating at RRU or antenna port

### Feeder/Cable Issues
- Intermittent sector outages (especially in wind/rain)
- Gradual RF performance degradation over time
- Water in feeder line (fluctuating VSWR)
- Connector corrosion (visible on inspection)
- Physical damage (cuts, kinks, crushing)

### Passive Intermodulation (PIM)
- Interference on specific frequencies
- Uplink noise increase (UL SINR degradation)
- Throughput drop in upload direction
- PIM level >-107 dBc (normal <-150 dBc)
- Affects high-power sites more (macro sites)

## Resolution Steps

### Immediate Actions (0-15 minutes)

1. **Identify RF Path Issue Scope**
   ```
   Check: VSWR readings per sector (alarm if >1.5)
   Check: Transmit power vs configured (derating indicator)
   Check: Reflected power measurements
   Check: PIM test results (if available)
   Check: Recent maintenance or weather events
   Analyze: Coverage map changes (drive test data)
   ```

2. **Remote Diagnostics**
   ```
   Command: show antenna-status SECTOR_ID
   Command: show vswr-measurements SECTOR_ID
   Command: show transmit-power-history SECTOR_ID
   Command: show pim-readings SECTOR_ID (if PIM detector installed)
   Compare: Current values vs baseline (commission data)
   Trend: VSWR increasing over time? (feeder degradation)
   ```

3. **Quick Mitigation Actions**
   - **For high VSWR**:
   ```
   If VSWR 1.5-2.0: Reduce power to 80% to protect RRU
   If VSWR 2.0-3.0: Reduce power to 50% or disable sector
   If VSWR >3.0: Disable sector immediately (RRU protection)
   Action: Notify neighboring cells to increase power (compensate coverage)
   ```

   - **For coverage issues**:
   ```
   If suspected misalignment: Cross-check with neighboring cells
   Action: Adjust neighbor cell parameters for temporary coverage
   Action: Increase power on overlap sectors
   Action: Modify handover thresholds temporarily
   ```

### Short-term Mitigation (15-60 minutes)

4. **Antenna Alignment Verification**
   - **Using Remote Tools** (if available):
   ```
   Check: Azimuth reading from antenna servo/motor
   Check: Tilt reading (mechanical and electrical)
   Compare: Current vs design values (site database)
   Deviation tolerance: ±3° azimuth, ±1° tilt
   If out of range: Mark for field correction
   ```

   - **Using Drive Test Data**:
   ```
   Analyze: RSRP/RSRQ heatmap around site
   Identify: Areas with unexpected strong/weak signal
   Compare: Current coverage vs baseline (commission)
   Estimate: Azimuth deviation based on coverage pattern
   ```

5. **VSWR Troubleshooting**
   - **Identify fault location** (Time Domain Reflectometry - TDR):
   ```
   If VSWR fault at 0m: RRU antenna port issue
   If VSWR fault at 5-30m: Jumper or connector issue (top of tower)
   If VSWR fault at 30-80m: Main feeder line issue
   If VSWR fault at 80-100m: Antenna input connector issue

   Common faults:
     - 0m: Damaged RRU connector, wrong adapter
     - 10-20m: Loose jumper connector (top of tower)
     - 40-60m: Feeder kink or pinch point
     - 80m+: Antenna connector corrosion, water ingress
   ```

6. **PIM Troubleshooting**
   - **Identify PIM Source**:
   ```
   Test: Inject two test tones (F1 and F2)
   Measure: Intermodulation products (2F1-F2, 2F2-F1, etc.)
   Location: Use PIM hunting tool to locate faulty component

   Common PIM sources:
     - Loose connectors (most common - 60%)
     - Corroded/dirty connectors (25%)
     - Damaged feeders (10%)
     - Antenna internal issues (5%)
   ```

### Long-term Resolution (1-8 hours)

7. **Field Team Dispatch - Antenna Work**
   - **Safety Requirements** (Tower Climbing):
   ```
   Certification: Tower climber certification required
   Equipment: Fall protection, rescue kit, RF safety monitor
   Weather: No work if wind >30 mph or lightning within 10 miles
   Coordination: Notify FAA if tower >200 ft or near airport
   RF Safety: Power down or reduce power during work near antennas
   ```

   - **Work Order Details**:
   ```
   Include: Site ID, tower height, sector ID
   Include: Suspected issue (alignment, VSWR, PIM)
   Include: Safety requirements and access instructions
   Include: Required tools (torque wrench, PIM tester, TDR)
   Include: Spare parts needed (connectors, jumpers, etc.)
   ```

8. **On-Site RF Path Repairs**

   **Antenna Realignment Procedure:**
   ```
   Step 1: Verify design parameters (azimuth, tilt, height)
   Step 2: Climb tower with calibrated compass and inclinometer
   Step 3: Measure current antenna pointing
   Step 4: Loosen mounting brackets
   Step 5: Adjust azimuth to design value (±1°)
   Step 6: Adjust mechanical tilt (if applicable)
   Step 7: Tighten all bolts to specified torque (50-70 ft-lbs)
   Step 8: Document final alignment (photo + measurements)
   Step 9: Remote verification via KPIs
   Duration: 1-2 hours per sector
   ```

   **VSWR Issue Resolution:**
   ```
   Step 1: Power down RRU for safety
   Step 2: Disconnect antenna feeders at RRU
   Step 3: Test VSWR of feeder+antenna from RRU end
   Step 4: If VSWR OK: Check RRU antenna port (clean/replace)
   Step 5: If VSWR high: Climb tower to inspect path
   Step 6: Inspect all connectors (7/16 DIN typically)
   Step 7: Clean connectors with contact cleaner
   Step 8: Check torque on connectors (15-20 ft-lbs for 7/16 DIN)
   Step 9: Replace damaged jumpers or feeders
   Step 10: Retest VSWR (target <1.3:1)
   Step 11: Weatherproof all connections (tape, boots)
   Duration: 2-4 hours depending on issue location
   ```

   **PIM Remediation:**
   ```
   Step 1: Perform PIM test from RRU location (baseline)
   Step 2: Disconnect and inspect each connector in path
   Step 3: Clean all connectors with lint-free cloth + alcohol
   Step 4: Apply anti-corrosion compound
   Step 5: Reassemble with proper torque (15-20 ft-lbs)
   Step 6: Retest PIM after each connection
   Step 7: Replace components if PIM persists
   Step 8: Final PIM test (target <-107 dBc, ideal <-150 dBc)
   Duration: 2-6 hours (PIM hunting can be time-consuming)
   ```

   **Feeder/Jumper Replacement:**
   ```
   Step 1: Identify cable specifications (impedance, length, connectors)
   Step 2: Procure replacement cable (same or better spec)
   Step 3: Plan cable routing (avoid sharp bends, minimum bend radius)
   Step 4: Power down RRU and disconnect old cable
   Step 5: Route new cable and secure with proper hangers
   Step 6: Install connectors or terminate if field-installable
   Step 7: Test VSWR and PIM before connecting to RRU
   Step 8: Connect to RRU and final testing
   Step 9: Weatherproof and label cable
   Duration: 3-6 hours depending on cable length and routing
   ```

9. **Performance Validation**
   - **Antenna Alignment Validation**:
   ```
   Test: Coverage drive test in intended direction
   Verify: RSRP/RSRQ in design range (-80 to -100 dBm typical)
   Verify: Reduced interference with neighbors
   Verify: Handover performance improved (HOSR >98%)
   Compare: Coverage map before/after realignment
   ```

   - **VSWR Validation**:
   ```
   Measure: VSWR <1.3:1 on all affected sectors
   Verify: Transmit power at configured value (no derating)
   Verify: Reflected power <2% of forward power
   Monitor: VSWR stable over 24 hours (no weather impact)
   ```

   - **PIM Validation**:
   ```
   Measure: PIM level <-107 dBc (pass), ideally <-150 dBc
   Verify: Uplink SINR improved (>10 dB for cell edge)
   Verify: Upload throughput restored to normal
   Monitor: PIM level stable over time (no degradation)
   ```

### Advanced Diagnostics (4-24 hours)

10. **Drive Test and RF Optimization**
    ```
    Coverage Drive Test:
      - Route: Circle around site at 500m, 1km, 2km radius
      - Measure: RSRP, RSRQ, SINR, throughput, handovers
      - Document: GPS coordinates of weak/strong areas
      - Compare: Against design coverage predictions

    Interference Hunting:
      - Spectrum scan: 700 MHz - 2.6 GHz (LTE bands)
      - Identify: External interference sources
      - Measure: PIM products in uplink frequencies
      - Coordinate: With other operators if co-sited

    Post-Repair Optimization:
      - Fine-tune antenna azimuth (±2° adjustments)
      - Adjust electrical tilt (±1° for coverage tuning)
      - Optimize neighbor list based on new coverage
      - Update handover thresholds for seamless mobility
    ```

## Escalation Path
- **L1 NOC**: Detection, VSWR monitoring, remote diagnostics
- **L2 RF Engineer**: Coverage analysis, alignment verification, optimization
- **Tower Crew**: Physical inspection, connector cleaning, realignment
- **L3 RF Planning**: Coverage redesign, antenna replacement planning
- **Structural Engineer**: Tower integrity issues, mounting concerns
- **Vendor TAC**: Antenna/feeder defects, RMA for faulty equipment

## Prevention Measures

### Regular Maintenance (Proactive)
- **Quarterly Visual Inspections**:
  - Check antenna physical condition (no visible damage)
  - Verify mounting hardware tight (no loose bolts)
  - Inspect radome for cracks or damage
  - Check feeder weatherproofing (tape, boots intact)

- **Annual RF Performance Audit**:
  - VSWR sweep test on all sectors
  - PIM test on high-power sectors (>40W)
  - Antenna alignment verification (compass + inclinometer)
  - Connector torque check and retightening
  - Feeder visual inspection (full cable run)

### Predictive Maintenance
- **Trend Monitoring** (Weekly):
  - VSWR trending (detect gradual increases)
  - Transmit power derating events
  - Coverage KPI degradation (CSSR, HOSR)
  - Customer complaint hot spots

- **Condition-Based Actions**:
  - VSWR >1.3 but <1.5: Schedule inspection within 30 days
  - VSWR 1.5-2.0: Schedule repair within 7 days
  - VSWR >2.0: Emergency dispatch within 24 hours
  - PIM >-107 dBc: Schedule remediation within 14 days

### Design Best Practices
- **Antenna System Design**:
  - Use 7/16 DIN connectors (better PIM performance than N-type)
  - Minimize number of connectors (each adds insertion loss and PIM risk)
  - Proper cable management (avoid stress, maintain bend radius >10x diameter)
  - Weatherproofing from day one (prevent water ingress)

- **Quality Standards**:
  - Commission VSWR <1.2:1 (allows margin for degradation)
  - Commission PIM <-150 dBc (well below -107 dBc threshold)
  - Document baseline (photos, measurements, alignment data)
  - Use only qualified tower crews (certified climbers)

## Related Issues
- See also: "Cell Tower Outage Resolution" for complete sector down scenarios
- See also: "CSSR Degradation Resolution" for RF performance impacts
- See also: "Network Congestion Resolution" for coverage-related capacity issues

## Success Metrics
- **VSWR Threshold**: <1.3:1 (normal), 1.3-1.5 (warning), >1.5 (alarm)
- **PIM Level**: <-150 dBc (ideal), <-107 dBc (acceptable), >-107 dBc (alarm)
- **Antenna Alignment Accuracy**: ±3° azimuth, ±1° tilt from design
- **MTTR (Mean Time to Repair)**:
  - Realignment: <4 hours
  - VSWR issue: <6 hours
  - PIM remediation: <8 hours
- **First-Time Fix Rate**: >85% (no repeat visits for same issue)

## Technical Specifications

### VSWR and Return Loss
- **VSWR 1.0:1**: Perfect match, 0% reflected power
- **VSWR 1.2:1**: 1% reflected power, excellent
- **VSWR 1.3:1**: 1.7% reflected power, acceptable
- **VSWR 1.5:1**: 4% reflected power, marginal (investigate)
- **VSWR 2.0:1**: 11% reflected power, alarm condition
- **Return Loss (dB)** = -20 * log10((VSWR-1)/(VSWR+1))

### PIM Standards
- **Industry Standard**: <-107 dBc for LTE/5G systems
- **Best Practice**: <-150 dBc at commissioning
- **Measurement**: Use two-tone test at rated power
- **Products**: Typically measure 3rd order (2F1-F2, 2F2-F1)

### Feeder Specifications
- **Impedance**: 50 Ω (antenna systems)
- **Cable Types**: 1/2", 7/8", 1-1/4" (diameter)
- **Loss**: ~3-10 dB per 100m depending on frequency and cable size
- **Connectors**: 7/16 DIN (most common), N-type, 4.3-10
- **Weatherproofing**: Coax seal tape + rubber boot + heat shrink

### Antenna Specifications
- **Typical Beamwidth**: 65° horizontal, 7-15° vertical
- **Gain**: 15-18 dBi (macro antennas)
- **Polarization**: Dual-polarized (±45°) for MIMO
- **Tilt Range**: Mechanical 0-10°, Electrical 0-12° (RET antennas)
- **Wind Rating**: Typically rated for 150 mph survival, 50 mph operational
