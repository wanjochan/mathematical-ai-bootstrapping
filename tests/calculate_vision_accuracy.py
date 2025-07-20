"""Calculate exact accuracy of vision model detection"""

import json

# Expected elements (ground truth)
expected = {
    'button': 3,      # Cancel, Save, Close(X)
    'input': 2,       # Username, Email
    'checkbox': 2,    # Enable notifications, Auto-save
    'radio': 2,       # Light theme, Dark theme
    'dropdown': 1,    # Language dropdown
}

# Load detection results
with open('cybercorp_node/vision_analysis_results.json', 'r') as f:
    results = json.load(f)

detected = results['type_distribution']

# Calculate accuracy
total_expected = sum(expected.values())
total_detected = sum(detected.get(k, 0) for k in expected.keys())
total_correct = 0

print("Vision Model Accuracy Report")
print("=" * 50)
print(f"Expected interactive elements: {total_expected}")
print(f"Detected interactive elements: {total_detected}")
print()

print("Per-element analysis:")
for elem_type in expected:
    expected_count = expected[elem_type]
    detected_count = detected.get(elem_type, 0)
    
    # Calculate per-type accuracy (no overcounting)
    correct = min(expected_count, detected_count)
    total_correct += correct
    
    accuracy = (correct / expected_count * 100) if expected_count > 0 else 0
    status = "OK" if detected_count == expected_count else "FAIL"
    
    print(f"{status} {elem_type:10} expected: {expected_count}, detected: {detected_count}, accuracy: {accuracy:.0f}%")

# Overall accuracy
overall_accuracy = (total_correct / total_expected * 100) if total_expected > 0 else 0

print()
print(f"Overall accuracy: {overall_accuracy:.1f}%")
print(f"Target: 95%")
print(f"Status: {'PASS' if overall_accuracy >= 95 else 'FAIL'}")

# Detailed analysis
print()
print("Issues identified:")
if detected.get('checkbox', 0) == 0:
    print("- No checkboxes detected (expected 2)")
if detected.get('dropdown', 0) == 0:
    print("- No dropdown detected (expected 1)")
if detected.get('radio', 0) > expected['radio']:
    print(f"- Radio buttons over-detected ({detected['radio']} vs {expected['radio']} expected)")
if detected.get('input', 0) > expected['input']:
    print(f"- Input fields over-detected ({detected['input']} vs {expected['input']} expected)")
if detected.get('button', 0) < expected['button']:
    print(f"- Missing {expected['button'] - detected.get('button', 0)} button(s) (likely Close button)")

print()
print("Recommendations:")
print("- Fix checkbox detection (currently being misclassified as radio)")
print("- Implement dropdown detection (currently missing)")
print("- Add Close button detection (top-right X button)")
print("- Reduce false positives for input fields")