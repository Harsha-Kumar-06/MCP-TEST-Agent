"""
Upgrade Flask UI to use Gemini-Enhanced Parser
Run this script to enable dynamic learning!
"""
import os
import shutil

print("="*70)
print("🚀 GEMINI-ENHANCED PARSER UPGRADE")
print("="*70)

# Paths
project_dir = r"c:\Users\Harsha Kumar\Desktop\DRAVYN\Agents\Swarm Pattern"
portfolio_dir = os.path.join(project_dir, "portfolio_swarm")
text_parser = os.path.join(portfolio_dir, "text_parser.py")
text_parser_gemini = os.path.join(portfolio_dir, "text_parser_gemini.py")
backup_file = os.path.join(portfolio_dir, "text_parser_static_backup.py")

# Check files exist
if not os.path.exists(text_parser_gemini):
    print("❌ Error: text_parser_gemini.py not found!")
    print("   Please make sure the Gemini parser file exists.")
    exit(1)

# Backup existing parser
if os.path.exists(text_parser):
    print(f"\n📦 Backing up current parser...")
    shutil.copy2(text_parser, backup_file)
    print(f"✅ Backup saved: {backup_file}")

# Replace with Gemini parser
print(f"\n🔄 Replacing parser with Gemini-enhanced version...")
shutil.copy2(text_parser_gemini, text_parser)
print(f"✅ Parser upgraded!")

print("\n" + "="*70)
print("✅ UPGRADE COMPLETE!")
print("="*70)

print("\n🎯 What changed:")
print("  ✅ Parser now learns new tickers automatically")
print("  ✅ Dynamic sector classification")  
print("  ✅ ESG score estimation")
print("  ✅ Caching for instant future lookups")
print("  ✅ Handles ANY company name")

print("\n🚀 Next steps:")
print("  1. Restart your Flask server (Ctrl+C and run flask_ui.py again)")
print("  2. Try parsing unknown companies like:")
print("     - 'Snowflake', 'Palantir', 'CrowdStrike'")
print("  3. Watch the knowledge cache grow in 'portfolio_knowledge_cache.json'")

print("\n💾 Files:")
print(f"  - Active parser: {text_parser}")
print(f"  - Backup: {backup_file}")
print(f"  - Gemini version: {text_parser_gemini}")

print("\n📊 To revert to static parser:")
print("  copy portfolio_swarm\\text_parser_static_backup.py portfolio_swarm\\text_parser.py")

print("\n" + "="*70)
print("Parser is ready! Restart Flask and try it out! 🎉")
print("="*70)
