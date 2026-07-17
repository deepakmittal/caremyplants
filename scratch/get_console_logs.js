const WebSocket = require('../mobile/node_modules/ws');
const http = require('http');

// 1. Fetch the debugging targets
http.get('http://localhost:9222/json', (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
        try {
            const targets = JSON.parse(data);
            const pageTarget = targets.find(t => t.type === 'page' && t.url.includes('localhost:5173'));
            if (!pageTarget) {
                console.error("Could not find the localhost:8081 page target. Targets found:", targets);
                process.exit(1);
            }

            console.log("Connecting to target WebSocket:", pageTarget.webSocketDebuggerUrl);
            const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);

            ws.on('open', () => {
                // Enable Console and Runtime domains
                ws.send(JSON.stringify({ id: 1, method: 'Console.enable' }));
                ws.send(JSON.stringify({ id: 2, method: 'Runtime.enable' }));
                ws.send(JSON.stringify({ id: 3, method: 'Page.reload' }));
                console.log("Listening for console messages and exceptions...");
            });

            ws.on('message', (message) => {
                const event = JSON.parse(message);
                
                // Print console messages
                if (event.method === 'Console.messageAdded') {
                    console.log(`[Browser Console ${event.params.message.level}]:`, event.params.message.text);
                }
                
                // Print exceptions
                if (event.method === 'Runtime.exceptionThrown') {
                    const details = event.params.exceptionDetails;
                    console.error(`[Browser Exception]:`, details.exception.description || details.text);
                    if (details.stackTrace) {
                        console.error("Stack trace:");
                        details.stackTrace.callFrames.forEach(f => {
                            console.error(`  at ${f.functionName} (${f.url}:${f.lineNumber}:${f.columnNumber})`);
                        });
                    }
                }
            });

            ws.on('error', (err) => {
                console.error("WebSocket error:", err);
            });

            // Run for 3 seconds then exit
            setTimeout(() => {
                console.log("Finished listening.");
                ws.close();
                process.exit(0);
            }, 4000);

        } catch (e) {
            console.error("Failed to parse targets JSON:", e);
            process.exit(1);
        }
    });
}).on('error', (err) => {
    console.error("Failed to connect to Chrome debug port:", err);
    process.exit(1);
});
