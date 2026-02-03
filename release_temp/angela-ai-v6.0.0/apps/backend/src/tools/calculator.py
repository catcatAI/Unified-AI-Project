import asyncio
from typing import Literal

from pydantic import BaseModel, Field

from apps.backend.src.tools.base_tool import BaseTool


class CalculatorArgs(BaseModel):
    """Pydantic schema for the arguments of the calculator tool."""

    a: float = Field(..., description="The first number for the operation.")
    b: float = Field(..., description="The second number for the operation.")
    operator: Literal["+", "-", "*", "/"] = Field(
        ...,
        description="The mathematical operation to perform.",
    )


class CalculatorTool(BaseTool):
    """A tool that performs basic arithmetic operations.
    It serves as a simple, concrete example of a tool built on the BaseTool interface.
    """

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "A simple calculator that can perform addition, subtraction, multiplication, and division on two numbers."

    @property
    def args_schema(self) -> type[BaseModel]:
        return CalculatorArgs

    async def execute(self, **kwargs) -> str:
        """Executes the calculation and returns the result as a string."""
        # Simulate a small amount of I/O or processing time
        await asyncio.sleep(0.05)

        try:
            validated_args = self.args_schema(**kwargs)
            a = validated_args.a
            b = validated_args.b
            operator = validated_args.operator

            if operator == "+":
                result = a + b
            elif operator == "-":
                result = a - b
            elif operator == "*":
                result = a * b
            elif operator == "/":
                if b == 0:
                    return "Error: Cannot divide by zero."
                result = a / b
            return f"The result is {result}."
        except Exception as e:
            # This will catch Pydantic validation errors and other unexpected issues.
            return f"Error executing calculator: {e!s}"
