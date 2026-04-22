"""Example: Extract Kimi internal analysis code via Agent SDK.

Usage:
    export MOONSHOT_API_KEY=your-key
    python examples/api_extract_kimi_code.py

Requires: pip install kimi-agent-sdk
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chat_export.api.platforms.kimi.agent_sdk import KimiAgentSDKAdapter


async def main():
    adapter = KimiAgentSDKAdapter()
    await adapter.authenticate()

    # Example: Ask Kimi to analyze music files
    result = await adapter.extract_code_from_files(
        file_description=(
            "File 1: original_song.mp3 (original song)\n"
            "File 2: my_recording.wav (my singing recording)"
        ),
        analysis_prompt=(
            "请分析以下两个音频文件，判断录音是否适合翻唱原唱。\n"
            "要求：\n"
            "1. 输出所有分析步骤的完整 Python 代码\n"
            "2. 使用 librosa 进行音频特征提取\n"
            "3. 包含音高分析、节奏分析、频谱分析\n"
            "4. 给出 0-100 的适合性评分"
        ),
    )

    print(f"Extracted {len(result['extracted_code'])} code blocks:")
    for i, code_block in enumerate(result["extracted_code"], 1):
        print(f"\n{'='*60}")
        print(f"Code Block {i} ({code_block['tool_name']}):")
        print(f"{'='*60}")
        print(code_block["code"][:500])
        if len(code_block["code"]) > 500:
            print(f"... ({len(code_block['code'])} chars total)")

    # Save results
    output_path = Path("./exports/kimi_extracted_code.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "extracted_code": result["extracted_code"],
                "tool_calls": result["tool_calls"],
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
