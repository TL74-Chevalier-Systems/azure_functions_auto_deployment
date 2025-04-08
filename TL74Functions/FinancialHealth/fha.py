from edgar import *
import pandas as pd
from dotenv import load_dotenv
import os
import json

def fha(accn):

    identity = os.getenv("EDGAR_IDENTITY")
    set_identity(identity)

    class DB_ANALYSIS:
        def __init__(self):
            self.value = None
            self.definition = None
            self.if_missing = None
            self.missing_explain = None
            self.if_generate = None
            self.generate_explain = None

    try:
        filing = get_by_accession_number(str(accn))
    except Exception as e:
        return "FHA Error: unable to find filing with accession number " + str(accn)

    try:
        company = Company(str(filing.cik)).get_facts().to_pandas()
    except Exception as e:
        return "FHA Error: unable to generate pandas dataframe for company with CIK " + str(filing.cik)

    try:
        company_accn_subset = company[(company['namespace'] == 'us-gaap') & (company['accn'] == str(accn))]
    except Exception as e:
        return f"FHA Error extracting rows for accession number {accn}: {e}"

    try:
        subset_json_dict = {} # Convert the dataframe to a JSON-serializable dictionary, keyed by the row index
        company_accn_subset = company_accn_subset.reset_index()
        for idx, row in company_accn_subset.iterrows():
            row_data = row.to_dict()  # Convert each row to a dictionary
            subset_json_dict[str(idx)] = row_data  # Use the dataframe index as the key, convert to string for JSON compatibility

    except Exception as e:
        return f"FHA Error converting dataframe subset to JSON: {e}"

    try:
        company['end'] = pd.to_datetime(company['end'])
        company['timestamp'] = company['end'].astype('int64')
    except Exception as e:
        return "FHA Error: unable to parse/organize date format"

    def retrieve_value_full(company, accn, fact_name):
        try:
            filtered_df = company[(company['namespace'] == 'us-gaap') & (company['accn'] == str(accn)) & (company['fact'] == str(fact_name))]
            filtered_df = filtered_df.loc[filtered_df['timestamp'].idxmax()]
            value = filtered_df['val']
            return value, "NO", "N/A"
        except Exception as e:
            return "N/A", "YES", "Unable to locate parameter in data sheets"
        
    def retrieve_value_partial(company, accn, fact_name):
        try:
            filtered_df = company[(company['namespace'] == 'us-gaap') & (company['accn'] == str(accn)) & (company['fact'] == str(fact_name))]
            filtered_df = filtered_df.loc[filtered_df['timestamp'].idxmax()]
            value = filtered_df['val']
            return value
        except Exception as e:
            return "N/A"


    assets = DB_ANALYSIS()
    liabilities = DB_ANALYSIS()
    equity = DB_ANALYSIS()

    assets.value, assets.if_missing, assets.missing_explain = retrieve_value_full(company, accn, "Assets")
    equity.value, equity.if_missing, equity.missing_explain = retrieve_value_full(company, accn, "StockholdersEquity")

    if assets.value != "N/A" and equity.value != "N/A":
        liabilities.value = int(assets.value) - int(equity.value)
        liabilities.if_missing = "NO"
        liabilities.missing_explain = "N/A"
    else:
        liabilities.value = "N/A"
        liabilities.if_missing = "YES"
        liabilities.missing_explain = "Unable to locate parameter in data sheets"


    revenue = DB_ANALYSIS()
    expenses = DB_ANALYSIS()
    net_income = DB_ANALYSIS()

    revenue.value, revenue.if_missing, revenue.missing_explain = retrieve_value_full(company, accn, "Revenues")
    net_income.value, net_income.if_missing, net_income.missing_explain = retrieve_value_full(company, accn, "NetIncomeLoss")

    if revenue.value != "N/A" and net_income.value != "N/A":
        expenses.value = int(revenue.value) - int(net_income.value)
        expenses.if_missing = "NO"
        expenses.missing_explain = "N/A"
    else:
        expenses.value = "N/A"
        expenses.if_missing = "YES"
        expenses.missing_explain = "Unable to locate parameter in data sheets"


    operate_act = DB_ANALYSIS()
    invest_act = DB_ANALYSIS()
    finance_act = DB_ANALYSIS()

    operate_act.value, operate_act.if_missing, operate_act.missing_explain = retrieve_value_full(company, accn, "NetCashProvidedByUsedInOperatingActivities")
    invest_act.value, invest_act.if_missing, invest_act.missing_explain = retrieve_value_full(company, accn, "NetCashProvidedByUsedInInvestingActivities")
    finance_act.value, finance_act.if_missing, finance_act.missing_explain = retrieve_value_full(company, accn, "NetCashProvidedByUsedInFinancingActivities")


    current_ratio = DB_ANALYSIS()

    INTR_current_assets = retrieve_value_partial(company, accn, "AssetsCurrent")
    INTR_current_liabilities = retrieve_value_partial(company, accn, "LiabilitiesCurrent")

    if INTR_current_assets != "N/A" and INTR_current_liabilities != "N/A":
        current_ratio.value = float(INTR_current_assets) / float(INTR_current_liabilities)
        current_ratio.if_missing = "NO"
        current_ratio.missing_explain = "N/A"
    else:
        current_ratio.value = "N/A"
        current_ratio.if_missing = "YES"
        current_ratio.missing_explain = "Unable to locate parameter in data sheets"


    quick_ratio = DB_ANALYSIS()

    INTR_cash_and_cash_equivalents = retrieve_value_partial(company, accn, "CashAndCashEquivalentsAtCarryingValue")
    INTR_short_term_investments = retrieve_value_partial(company, accn, "ShortTermInvestments")
    INTR_account_receivables = retrieve_value_partial(company, accn, "AccountsReceivableNetCurrent")

    if INTR_cash_and_cash_equivalents != "N/A" and INTR_short_term_investments != "N/A" and INTR_account_receivables != "N/A" and INTR_current_liabilities != "N/A":
        quick_ratio.value = float((INTR_cash_and_cash_equivalents + INTR_short_term_investments + INTR_account_receivables)) / float(INTR_current_liabilities)
        quick_ratio.if_missing = "NO"
        quick_ratio.missing_explain = "N/A"
    else:
        quick_ratio.value = "N/A"
        quick_ratio.if_missing = "YES"
        quick_ratio.missing_explain = "Unable to locate parameter in data sheets"

    
    debt_to_equity_ratio = DB_ANALYSIS()

    if liabilities.value != "N/A" and equity.value != "N/A":
        debt_to_equity_ratio.value = float(liabilities.value) / float(equity.value)
        debt_to_equity_ratio.if_missing = "NO"
        debt_to_equity_ratio.missing_explain = "N/A"
    else:
        debt_to_equity_ratio.value = "N/A"
        debt_to_equity_ratio.if_missing = "YES"
        debt_to_equity_ratio.missing_explain = "Unable to locate parameter in data sheets"


    interest_coverage_ratio = DB_ANALYSIS()

    INTR_cost_of_goods_sold = retrieve_value_partial(company, accn, "CostOfGoodsAndServicesSold")
    INTR_operating_expenses = retrieve_value_partial(company, accn, "OperatingIncomeLoss")
    INTR_interest_expense = retrieve_value_partial(company, accn, "InterestAndDebtExpense")

    if revenue.value != "N/A" and INTR_cost_of_goods_sold != "N/A" and INTR_operating_expenses != "N/A" and INTR_interest_expense != "N/A":
        interest_coverage_ratio.value = float((revenue.value - INTR_cost_of_goods_sold - INTR_operating_expenses)) / float(INTR_interest_expense)
        interest_coverage_ratio.if_missing = "NO"
        interest_coverage_ratio.missing_explain = "N/A"
    else:
        interest_coverage_ratio.value = "N/A"
        interest_coverage_ratio.if_missing = "YES"
        interest_coverage_ratio.missing_explain = "Unable to locate parameter in data sheets"


    gross_margin_ratio = DB_ANALYSIS()

    INTR_gross_profit = retrieve_value_partial(company, accn, "GrossProfit")

    if INTR_gross_profit != "N/A" and revenue.value != "N/A":
        gross_margin_ratio.value = float(INTR_gross_profit) / float(revenue.value)
        gross_margin_ratio.if_missing = "NO"
        gross_margin_ratio.missing_explain = "N/A"
    else:
        gross_margin_ratio.value = "N/A"
        gross_margin_ratio.if_missing = "YES"
        gross_margin_ratio.missing_explain = "Unable to locate parameter in data sheets"


    operating_margin_ratio = DB_ANALYSIS()

    INTR_operating_income = INTR_operating_expenses

    if INTR_operating_income != "N/A" and revenue.value != "N/A":
        operating_margin_ratio.value = float(INTR_operating_income) / float(revenue.value)
        operating_margin_ratio.if_missing = "NO"
        operating_margin_ratio.missing_explain = "N/A"
    else:
        operating_margin_ratio.value = "N/A"
        operating_margin_ratio.if_missing = "YES"
        operating_margin_ratio.missing_explain = "Unable to locate parameter in data sheets"


    net_margin_ratio = DB_ANALYSIS()

    if net_income.value != "N/A" and revenue.value != "N/A":
        net_margin_ratio.value = float(net_income.value) / float(revenue.value)
        net_margin_ratio.if_missing = "NO"
        net_margin_ratio.missing_explain = "N/A"
    else:
        net_margin_ratio.value = "N/A"
        net_margin_ratio.if_missing = "YES"
        net_margin_ratio.missing_explain = "Unable to locate parameter in data sheets"


    inventory_turnover_ratio = DB_ANALYSIS()

    INTR_cost_of_revenue = retrieve_value_partial(company, accn, "CostOfRevenue")
    INTR_inventory = retrieve_value_partial(company, accn, "InventoryNet")

    if INTR_cost_of_revenue != "N/A" and INTR_inventory != "N/A":
        inventory_turnover_ratio.value = float(INTR_cost_of_revenue) / float(INTR_inventory)
        inventory_turnover_ratio.if_missing = "NO"
        inventory_turnover_ratio.missing_explain = "N/A"
    else:
        inventory_turnover_ratio.value = "N/A"
        inventory_turnover_ratio.if_missing = "YES"
        inventory_turnover_ratio.missing_explain = "Unable to locate parameter in data sheets"


    asset_turnover_ratio = DB_ANALYSIS()

    INTR_net_ppe = retrieve_value_partial(company, accn, "PropertyPlantAndEquipmentNet")

    if revenue.value != "N/A" and INTR_net_ppe != "N/A":
        asset_turnover_ratio.value = float(revenue.value) / float(INTR_net_ppe)
        asset_turnover_ratio.if_missing = "NO"
        asset_turnover_ratio.missing_explain = "N/A"
    else:
        asset_turnover_ratio.value = "N/A"
        asset_turnover_ratio.if_missing = "YES"
        asset_turnover_ratio.missing_explain = "Unable to locate parameter in data sheets"


    def create_analysis_json(title, definition, analysis_obj, if_generated="NO", generated_explanation="N/A"):
        return {
            title: {
                "Definition": definition,
                "Value": str(analysis_obj.value),
                "If Missing": str(analysis_obj.if_missing),
                "Missing Explanation": str(analysis_obj.missing_explain),
                "If Generated": if_generated,
                "Generated Explanation": generated_explanation
            }
        }

    data = {}
    analyses = [
        ("Assets", "Resources owned by a company that provide economic value.", assets),
        ("Liabilities", "Obligations or debts a company owes to others.", liabilities),
        ("Equity", "The residual interest in the company's assets after deducting liabilities.", equity),
        ("Revenue", "Total income generated from the sale of goods or services.", revenue),
        ("Expenses", "Costs incurred to generate revenue and operate the business.", expenses),
        ("Net Income", "Profit remaining after all expenses, taxes, and costs are deducted from revenue.", net_income),
        ("Operating Activities", "Cash flows from a company's primary business operations.", operate_act),
        ("Investing Activities", "Cash flows related to the acquisition or sale of long-term assets and investments.", invest_act),
        ("Financing Activities", "Cash flows from transactions involving debt, equity, and dividend payments.", finance_act),
        ("Current Ratio", "Measures a company's ability to pay short-term obligations with its current assets.", current_ratio, "YES", "calculated by (current assets) / (current liabilities)"),
        ("Quick Ratio", "Assesses liquidity by comparing liquid assets to current liabilities, excluding inventory.", quick_ratio, "YES", "calculated by (cash and cash equivalents + short term investments + account receivables) / (current liabilities)"),
        ("Debt to Equity Ratio", "Evaluates financial leverage by comparing total debt to shareholders' equity.", debt_to_equity_ratio, "YES", "calculated by (liabilities) / (stock holder equity)"),
        ("Interest Coverage Ratio", "Indicates how easily a company can cover interest payments with its operating income.", interest_coverage_ratio, "YES", "calculated by (earnings before interest and taxes) / (interest expense)"),
        ("Gross Margin Ratio", "Percentage of revenue remaining after subtracting cost of goods sold.", gross_margin_ratio, "YES", "calculated by (gross profit) / (revenue)"),
        ("Operating Margin Ratio", "Shows the percentage of revenue left after covering operating expenses.", operating_margin_ratio, "YES", "calculated by (operating income) / (revenue)"),
        ("Net Margin Ratio", "Represents the percentage of revenue remaining as profit after all expenses.", net_margin_ratio, "YES", "calculated by (net income) / (revenue)"),
        ("Inventory Turnover Ratio", "Measures how efficiently a company sells and replaces its inventory over a period.", inventory_turnover_ratio, "YES", "calculated by (cost of revenue) / (inventory)"),
        ("Asset Turnover Ratio", "Indicates how effectively a company uses its assets to generate revenue.", asset_turnover_ratio, "YES", "calculated by (revenue) / (property plant and equipment)")
    ]

    # Loop through and add each analysis to the data dict
    for item in analyses:
        # Handle the optional if_generated and generated_explanation
        if len(item) == 3:
            title, definition, analysis_obj = item
            data.update(create_analysis_json(title, definition, analysis_obj))
        else:
            title, definition, analysis_obj, if_generated, generated_explanation = item
            data.update(create_analysis_json(title, definition, analysis_obj, if_generated, generated_explanation))

    output_json = {"raw": subset_json_dict, "calculated": data}
    
    return output_json

