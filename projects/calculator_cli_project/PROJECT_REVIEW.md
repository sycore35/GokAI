=== FILE: calculator.py ===
```python
class Calculator:
    def add(self, a: float, b: float) -> float:
        return a + b

    def subtract(self, a: float, b: float) -> float:
        return a - b

    def multiply(self, a: float, b: float) -> float:
        return a * b

    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError('Cannot divide by zero')
        return a / b
```

=== FILE: test_calculator.py ===
```python
import pytest
from calculator import Calculator

def test_calculator_operations():
    calc = Calculator()
    assert calc.add(2, 3) == 5
    assert calc.subtract(10, 4) == 6
    assert calc.multiply(3, 7) == 21
    assert calc.divide(8, 2) == 4

def test_divide_by_zero():
    calc = Calculator()
    with pytest.raises(ValueError):
        calc.divide(5, 0)
```
