# Fiber Cut Resolution Runbook

## Problem Description
Fiber cut causing complete loss of service to multiple cell sites and affecting backhaul connectivity.

## Symptoms
- Multiple cell sites offline simultaneously
- Complete loss of backhaul connectivity
- No alarms from affected sites (due to connectivity loss)
- Customer complaints concentrated in specific geographic area

## Resolution Steps

### Immediate Actions (0-15 minutes)

1. **Identify Affected Scope**
   - Query network topology to identify all sites on affected fiber ring
   - Determine customer impact radius
   - Check for redundant paths availability

2. **Activate Backup Paths**
   ```
   Command: activate-backup-ring RING_ID
   Expected Result: Traffic rerouted within 2-3 minutes
   ```

3. **Notify Field Operations**
   - Create emergency dispatch ticket
   - Priority: P1 - CRITICAL
   - Include GPS coordinates of likely cut location

### Short-term Mitigation (15-60 minutes)

4. **Deploy Temporary Microwave Links**
   - For critical sites without automatic failover
   - Coordinate with microwave team
   - Expected restoration: 45-60 minutes

5. **Traffic Management**
   - Implement traffic shaping on backup paths
   - Prioritize voice and emergency services
   - Block non-essential data services if needed

### Long-term Resolution (1-4 hours)

6. **Fiber Restoration**
   - Dispatch fiber splicing team
   - Typical repair time: 2-4 hours
   - Require police assistance for traffic control if needed

7. **Service Validation**
   - Run end-to-end connectivity tests
   - Verify all KPIs returned to normal
   - Clear all related alarms

## Escalation Path
- L1 NOC: Initial detection and backup activation
- L2 Network Engineer: Traffic management and optimization
- L3 Architect: Major rerouting decisions
- Field Operations Manager: Dispatch coordination
- Executive: If >10,000 customers affected for >1 hour

## Prevention Measures
- Implement ring protection on all fiber routes
- Maintain updated fiber route maps
- Regular backup path testing (monthly)
- Coordinate with local construction permits