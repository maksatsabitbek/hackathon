# CSSR Degradation Resolution Runbook

## Problem Description
Call Setup Success Rate (CSSR) degradation indicating issues with RRC connection establishment or call setup procedures.

## Symptoms
- CSSR drops below threshold (normal: >99%, degraded: 95-98%, critical: <95%)
- Increase in RRC connection failures
- High RACH (Random Access Channel) failure rate
- Customer complaints about "call failed" or "cannot connect to network"
- Increase in retransmission attempts

## Root Cause Analysis

### Common Causes
1. **Radio Interference** (40% of cases)
   - External interference from new equipment
   - Intermodulation products
   - Adjacent channel interference

2. **Network Congestion** (30% of cases)
   - RACH preamble depletion
   - PRB (Physical Resource Block) saturation
   - Processor overload on eNodeB

3. **Configuration Issues** (20% of cases)
   - Incorrect RACH parameters
   - Timer misconfiguration (T300, T301)
   - Mobility parameters (handover thresholds)

4. **Hardware Degradation** (10% of cases)
   - RRU performance degradation
   - Antenna feeder issues
   - Timing/synchronization problems

## Resolution Steps

### Immediate Actions (0-15 minutes)

1. **Identify Degradation Scope**
   ```
   Query: CSSR by sector for last 24 hours
   Query: RRC connection failure reasons
   Query: RACH success rate per sector
   Compare: Current vs baseline performance
   ```

2. **Quick Diagnostics**
   - Check sector load (PRB utilization)
   - Verify timing/synchronization status
   - Check for new alarms or configuration changes
   - Review recent optimization activities

3. **Immediate Countermeasures**
   ```
   Action: Increase RACH preambles from 64 to 128
   Action: Enable CSSR improvement feature flags
   Action: Adjust admission control thresholds
   Expected improvement: 2-5% CSSR increase within 15 min
   ```

### Short-term Mitigation (15-60 minutes)

4. **Interference Mitigation**
   - Run spectrum analyzer scan on affected sectors
   - Enable interference rejection algorithms:
   ```
   Command: enable-interference-cancellation SECTOR_ID
   Command: adjust-frequency-hopping SECTOR_ID
   Command: enable-icic (Inter-Cell Interference Coordination)
   ```
   - Coordinate with neighboring operators if needed

5. **Capacity Optimization**
   - Load balancing across sectors:
   ```
   Action: Adjust cell reselection parameters
   Action: Enable MLB (Mobility Load Balancing)
   Action: Reduce cell border overlap (adjust power/tilt)
   ```
   - Deploy carrier aggregation to increase capacity
   - Consider temporary admission control for heavy users

6. **Parameter Optimization**
   ```
   Optimize: T300 timer (RRC connection setup) - increase from 2s to 4s
   Optimize: T304 timer (handover execution) - increase from 100ms to 150ms
   Optimize: RACH backoff parameters for congestion scenarios
   Optimize: Msg3 retransmission attempts (increase from 3 to 5)
   ```

### Long-term Resolution (1-4 hours)

7. **RF Optimization**
   - Conduct drive test to identify coverage holes
   - Adjust antenna azimuth/tilt for optimal coverage
   - Optimize neighbor relations:
   ```
   Action: Add missing neighbors (ANR analysis)
   Action: Remove weak/interfering neighbors
   Action: Adjust handover thresholds (RSRP/RSRQ)
   ```

8. **Network Expansion (if capacity issue)**
   - Deploy additional carriers on affected sectors
   - Activate dormant carriers (if available)
   - Plan for cell splits or new sites
   - Implement SON (Self-Organizing Network) features

9. **Hardware Remediation**
   - Replace degraded RRUs (if VSWR/output power issues detected)
   - Check and clean antenna connectors
   - Verify timing source (GPS/PTP synchronization)
   - Inspect and replace damaged feeders/cables

### Validation and Monitoring

10. **Performance Validation**
    ```
    Verify: CSSR returned to >99% for at least 1 hour
    Verify: RRC connection failure rate <1%
    Verify: RACH success rate >98%
    Verify: No increase in handover failures
    Monitor: Customer complaint trends
    ```

## Escalation Path
- **L1 NOC**: Detection, quick diagnostics, parameter adjustments
- **L2 RF Optimization**: Detailed analysis, parameter tuning, neighbor optimization
- **L3 RF Planning**: Major RF redesign, frequency refarming, capacity planning
- **Radio Vendor Support**: Complex RAN software issues, feature activation
- **Network Executive**: If CSSR <90% for >2 hours OR >20,000 customers affected

## Prevention Measures
- **Proactive Monitoring**
  - Set CSSR KPI thresholds: Warning <98%, Critical <95%
  - Monitor trend analysis (week-over-week comparison)
  - Automatic alerts for sudden degradation (>2% drop in 1 hour)

- **Regular Optimization**
  - Monthly RF optimization campaigns
  - Quarterly neighbor relation audits
  - Annual antenna alignment verification
  - Continuous SON algorithm tuning

- **Capacity Planning**
  - Weekly traffic forecasting
  - Preemptive carrier activation during events
  - Buffer capacity planning (20% headroom)

## Related Issues
- See also: "Network Congestion Resolution" for PRB saturation
- See also: "Handover Failure Resolution" for mobility issues
- See also: "Cell Tower Outage" for hardware-related failures

## Success Metrics
- **Target CSSR**: >99.5% (industry standard)
- **Recovery Time**: <1 hour for degradation 95-98%, <30 min for <95%
- **RRC Failure Rate**: <0.5%
- **RACH Success Rate**: >98%
- **Customer Impact**: Zero complaints if CSSR >98%

## Technical Reference
- 3GPP TS 36.331: RRC protocol specification
- 3GPP TS 36.321: MAC layer procedures (RACH)
- 3GPP TS 36.133: Requirements for UE measurements
