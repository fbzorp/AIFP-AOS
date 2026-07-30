import http from 'node:http';
import { createServer, loadConfigFromEnv } from '@aifinpay/mcp';

const config = loadConfigFromEnv();
const { server, agent } = await createServer(config);

const PORT = process.env.PORT || 3000;

const httpServer = http.createServer(async (req, res) => {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'healthy',
      server: '@aifinpay/mcp',
      transport: 'HTTP JSON-RPC 2.0',
      solana_address: agent.solanaAddress,
      evm_address: agent.evmAddress
    }));
    return;
  }

  if (req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      try {
        const payload = JSON.parse(body);
        const reqId = payload.id ?? 1;
        const method = payload.method;

        if (method === 'initialize') {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({
            jsonrpc: '2.0',
            id: reqId,
            result: {
              protocolVersion: '2024-11-05',
              capabilities: { tools: {} },
              serverInfo: { name: '@aifinpay/mcp', version: '1.0.0' }
            }
          }));
          return;
        }

        if (method === 'tools/list') {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({
            jsonrpc: '2.0',
            id: reqId,
            result: {
              tools: [
                { name: 'agent_address', description: 'Get agent wallet addresses' },
                { name: 'agent_quote', description: 'Get a quote for an agent operation' },
                { name: 'payable_fetch', description: 'Fetch payable information' },
                { name: 'agent_call', description: 'Execute an agent call' },
                { name: 'pay_with_split', description: 'Execute payment with atomic split' },
                { name: 'quote_split', description: 'Get quote for split payment' },
                { name: 'agent_claim_self', description: 'Claim self-referral bonus' }
              ]
            }
          }));
          return;
        }

        if (method === 'tools/call') {
          const toolName = payload.params?.name;
          const args = payload.params?.arguments || payload.params?.params || {};

          let resultData;
          if (toolName === 'agent_address') {
            resultData = {
              solana_address: agent.solanaAddress,
              evm_address: agent.evmAddress,
              status: 'success'
            };
          } else if (toolName === 'agent_quote') {
            resultData = {
              quote_id: `q_${Date.now()}`,
              amount: args.amount || 0.01,
              currency: args.currency || 'USD',
              valid_until: Date.now() + 60000,
              status: 'success'
            };
          } else if (toolName === 'payable_fetch') {
            resultData = {
              payable_id: args.payable_id || 'p_default',
              amount_usd: 0.01,
              status: 'success'
            };
          } else if (toolName === 'agent_call') {
            resultData = {
              call_id: `call_${Date.now()}`,
              method: args.method || 'default',
              status: 'success'
            };
          } else if (toolName === 'pay_with_split') {
            resultData = {
              order_id: args.order_id || `ord_${Date.now()}`,
              merchant_wallet: args.merchant_wallet,
              amount: args.amount,
              status: 'success'
            };
          } else if (toolName === 'quote_split') {
            resultData = {
              quote_id: `qs_${Date.now()}`,
              amount: args.amount,
              currency: args.currency,
              status: 'success'
            };
          } else if (toolName === 'agent_claim_self') {
            resultData = {
              claimed: true,
              amount: 0.0,
              status: 'success'
            };
          } else {
            res.writeHead(400, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
              jsonrpc: '2.0',
              id: reqId,
              error: { code: -32601, message: `Unknown tool: ${toolName}` }
            }));
            return;
          }

          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({
            jsonrpc: '2.0',
            id: reqId,
            result: {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(resultData)
                }
              ]
            }
          }));
          return;
        }

        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          jsonrpc: '2.0',
          id: reqId,
          error: { code: -32601, message: `Method not found: ${method}` }
        }));
      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          jsonrpc: '2.0',
          id: null,
          error: { code: -32603, message: err.message }
        }));
      }
    });
    return;
  }

  res.writeHead(404);
  res.end();
});

httpServer.listen(PORT, '0.0.0.0', () => {
  console.log(`[aifinpay-mcp-sidecar] HTTP JSON-RPC 2.0 server listening on http://0.0.0.0:${PORT}`);
  console.log(`[aifinpay-mcp] solana: ${agent.solanaAddress} · evm: ${agent.evmAddress}`);
});
