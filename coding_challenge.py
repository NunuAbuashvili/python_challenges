"""
Coding Challenge - Transfer Grouping by Country and Period

Edge cases:
- An empty list of applicants;
- Applicant ID is missing (handled as 'Unknown_Index');
- An empty list of transfers;
- Identical transfers within the same applicant;
- All transfers invalid/dropped after cleaning;
- Incorrect data types or malformed transfer data structure:
    - 'country': All values should be uppercase strings (.upper(), .strip()).
    - 'period': All values should be integers.
    - 'amountgel': All values should be of float type.
    - 'source': All values should be uppercase strings.
- Missing values:
    - Rows with missing country, period or amount should be dropped.
    - Rows with missing source can be modified as 'Unknown'.
- Missing entire columns;
- Empty string values;
- Negative values for 'period' or 'amountgel'.
"""
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def join_unique_sources(sources: pd.Series) -> str:
    """
    Join unique source values alphabetically with '/'.

    Args:
        sources: pandas Series of source values

    Returns:
        String of unique sources joined by '/'
    """
    return '/'.join(sorted(sources.unique()))


def clean_and_validate_transfers(df: pd.DataFrame, applicant_id: str) -> Optional[pd.DataFrame]:
    """
    Clean and validate transfer data for a single applicant.

    Args:
        df: DataFrame containing transfer data
        applicant_id: ID of the applicant for logging purposes

    Returns:
        Cleaned DataFrame or None if no valid data remains
    """
    if df.empty:
        return None

    initial_rows = len(df)

    # Replace empty or whitespace-only strings with NaN
    # \s*: Means zero or more whitespace characters (spaces, tabs, etc.)
    df_cleaned = df.replace(r'^\s*$', np.nan, regex=True).copy()

    # Remove rows with missing critical values ('country', 'period', 'amountgel')
    df_cleaned = df_cleaned.dropna(subset=['country', 'period', 'amountgel'])
    # Fill missing 'source' values with 'Unknown'
    df_cleaned['source'] = df_cleaned['source'].fillna('Unknown')

    if df_cleaned.empty:
        logger.warning(f'Applicant {applicant_id}: All rows removed due to missing critical data.')
        return None

    # Convert data types
    try:
        df_cleaned['country'] = df_cleaned['country'].astype(str).str.upper().str.strip()
        df_cleaned['period'] = pd.to_numeric(df_cleaned['period'], errors='coerce')
        df_cleaned['amountgel'] = pd.to_numeric(df_cleaned['amountgel'], errors='coerce')
        df_cleaned['source'] = df_cleaned['source'].astype(str).str.upper().str.strip()

        # Remove any rows where numeric conversion failed
        df_cleaned = df_cleaned.dropna(subset=['period', 'amountgel'])

        # Remove duplicates
        df_cleaned = df_cleaned.drop_duplicates()

        # Remove rows with logically invalid values ('period' or 'amountgel' < 0)
        df_cleaned = df_cleaned[
            (df_cleaned['period'] > 0) &
            (df_cleaned['amountgel'] > 0)
        ]

        if df_cleaned.empty:
            logger.warning(f'Applicant {applicant_id}: All rows removed due to invalid data or business rules.')
            return None

        # Convert 'period' and 'amountgel' to proper data types
        df_cleaned['period'] = df_cleaned['period'].astype(int)
        df_cleaned['amountgel'] = df_cleaned['amountgel'].astype(float)

        final_rows = len(df_cleaned)
        removed_rows = initial_rows - final_rows

        if removed_rows > 0:
            logger.info(f'Applicant {applicant_id}: Removed {removed_rows} invalid row(s).')

        return df_cleaned

    except Exception as error:
        logger.error(f'Applicant {applicant_id}: Data cleaning failed - {str(error)}')
        return None

def group_and_aggregate_transfers(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Group transfers by country and period, then aggregate amounts and sources.

    This function:
        - Groups the cleaned transfer data by the ('country', 'period') pair.
        - Sums the 'amountgel' values for each group to get the total transferred amount.
        - Collects all unique 'source' values per group, sorts them alphabetically, and joins them with '/'.

    Args:
        df: Cleaned DataFrame with transfer data

    Returns:
        List of dictionaries containing grouped transfer records
    """
    try:
        aggregated = df.groupby(['country', 'period']).agg(
            amountgel=('amountgel', 'sum'),
            source=('source', join_unique_sources)
        )
        aggregated = aggregated.sort_values(['country', 'period']).reset_index()

        return aggregated.to_dict('records')

    except Exception as error:
        logger.error(f'Aggregation failed: {str(error)}')
        return []


def process_applicant_transfers(applicants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process transfer data for multiple applicants with grouping and aggregation.

    This function groups transfers by (country, period) pairs for each applicant,
    computes total amounts, and collects unique sources.

    Args:
        applicants: List of dictionaries, each containing:
            - applicant_id: Unique identifier for the applicant.
            - transfers: List of transfer dictionaries with keys:
                - country: The country the transfer was made from.
                - period: A numerical value indicating the time period.
                - amountgel: Amount of the transfer in GEL.
                - source: Source label for the transfer.

    Returns:
        List of dictionaries, each containing:
            - applicant_id: Unique identifier for the applicant.
            - grouped_transfers: List of grouped transfer records, sorted by country then period.
    """
    if not applicants:
        logger.warning('No applications provided for processing.')
        return []

    logger.info(f'Processing {len(applicants)} applicants.')
    processed_applicants = []

    for i, applicant in enumerate(applicants, start=1):
        applicant_id = applicant.get('applicant_id', f'Unknown_{i}')
        transfers = applicant.get('transfers', [])

        # Handle empty transfers
        if not transfers:
            logger.info(f'Applicant {applicant_id}: No transfer records found.')
            processed_applicants.append({
                'applicant_id': applicant_id,
                'grouped_transfers': [],
            })
            continue

        try:
            # Convert to Pandas DataFrame
            df = pd.DataFrame(transfers)
            # Clean and validate the transfers
            cleaned_df = clean_and_validate_transfers(df, applicant_id)

            if cleaned_df is None or cleaned_df.empty:
                processed_applicants.append({
                    'applicant_id': applicant_id,
                    'grouped_transfers': [],
                })
                continue

            # Group and aggregate the transfers
            grouped_transfers = group_and_aggregate_transfers(cleaned_df)
            processed_applicants.append({
                'applicant_id': applicant_id,
                'grouped_transfers': grouped_transfers,
            })

        except Exception as error:
            logger.error(f'Applicant {applicant_id}: Data processing failed - {str(error)}')
            processed_applicants.append({
                'applicant_id': applicant_id,
                'grouped_transfers': [],
            })

    logger.info(f'Completed processing {len(processed_applicants)} applicants.')
    return processed_applicants


if __name__ == '__main__':
    applicants_1 = [
        {
            "applicant_id": "APP_001",
            "transfers": [
                {"country": "USA", "period": 1, "amountgel": 100.0, "source": "A"},
                {"country": "USA", "period": 1, "amountgel": 50.0, "source": "B"},
                {"country": "GE", "period": 2, "amountgel": 200.0, "source": "M"},
                {"country": "USA", "period": 2, "amountgel": 75.0, "source": "A"},
                {"country": "GE", "period": 1, "amountgel": 120.0, "source": "B"}
            ]
        },
        {
            "applicant_id": "APP_002",
            "transfers": [
                {"country": "UK", "period": 1, "amountgel": 300.0, "source": "C"},
                {"country": "UK", "period": 1, "amountgel": 100.0, "source": "A"}
            ]
        }
    ]

    print('\n*********************************')
    print('Test no. 1: When all of the data is present and correct.')
    print('Results:')
    results = process_applicant_transfers(applicants_1)
    for result in results:
        print(result)

    applicants_2 = []
    print('\n*********************************')
    print('Test no. 2: With an empty list of applicants.')
    print('Results:')
    results = process_applicant_transfers(applicants_2)
    for result in results:
        print(result)

    applicants_3 = [
        {
            "transfers": [
                {"country": "FR", "period": 1, "amountgel": 150.0, "source": "X"},
                {"country": "FR", "period": 2, "amountgel": 100.0, "source": "Y"}
            ]
        }
    ]
    print('\n*********************************')
    print('Test no. 3: When missing an applicant ID.')
    print('Results:')
    results = process_applicant_transfers(applicants_3)
    for result in results:
        print(result)

    applicants_4 = [
        {
            "applicant_id": "APP_003",
            "transfers": []
        }
    ]
    print('\n*********************************')
    print('Test no. 4: With an empty list of transfers.')
    print('Results:')
    results = process_applicant_transfers(applicants_4)
    for result in results:
        print(result)

    applicants_5 = [
        {
            "applicant_id": "APP_004",
            "transfers": [
                {"country": "GE", "period": 1, "amountgel": 100.0, "source": "A"},
                {"country": "GE", "period": 1, "amountgel": 100.0, "source": "A"}
            ]
        }
    ]
    print('\n*********************************')
    print('Test no. 5: With identical transfer records.')
    print('Results:')
    results = process_applicant_transfers(applicants_5)
    for result in results:
        print(result)

    applicants_6 = [
        {
            "applicant_id": "APP_005",
            "transfers": [
                {"country": None, "period": 1, "amountgel": 100.0, "source": "A"},
                {"country": "USA", "period": None, "amountgel": 200.0, "source": "B"},
                {"country": "USA", "period": 2, "amountgel": None, "source": "C"},
                {"country": "USA", "period": 2, "amountgel": 100.0, "source": None},
                {"country": "USA", "period": 2, "amountgel": 160.0, "source": "B"},  # Valid
            ]
        }
    ]
    print('\n*********************************')
    print('Test no. 6: With missing data.')
    print('Results:')
    results = process_applicant_transfers(applicants_6)
    for result in results:
        print(result)

    applicants_7 = [
        {
            "applicant_id": "APP_006",
            "transfers": [
                {"country": "USA", "period": -1, "amountgel": 100.0, "source": "A"},  # Negative period
                {"country": "USA", "period": 2, "amountgel": -50.0, "source": "B"},  # Negative amount
                {"country": "USA", "period": 3, "amountgel": "one hundred GEL", "source": "C"},  # Invalid amount
                {"country": "USA", "period": 4, "amountgel": 75.0, "source": "D"},  # Valid
                {"country": "GE", "period": 2, "amountgel": 135.0, "source": "b"},  # Lowercase source
                {"country": "ge", "period": 2, "amountgel": 270.0, "source": "B"},  # Lowercase country
            ]
        }
    ]
    print('\n*********************************')
    print('Test no. 7: With mixed valid and invalid (negative values, lowercase values) values.')
    print('Results:')
    results = process_applicant_transfers(applicants_7)
    for result in results:
        print(result)

    applicants_8 = [
        {
            "applicant_id": "APP_007",
            "transfers": [
                {"country": "GE", "period": 1, "amountgel": 100.0, "source": "A"},  # Valid
                {"country": "GE", "period": 1, "amountgel": None, "source": "B"},
                {"country": "GE", "period": "two", "amountgel": 50.0, "source": "C"},  # Invalid period
                {"country": "GE", "period": 2, "amountgel": 150.0},  # Missing source
                {"period": 3, "amountgel": 120.0, "source": "A"},  # Missing country
                {"country": "USA", "period": 3, "source": "C"},  # Missing amount
                {"country": "USA", "amountgel": 110.0, "source": "B"},  # Missing period
            ]
        }
    ]
    print('\n*********************************')
    print('Test no. 8: Data with missing keys or invalid data.')
    print('Results:')
    results = process_applicant_transfers(applicants_8)
    for result in results:
        print(result)

    applicants_9 = [
        {
            "applicant_id": "APP_008",
            "transfers": [
                {"country": "", "period": 1, "amountgel": 100.0, "source": "A"},
                {"country": "GE", "period": 2, "amountgel": 200.0, "source": ""},  # Valid
                {"country": "GE", "period": "", "amountgel": 100.0, "source": "A"},
                {"country": "GE", "period": 1, "amountgel": "", "source": "A"},
            ]
        }
    ]
    print('\n*********************************')
    print('Test no. 9: Data with empty strings.')
    print('Results:')
    results = process_applicant_transfers(applicants_9)
    for result in results:
        print(result)

    applicants_10 = [
        {
            "applicant_id": "APP_009",
            "transfers": [
                {"country": "FR", "period": 1, "amountgel": 100.0, "source": "A"},  # Valid
                {"country": "FR", "period": "2", "amountgel": 300.0, "source": "B"},  # String-type period
                {"country": "FR", "period": 2, "amountgel": "400.0", "source": "C"},  # String-type amount
                {"country": "FR", "period": 3, "amountgel": 240, "source": "D"}  # Int-type amount
            ]
        }
    ]
    print('\n*********************************')
    print('Test no. 10: Data with incorrect data types.')
    print('Results:')
    results = process_applicant_transfers(applicants_10)
    for result in results:
        print(result)
