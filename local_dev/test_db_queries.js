const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Use the same database path as the server
const DB_PATH = path.join(__dirname, 'local_incidents.db');

console.log('🧪 Testing database queries...');
console.log('📂 Database path:', DB_PATH);

const db = new sqlite3.Database(DB_PATH, (err) => {
    if (err) {
        console.error('❌ Error connecting to database:', err);
        return;
    }
    console.log('✅ Connected to database');
    
    // Test 1: Total incidents
    console.log('\n📊 Test 1: Total incidents');
    db.get('SELECT COUNT(*) as count FROM incidents', [], (err, row) => {
        if (err) {
            console.error('❌ Error:', err);
        } else {
            console.log('✅ Total incidents:', row.count);
        }
    });
    
    // Test 2: High priority incidents
    console.log('\n🚨 Test 2: High priority incidents');
    db.get('SELECT COUNT(*) as count FROM incidents WHERE priority_score >= 8', [], (err, row) => {
        if (err) {
            console.error('❌ Error:', err);
        } else {
            console.log('✅ High priority incidents:', row.count);
        }
    });
    
    // Test 3: Recent incidents (last hour)
    console.log('\n⏰ Test 3: Recent incidents (last hour)');
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    console.log('🕐 One hour ago timestamp:', oneHourAgo);
    
    db.get(`
        SELECT COUNT(*) as count 
        FROM incidents 
        WHERE processed_at > ?
    `, [oneHourAgo], (err, row) => {
        if (err) {
            console.error('❌ Error:', err);
        } else {
            console.log('✅ Recent incidents:', row.count);
        }
    });
    
    // Test 4: Sample of recent timestamps
    console.log('\n📅 Test 4: Sample timestamps');
    db.all(`
        SELECT processed_at, timestamp 
        FROM incidents 
        ORDER BY rowid DESC 
        LIMIT 5
    `, [], (err, rows) => {
        if (err) {
            console.error('❌ Error:', err);
        } else {
            console.log('✅ Sample timestamps:');
            rows.forEach((row, i) => {
                console.log(`  ${i+1}. processed_at: ${row.processed_at}`);
                console.log(`     timestamp: ${row.timestamp}`);
            });
        }
    });
    
    // Test 5: Agent activities table
    console.log('\n🤖 Test 5: Agent activities');
    db.get('SELECT COUNT(*) as count FROM agent_activities', [], (err, row) => {
        if (err) {
            console.error('❌ Error (table might not exist):', err.message);
        } else {
            console.log('✅ Total agent activities:', row.count);
            
            // Test recent agent activities
            const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString();
            db.all(`
                SELECT agent_name, COUNT(*) as count 
                FROM agent_activities 
                WHERE timestamp > ?
                GROUP BY agent_name
            `, [oneHourAgo], (err, rows) => {
                if (err) {
                    console.error('❌ Error getting recent agent activities:', err);
                } else {
                    console.log('✅ Recent agent activities:');
                    rows.forEach(row => {
                        console.log(`  ${row.agent_name}: ${row.count}`);
                    });
                }
                
                // Close database
                db.close((err) => {
                    if (err) {
                        console.error('❌ Error closing database:', err);
                    } else {
                        console.log('\n✅ Database connection closed');
                    }
                });
            });
        }
    });
});
