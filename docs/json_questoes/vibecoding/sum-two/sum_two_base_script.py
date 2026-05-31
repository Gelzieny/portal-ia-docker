sum_two_base = """def two_sum(nums: list[int], target: int) -> list[int]:
    pass
"""

sum_two_gabarito = """def two_sum(nums: list[int], target: int) -> list[int]:
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[j] == target - nums[i]:
                return [i, j]
    return []
"""

sum_two_context = """tests = [
    {
        "input": [2, 7, 11, 15],
        "target": 9,
        "output": [0, 1],
    },
    {
        "input": [3, 2, 4],
        "target": 6,
        "output": [1, 2],
    },
    {
        "input": [3, 3],
        "target": 6,
        "output": [0, 1],
    },
]

{respostaModelo}

for item in tests:
    result = two_sum(item["input"], item["target"])
    if result != item["output"]:
        raise AssertionError(
            "Resposta incorreta, esperado "
            + str(item["output"])
            + " e obtido "
            + str(result)
            + " para o input "
            + str(item["input"])
        )
"""
