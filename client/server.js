const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');
const { GoogleGenerativeAI } = require('@google/generative-ai');

// Load environment variables
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
    cors: {
        origin: process.env.CORS_ORIGIN || "*",
        methods: ["GET", "POST"]
    }
});

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Configuration
const PORT = process.env.PORT || 3002;
const DB_PATH = process.env.NODE_ENV === 'production' || process.env.DOCKER_ENV 
    ? process.env.DOCKER_DB_PATH 
    : process.env.DB_PATH;
const AGENT_DB_PATH = process.env.NODE_ENV === 'production' || process.env.DOCKER_ENV 
    ? process.env.DOCKER_AGENT_DB_PATH 
    : process.env.AGENT_DB_PATH;
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const GEMINI_MODEL = process.env.GEMINI_MODEL || 'gemini-1.5-flash';

// Validate required environment variables
if (!GEMINI_API_KEY) {
    console.error('❌ GEMINI_API_KEY is required. Please set it in your .env file.');
    process.exit(1);
}

if (!DB_PATH || !AGENT_DB_PATH) {
    console.error('❌ Database paths are required. Please set DB_PATH and AGENT_DB_PATH in your .env file.');
    process.exit(1);
}

console.log('🔧 Configuration loaded:');
console.log(`   - Port: ${PORT}`);
console.log(`   - Environment: ${process.env.NODE_ENV || 'development'}`);
console.log(`   - DB Path: ${DB_PATH}`);
console.log(`   - Agent DB Path: ${AGENT_DB_PATH}`);
console.log(`   - Gemini Model: ${GEMINI_MODEL}`);

// Initialize Gemini AI
const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

// Global state
let connectedClients = 0;
let stats = {
    totalIncidents: 0,
    highPriority: 0,
    processingRate: 0,
    agentActivity: {
        notification_agent: 0,
        trend_analysis_agent: 0,
        resource_allocation_agent: 0,
        news_insights_agent: 0
    }
};

// Database connection
let db = null;
let agentDb = null;

function initializeDatabases() {
    try {
        if (fs.existsSync(DB_PATH)) {
            db = new sqlite3.Database(DB_PATH);
            console.log('✅ Connected to incidents database');
        } else {
            console.log('⚠️  Incidents database not found. Will connect when available.');
        }

        if (fs.existsSync(AGENT_DB_PATH)) {
            agentDb = new sqlite3.Database(AGENT_DB_PATH);
            console.log('✅ Connected to agent activity database');
        } else {
            console.log('⚠️  Agent database not found. Will connect when available.');
        }
    } catch (error) {
        console.error('❌ Database connection error:', error);
    }
}

// Socket.IO connection handling
io.on('connection', (socket) => {
    connectedClients++;
    console.log(`🔌 Client connected. Total clients: ${connectedClients}`);
    
    // Send initial stats
    socket.emit('stats_update', stats);
    
    // Send recent incidents
    if (db) {
        getRecentIncidents((incidents) => {
            incidents.forEach(incident => {
                socket.emit('new_incident', incident);
            });
        });
    }

    socket.on('disconnect', () => {
        connectedClients--;
        console.log(`🔌 Client disconnected. Total clients: ${connectedClients}`);
    });
});

// API Routes
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        connectedClients,
        databaseConnected: !!db && !!agentDb
    });
});

app.get('/api/incidents/recent', (req, res) => {
    if (!db) {
        return res.status(503).json({ error: 'Database not available' });
    }
    
    getRecentIncidents((incidents) => {
        res.json({ incidents });
    });
});

app.get('/api/stats', (req, res) => {
    res.json(stats);
});

// AI Insights endpoint
app.get('/api/insights', async (req, res) => {
    if (!db) {
        return res.status(503).json({ error: 'Database not available' });
    }
    
    try {
        const insights = await generateAIInsights();
        res.json({ insights });
    } catch (error) {
        console.error('❌ Error generating AI insights:', error);
        res.status(500).json({ error: 'Failed to generate insights' });
    }
});

// AI Insights generation function
async function generateAIInsights() {
    return new Promise((resolve, reject) => {
        if (!db) {
            reject(new Error('Database not available'));
            return;
        }

        // Get recent incidents data for analysis
        const query = `
            SELECT 
                event_type,
                severity_level,
                priority_score,
                location_name,
                area_category,
                timestamp,
                weather_condition,
                traffic_density,
                assigned_department,
                event_status
            FROM incidents 
            WHERE datetime(timestamp) >= datetime('now', '-24 hours')
            ORDER BY priority_score DESC 
            LIMIT 50
        `;

        db.all(query, [], async (err, rows) => {
            if (err) {
                reject(err);
                return;
            }

            try {
                // Prepare data for AI analysis
                const incidentSummary = prepareIncidentSummary(rows);
                
                // Generate AI insights using Gemini
                const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
                
                const prompt = `
                You are a city management AI assistant analyzing real-time incident data for Bengaluru city. 
                
                Based on the following incident data from the last 24 hours, provide key insights in JSON format:

                Incident Summary:
                ${incidentSummary}

                Please provide insights in this exact JSON structure:
                {
                    "priority_alerts": [
                        {
                            "type": "string",
                            "message": "string",
                            "severity": "high|medium|low",
                            "affected_areas": ["string"]
                        }
                    ],
                    "trends": [
                        {
                            "category": "string",
                            "trend": "increasing|decreasing|stable",
                            "description": "string",
                            "impact": "string"
                        }
                    ],
                    "recommendations": [
                        {
                            "action": "string",
                            "priority": "high|medium|low",
                            "department": "string",
                            "timeline": "string"
                        }
                    ],
                    "area_analysis": [
                        {
                            "area": "string",
                            "incident_count": "number",
                            "dominant_type": "string",
                            "status": "string"
                        }
                    ]
                }

                Focus on actionable insights, patterns, and immediate priority areas that need attention.
                `;

                const result = await model.generateContent(prompt);
                const response = await result.response;
                const text = response.text();
                
                // Parse the JSON response
                let aiInsights;
                try {
                    // Extract JSON from the response (remove any markdown formatting)
                    const jsonMatch = text.match(/\{[\s\S]*\}/);
                    if (jsonMatch) {
                        aiInsights = JSON.parse(jsonMatch[0]);
                    } else {
                        throw new Error('No valid JSON found in response');
                    }
                } catch (parseError) {
                    console.warn('Failed to parse AI response as JSON, using fallback');
                    aiInsights = createFallbackInsights(rows);
                }

                // Add metadata
                aiInsights.generated_at = new Date().toISOString();
                aiInsights.data_period = '24 hours';
                aiInsights.total_incidents_analyzed = rows.length;

                resolve(aiInsights);

            } catch (error) {
                console.error('Error generating AI insights:', error);
                // Fallback to rule-based insights
                resolve(createFallbackInsights(rows));
            }
        });
    });
}

function prepareIncidentSummary(incidents) {
    const summary = {
        total: incidents.length,
        by_type: {},
        by_severity: {},
        by_area: {},
        high_priority: incidents.filter(i => i.priority_score >= 8).length,
        active_incidents: incidents.filter(i => i.event_status === 'in_progress').length
    };

    incidents.forEach(incident => {
        // Count by type
        summary.by_type[incident.event_type] = (summary.by_type[incident.event_type] || 0) + 1;
        
        // Count by severity
        summary.by_severity[incident.severity_level] = (summary.by_severity[incident.severity_level] || 0) + 1;
        
        // Count by area
        summary.by_area[incident.area_category] = (summary.by_area[incident.area_category] || 0) + 1;
    });

    return JSON.stringify(summary, null, 2);
}

function createFallbackInsights(incidents) {
    const highPriority = incidents.filter(i => i.priority_score >= 8);
    const trafficIncidents = incidents.filter(i => i.event_type.includes('traffic'));
    
    return {
        priority_alerts: [
            {
                type: "High Priority Incidents",
                message: `${highPriority.length} high-priority incidents require immediate attention`,
                severity: highPriority.length > 5 ? "high" : "medium",
                affected_areas: [...new Set(highPriority.map(i => i.location_name))].slice(0, 3)
            }
        ],
        trends: [
            {
                category: "Traffic",
                trend: trafficIncidents.length > 10 ? "increasing" : "stable",
                description: `${trafficIncidents.length} traffic-related incidents in the last 24 hours`,
                impact: "Moderate impact on city mobility"
            }
        ],
        recommendations: [
            {
                action: "Deploy additional resources to high-priority areas",
                priority: "high",
                department: "BBMP",
                timeline: "Immediate"
            }
        ],
        area_analysis: [
            {
                area: "Multiple areas",
                incident_count: incidents.length,
                dominant_type: "mixed",
                status: "monitoring"
            }
        ],
        generated_at: new Date().toISOString(),
        data_period: '24 hours',
        total_incidents_analyzed: incidents.length
    };
}

// Location details endpoint for map clicks
app.get('/api/incidents/location/:lat/:lng', (req, res) => {
    if (!db) {
        return res.status(503).json({ error: 'Database not available' });
    }
    
    const { lat, lng } = req.params;
    const latitude = parseFloat(lat);
    const longitude = parseFloat(lng);
    
    const query = `
        SELECT * FROM incidents 
        WHERE ABS(latitude - ?) < 0.01 AND ABS(longitude - ?) < 0.01
        ORDER BY timestamp DESC 
        LIMIT 10
    `;
    
    db.all(query, [latitude, longitude], (err, rows) => {
        if (err) {
            console.error('❌ Error fetching location incidents:', err);
            res.status(500).json({ error: 'Database error' });
            return;
        }
        res.json({ incidents: rows || [] });
    });
});

// Heat map data endpoint
app.get('/api/heatmap', (req, res) => {
    if (!db) {
        return res.status(503).json({ error: 'Database not available' });
    }
    
    const query = `
        SELECT latitude, longitude, priority_score as weight
        FROM incidents 
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY timestamp DESC 
        LIMIT 1000
    `;
    
    db.all(query, [], (err, rows) => {
        if (err) {
            console.error('❌ Error fetching heat map data:', err);
            res.status(500).json({ error: 'Database error' });
            return;
        }
        res.json({ data: rows || [] });
    });
});

// Database query functions
function getRecentIncidents(callback) {
    if (!db) {
        callback([]);
        return;
    }
    
    const query = `
        SELECT * FROM incidents 
        ORDER BY timestamp DESC 
        LIMIT 50
    `;
    
    db.all(query, [], (err, rows) => {
        if (err) {
            console.error('❌ Error fetching incidents:', err);
            callback([]);
            return;
        }
        callback(rows || []);
    });
}

function getAgentActivity(callback) {
    if (!agentDb) {
        callback({});
        return;
    }
    
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    const query = `
        SELECT agent_name, COUNT(*) as count 
        FROM agent_activities 
        WHERE timestamp > ?
        GROUP BY agent_name
    `;
    
    agentDb.all(query, [oneHourAgo], (err, rows) => {
        if (err) {
            console.error('❌ Error fetching agent activity:', err);
            callback({});
            return;
        }
        
        const activity = {};
        rows.forEach(row => {
            activity[row.agent_name] = row.count;
        });
        callback(activity);
    });
}

function updateStats() {
    if (!db) {
        console.log('⚠️  updateStats: No database connection');
        return;
    }
    
    console.log('🔄 Updating stats...');
    
    // Get total incidents
    db.get('SELECT COUNT(*) as count FROM incidents', [], (err, row) => {
        if (err) {
            console.error('❌ Error getting total incidents:', err);
        } else if (row) {
            console.log(`📊 Total incidents: ${row.count}`);
            stats.totalIncidents = row.count;
        }
    });
    
    // Get high priority incidents
    db.get('SELECT COUNT(*) as count FROM incidents WHERE priority_score >= 8', [], (err, row) => {
        if (err) {
            console.error('❌ Error getting high priority incidents:', err);
        } else if (row) {
            console.log(`🚨 High priority incidents: ${row.count}`);
            stats.highPriority = row.count;
        }
    });
    
    // Calculate processing rate (incidents per minute in last hour)
    // Use processed_at column which has ISO format timestamps
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    console.log(`⏰ Querying incidents since: ${oneHourAgo}`);
    db.get(`
        SELECT COUNT(*) as count 
        FROM incidents 
        WHERE processed_at > ?
    `, [oneHourAgo], (err, row) => {
        if (err) {
            console.error('❌ Error getting processing rate:', err);
        } else if (row) {
            console.log(`⚡ Recent incidents (last hour): ${row.count}`);
            stats.processingRate = Math.round(row.count / 60 * 100) / 100;
        }
    });
    
    // Get agent activity
    getAgentActivity((activity) => {
        console.log('🤖 Agent activity:', activity);
        stats.agentActivity = {
            notification_agent: activity.notification_agent || 0,
            trend_analysis_agent: activity.trend_analysis_agent || 0,
            resource_allocation_agent: activity.resource_allocation_agent || 0,
            news_insights_agent: activity.news_insights_agent || 0
        };
        
        console.log('📡 Broadcasting stats:', stats);
        // Broadcast updated stats
        io.emit('stats_update', stats);
    });
}

// Database monitoring for new incidents
function monitorIncidents() {
    if (!db) {
        // Try to reconnect
        initializeDatabases();
        return;
    }
    
    // Get the latest incident
    const query = `
        SELECT * FROM incidents 
        ORDER BY rowid DESC 
        LIMIT 1
    `;
    
    db.get(query, [], (err, row) => {
        if (err) {
            console.error('❌ Error monitoring incidents:', err);
            return;
        }
        
        if (row && row.rowid > (monitorIncidents.lastRowId || 0)) {
            monitorIncidents.lastRowId = row.rowid;
            
            // Broadcast new incident
            io.emit('new_incident', row);
            
            // Check if it's high priority for notification
            if (row.priority_score >= 8) {
                const notification = {
                    type: 'EMERGENCY',
                    message: `🚨 HIGH PRIORITY: ${row.event_type.replace('_', ' ')} at ${row.location_name}`,
                    timestamp: new Date().toISOString(),
                    incident_id: row.id
                };
                io.emit('notification', notification);
            } else if (row.priority_score >= 6) {
                const notification = {
                    type: 'ALERT',
                    message: `⚠️ MEDIUM PRIORITY: ${row.event_type.replace('_', ' ')} at ${row.location_name}`,
                    timestamp: new Date().toISOString(),
                    incident_id: row.id
                };
                io.emit('notification', notification);
            }
        }
    });
}

// Monitor agent activity for notifications
function monitorAgentActivity() {
    if (!agentDb) {
        // Try to reconnect
        initializeDatabases();
        return;
    }
    
    const query = `
        SELECT * FROM agent_activities 
        ORDER BY rowid DESC 
        LIMIT 5
    `;
    
    agentDb.all(query, [], (err, rows) => {
        if (err) {
            console.error('❌ Error monitoring agent activity:', err);
            return;
        }
        
        rows.forEach(row => {
            if (row.rowid > (monitorAgentActivity.lastRowId || 0)) {
                monitorAgentActivity.lastRowId = Math.max(monitorAgentActivity.lastRowId || 0, row.rowid);
                
                // Parse JSON details
                let details = {};
                try {
                    details = JSON.parse(row.details || '{}');
                } catch (e) {
                    console.error('❌ Error parsing agent details:', e);
                    details = {};
                }
                
                // Create notification based on agent activity
                let notification = null;
                
                if (row.agent_name === 'notification_agent' && details.priority_score >= 8.0) {
                    notification = {
                        type: 'EMERGENCY',
                        message: `🚨 Emergency notification sent for incident ${row.incident_id}`,
                        timestamp: row.timestamp,
                        agent: row.agent_name
                    };
                } else if (row.agent_name === 'trend_analysis_agent') {
                    notification = {
                        type: 'INFO',
                        message: `📊 Trend Alert: ${details.insight || 'Pattern detected'}`,
                        timestamp: row.timestamp,
                        agent: row.agent_name
                    };
                } else if (row.agent_name === 'resource_allocation_agent') {
                    notification = {
                        type: 'INFO',
                        message: `🎯 Resource Update: ${details.allocation ? JSON.stringify(details.allocation) : 'Allocation optimized'}`,
                        timestamp: row.timestamp,
                        agent: row.agent_name
                    };
                } else if (row.agent_name === 'news_insights_agent') {
                    notification = {
                        type: 'INFO',
                        message: `📰 News Update: ${details.news_impact || 'Daily summary generated'}`,
                        timestamp: row.timestamp,
                        agent: row.agent_name
                    };
                }
                
                if (notification) {
                    io.emit('notification', notification);
                }
            }
        });
    });
}

// Periodic tasks
const STATS_UPDATE_INTERVAL = parseInt(process.env.STATS_UPDATE_INTERVAL) || 2000;
const STATS_BROADCAST_INTERVAL = parseInt(process.env.STATS_BROADCAST_INTERVAL) || 10000;

setInterval(() => {
    updateStats();
    monitorIncidents();
    monitorAgentActivity();
}, STATS_UPDATE_INTERVAL);

setInterval(() => {
    // Broadcast stats
    io.emit('stats_update', stats);
}, STATS_BROADCAST_INTERVAL);

console.log(`⏱️  Update intervals configured: Stats=${STATS_UPDATE_INTERVAL}ms, Broadcast=${STATS_BROADCAST_INTERVAL}ms`);

// Initialize
initializeDatabases();

// Start server
server.listen(PORT, () => {
    console.log('🚀 City Pulse WebSocket Server Started');
    console.log('=====================================');
    console.log(`📡 Server running on port ${PORT}`);
    console.log(`🌐 Dashboard: http://localhost:${PORT}`);
    console.log(`🔌 WebSocket: ws://localhost:${PORT}`);
    console.log('=====================================');
    
    // Initial stats update
    setTimeout(updateStats, 1000);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down server...');
    
    if (db) {
        db.close((err) => {
            if (err) {
                console.error('❌ Error closing incidents database:', err);
            } else {
                console.log('✅ Incidents database closed');
            }
        });
    }
    
    if (agentDb) {
        agentDb.close((err) => {
            if (err) {
                console.error('❌ Error closing agent database:', err);
            } else {
                console.log('✅ Agent database closed');
            }
        });
    }
    
    server.close(() => {
        console.log('✅ Server closed');
        process.exit(0);
    });
});

module.exports = app;
