// Quick test to run the exact same queries as the server
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const DB_PATH = path.join(__dirname, 'local_incidents.db');
console.log('Database path:', DB_PATH);

const db = new sqlite3.Database(DB_PATH, (err) => {
    if (err) {
        console.error('Error:', err);
        return;
    }
    
    console.log('✅ Connected to database');
    
    // Test the exact same queries as updateStats
    console.log('\n=== TESTING EXACT QUERIES FROM updateStats ===');
    
    // 1. Total incidents
    db.get('SELECT COUNT(*) as count FROM incidents', [], (err, row) => {
        if (err) {
            console.error('❌ Total incidents error:', err);
        } else {
            console.log('📊 Total incidents:', row.count);
        }
    });
    
    // 2. High priority incidents  
    db.get('SELECT COUNT(*) as count FROM incidents WHERE priority_score >= 8', [], (err, row) => {
        if (err) {
            console.error('❌ High priority error:', err);
        } else {
            console.log('🚨 High priority incidents:', row.count);
        }
    });
    
    // 3. Recent incidents (last hour) - EXACT same logic as server
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    console.log('⏰ One hour ago timestamp:', oneHourAgo);
    
    db.get(`
        SELECT COUNT(*) as count 
        FROM incidents 
        WHERE processed_at > ?
    `, [oneHourAgo], (err, row) => {
        if (err) {
            console.error('❌ Recent incidents error:', err);
        } else {
            console.log('⚡ Recent incidents (last hour):', row.count);
        }
        
        // Close database
        db.close();
    });
});
