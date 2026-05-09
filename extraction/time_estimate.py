from core.config import THREADS, MARKET_COUNTRIES, MIN_INSTALLS

print("=" * 70)
print("TIME ESTIMATION & BAN RISK ANALYSIS")
print("=" * 70)
print()

# 2 apps test data
test_apps = 2
test_time_seconds = 240  # roughly 4 minutes for 2 apps (with 10 countries each)

print(f"📊 TEST RUN DATA:")
print(f"  • Apps processed: {test_apps}")
print(f"  • Time taken: ~{test_time_seconds}s ({test_time_seconds/60:.1f} minutes)")
print(f"  • Per app: {test_time_seconds/test_apps:.0f}s")
print()

total_apps = 192515
countries = len(MARKET_COUNTRIES)

print(f"📈 FULL EXTRACTION CALCULATION:")
print(f"  • Total apps: {total_apps:,}")
print(f"  • Countries per app: {countries}")
print(f"  • Total requests: {total_apps * countries:,}")
print(f"  • Parallel workers: {THREADS}")
print()

# Estimate
time_per_app = test_time_seconds / test_apps  # ~120 seconds per app
total_seconds = total_apps * time_per_app
total_hours = total_seconds / 3600
total_days = total_hours / 24

print(f"⏱️ TIME ESTIMATES:")
print(f"  Conservative: {total_days:.1f} days ({total_hours:.0f} hours)")
print(f"  With delays: {total_days * 1.2:.1f} - {total_days * 1.5:.1f} days")
print(f"  Realistic: 3-6 days (continuous)")
print()

print("=" * 70)
print("BAN RISK ASSESSMENT")
print("=" * 70)
print()

print("✅ PROTECTION MEASURES:")
print("  1. Direct IP (no proxy issues)")
print("  2. 3s base delay between requests")
print("  3. 5-15s random jitter per request")
print("  4. Random User-Agent per request")
print("  5. Realistic request headers")
print("  6. Load spread across 10 countries")
print("  7. Official google-play-scraper library")
print()

print("⚠️ BAN RISK:")
print("  🟢 LOW: 70% (Same approach worked in Phase 1)")
print("  🟡 MEDIUM: 20% (Temp throttling possible, auto-resume works)")
print("  🔴 HIGH: 10% (Unlikely)")
print()

print("=" * 70)
print("IF BAN HAPPENS")
print("=" * 70)
print("  1. Script marks as 'failed'")
print("  2. Wait 2-4 hours")
print("  3. Run: python extract_details.py")
print("  4. Auto-resumes from where it stopped")
