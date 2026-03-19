# Cell Tower Outage Resolution Runbook

## Problem Description
Cell tower or eNodeB outage causing loss of wireless service in a specific coverage area.

## Symptoms
- Complete loss of service in specific cell sector or entire site
- Failed ping tests to cell site equipment
- Radio interface alarms (e.g., "eNodeB Unreachable")
- Spike in customer complaints from specific geographic area
- Call setup failures and data session drops

## Resolution Steps

### Immediate Actions (0-15 minutes)

1. **Verify Outage Scope**
   - Check if single sector, multiple sectors, or entire site affected
   - Query cell site status via EMS (Element Management System)
   - Determine number of affected customers
   - Check neighbor cell capacity for handover support

2. **Remote Diagnostics**
   ```
   Command: check-cell-status SITE_ID SECTOR_ID
   Command: ping-cell-equipment SITE_ID
   Command: check-power-status SITE_ID
   Expected Result: Identify root cause (power, transport, RF equipment)
   ```

3. **Enable Emergency Load Balancing**
   - Increase power on neighboring cells by 3-6 dB
   - Adjust antenna tilt on adjacent sectors
   - Enable carrier aggregation on neighboring sites
   - Expected capacity increase: 20-30%

### Short-term Mitigation (15-60 minutes)

4. **Remote Restart Procedures**
   - If transport link is up but eNodeB unresponsive:
   ```
   Command: remote-reboot SITE_ID
   Wait: 5-10 minutes for full initialization
   Verify: Cell registration and KPI metrics
   ```
   - Success rate: ~40% for software-related issues

5. **Activate COW (Cell on Wheels)**
   - For extended outages affecting >2,000 customers
   - Deployment time: 45-90 minutes
   - Coordinates required: GPS location + azimuth
   - Power source: Generator or grid connection

6. **Traffic Offload**
   - Enable WiFi calling announcements via SMS
   - Redirect traffic to nearby indoor systems (DAS)
   - Implement temporary roaming with partner networks

### Long-term Resolution (1-4 hours)

7. **Field Technician Dispatch**
   - Create service ticket with priority based on customer impact:
     - P1: >5,000 customers OR critical infrastructure
     - P2: 1,000-5,000 customers
     - P3: <1,000 customers
   - Include in ticket:
     - Site ID and GPS coordinates
     - Symptoms and diagnostics results
     - Access instructions and security codes
     - Required parts based on diagnostics

8. **Common Hardware Fixes**
   - **Power Issues**: Reset breakers, check battery backup, verify generator
   - **Transport Issues**: Check fiber connection, replace SFPs, verify IP config
   - **RF Issues**: Replace RRU (Remote Radio Unit), check antenna feeders
   - **Software Issues**: Reload configuration, update firmware

9. **Service Validation**
   ```
   Test: Drive test around site (RSRP, RSRQ, SINR)
   Test: Call setup success rate (target: >98%)
   Test: Data throughput test (target: >50 Mbps downlink)
   Verify: All alarms cleared
   Verify: KPIs within threshold for 30 minutes
   ```

## Escalation Path
- **L1 NOC**: Initial detection, remote diagnostics, COW activation
- **L2 RF Engineer**: Load balancing, neighbor optimization
- **L3 Radio Planning**: Major coverage adjustments, frequency refarming
- **Field Operations Supervisor**: Technician dispatch, spare parts coordination
- **Regional VP**: If outage >4 hours OR >10,000 customers affected

## Prevention Measures
- Implement dual-power supply (grid + battery + generator)
- Regular preventive maintenance (quarterly site visits)
- Redundant transport links (primary + backup fiber/microwave)
- Automatic neighbor relations (ANR) configuration
- Predictive analytics on equipment health metrics
- Environmental monitoring (temperature, humidity, intrusion)

## Related Issues
- See also: "Power Failure Resolution" for AC/DC issues
- See also: "Fiber Cut Resolution" for transport-related outages
- See also: "Hardware Failure Resolution" for BBU/RRU replacement procedures

## Success Metrics
- Mean Time to Detect (MTTD): <5 minutes
- Mean Time to Restore (MTTR): <2 hours for P1, <4 hours for P2
- Customer Impact: Minimize to <5,000 customers per incident
- Restoration Success Rate: >95% within SLA timeframes
