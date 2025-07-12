import unittest
from src.core_ai.meta_formulas.meta_formula import MetaFormula
from src.core_ai.meta_formulas.errx import ErrX
from src.core_ai.meta_formulas.undefined_field import UndefinedField

class TestMetaFormulas(unittest.TestCase):
    def test_meta_formula(self):
        meta_formula = MetaFormula("Test Formula", "This is a test formula.")
        with self.assertRaises(NotImplementedError):
            meta_formula.execute()

    def test_errx(self):
        errx = ErrX("test_error", {"detail": "This is a test error."})
        self.assertEqual(errx.error_type, "test_error")
        self.assertEqual(errx.details, {"detail": "This is a test error."})

    def test_undefined_field(self):
        undefined_field = UndefinedField("test_context")
        probe_result = undefined_field.probe()
        self.assertEqual(probe_result, {"boundary_information": "Boundary of undefined field related to: test_context"})

if __name__ == '__main__':
    unittest.main()
