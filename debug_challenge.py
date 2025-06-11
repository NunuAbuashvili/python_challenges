"""
Debug Challenge - Payment Calculator

Notes:
(income share / base) * amount -> Calculate a share of a total amount based on
income contribution or similar ratios. It is used to find how much of the total amount
someone should get, based on their share of something.
Income share: The portion of income attributed to a person, branch, product, or entity.
Base: The total income (or another metric) across all entities being considered.
Amount: A total value that needs to be distributed (e.g. interest, fees, profit, or cost).

Bugs:
- incomeshare = float(pay.get('incomeshare') or 1) -> In this case, 0 will be evaluated as False,
and will be replaced by 1, which is incorrect.
- 'base' might be 0, so we will get ZeroDivisionError.
- 'incomeshare' should be in the range of [0, 1].
- 'currency' value might have leading or trailing spaces.
- Invalid types or missing values will raise TypeError or ValueError.
- If 'active' is an emtpy string, it will be treated as False.
- 'incomeshare', 'amount', 'base' should not be negative values.
- Missing keys will result in TypeError.
- It would be better to return an empty list if 'payments' is None.
- Would be better to add logging support for further debugging.
"""
import logging
from typing import List, Dict, Any


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_payments_original(applicants):
    payment_by_currency = {}
    for app in applicants:
        currency = str(app.get('currency', 'GEL')).upper()
        payments = app.get('payments')
        for pay in payments:
            if pay.get('active', True):
                incomeshare = float(pay.get('incomeshare') or 1)
                base = pay.get('base')
                ratio = incomeshare / base
                amount = float(pay.get('amount', 0))
                payment_by_currency[currency] = payment_by_currency.get(currency, 0) + amount * ratio

    return payment_by_currency


def calculate_payments_modified(applicants: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Process applicants and calculate payments by currency.
    For each active payment: (incomeshare / base) * amount

    Args:
        applicants: A list of applicants with payment data.

    Returns:
        A dictionary with currencies as keys and total payment amounts as values.
    """
    if not applicants:
        logger.warning('No applications provided for further calculation.')
        return {}

    logger.info(f'Processing {len(applicants)} applicants.')
    payment_by_currency = {}

    for applicant_idx, applicant in enumerate(applicants, start=1):
        # Get currency, default to "GEL" if missing, and handle formatting
        currency = str(applicant.get('currency', 'GEL').upper().strip())
        if not currency:
            logger.warning(f'Applicant {applicant_idx}: Empty currency. Automatically set to GEL.')
            currency = 'GEL'

        # Get a list of payments for the applicant
        payments = applicant.get('payments', [])
        if not payments:
            logger.warning(f'Applicant {applicant_idx}: No payments provided.')
            continue

        for payment_idx, payment in enumerate(payments, start=1):
            try:
                active = payment.get('active', True)
                # When active is an empty string
                if active == '':
                    active = True

                if not active:
                    continue

                # Convert and validate incomeshare
                try:
                    incomeshare = float(payment.get('incomeshare', 1))
                    if incomeshare < 0 or incomeshare > 1:
                        logger.warning(f'Applicant {applicant_idx}, Payment {payment_idx}: Invalid incomeshare value.')
                        continue
                except (TypeError, ValueError) as error:
                    logger.warning(f'Applicant {applicant_idx}, Payment {payment_idx}: Invalid incomeshare value.')
                    continue

                # Convert and validate base
                base_value = payment.get('base')
                if base_value is None:
                    logger.warning(f'Applicant {applicant_idx}, Payment {payment_idx}: Empty base.')
                    continue

                try:
                    base = float(base_value)
                except (TypeError, ValueError) as error:
                    logger.warning(f'Applicant {applicant_idx}, Payment {payment_idx}: Invalid base value.')
                    continue

                if base <= 0:
                    logger.warning(f'Applicant {applicant_idx}, Payment {payment_idx}: Base <= 0.')
                    continue

                # Convert amount
                try:
                    amount = float(payment.get('amount', 0))
                    if amount < 0:
                        logger.warning(f'Applicant {applicant_idx}, Payment {payment_idx}: Invalid amount value.')
                        continue
                except (TypeError, ValueError) as error:
                    logger.warning(f'Applicant {applicant_idx}, Payment {payment_idx}: Invalid amount value.')
                    continue

                # Calculate ratio and final amount
                ratio = incomeshare / base
                calculated_amount = amount * ratio

                # Add to currency total
                payment_by_currency[currency] = payment_by_currency.get(currency, 0) + calculated_amount

            except Exception as error:
                logger.warning(f'Applicant {applicant_idx}, Payment {payment_idx}: Unexpected error - {str(error)}')
                continue

    return payment_by_currency


if __name__ == '__main__':
    applicants_1 = [
        {
            "currency": "USD",
            "payments": [
                {
                    "active": True,
                    "incomeshare": 0.2,
                    "amount": 1000,
                    "base": 0.5
                },
                {
                    "active": False,
                    "incomeshare": 0.3,
                    "amount": 500,
                    "base": 0.4
                }
            ]
        }
    ]

    print('\n*********************************')
    print('Test no. 1: When all of the data is present and valid.')
    result_for_original = calculate_payments_original(applicants_1)
    print("Result of the original function:", result_for_original)  # {'USD': 400.0}
    result_for_modified = calculate_payments_modified(applicants_1)
    print("Result of the modified function:", result_for_modified)  # {'USD': 400.0}

    applicants_2 = [
        {
            "currency": "USD",
            "payments": [
                {"active": True, "incomeshare": 0, "amount": 100, "base": 0.5},
            ]
        }
    ]
    print('\n*********************************')
    print('Test no. 2: When income share is equal to 0.')
    result_for_original = calculate_payments_original(applicants_2)
    print("Result of the original function:", result_for_original)  # {'USD': 200.0}
    result_for_modified = calculate_payments_modified(applicants_2)
    print("Result of the modified function:", result_for_modified)  # {'USD': 0.0}

    applicants_3 = [
        {
            "currency": "USD",
            "payments": [
                {"active": True, "incomeshare": 0.2, "amount": 100, "base": 0},
                {"active": True, "incomeshare": 0.2, "amount": 100, "base": 0.5},
            ]
        }
    ]
    print('\n*********************************')
    print('Test no. 3: When base is equal to 0.')
    # result_for_original = calculate_payments_original(applicants_3)  # Raises a ZeroDivisionError
    # print("Result of the original function:", result_for_original)
    result_for_modified = calculate_payments_modified(applicants_3)
    print("Result of the modified function:", result_for_modified)  # {'USD': 40.0}

    applicants_4 = [
        {
            "currency": "USD",
            "payments": [
                {"active": True, "incomeshare": 1.2, "amount": 2000, "base": 0.5},
            ]
        }
    ]
    print('\n*********************************')
    print('Test no. 4: When incomeshare is more than 1.')
    result_for_original = calculate_payments_original(applicants_4)
    print("Result of the original function:", result_for_original)  # {'USD': 4800.0}
    result_for_modified = calculate_payments_modified(applicants_4)
    print("Result of the modified function:", result_for_modified)  # {}

    applicants_5 = [
        {
            "currency": "usd",
            "payments": [
                {"active": True, "incomeshare": 0.2, "amount": 2000, "base": 0.5},
                {"active": True, "incomeshare": 0.4, "amount": 1000, "base": 1}
            ]
        },
        {
            "currency": "USD  ",
            "payments": [
                {"incomeshare": 0.2, "amount": 1000, "base": 0.5},
            ]
        }
    ]
    print('\n*********************************')
    print('Test no. 5: When the currency value has leading or/and trailing spaces.')
    result_for_original = calculate_payments_original(applicants_5)
    print("Result of the original function:", result_for_original)  # {'USD': 1200.0, 'USD  ': 400.0}
    result_for_modified = calculate_payments_modified(applicants_5)
    print("Result of the modified function:", result_for_modified)  # {'USD': 1600.0}

    applicants_6 = [
        {
            "currency": "USD",
            "payments": [
                {"active": True, "incomeshare": '0.2', "amount": '2000', "base": '0.5'},
            ]
        }
    ]
    print('\n*********************************')
    print('Test no. 6: Numbers with incorrect data types (str).')
    # result_for_original = calculate_payments_original(applicants_6)
    # print("Result of the original function:", result_for_original)  # Raises a TypeError
    result_for_modified = calculate_payments_modified(applicants_6)
    print("Result of the modified function:", result_for_modified)  # {'USD': 800.0}

    applicants_7 = [
        {
            "currency": "USD",
            "payments": [
                {"active": '', "incomeshare": 0.2, "amount": 2000, "base": 0.5},
            ]
        }
    ]
    print('\n*********************************')
    print('Test no. 7: When active is an empty string.')
    result_for_original = calculate_payments_original(applicants_7)
    print("Result of the original function:", result_for_original)  # {}
    result_for_modified = calculate_payments_modified(applicants_7)
    print("Result of the modified function:", result_for_modified)  # {'USD': 800.0}

    applicants_8 = [
        {
            "currency": "USD",
            "payments": [
                {"active": True, "incomeshare": -0.2, "amount": -2000, "base": -0.5},
            ]
        }
    ]
    print('\n*********************************')
    print('Test no. 8: With negative values.')
    result_for_original = calculate_payments_original(applicants_8)
    print("Result of the original function:", result_for_original)  # {'USD': -800.0}
    result_for_modified = calculate_payments_modified(applicants_8)
    print("Result of the modified function:", result_for_modified)  # {}

    applicants_9 = [
        {
            "currency": "USD",
            "payments": [
                {
                    "active": True,
                    "incomeshare": 'half point five',
                    "amount": 'one hundred',
                    "base": 0.2
                }
            ]
        }
    ]
    print('\n*********************************')
    print('Test no. 9: With nonvalid data types, that cannot be converted to floats.')
    # result_for_original = calculate_payments_original(applicants_9)
    # print("Result of the original function:", result_for_original)  # Raises ValueError
    result_for_modified = calculate_payments_modified(applicants_9)
    print("Result of the modified function:", result_for_modified)  # {}

    applicants_10 = [
        {
            "currency": "USD",
            "payments": [
                {"active": True}
            ]
         }
    ]
    print('\n*********************************')
    print('Test no. 10: With missing keys.')
    # result_for_original = calculate_payments_original(applicants_10)
    # print("Result of the original function:", result_for_original)  # Raises TypeError
    result_for_modified = calculate_payments_modified(applicants_10)
    print("Result of the modified function:", result_for_modified)  # {}
