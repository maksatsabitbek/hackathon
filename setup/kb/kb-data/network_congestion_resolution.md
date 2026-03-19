# Network Congestion Resolution Runbook

## Problem Description
Network congestion causing service degradation due to insufficient capacity to handle traffic demand.

## Symptoms
- High PRB (Physical Resource Block) utilization (>85% sustained)
- Increased call blocking rate (CBR >2%)
- Slow data speeds (throughput <50% of normal)
- High packet loss and latency (>100ms)
- User complaints about "slow internet" or "call not connecting"
- Increased handover failures due to target cell congestion

## Congestion Severity Levels
- **Level 1 (Warning)**: PRB utilization 70-85%, minor user impact
- **Level 2 (Moderate)**: PRB utilization 85-95%, noticeable degradation
- **Level 3 (Critical)**: PRB utilization >95%, severe service impact
- **Level 4 (Emergency)**: Complete capacity saturation, call blocking >10%

## Resolution Steps

### Immediate Actions (0-15 minutes)

1. **Identify Congestion Scope**
   ```
   Query: PRB utilization per sector (last 2 hours)
   Query: Number of active users per cell
   Query: Top bandwidth consumers (per IMSI/device)
   Query: Traffic type breakdown (voice, video, gaming, etc.)
   Map: Geographic distribution of congestion
   ```

2. **Quick Load Shedding**
   - Implement traffic priority policies:
   ```
   Action: Prioritize voice and emergency calls (QCI 1, 5)
   Action: Throttle video streaming to 480p (QCI 8, 9)
   Action: Limit P2P and background traffic (QCI 9)
   Action: Enable fair scheduling to prevent user starvation
   ```

3. **Immediate Capacity Boost**
   ```
   Action: Activate dormant carriers (if available)
   Action: Enable 256-QAM modulation for capable devices
   Action: Activate carrier aggregation (2CC → 3CC or more)
   Action: Enable MIMO rank adaptation (2x2 → 4x4 if supported)
   Expected: 30-50% capacity increase
   ```

### Short-term Mitigation (15-60 minutes)

4. **Traffic Steering and Load Balancing**
   - **MLB (Mobility Load Balancing)**:
   ```
   Action: Reduce cell reselection threshold for congested cells
   Action: Increase handover bias toward neighbor cells
   Action: Enable automatic inter-frequency load balancing
   Action: Adjust serving cell quality offset (Qoffset)
   ```

   - **WiFi Offload**:
   ```
   Action: Enable RAN-assisted WiFi offload (RANW)
   Action: Send SMS to users promoting WiFi calling
   Action: Adjust WiFi steering RSSI thresholds
   Expected: 20-40% traffic offload to WiFi
   ```

5. **Spectrum Optimization**
   - **Carrier Prioritization**:
   ```
   Action: Move data-heavy users to mid-band (2.5 GHz, n41)
   Action: Keep voice users on low-band (700 MHz, 850 MHz)
   Action: Enable dynamic spectrum sharing (DSS) if 5G available
   ```

   - **Bandwidth Expansion**:
   ```
   Action: Increase channel bandwidth (10 MHz → 20 MHz if spectrum available)
   Action: Activate contiguous carrier aggregation
   Action: Enable supplemental uplink (SUL) for uplink congestion
   ```

6. **Admission Control**
   - Implement smart admission policies:
   ```
   Action: Enable access class barring (ACB) for delay-tolerant services
   Action: Set RACH backoff for non-emergency traffic
   Action: Limit new RRC connections if PRB >90%
   Action: Prioritize existing sessions over new connections
   ```

### Long-term Resolution (1-6 hours)

7. **Deploy Temporary Capacity (COW/COLT)**
   - **COW (Cell on Wheels)**:
     - Deployment time: 1-2 hours
     - Capacity boost: 500-1000 simultaneous users
     - Use cases: Events, emergencies, planned activities

   - **COLT (Cell on Light Truck)**:
     - Deployment time: 30-60 minutes
     - Capacity boost: 200-500 simultaneous users
     - More mobile, faster deployment

8. **Network Optimization**
   - **Traffic Engineering**:
   ```
   Action: Analyze peak traffic patterns (hourly/daily)
   Action: Implement time-based QoS policies
   Action: Schedule heavy background tasks to off-peak hours
   Action: Enable congestion-based tariff alerts (if policy allows)
   ```

   - **Coverage Optimization**:
   ```
   Action: Reduce cell overlap in congested areas (adjust tilt/power)
   Action: Optimize handover parameters to spread load
   Action: Fine-tune ANR (Automatic Neighbor Relations)
   ```

9. **Permanent Capacity Expansion Planning**
   - Identify capacity expansion needs:
     - New cell sites in hotspot areas
     - Additional carriers on existing sites
     - Small cell deployment (indoor/outdoor)
     - Upgrade to higher-order MIMO (8T8R, Massive MIMO)

   - Implementation timeline:
     - Carrier activation: 1-2 weeks
     - Small cells: 2-4 weeks
     - New macro sites: 3-6 months

### Special Event Planning

10. **Pre-planned Event Mitigation** (Sports, Concerts, Conferences)
    ```
    Pre-event: Deploy COW/COLT 24 hours before
    Pre-event: Activate all available carriers
    Pre-event: Pre-provision WiFi offload capacity
    During event: Real-time monitoring with 15-min intervals
    During event: Dedicated engineer on standby
    Post-event: Gradual capacity scale-down
    ```

## Escalation Path
- **L1 NOC**: Detection, immediate countermeasures, traffic priority
- **L2 Capacity Engineer**: Load balancing, spectrum optimization, parameter tuning
- **L3 Network Planning**: Capacity expansion planning, permanent solutions
- **WiFi Team**: WiFi offload coordination, hotspot deployment
- **COW Operations**: Emergency capacity deployment
- **Executive**: If congestion >4 hours OR >50,000 customers affected

## Prevention Measures

### Proactive Capacity Management
- **Daily Monitoring**:
  - Track PRB utilization trends (week-over-week)
  - Identify capacity hotspots before saturation
  - Set alerts at 70% PRB utilization

- **Weekly Analysis**:
  - Traffic forecasting based on historical data
  - Identify seasonal patterns (holidays, events)
  - Plan carrier activations proactively

- **Monthly Planning**:
  - Capacity review meetings
  - Cell site expansion planning
  - Spectrum refarming decisions

### Automation and AI/ML
- Implement SON (Self-Organizing Network) features:
  - Auto carrier activation/deactivation
  - Dynamic load balancing
  - Predictive capacity scaling

- Deploy AI/ML models:
  - Traffic prediction (1-7 day forecasts)
  - Anomaly detection (unusual traffic spikes)
  - Automatic parameter optimization

### Network Design Best Practices
- Maintain 30% capacity buffer during normal hours
- Deploy multi-layer networks (macro + small cells)
- Implement inter-RAT load balancing (4G ↔ 5G)
- Regular spectrum audits and optimization

## Related Issues
- See also: "CSSR Degradation" for connection setup impacts
- See also: "High Latency Resolution" for transport congestion
- See also: "Cell Tower Outage" for site-level capacity loss

## Success Metrics
- **Target PRB Utilization**: <70% average, <85% peak
- **Call Blocking Rate**: <1% (normal), <2% (acceptable), >2% (critical)
- **Data Throughput**: >70% of theoretical maximum
- **User Satisfaction**: Customer complaints <0.1% of affected users
- **Congestion Duration**: Resolve Level 3/4 congestion in <1 hour

## Traffic Thresholds (Example for 20 MHz LTE carrier)
- **Normal Load**: <70 PRB utilization (~50 Mbps average throughput)
- **High Load**: 70-85 PRB utilization (30-50 Mbps average)
- **Congestion**: 85-95 PRB utilization (15-30 Mbps average)
- **Saturation**: >95 PRB utilization (<15 Mbps, frequent blocking)

## QoS Priority Classes (3GPP QCI)
- **QCI 1**: VoLTE, emergency calls (highest priority)
- **QCI 5**: IMS signaling
- **QCI 6-7**: Video streaming, real-time gaming
- **QCI 8-9**: Web browsing, standard video
- **QCI 9**: Background downloads, P2P (lowest priority)
