# TL74 Azure Functions

A collection of Azure Functions that process SEC filing data for financial analysis and LLM-based insights.

## Overview

This project provides a serverless architecture for processing SEC filings (10-K, 10-Q, 13F-HR) through multiple analysis pipelines:

1. **Entry Point Function**: Receives filing information and coordinates analysis workflows
2. **Financial Health Analysis**: Extracts and calculates key financial ratios and metrics
3. **13F Holding Analysis**: Extracts and simplifies institutional financial holding data
4. **LLM Analysis**: Provides advanced natural language analysis of filings

The system stores all results in Azure Cosmos DB, creating a comprehensive financial data repository.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌───────────────────┐
│ Entry Point │────>│ Financial    │     │                   │
│ Function    │     │ Health       │────>│                   │
└─────────────┘     │ Analysis     │     │                   │
       │            └──────────────┘     │                   │            ┌────────────────┐
       │            ┌──────────────┐     │                   │            │   Frontend     │ 
       └───────────>│ 13F Analysis │────>│ Azure Cosmos DB   │─ ─ ─ ─ ─ ─>│ (External to   │
       │            │              │     │                   │            │          repo) │
       │            └──────────────┘     │                   │            └────────────────┘
       │            ┌──────────────┐     │                   │
       └───────────>│ LLM Analysis │────>│                   │
                    │              │     │                   │
                    └──────────────┘     └───────────────────┘

```

## Features

- **Automated SEC Filing Processing**: Automatically processes SEC filings when they become available
- **Financial Health Analysis**: Calculates key financial metrics including:
  - Liquidity ratios (Current Ratio, Quick Ratio)
  - Solvency ratios (Debt to Equity, Interest Coverage)
  - Profitability ratios (Gross Margin, Operating Margin, Net Margin)
  - Efficiency ratios (Inventory Turnover, Asset Turnover)
- **13F Holding Analysis**: Determines financial data including:
  - Share Amounts and Values of company stocks held by institutional managers
  - Comparative holdings of a company between periods
- **LLM-Based Analysis**: Uses large language models to analyze:
  - Competitive analysis
  - Risk assessment
- **Scalable Serverless Architecture**: Built on Azure Functions for automatic scaling
- **Persistent Storage**: All analyses are stored in Azure Cosmos DB

## Technology Stack

- **Azure Functions**: Serverless compute platform
- **Azure Cosmos DB**: NoSQL database for storing analysis results
- **Python**: Main programming language
- **EDGAR Tools**: SEC filing access and processing
- **OpenAI API**: For LLM-based analysis
- **GitHub Actions**: CI/CD pipeline for automatic deployment

## Step-by-Step Deployment Guide

### Prerequisites

Before deploying the TL74 Azure Functions, ensure you have:

1. An Azure account with an active subscription
2. A GitHub account
3. Git installed on your local machine
4. Access to SEC EDGAR API (registered email address)
5. Access to OpenAI API or equivalent LLM service

### Step 1: Set Up Azure Resources

1. **Create an Azure Function App**:
   - Log in to the [Azure Portal](https://portal.azure.com)
   - Click "Create a resource" > "Compute" > "Function App"
   - Fill in the basic details:
     - Subscription: Select your subscription
     - Resource Group: Create new or use existing
     - Function App name: `TL74FunctionsApp` (must be globally unique)
     - Publish: Code
     - Runtime stack: Python
     - Version: 3.11
     - Region: Choose a region close to your location
   - Click "Review + create" > "Create"
   - Wait for deployment to complete

2. **Create an Azure Cosmos DB Account**:
   - In the Azure Portal, click "Create a resource" > "Databases" > "Azure Cosmos DB"
   - Select "Core (SQL) API"
   - Fill in the required details:
     - Subscription: Select your subscription
     - Resource Group: Use the same as for Function App
     - Account Name: `TL74CosmosDB` (must be globally unique)
     - Location: Choose the same region as your Function App
     - Capacity mode: Provisioned throughput
   - Click "Review + create" > "Create"
   - Wait for deployment to complete

3. **Create a Database and Container in Cosmos DB**:
   - Once the Cosmos DB account is created, go to its resource page
   - Click "Data Explorer" > "New Database"
   - Database id: `TL74Database`
   - Throughput: Manual (400 RU/s minimum for cost-effectiveness)
   - Click "OK"
   - Select the created database > "New Container"
   - Container id: `Filings`
   - Partition key: `/ticker` (ensure the leading slash)
   - Click "OK"

### Step 2: Configure Development Environment

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/TL74-Functions.git
   cd TL74-Functions
   ```

2. **Initialize and Update Submodules**:
   ```bash
   git submodule update --init --recursive
   ```

### Step 3: Configure GitHub Secrets

In your GitHub repository:

1. Go to "Settings" > "Secrets and variables" > "Actions"
2. Add the following secrets:
   - `AZURE_FUNCTIONAPP_PUBLISH_PROFILE`: 
     - Go to your Function App in the Azure Portal
     - Click "Overview" > "Get publish profile"
     - Download the file and copy its entire contents
     - Paste as the secret value
   - `LLM_ANALYSIS_SSH`: Your SSH private key for LLM analysis repo
   - `ANALYSIS_13F_SSH`: Your SSH private key for 13F-Analysis repo

### Step 4: Configure Azure Function App Settings

1. **Set Application Settings in Azure Portal**:
   - Go to your Function App in the Azure Portal
   - Click "Configuration" > "Application settings" > "New application setting"
   - Add the following key-value pairs:

   ```
   # Azure Cosmos DB
   COSMOS_DB_URL=https://your-cosmosdb-name.documents.azure.com:443/
   COSMOS_DB_KEY=your_cosmos_db_primary_key
   COSMOS_DB_DATABASE=TL74Database
   COSMOS_DB_CONTAINER_FILINGS=Filings

   # API Keys
   TRIGGER_API_KEY=your_function_app_default_key

   # SEC EDGAR
   EDGAR_IDENTITY=your_email@example.com

   # OpenAI/LLM Configuration
   BASE_URL=https://api.openai.com/v1
   MAX_TOKENS=4096
   ```

   - Get the Cosmos DB URL and key from the Azure Cosmos DB resource under "Keys"
   - Get the TRIGGER_API_KEY from Function App > App keys > _master
   - Click "Save"

### Step 5: Deploy the Function App

**Option 1: Automatic Deployment via GitHub Actions**

1. Push your changes to GitHub:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. This will automatically trigger the GitHub Actions workflow defined in `.github/workflows/deploy.yml`

3. Monitor the deployment in the "Actions" tab of your GitHub repository

**Option 2: Manual Deployment via Azure Functions Core Tools**

1. Install Azure Functions Core Tools:
   ```bash
   npm install -g azure-functions-core-tools@4
   ```

2. Log in to Azure:
   ```bash
   az login
   ```

3. Deploy the function app:
   ```bash
   cd TL74Functions
   func azure functionapp publish TL74FunctionsApp
   ```

### Step 6: Verify Deployment

1. **Test the EntryPoint Function**:
   - In the Azure Portal, go to your Function App
   - Select "Functions" > "EntryPoint" > "Code + Test"
   - Click "Test/Run"
   - For the body, enter:
     ```json
     {
       "accession_code": "0000000000-00-000000",
       "ticker": "AAPL",
       "date": "2023-01-01",
       "form": "10-K"
     }
     ```
   - Click "Run"
   - You should see a successful response

2. **Verify Cosmos DB Entries**:
   - Go to your Cosmos DB account in Azure Portal
   - Click "Data Explorer"
   - Expand your database and container
   - You should see a document with the entry details

### Step 7: Monitoring

1. **Set Up Application Insights** (optional but recommended):
   - In the Azure Portal, go to your Function App
   - Click "Application Insights" > "Turn on Application Insights"
   - Follow the prompts to create a new Application Insights resource
   - This will enable detailed monitoring and logging

2. **View Function Logs**:
   - In your Function App, click "Functions" > Select a function > "Monitor"
   - Here you can view invocation logs and track function performance

## Usage

### Processing a Filing

To process a filing, send a POST request to the EntryPoint function with the following parameters:

```json
{
  "accession_code": "0000000000-00-000000",
  "ticker": "SYMB",
  "date": "2023-01-01",
  "form": "10-K"
}
```

The system will:
1. Store the filing information in Cosmos DB
2. Trigger the Financial Health Analysis (for 10-K and 10-Q forms)
3. Trigger the 13F Holding Analysis (for 13F-HR forms)
4. Trigger the LLM Analysis (for 10-K and 10-Q forms)
5. Update the Cosmos DB record with the analysis results

## Troubleshooting

- **Deployment Failures**: Check GitHub Actions logs for error details
- **Function Execution Errors**: Check Application Insights or Function logs
- **Missing Environment Variables**: Verify all application settings are correctly set
- **Submodule Issues**: Ensure SSH keys are correctly configured and submodules are initialized

## Project Structure

```
TL74Functions/
├── EntryPoint/                  # Main entry function
│   ├── __init__.py
│   ├── function.json
│   └── helpers.py              
├── FinancialHealth/             # Financial analysis function
│   ├── __init__.py
│   ├── function.json
│   ├── fha.py                   # Main analysis logic
│   └── fha_wrapper.py           # Handles requests & DB operations
├── 13F/                         # 13F analysis function
│   ├── __init__.py
│   ├── function.json
│   ├── wrapper_13f.py           # Handles requests & DB operations
│   └── 13F-Analysis/            # Submodule with 13F analysis code
├── LLMAnalysis/                 # LLM analysis function
│   ├── __init__.py
│   ├── function.json
│   ├── llm_analy_wrapper.py     # Handles requests & DB operations
│   └── llm_analysis_repo/       # Submodule with LLM analysis code
├── host.json                    # Function app configuration
└── requirements.txt             # Python dependencies
```
