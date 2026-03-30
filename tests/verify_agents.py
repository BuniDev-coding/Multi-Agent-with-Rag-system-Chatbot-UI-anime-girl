import asyncio
import os
import sys
from pathlib import Path

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.agent import run_agent

async def test_design_fetching():
    print("Testing Design Fetching...")
    response = await run_agent("สร้างหน้าเว็บ Landing Page สำหรับ Tigersoft โปรดใช้สีของบริษัท", [])
    print(f"Response: {response[:200]}...")
    if "#F4001A" in response or "Vivid Red" in response:
        print("✅ Correct color (#F4001A) found in response.")
    else:
        print("❌ Brand color not found in response.")
    
    if "Plus Jakarta Sans" in response:
        print("✅ Correct font (Plus Jakarta Sans) found in response.")
    else:
        print("❌ Brand font not found.")

async def test_consultant_routing():
    print("\nTesting Consultant Routing...")
    response = await run_agent("ช่วยวางแผนการพัฒนาโปรเจกต์ใหม่ที่เกี่ยวกับ AI ให้หน่อยครับ เอาแบบภาพรวมกว้างๆ", [])
    print(f"Response: {response[:200]}...")
    if "[Consultant Agent]" in response:
        print("✅ Successfully routed to Consultant Agent.")
    else:
        print("❌ Routing to Consultant Agent failed.")

async def test_file_context():
    print("\nTesting File Context...")
    user_message = "[File: data.txt]\n```\nTarget Market: SME in Thailand\nFocus: HR Software\n```\n\nBuild a website summary based on this file."
    response = await run_agent(user_message, [])
    print(f"Response: {response[:200]}...")
    if "SME" in response and "HR" in response:
        print("✅ Data from file extracted successfully.")
    else:
        print("❌ Failed to extract data from file.")

if __name__ == "__main__":
    asyncio.run(test_design_fetching())
    asyncio.run(test_consultant_routing())
    asyncio.run(test_file_context())
