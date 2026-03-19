# Power Failure Resolution Runbook

## Problem Description
AC power failure or DC power system issues affecting network equipment operation at cell sites or central offices.

## Symptoms
- Site down alarms with power-related root cause
- Battery voltage dropping rapidly
- Generator failure alarms
- Multiple equipment resets or reboots
- Environmental alarms (high temperature, fan failure)
- Gradual service degradation before complete outage

## Power System Components
1. **AC Power**: Primary utility feed, backup generator
2. **DC Power**: Rectifiers, batteries (typically 48V DC systems)
3. **Power Distribution**: Breakers, fuses, distribution panels
4. **Backup Systems**: Battery banks (2-4 hour backup), diesel generators
5. **Monitoring**: Smart meters, battery management systems (BMS)

## Resolution Steps

### Immediate Actions (0-15 minutes)

1. **Assess Power Failure Scope**
   ```
   Query: Sites on battery backup (critical - limited runtime)
   Query: Sites with generator running (stable but needs fuel monitoring)
   Query: Sites with complete power loss (immediate outage)
   Query: Commercial power status in affected area (utility outage map)
   Priority: Sites with <30 min battery backup remaining
   ```

2. **Battery Runtime Estimation**
   - Calculate remaining backup time:
   ```
   Formula: Runtime = (Battery Capacity × Voltage) / Load
   Example: (100Ah × 48V) / 1000W = 4.8 hours at full charge

   Check: Current battery voltage (normal: 54V, critical: <46V)
   Check: State of charge (SOC) percentage
   Check: Load on DC system (in Amperes)
   Alert: If remaining runtime <1 hour → P1 escalation
   ```

3. **Activate Emergency Procedures**
   - **For sites on battery (<1 hour backup)**:
   ```
   Action: Dispatch mobile generator immediately (ETA target: 30 min)
   Action: Reduce load - shut down non-critical equipment
   Action: Enable power saving mode on radio equipment
   Action: Notify field ops and fuel delivery service
   ```

   - **For sites with generator issues**:
   ```
   Action: Remote generator restart command
   Action: Check fuel level and auto-refill status
   Action: Dispatch technician if remote start fails
   ```

### Short-term Mitigation (15-60 minutes)

4. **Load Shedding to Extend Battery Life**
   - Shut down non-essential equipment:
   ```
   Priority 1 (Keep): Core radio equipment (eNodeB, BBU, RRU)
   Priority 1 (Keep): Transport equipment (routers, switches)
   Priority 1 (Keep): Critical monitoring systems

   Shut down: HVAC/Cooling (if ambient temp <30°C)
   Shut down: Redundant power supplies
   Shut down: Non-critical lighting
   Shut down: Legacy equipment (2G/3G if 4G/5G available)

   Expected: 30-50% load reduction, 2x battery runtime extension
   ```

5. **Generator Deployment**
   - **Mobile Generator Connection**:
   ```
   Step 1: Position generator 10-15 feet from site
   Step 2: Connect to transfer switch or manual bypass
   Step 3: Start generator and verify voltage/frequency (120/240V, 60Hz)
   Step 4: Transfer load from battery to generator
   Step 5: Monitor for 15 minutes for stability
   Step 6: Recharge batteries while on generator power

   Fuel planning: 5 kW generator consumes ~0.5 gal/hour
   Refuel schedule: Every 8-12 hours for typical site
   ```

6. **Temporary Power Solutions**
   - **Battery Bank Swapping**:
     - Deploy fully charged battery banks (if available)
     - Hot-swap batteries without service interruption
     - Transport depleted batteries for recharging

   - **Power Sharing**:
     - If neighboring site has commercial power:
       - Run temporary power cable (if distance <100m)
       - Use portable transformer if voltage conversion needed

### Long-term Resolution (1-8 hours)

7. **Commercial Power Restoration**
   - **Utility Coordination**:
   ```
   Action: Contact utility company for restoration ETA
   Action: Verify site is on priority restoration list (critical infrastructure)
   Action: Provide site GPS coordinates and account number
   Action: Request emergency crew if >10 sites affected
   Expected utility restoration: 4-24 hours (varies by cause)
   ```

8. **On-site Troubleshooting**
   - **AC Power Issues**:
   ```
   Check: Main breaker status (tripped?)
   Check: Fuses in distribution panel
   Check: Wiring for damage or loose connections
   Check: Transfer switch operation (if generator present)
   Test: Voltage at input (should be 120/240V ±10%)
   Fix: Reset breakers, replace fuses, tighten connections
   ```

   - **DC Power Issues**:
   ```
   Check: Rectifier status (convert AC to DC)
   Check: Battery bank voltage and temperature
   Check: DC distribution panel and breakers
   Test: Battery discharge test (capacity verification)
   Fix: Replace failed rectifier modules, repair DC wiring
   ```

9. **Battery System Recovery**
   - **Post-outage Battery Recharge**:
   ```
   Recharge rate: Typically 10-20% of battery capacity (10A-20A for 100Ah)
   Recharge time: 6-12 hours for full recharge after deep discharge
   Monitor: Battery temperature during recharge (<40°C)
   Monitor: Voltage recovery (should reach 54-56V when fully charged)
   Test: Capacity test after recharge (should be >80% of rated capacity)
   ```

   - **Battery Replacement (if degraded)**:
   ```
   Indicators: Voltage <46V under load, capacity <60% of rated
   Action: Schedule battery bank replacement
   Timeline: Emergency replacement <24 hours, planned replacement <1 week
   ```

### Validation and Recovery

10. **Service Restoration and Validation**
    ```
    Verify: Commercial power restored and stable for 30 min
    Verify: Batteries recharging properly (current flow >0)
    Verify: All equipment powered on and operational
    Verify: Cell site KPIs returned to normal (CSSR, throughput)
    Verify: Generator shut down and secured (if used)
    Document: Total outage duration, battery runtime used, root cause
    ```

## Escalation Path
- **L1 NOC**: Initial detection, battery runtime calculation, generator dispatch
- **Power Technician**: On-site troubleshooting, AC/DC repairs, battery replacement
- **Facilities Manager**: Generator fleet management, fuel delivery, HVAC repairs
- **Utility Liaison**: Coordination with power company for restoration
- **Site Operations Manager**: Multi-site power outages, long-term planning
- **Executive**: If >20 sites down OR >12 hour outage OR >50,000 customers affected

## Prevention Measures

### Proactive Monitoring
- **Battery Health Monitoring**:
  - Daily voltage and SOC checks
  - Monthly capacity discharge tests
  - Quarterly battery impedance testing
  - Annual full load testing
  - Track battery age (replace every 3-5 years)

- **Power System Audits**:
  - Weekly generator auto-start tests
  - Monthly fuel level checks and refills
  - Quarterly transfer switch testing
  - Annual electrical safety inspection

### Redundancy and Resilience
- **Multi-layer Backup**:
  - Layer 1: Commercial AC power (primary)
  - Layer 2: Battery backup (2-4 hour runtime)
  - Layer 3: Auto-start generator (long-term backup)
  - Layer 4: Mobile generator on standby (for generator failures)

- **Design Best Practices**:
  - Size batteries for 4-hour runtime minimum (8-hour for critical sites)
  - Dual utility feeds where available (A+B power)
  - Automatic transfer switches (ATS) for seamless failover
  - Remote power monitoring and control systems
  - Pre-positioned mobile generators in high-risk areas

### Emergency Preparedness
- **Storm Season Planning**:
  - Pre-stock fuel at high-risk sites (72-hour supply)
  - Pre-deploy mobile generators to vulnerable areas
  - Coordinate with utility companies for priority restoration
  - Establish emergency fuel supply contracts

- **Documentation**:
  - Maintain site power diagrams and single-line drawings
  - Document generator connection procedures per site
  - Track battery replacement history
  - Emergency contact list (utility, fuel vendor, generator rental)

## Related Issues
- See also: "Cell Tower Outage Resolution" for service restoration
- See also: "Environmental Alarm Resolution" for HVAC/cooling failures
- See also: "Generator Failure Resolution" for backup power issues

## Success Metrics
- **Battery Runtime**: Minimum 4 hours (target: 8 hours for critical sites)
- **Generator Deployment Time**: <30 min for P1 sites, <2 hours for P2 sites
- **Power Restoration MTTR**: <4 hours with generator, <24 hours for AC restoration
- **Battery Health**: >90% of batteries with capacity >80% of rated
- **Generator Reliability**: >95% successful auto-start rate

## Technical Specifications

### Typical Cell Site Power Requirements
- **Macro Site**: 2-5 kW (average), 8-12 kW (peak with HVAC)
- **Small Cell**: 100-500W
- **Indoor DAS**: 500-2000W per site

### Battery System Specifications
- **Voltage**: 48V DC nominal (42V-56V operating range)
- **Capacity**: 100-500 Ah (provides 2-8 hour backup at typical load)
- **Chemistry**: VRLA (Valve Regulated Lead Acid) or Lithium-ion
- **Lifespan**: 3-5 years (VRLA), 7-10 years (Lithium-ion)
- **Discharge Limit**: Should not discharge below 1.75V per cell (42V for 48V system)

### Generator Specifications
- **Portable**: 5-15 kW, diesel or propane
- **Fixed Installation**: 20-50 kW, diesel (for large sites/central offices)
- **Auto-start**: 10-30 second start time from power failure
- **Fuel Consumption**: ~0.5-1 gallon/hour per 5 kW load
- **Noise Level**: <75 dBA at 7 meters (meet local ordinances)
