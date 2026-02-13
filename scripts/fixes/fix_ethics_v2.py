#!/usr/bin/env python3
"""Final fix for ethics_manager.py"""

# Read the file
with open('/home/cat/桌面/Unified-AI-Project/apps/backend/src/core/ethics/ethics_manager.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix specific lines
if len(lines) > 357:
    # Line 357 (index 356): add comma after 'action' dict
    if "'action': {'require_explanation': True, 'document_reasoning': True}" in lines[356]:
        lines[356] = lines[356].replace("'action': {'require_explanation': True, 'document_reasoning': True}",
                                          "'action': {'require_explanation': True, 'document_reasoning': True},")

if len(lines) > 363:
    # Line 364 (index 363): fix function definition
    lines[363] = "    async def review_content(self, content: str, content_id: str, context: Dict[str, Any] = None) -> EthicsReviewResult:\n"

# Write back
with open('/home/cat/桌面/Unified-AI-Project/apps/backend/src/core/ethics/ethics_manager.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed ethics_manager.py v2")