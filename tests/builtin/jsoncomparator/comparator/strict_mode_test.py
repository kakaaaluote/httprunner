from httprunner.builtin.jsoncomparator.comparator import JSONComparator


class TestJSONComparatorStrictMode:
    json_comparator = JSONComparator(True)

    def test_compare_json_objects_unexpected_key(self):
        result = self.json_comparator.compare_json(
            {"a": 1, "b": 2}, {"a": 1, "b": 2, "c": 3}
        )
        print(result.fail_messages)
        assert not result.is_success

        # Exchange actual and expected.
        result = self.json_comparator.compare_json(
            {"a": 1, "b": 2, "c": 3}, {"a": 1, "b": 2}
        )
        print(result.fail_messages)
        assert not result.is_success

    def test_compare_json_arrays_order_not_equal(self):
        result = self.json_comparator.compare_json([1, 2, 3], [3, 2, 1])
        print(result.fail_messages)
        assert not result.is_success

    def test_compare_json_arrays_nested_order_not_equal(self):
        result = self.json_comparator.compare_json({"a": [1, 2, 3]}, {"a": [3, 2, 1]})
        print(result.fail_messages)
        assert not result.is_success

    def test_nested(self):
        expected = {
            "id": 1,
            "address": {
                "addr1": "123 Main",
                "addr2": None,
                "city": "Houston",
                "state": "TX",
            },
        }
        actual_pass = {
            "id": 1,
            "address": {
                "addr1": "123 Main",
                "addr2": None,
                "city": "Houston",
                "state": "TX",
            },
        }
        actual_fail = {
            "id": 1,
            "address": {
                "addr1": "123 Main",
                "addr2": None,
                "city": "Austin",
                "state": "TX",
            },
        }

        result = self.json_comparator.compare_json(expected, actual_pass)
        assert result.is_success

        result = self.json_comparator.compare_json(expected, actual_fail)
        print(result.fail_messages)
        assert not result.is_success

    def test_very_nested(self):
        expected = {
            "a": {
                "b": {
                    "c": {
                        "d": {
                            "e": {
                                "f": {
                                    "g": {
                                        "h": {
                                            "i": {
                                                "j": {
                                                    "k": {
                                                        "l": {
                                                            "m": {
                                                                "n": {
                                                                    "o": {"p": "blah"}
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        actual_pass = {
            "a": {
                "b": {
                    "c": {
                        "d": {
                            "e": {
                                "f": {
                                    "g": {
                                        "h": {
                                            "i": {
                                                "j": {
                                                    "k": {
                                                        "l": {
                                                            "m": {
                                                                "n": {
                                                                    "o": {"p": "blah"}
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        actual_fail = {
            "a": {
                "b": {
                    "c": {
                        "d": {
                            "e": {
                                "f": {
                                    "g": {
                                        "h": {
                                            "i": {
                                                "j": {
                                                    "k": {
                                                        "l": {
                                                            "m": {
                                                                "n": {
                                                                    "o": {"z": "blah"}
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        result_pass = self.json_comparator.compare_json(expected, actual_pass)
        assert result_pass.is_success

        result_fail = self.json_comparator.compare_json(expected, actual_fail)
        print(result_fail.fail_messages)
        assert not result_fail.is_success

    def test_complex_array(self):
        expected = {
            "id": 1,
            "name": "Joe",
            "friends": [
                {"id": 2, "name": "Pat", "pets": ["dog"]},
                {"id": 3, "name": "Sue", "pets": ["bird", "fish"]},
            ],
            "pets": [],
        }
        actual_pass_strict = {
            "id": 1,
            "name": "Joe",
            "friends": [
                {"id": 2, "name": "Pat", "pets": ["dog"]},
                {"id": 3, "name": "Sue", "pets": ["bird", "fish"]},
            ],
            "pets": [],
        }
        actual_fail_strict = {
            "id": 1,
            "name": "Joe",
            "friends": [
                {"id": 3, "name": "Sue", "pets": ["fish", "bird"]},
                {"id": 2, "name": "Pat", "pets": ["dog"]},
            ],
            "pets": [],
        }

        result_pass_strict = self.json_comparator.compare_json(
            expected, actual_pass_strict
        )
        assert result_pass_strict.is_success

        result_fail_strict = self.json_comparator.compare_json(
            expected, actual_fail_strict
        )
        print(result_fail_strict.fail_messages)

    def test_array_of_arrays(self):
        expected = {"id": 1, "stuff": [[1, 2], [2, 3], [], [3, 4]]}
        actual_pass = {"id": 1, "stuff": [[1, 2], [2, 3], [], [3, 4]]}
        actual_fail = {"id": 1, "stuff": [[1, 2], [2, 3], [3, 4], []]}

        result_pass = self.json_comparator.compare_json(expected, actual_pass)
        assert result_pass.is_success

        result_fail = self.json_comparator.compare_json(expected, actual_fail)
        print(result_fail.fail_messages)
        assert not result_fail.is_success
