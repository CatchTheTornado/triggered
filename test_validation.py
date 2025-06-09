from triggered.test_trigger import TestTrigger

def test_validation():
    # Test valid configuration
    valid_config = {
        "name": "test_trigger",
        "interval": 60,
        "max_retries": 5
    }
    is_valid, error = TestTrigger.validate_config(valid_config)
    print(f"Valid config test: {'PASSED' if is_valid else 'FAILED'}")
    if not is_valid:
        print(f"Error: {error}")

    # Test invalid configuration (missing required field)
    invalid_config = {
        "interval": 60
    }
    is_valid, error = TestTrigger.validate_config(invalid_config)
    print(f"Missing required field test: {'PASSED' if not is_valid else 'FAILED'}")
    if is_valid:
        print("Error: Should have failed validation")

    # Test invalid configuration (wrong type)
    invalid_type_config = {
        "name": "test_trigger",
        "interval": "60",  # Should be int
        "max_retries": 5
    }
    is_valid, error = TestTrigger.validate_config(invalid_type_config)
    print(f"Wrong type test: {'PASSED' if not is_valid else 'FAILED'}")
    if is_valid:
        print("Error: Should have failed validation")

if __name__ == "__main__":
    test_validation() 