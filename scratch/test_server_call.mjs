import { createServer, loadConfigFromEnv } from '@aifinpay/mcp';

async function main() {
    const config = loadConfigFromEnv();
    const { server, agent } = await createServer(config);
    console.log("Server created successfully.");
    console.log("Solana:", agent.solanaAddress);
    console.log("EVM:", agent.evmAddress);
}

main().catch(console.error);
