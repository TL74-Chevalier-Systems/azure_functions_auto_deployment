# TL74 Azure Functions

A collection of Azure Functions that process SEC filing data for financial analysis and LLM-based insights.

## Overview

This project provides a serverless architecture for processing SEC filings (10-K, 10-Q, 13F-HR) through multiple analysis pipelines:

1. **Entry Point Function**: Receives filing information and coordinates analysis workflows
2. **Financial Health Analysis**: Extracts and calculates key financial ratios and metrics
3. **LLM Analysis**: Provides advanced natural language analysis of filings

The system stores all results in Azure Cosmos DB, creating a comprehensive financial data repository.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌───────────────────┐
│ Entry Point │────>│ Financial    │────>│                   │
│ Function    │     │ Health       │     │                   │
└─────────────┘     │ Analysis     │     │                   │
       │            └──────────────┘     │                   │
       │                                 │   Azure Cosmos DB │
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

## Setup and Configuration

### Prerequisites

- Azure subscription
- Azure Function App 
- Azure Cosmos DB instance
- GitHub account
- SEC EDGAR identity (email)
- OpenAI API access

### Environment Variables

The following environment variables must be configured:

```
# Azure Cosmos DB
COSMOS_DB_URL
COSMOS_DB_KEY
COSMOS_DB_DATABASE
COSMOS_DB_CONTAINER_FILINGS

# API Keys
TRIGGER_API_KEY

# SEC EDGAR
EDGAR_IDENTITY

# OpenAI/LLM Configuration
BASE_URL
MAX_TOKENS
```

### Deployment

This project uses GitHub Actions for CI/CD. When you push to the repository, it automatically deploys to your Azure Function App.

1. Set up the GitHub secrets:
   - `AZURE_FUNCTIONAPP_PUBLISH_PROFILE`: The publish profile from your Azure Function App
   - `LLM_ANALYSIS_SSH`: SSH key for the LLM analysis submodule

2. Push to the repository to trigger the deployment workflow

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
3. Trigger the LLM Analysis (for 10-K and 10-Q forms)
4. Update the Cosmos DB record with the analysis results

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
├── LLMAnalysis/                 # LLM analysis function
│   ├── __init__.py
│   ├── function.json
│   ├── llm_analy_wrapper.py     # Handles requests & DB operations
│   └── llm_analysis_repo/       # Submodule with LLM analysis code
├── host.json                    # Function app configuration
└── requirements.txt             # Python dependencies
```
