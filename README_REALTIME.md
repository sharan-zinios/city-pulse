# 🌊 City Pulse Real-Time Incident Management System

A **production-grade, real-time incident management system** for Bengaluru city using Google Cloud's native services, intelligent agents, and streaming data processing.

## 🏗️ Architecture Overview

### **Real-Time Data Flow**
```
Incident Sources → Pub/Sub → Stream Processor → BigQuery + Firestore
                     ↓
              Intelligent Agents → Notifications + Analytics
                     ↓
                 Cloud Functions → External Services
```

### **Core Components**

#### **1. 🌊 Streaming Infrastructure**
- **Pub/Sub Topics**: Real-time message streaming
- **Cloud Run Jobs**: Scalable stream processing
- **Firestore**: Real-time UI updates
- **BigQuery**: Data lake with vector search

#### **2. 🤖 Intelligent Agents**
- **Notification Agent**: Emergency alerts and stakeholder notifications
- **Trend Analysis Agent**: Pattern recognition and predictive insights
- **Resource Allocation Agent**: Optimal resource distribution
- **News Insights Agent**: Daily summaries and hot topics

#### **3. ☁️ Serverless Processing**
- **Cloud Functions**: Event-driven processing
- **Cloud Scheduler**: Periodic analytics and reports
- **Cloud Monitoring**: System health and alerting

#### **4. 📊 Real-Time Analytics**
- **Vector Search**: Semantic incident matching
- **Graph Database**: Relationship analysis
- **AI-Powered Insights**: Contextual recommendations

## 🚀 Quick Start

### **Prerequisites**
- Google Cloud Project with billing enabled
- `gcloud` CLI installed and authenticated
- `terraform` installed
- Python 3.8+ installed

### **1. Environment Setup**
```powershell
# Set your project ID
$env:PROJECT_ID = "your-project-id"

# Clone and navigate to project
git clone <repository-url>
cd city-pulse
```

### **2. Deploy Infrastructure**
```powershell
# Deploy complete real-time system
.\deploy_realtime.ps1

# Or deploy with historical data loading
.\deploy_realtime.ps1 -LoadHistoricalData
```

### **3. Test the System**
```bash
# Get API URL
API_URL=$(gcloud run services describe city-pulse-api --region=asia-south1 --format="value(status.url)")

# Test health endpoint
curl $API_URL/health

# Test incident search
curl -X POST $API_URL/incidents/search \
  -H "Content-Type: application/json" \
  -d '{
    "question": "traffic accidents near Koramangala",
    "coordinates": [12.9352, 77.6245],
    "radius_km": 3
  }'
```

## 📋 System Components

### **Streaming Pipeline** (`streaming/`)
- **`realtime_processor.py`**: Main streaming processor
- **`BulkDataLoader`**: Historical data loading
- **Pub/Sub Integration**: Message processing and routing

### **Intelligent Agents** (`agents/`)
- **`BaseAgent`**: Abstract agent framework
- **`NotificationAgent`**: Emergency notifications
- **`TrendAnalysisAgent`**: Pattern analysis
- **`ResourceAllocationAgent`**: Resource optimization
- **`NewsInsightsAgent`**: Daily summaries

### **Cloud Functions** (`functions/`)
- **`notification_processor`**: Handle notifications
- **`analytics_aggregator`**: Aggregate metrics
- **`trend_analyzer`**: Analyze trends
- **`data_quality_monitor`**: Monitor system health

### **Infrastructure** (`infra/`)
- **Terraform Configuration**: Complete GCP infrastructure
- **Pub/Sub Topics**: Message streaming
- **BigQuery Tables**: Data storage and analytics
- **Firestore**: Real-time UI state
- **Monitoring**: Alerts and dashboards

## 🔄 Real-Time Data Processing

### **Incident Ingestion Flow**
1. **Incident Reported** → Published to `incident-stream` topic
2. **Stream Processor** → Generates embeddings, processes data
3. **BigQuery Storage** → Stores in partitioned tables
4. **Firestore Update** → Real-time UI synchronization
5. **Agent Triggers** → Intelligent processing for high-priority incidents

### **Agent Processing**
```python
# High-priority incident triggers multiple agents
if incident.priority_score >= 8.0:
    - NotificationAgent: Send emergency alerts
    - TrendAnalysisAgent: Analyze patterns
    - ResourceAllocationAgent: Optimize resources
```

### **Real-Time Analytics**
- **Hourly Aggregations**: Incident counts, priority scores
- **Trend Detection**: Pattern recognition and anomalies
- **Predictive Insights**: AI-powered recommendations

## 🤖 Intelligent Agents

### **1. Notification Agent**
**Purpose**: Handle emergency notifications and stakeholder alerts

**Features**:
- Emergency blast notifications for high-priority incidents
- Department-specific alerts
- Citizen safety updates
- Integration with external services (email, SMS, push notifications)

**Triggers**:
- Priority score ≥ 8.0: Emergency blast
- Priority score ≥ 7.0: Department alerts
- Status changes: Citizen updates

### **2. Trend Analysis Agent**
**Purpose**: Analyze incident patterns and generate insights

**Features**:
- Historical trend analysis
- Hotspot detection
- Pattern recognition
- Predictive modeling

**Outputs**:
- Trend reports stored in Firestore
- AI-generated insights and recommendations
- Risk assessments for current incidents

### **3. Resource Allocation Agent**
**Purpose**: Optimize resource distribution across departments

**Features**:
- Current workload analysis
- Optimal department assignment
- Resource requirement estimation
- Capacity planning

**Algorithms**:
- Load balancing across departments
- Priority-based resource allocation
- Predictive resource planning

### **4. News Insights Agent**
**Purpose**: Generate summaries and identify hot topics

**Features**:
- Daily incident summaries
- Hot topic identification
- Impact analysis
- Executive reporting

**Outputs**:
- Daily summary reports
- Trending incident analysis
- Executive dashboards

## 📊 Data Architecture

### **BigQuery Tables**

#### **`real_time_incidents`**
- **Partitioned by**: `timestamp` (daily)
- **Clustered by**: `priority_score`, `event_status`, `assigned_department`
- **Purpose**: Live incident data with embeddings

#### **`analytics`**
- **Partitioned by**: `timestamp` (daily)
- **Purpose**: Aggregated metrics and analytics events

#### **`embeddings`**
- **Purpose**: Historical incident embeddings for ML

### **Firestore Collections**

#### **`incidents`**
- **Purpose**: Real-time incident state for UI
- **Updates**: Live synchronization with BigQuery

#### **`notifications`**
- **Purpose**: Active notifications and alerts
- **TTL**: Auto-expire after 24 hours

#### **`trend_analysis`**
- **Purpose**: AI-generated insights and trends
- **Updates**: Daily trend analysis results

#### **`agent_activities`**
- **Purpose**: Agent execution logs and status
- **Monitoring**: Agent performance tracking

## 🔧 Configuration

### **Environment Variables**
```bash
PROJECT_ID=your-project-id          # GCP Project ID
REGION=asia-south1                  # Deployment region
```

### **Pub/Sub Topics**
- `incident-stream`: New incident events
- `notification-stream`: Notification events
- `analytics-stream`: Analytics events
- `agent-tasks`: Agent task queue

### **Cloud Functions**
- `notification-processor`: Process notifications
- `analytics-aggregator`: Aggregate analytics (every 6 hours)
- `trend-analyzer`: Analyze trends (3x daily)
- `data-quality-monitor`: Monitor system health

## 📈 Monitoring and Alerting

### **Key Metrics**
- **Incident Processing Rate**: Messages/second through Pub/Sub
- **Agent Response Time**: Time to process high-priority incidents
- **Data Quality Score**: Completeness and freshness metrics
- **System Health**: Service availability and error rates

### **Alerts**
- **High Priority Incidents**: >10 incidents/5min
- **Data Staleness**: No incidents >1 hour
- **Agent Failures**: Agent processing errors
- **System Errors**: Cloud Function failures

### **Dashboards**
- **Real-time Incident Dashboard**: Live incident map and statistics
- **Department Dashboard**: Department-specific metrics
- **Analytics Dashboard**: Trends and insights
- **System Health Dashboard**: Infrastructure monitoring

## 🔒 Security and Compliance

### **Authentication**
- **Service Accounts**: Least-privilege access
- **IAM Roles**: Fine-grained permissions
- **API Security**: Authenticated endpoints

### **Data Privacy**
- **PII Handling**: Anonymized citizen data
- **Data Retention**: Automated cleanup policies
- **Audit Logging**: Complete activity tracking

## 🚀 Deployment Options

### **Full Deployment**
```powershell
.\deploy_realtime.ps1
```

### **Partial Deployment**
```powershell
# Skip infrastructure (if already deployed)
.\deploy_realtime.ps1 -SkipInfra

# Skip Cloud Functions
.\deploy_realtime.ps1 -SkipFunctions

# Skip services
.\deploy_realtime.ps1 -SkipServices
```

### **Development Mode**
```bash
# Local testing without GCP dependencies
python local_dev/simple_test.py
```

## 🧪 Testing

### **Unit Tests**
```bash
pytest tests/
```

### **Integration Tests**
```bash
# Test API endpoints
python tests/test_api.py

# Test streaming pipeline
python tests/test_streaming.py

# Test agents
python tests/test_agents.py
```

### **Load Testing**
```bash
# Simulate high incident volume
python tests/load_test.py --incidents=1000 --duration=300
```

## 📚 API Documentation

### **Incident Search**
```http
POST /incidents/search
Content-Type: application/json

{
  "question": "traffic accidents",
  "coordinates": [12.9716, 77.5946],
  "radius_km": 5,
  "event_types": ["traffic_accident"],
  "severity_levels": ["high", "medium"],
  "time_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  }
}
```

### **AI Analysis**
```http
POST /incidents/analyze
Content-Type: application/json

{
  "incident_id": "INC_BLR_2024_001234",
  "analysis_type": "comprehensive"
}
```

### **Real-time Statistics**
```http
GET /incidents/stats?department=BBMP&timeframe=24h
```

## 🔄 Data Flow Examples

### **New Incident Processing**
1. **Incident Reported** → `incident-stream` topic
2. **Stream Processor** → Generates embeddings, validates data
3. **BigQuery Insert** → Stores in `real_time_incidents` table
4. **Firestore Update** → Updates UI state in `incidents` collection
5. **Analytics Event** → Publishes to `analytics-stream`
6. **Agent Trigger** → High-priority incidents trigger agents

### **Notification Flow**
1. **High Priority Detected** → Agent publishes to `agent-tasks`
2. **Notification Agent** → Processes notification task
3. **AI Content Generation** → Creates contextual notifications
4. **External Services** → Sends emails, SMS, push notifications
5. **Firestore Update** → Updates notification status

### **Analytics Pipeline**
1. **Analytics Events** → Collected in `analytics-stream`
2. **Aggregation Function** → Runs every 6 hours
3. **BigQuery Analysis** → Processes metrics and trends
4. **Firestore Dashboard** → Updates real-time dashboards
5. **AI Insights** → Generates trend analysis and recommendations

## 🎯 Performance Optimization

### **Scaling Configuration**
- **Cloud Run**: Auto-scaling 0-10 instances
- **Pub/Sub**: Automatic message distribution
- **BigQuery**: Partitioned and clustered tables
- **Firestore**: Optimized document structure

### **Cost Optimization**
- **BigQuery**: Partitioning reduces query costs
- **Cloud Functions**: Pay-per-execution model
- **Storage**: Lifecycle policies for old data
- **Monitoring**: Efficient alerting thresholds

## 🛠️ Troubleshooting

### **Common Issues**

#### **Deployment Failures**
```bash
# Check Terraform state
cd infra && terraform state list

# Verify API enablement
gcloud services list --enabled
```

#### **Streaming Issues**
```bash
# Check Pub/Sub subscriptions
gcloud pubsub subscriptions list

# Monitor message processing
gcloud logging read "resource.type=cloud_run_job"
```

#### **Agent Failures**
```bash
# Check agent logs
gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=notification-processor"

# Monitor Firestore updates
gcloud firestore databases list
```

## 🔮 Future Enhancements

### **Planned Features**
- **Mobile App Integration**: Real-time citizen reporting
- **IoT Sensor Integration**: Automated incident detection
- **Advanced ML Models**: Predictive incident modeling
- **Multi-city Support**: Scalable to other cities
- **Voice Integration**: Voice-based incident reporting

### **Technical Improvements**
- **Edge Computing**: Reduce latency with edge processing
- **Advanced Analytics**: Real-time ML inference
- **Multi-region Deployment**: Global availability
- **Enhanced Security**: Zero-trust architecture

## 📞 Support

### **Documentation**
- **API Docs**: Available at `/docs` endpoint
- **Architecture Diagrams**: In `docs/` directory
- **Runbooks**: Operational procedures

### **Monitoring**
- **Health Checks**: `/health` endpoint
- **Metrics**: Cloud Monitoring dashboards
- **Logs**: Centralized logging in Cloud Logging

---

## 🎉 Success! 

Your **real-time City Pulse system** is now ready to handle Bengaluru's incident management with:

✅ **Real-time streaming** with Pub/Sub and Cloud Run  
✅ **Intelligent agents** for automated processing  
✅ **AI-powered insights** with Vertex AI  
✅ **Scalable infrastructure** on Google Cloud  
✅ **Production-grade monitoring** and alerting  

**Ready to transform city management with real-time intelligence!** 🏙️✨
