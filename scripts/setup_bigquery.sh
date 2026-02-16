#!/bin/bash
# Setup Google Cloud BigQuery for EcoCI carbon tracking

set -e

PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
DATASET_ID="${BIGQUERY_DATASET:-ecoci_metrics}"
TABLE_ID="pipeline_runs"

echo "🔧 Setting up BigQuery for EcoCI"
echo "Project: ${PROJECT_ID}"
echo "Dataset: ${DATASET_ID}"

# Create dataset
echo "📊 Creating dataset ${DATASET_ID}..."
bq mk --dataset \
  --location=US \
  --description="EcoCI carbon emissions tracking" \
  "${PROJECT_ID}:${DATASET_ID}" 2>/dev/null || echo "Dataset already exists"

# Create table with schema
echo "📋 Creating table ${TABLE_ID}..."
bq mk --table \
  "${PROJECT_ID}:${DATASET_ID}.${TABLE_ID}" \
  pipeline_id:INTEGER,project_id:INTEGER,project_name:STRING,run_timestamp:TIMESTAMP,total_duration_seconds:INTEGER,total_energy_wh:FLOAT,total_co2_grams:FLOAT,optimizations_applied:STRING,savings_percent:FLOAT,runner_region:STRING,gitlab_ci_yml_hash:STRING \
  2>/dev/null || echo "Table already exists"

echo ""
echo "✅ BigQuery setup complete!"
echo ""
echo "Test with a query:"
echo "bq query --use_legacy_sql=false 'SELECT COUNT(*) as total_runs FROM \`${PROJECT_ID}.${DATASET_ID}.${TABLE_ID}\`'"
echo ""
echo "View in console:"
echo "https://console.cloud.google.com/bigquery?project=${PROJECT_ID}&page=table&d=${DATASET_ID}&t=${TABLE_ID}"
