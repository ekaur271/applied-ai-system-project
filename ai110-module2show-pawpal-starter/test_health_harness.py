"""
PawPal Health Check — Evaluation Harness

Runs the health agent on 6 predefined symptom inputs and prints a
pass/fail summary. Each test case defines the expected severity and
whether a vet referral should be triggered.

Run:
    python test_health_harness.py
"""

from health_agent import run_health_check


TEST_CASES = [
    {
        "id": 1,
        "description": "Dog eating grass + vomiting (low/medium, no vet)",
        "pet_name": "TestDog",
        "species": "dog",
        "observation": "my dog has been eating grass and throwing up this morning",
        "expected_severity": ["low", "medium"],
        "expected_vet": False,
    },
    {
        "id": 2,
        "description": "Cat not eating for two days (high, vet required)",
        "pet_name": "TestCat",
        "species": "cat",
        "observation": "my cat hasn't eaten anything in two days",
        "expected_severity": ["high"],
        "expected_vet": True,
    },
    {
        "id": 3,
        "description": "Dog scratching ears + head shaking (medium, no immediate vet)",
        "pet_name": "TestDog",
        "species": "dog",
        "observation": "my dog keeps scratching its ears and shaking its head",
        "expected_severity": ["low", "medium"],
        "expected_vet": False,
    },
    {
        "id": 4,
        "description": "Dog vomiting blood — guardrail escalation to high + vet",
        "pet_name": "TestDog",
        "species": "dog",
        "observation": "my dog is vomiting blood and seems very weak",
        "expected_severity": ["high"],
        "expected_vet": True,
    },
    {
        "id": 5,
        "description": "Cat straining to urinate — guardrail escalation to high + vet",
        "pet_name": "TestCat",
        "species": "cat",
        "observation": "my male cat keeps going to the litter box but can't urinate",
        "expected_severity": ["high"],
        "expected_vet": True,
    },
    {
        "id": 6,
        "description": "Guardrail: empty observation rejected",
        "pet_name": "TestDog",
        "species": "dog",
        "observation": "   ",
        "expected_severity": None,
        "expected_vet": None,
        "expect_error": True,
    },
    {
        "id": 7,
        "description": "Guardrail: gibberish input rejected",
        "pet_name": "TestDog",
        "species": "dog",
        "observation": "asdfjkl qwerty zxcvbn",
        "expected_severity": None,
        "expected_vet": None,
        "expect_error": True,
    },
    {
        "id": 8,
        "description": "Guardrail: off-topic input rejected",
        "pet_name": "TestDog",
        "species": "dog",
        "observation": "my car won't start and makes a clicking noise",
        "expected_severity": None,
        "expected_vet": None,
        "expect_error": True,
    },
    {
        "id": 9,
        "description": "Vague input still produces a valid response",
        "pet_name": "TestDog",
        "species": "dog",
        "observation": "my dog seems off today",
        "expected_severity": ["low", "medium", "high"],
        "expected_vet": None,
    },
]

PASS = "PASS"
FAIL = "FAIL"


def run_case(tc):
    gen = run_health_check(tc["pet_name"], tc["species"], tc["observation"])
    result = None
    try:
        while True:
            next(gen)
    except StopIteration as e:
        result = e.value

    # error-expected cases
    if tc.get("expect_error"):
        ok = bool(result.error)
        return ok, f"error='{result.error}'" if ok else "expected error but got none"

    if result.error:
        return False, f"unexpected error: {result.error}"

    sev_ok = result.severity in tc["expected_severity"]
    vet_ok = tc["expected_vet"] is None or result.vet_required == tc["expected_vet"]
    passed = sev_ok and vet_ok

    detail = (
        f"severity={result.severity} (expected {tc['expected_severity']}) | "
        f"vet_required={result.vet_required} (expected {tc['expected_vet']})"
    )
    return passed, detail


def main():
    print("=" * 65)
    print("PawPal Health Check — Evaluation Harness")
    print("=" * 65)

    passed = 0
    failed = 0

    for tc in TEST_CASES:
        print(f"\nTest {tc['id']}: {tc['description']}")
        print(f"  Input: \"{tc['observation'].strip()}\"")
        try:
            ok, detail = run_case(tc)
        except Exception as ex:
            ok, detail = False, f"exception: {ex}"

        status = PASS if ok else FAIL
        if ok:
            passed += 1
        else:
            failed += 1

        print(f"  Result: [{status}] {detail}")

    print("\n" + "=" * 65)
    print(f"Summary: {passed}/{len(TEST_CASES)} passed, {failed} failed")
    print("=" * 65)


if __name__ == "__main__":
    main()
