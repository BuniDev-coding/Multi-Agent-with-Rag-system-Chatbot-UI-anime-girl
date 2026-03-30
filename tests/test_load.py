import sys
from pathlib import Path

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.agent import BRAND_GUIDELINES

print("Brand Guidelines loaded:")
print(f"Length: {len(BRAND_GUIDELINES)}")
if "Vivid Red" in BRAND_GUIDELINES:
    print("✅ Vivid Red found in guidelines.")
else:
    print("❌ Vivid Red not found.")
