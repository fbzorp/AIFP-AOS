#!/bin/bash
# Send a test alert to Alertmanager for verification

ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"

cat <<EOF | curl -XPOST "${ALERTMANAGER_URL}/api/v1/alerts" -H 'Content-Type: application/json' -d @-
[
  {
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning",
      "instance": "test-instance"
    },
    "annotations": {
      "summary": "This is a test alert from AIFP-AOS",
      "description": "Manual test alert to verify Alertmanager and webhook integration"
    },
    "generatorURL": "http://test-generator",
    "startsAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  }
]
EOF

echo "Test alert sent to Alertmanager at ${ALERTMANAGER_URL}"
echo "Check Alertmanager UI at ${ALERTMANAGER_URL} and verify Telegram notification"