from CatalystOptimizationSystem.core.extractor import build_prompt


def test_build_prompt_includes_icl_instruction():
    prompt = build_prompt(
        [
            {
                "instruction": "Extract raw values and raw units exactly as stated. Do not convert units.",
                "context": "The reaction was performed at 513 K.",
                "output": {"temperature": {"value": "513", "unit": "K"}},
            }
        ],
        "Text to extract from.",
        ["temperature"],
    )

    assert "Task instructions:" in prompt
    assert "Instruction:" in prompt
    assert "Do not convert units." in prompt
