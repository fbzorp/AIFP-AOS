import { createServer, loadConfigFromEnv } from '@aifinpay/mcp';

async function test() {
    const config = loadConfigFromEnv();
    const { server, agent } = await createServer(config);
    console.log('Solana Address:', agent.solanaAddress);
    console.log('EVM Address:', agent.evmAddress);
}

test().catch(console.error);
