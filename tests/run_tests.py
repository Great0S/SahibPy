import sys
import os
import traceback

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from test_scraper import (
    test_convert_date_format_explicit_month,
    test_convert_date_format_today_yesterday,
    test_filter_excluded_keywords_case_insensitive,
    test_url_joining,
)

TESTS = [
    test_convert_date_format_explicit_month,
    test_convert_date_format_today_yesterday,
    test_filter_excluded_keywords_case_insensitive,
    test_url_joining,
]

if __name__ == '__main__':
    failed = 0
    for t in TESTS:
        try:
            t()
            print(f"[OK] {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"[FAIL] {t.__name__}: {e}")
            traceback.print_exc()
        except Exception as e:
            failed += 1
            print(f"[ERROR] {t.__name__}: {e}")
            traceback.print_exc()
    if failed:
        print(f"\n{failed} tests failed")
        sys.exit(1)
    else:
        print("\nAll tests passed")
        sys.exit(0)
