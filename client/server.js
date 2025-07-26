const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Configuration
const PORT = process.env.PORT || 3002;
const DB_PATH = '/app/local_dev/local_incidents.db';
const AGENT_DB_PATH = '/app/local_dev/local_incidents.db';

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
        SELECT * FROM agent_activity 
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
setInterval(() => {
    updateStats();
    monitorIncidents();
    monitorAgentActivity();
}, 2000); // Check every 2 seconds

setInterval(() => {
    // Broadcast stats every 10 seconds
    io.emit('stats_update', stats);
}, 10000);

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
