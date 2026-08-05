"""Single entry point: rebuild every cache, chart, and the final HTML report."""
from analysis import build_report

if __name__ == "__main__":
    out = build_report.build()
    print(f"\nDone. Open {out} in a browser to view the report.")
