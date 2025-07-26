# 🏙️ City Pulse - Local Development Guide

This guide helps you test the City Pulse real-time incident management system locally before deploying to Google Cloud.

## 🚀 Quick Start

The fastest way to get started:

```powershell
# Generate 10k incidents and run simulator
.\quick_start.ps1

# Or with custom settings
.\quick_start.ps1 -IncidentCount 5000 -BatchSize 10 -BatchInterval 15
```

## 📋 Prerequisites

- **Python 3.8+** installed and in PATH
- **Windows PowerShell** (for quick start script)
- **~50MB free disk space** (for 10k incident dataset)

## 🛠️ Manual Setup

### Step 1: Generate Dataset

Create a realistic dataset of Bengaluru incidents:

```bash
# Generate 10,000 incidents (default)
python local_dev/generate_dataset.py

# Generate custom number of incidents
python local_dev/generate_dataset.py --count 5000 --output my_incidents.json
```

**Dataset Features:**
- Realistic Bengaluru locations (MG Road, Koramangala, Whitefield, etc.)
- 10 incident types (traffic accidents, potholes, power outages, etc.)
- Proper severity distribution (50% low, 30% medium, 20% high)
- Department assignments (BBMP, Traffic Police, BESCOM, etc.)
- Temporal patterns (peak hours, weather conditions)
- Geographic distribution across all areas of Bengaluru

### Step 2: Run Local Simulator

Start the real-time incident simulator:

```bash
# Basic usage
python local_dev/realtime_simulator.py

# With custom settings
python local_dev/realtime_simulator.py --dataset my_incidents.json --batch-size 5 --batch-interval 30
```

## 🎯 Simulator Features

### Real-Time Streaming Simulation
- **Batch Processing**: Feeds 5-10 incidents every 20 seconds (configurable)
- **Random Selection**: Picks incidents randomly from your dataset
- **Realistic Timing**: Simulates real-world incident reporting patterns

### Mock AI Agents
The simulator includes 4 intelligent agents that process incidents:

1. **🔔 Notification Agent**
   - Generates emergency alerts for high-priority incidents
   - Creates notification content with severity-based messaging
   - Simulates external notification sending

2. **📊 Trend Analysis Agent**
   - Identifies incident patterns and hotspots
   - Analyzes temporal trends (peak hours, seasonal patterns)
   - Generates insights about incident clustering

3. **🎯 Resource Allocation Agent**
   - Optimizes department resource allocation
   - Considers incident severity, location, and department workload
   - Suggests resource redistribution strategies

4. **📰 News Insights Agent**
   - Creates daily incident summaries
   - Identifies trending incident types
   - Generates public communication content

### Local Data Storage
- **SQLite Database**: Stores processed incidents locally
- **Agent Activity Log**: Tracks all agent processing activities
- **Statistics Tracking**: Real-time processing metrics

## 📊 Understanding the Output

### Real-Time Statistics
```
🏙️ CITY PULSE - LOCAL REAL-TIME SIMULATOR
==========================================
📊 REAL-TIME STATISTICS (Updated every 10 seconds)
--------------------------------------------------
⏱️  Runtime: 00:02:30
📥 Total Incidents Processed: 47
📈 Processing Rate: 18.8 incidents/minute
🔄 Current Batch: 8/10 incidents
⏳ Next Batch In: 12 seconds

🤖 AI AGENT ACTIVITY:
   🔔 Notifications: 12 sent
   📊 Trend Analysis: 8 completed
   🎯 Resource Plans: 15 generated
   📰 News Insights: 3 summaries

📍 TOP INCIDENT LOCATIONS:
   Koramangala: 8 incidents
   MG Road: 6 incidents
   Whitefield: 5 incidents

🚨 INCIDENT TYPES:
   traffic_accident: 15 (31.9%)
   pothole: 12 (25.5%)
   power_outage: 8 (17.0%)
   water_supply: 7 (14.9%)
   construction: 5 (10.6%)
```

### Agent Processing Examples
```
🔔 [NOTIFICATION] High-priority traffic accident at Koramangala
   → Emergency alert sent to Traffic Police
   → Estimated response time: 8 minutes

📊 [TREND ANALYSIS] Detected pothole cluster in South Bengaluru
   → 5 incidents in 2km radius
   → Recommendation: Preventive road maintenance

🎯 [RESOURCE ALLOCATION] BBMP workload optimization
   → Reallocate 2 teams from West to South zone
   → Expected 15% efficiency improvement

📰 [NEWS INSIGHTS] Daily summary generated
   → 47 incidents processed today
   → Traffic accidents up 12% from yesterday
   → Public advisory: Avoid MG Road 5-7 PM
```

## 🗂️ Generated Files

After running the simulator, you'll find:

```
local_dev/
├── historical_incidents.json      # Your incident dataset
├── local_incidents.db            # SQLite database with processed incidents
├── agent_activity.db             # Agent processing logs
├── generate_dataset.py           # Dataset generator
└── realtime_simulator.py         # Main simulator
```

## ⚙️ Configuration Options

### Dataset Generator Options
```bash
python local_dev/generate_dataset.py --help

Options:
  --count NUMBER     Number of incidents to generate (default: 10000)
  --output FILENAME  Output JSON file (default: historical_incidents.json)
```

### Simulator Options
```bash
python local_dev/realtime_simulator.py --help

Options:
  --dataset FILENAME      Dataset JSON file (default: historical_incidents.json)
  --batch-size NUMBER     Incidents per batch (default: 7)
  --batch-interval NUMBER Seconds between batches (default: 20)
  --stats-interval NUMBER Statistics update interval (default: 10)
```

### Quick Start Options
```powershell
.\quick_start.ps1 -Help

Options:
  -IncidentCount NUMBER      Number of incidents to generate (default: 10000)
  -DatasetFile FILENAME      Dataset filename (default: historical_incidents.json)
  -BatchSize NUMBER          Incidents per batch (default: 7)
  -BatchInterval NUMBER      Seconds between batches (default: 20)
  -SkipDatasetGeneration     Skip dataset generation if file exists
```

## 🧪 Testing Scenarios

### 1. High-Volume Testing
```bash
# Generate large dataset
python local_dev/generate_dataset.py --count 50000

# Fast processing
python local_dev/realtime_simulator.py --batch-size 15 --batch-interval 5
```

### 2. Slow Streaming Simulation
```bash
# Simulate slow incident reporting
python local_dev/realtime_simulator.py --batch-size 3 --batch-interval 60
```

### 3. Peak Hour Simulation
```bash
# Generate dataset focused on peak hours
python local_dev/generate_dataset.py --count 20000

# Process with higher frequency
python local_dev/realtime_simulator.py --batch-size 12 --batch-interval 10
```

## 🔍 Analyzing Results

### SQLite Database Queries
```sql
-- Connect to local database
sqlite3 local_dev/local_incidents.db

-- View processed incidents
SELECT event_type, location_name, severity_level, timestamp 
FROM incidents 
ORDER BY timestamp DESC 
LIMIT 10;

-- Incident distribution by area
SELECT area_category, COUNT(*) as count 
FROM incidents 
GROUP BY area_category 
ORDER BY count DESC;

-- High-priority incidents
SELECT * FROM incidents 
WHERE priority_score >= 8.0 
ORDER BY priority_score DESC;
```

### Agent Activity Analysis
```sql
-- Connect to agent database
sqlite3 local_dev/agent_activity.db

-- View agent processing activity
SELECT agent_type, task_type, COUNT(*) as count 
FROM agent_activity 
GROUP BY agent_type, task_type 
ORDER BY count DESC;

-- Recent notifications
SELECT * FROM agent_activity 
WHERE agent_type = 'NotificationAgent' 
ORDER BY timestamp DESC 
LIMIT 5;
```

## 🚀 Next Steps

After local testing:

1. **Modify Agent Logic**: Edit `local_dev/realtime_simulator.py` to customize AI agent behavior
2. **Test Different Scenarios**: Try various batch sizes and intervals
3. **Analyze Performance**: Review SQLite databases for insights
4. **Deploy to Cloud**: Use `deploy_realtime.ps1` for Google Cloud deployment

## 🐛 Troubleshooting

### Common Issues

**Dataset Generation Fails**
```bash
# Check Python installation
python --version

# Ensure you're in the right directory
ls local_dev/
```

**Simulator Won't Start**
```bash
# Check if dataset exists
ls historical_incidents.json

# Generate dataset if missing
python local_dev/generate_dataset.py
```

**SQLite Database Issues**
```bash
# Remove corrupted databases
rm local_dev/*.db

# Restart simulator
python local_dev/realtime_simulator.py
```

### Performance Tips

- **Large Datasets**: Use `--batch-size 10` or higher for faster processing
- **Memory Usage**: For 50k+ incidents, consider processing in chunks
- **Disk Space**: Each 10k incidents uses ~50MB of storage

## 📈 Performance Benchmarks

| Dataset Size | Generation Time | Processing Rate | Memory Usage |
|-------------|----------------|----------------|--------------|
| 1,000       | 10 seconds     | 25/min         | 50 MB        |
| 10,000      | 1.5 minutes    | 20/min         | 150 MB       |
| 50,000      | 7 minutes      | 18/min         | 400 MB       |

## 🔗 Related Documentation

- [Main README](../README.md) - Overall project documentation
- [Real-Time README](../README_REALTIME.md) - Production deployment guide
- [Deployment Script](../deploy_realtime.ps1) - Google Cloud deployment

---

**Happy Local Development! 🎉**

Test your AI agents locally, iterate quickly, and deploy with confidence to Google Cloud.
