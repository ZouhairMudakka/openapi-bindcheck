import copy
import unittest

from openapi_bindcheck.oracle import check_request, evaluate_case


class OracleTests(unittest.TestCase):
    def test_rejects_each_corrupted_wire_fact(self):
        expected = {"method": "PUT", "path": "/realms/old", "query": {"x": ["query"]},
                    "body": {"realm": "new"}, "header": {"X-Trace": "header"}, "absent_headers": ["X-Optional"]}
        wire = {"method": "PUT", "path": "/realms/old", "query": {"x": ["query"]},
                "body": {"realm": "new"}, "headers": {"x-trace": "header", "content-type": "application/json"}}
        self.assertEqual(check_request(expected, wire), [])
        for field, replacement in [("method", "POST"), ("path", "/realms/new"), ("query", {}),
                                   ("body", {"realm": "old"}), ("headers", {})]:
            corrupted = copy.deepcopy(wire)
            corrupted[field] = replacement
            with self.subTest(field=field):
                self.assertTrue(check_request(expected, corrupted))
        wire["headers"]["X-OPTIONAL"] = "leaked"
        self.assertIn("unexpected_header:X-Optional", check_request(expected, wire))

    def test_json_types_and_missing_null_are_not_conflated(self):
        for body in [True, 1.0, "1"]:
            self.assertEqual(check_request({"body": 1}, {"body": body}), ["body"])
        self.assertEqual(check_request({"body": {"a": [True]}}, {"body": {"a": [1]}}), ["body"])
        self.assertEqual(check_request({"body": None}, {}), ["body"])
        self.assertEqual(check_request({"body": None}, {"body": None}), [])

    def test_saved_pass_cannot_override_actual_failure(self):
        case = {"id": "witness", "expected": {"body": ["intended"]},
                "wire": [{"body": None}], "pass": True}
        self.assertFalse(evaluate_case(case)["pass"])

    def test_schema_and_expressibility_fail_even_when_wire_matches(self):
        case = {"id": "witness", "expected": {"body": 1}, "wire": [{"body": 1}]}
        for field, value in [("error", "failed"), ("schema_error", "invalid"), ("alias_collision", True)]:
            with self.subTest(field=field):
                self.assertFalse(evaluate_case(dict(case, **{field: value}))["pass"])

    def test_zero_and_multiple_requests_fail(self):
        for wire in [[], [{"body": 1}, {"body": 1}]]:
            self.assertIn("request_count", evaluate_case({"id": "w", "expected": {"body": 1}, "wire": wire})["failures"])

    def test_empty_or_unknown_expectation_rejected_even_without_request(self):
        for expected in [{}, {"boody": 1}]:
            with self.assertRaises(ValueError):
                evaluate_case({"id": "w", "expected": expected, "wire": []})


if __name__ == "__main__":
    unittest.main()
