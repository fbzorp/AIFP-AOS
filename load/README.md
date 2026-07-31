# Load Testing

This directory contains Locust load testing configuration for the AIFP-AOS API.

## Running Load Tests

### Prerequisites
- Docker Compose stack running (`docker compose -f docker-compose.dev.yml up`)
- Locust installed (`pip install locust`)

### Local Testing
```bash
# Run against local stack
locust -f locustfile.py --host=http://localhost:8000

# Headless mode with specific parameters
locust -f locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 60s
```

### Using Makefile
```bash
make load-test
```

### Docker-based Testing
```bash
# Run locust in Docker
docker run -p 8089:8089 -v $(pwd):/locust locustio/locust -f /locust/locustfile.py --host=http://host.docker.internal:8000
```

## Test Scenarios

### AIFPUser
- **Weight**: 5
- **Focus**: General API read operations
- **Endpoints**: Health check, content queue, approvals, payments list, engagement proposals
- **Pattern**: 60% read operations, 20% content/approval queue, 20% payments/proposals

### ContentUser  
- **Weight**: 2
- **Focus**: Content submission workflow
- **Endpoints**: Content queue view, content submission
- **Pattern**: 75% view queue, 25% submit content

### ApprovalUser
- **Weight**: 1
- **Focus**: Approval workflow
- **Endpoints**: Approvals list, content queue
- **Pattern**: 75% view approvals, 25% view content queue

## Important Notes

- **No Live Payments**: Load tests target read-only and enqueue paths only
- **No On-Chain Execution**: Payment execution endpoints are not load-tested
- **Rate Limiting**: Adjust wait times and user counts based on your environment
- **Authentication**: Some endpoints may require authentication - current tests are unauthenticated

## Parameters

- `-u, --users`: Number of concurrent users (default: 1)
- `-r, --spawn-rate`: Rate at which users spawn (default: 1 per second)
- `-t, --run-time`: Total run time (e.g., 60s, 5m)
- `--headless`: Run without web UI

## Example Results

After running load tests, you'll see:
- **RPS**: Requests per second
- **Failures**: Failed requests and error rates
- **Response Times**: Min, average, median, 95th percentile
- **Distribution**: Response time distribution across percentiles