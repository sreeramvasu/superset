# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import pytest
from marshmallow import ValidationError

from superset.utils.schema import (
    OneOfCaseInsensitive,
    validate_external_url,
    validate_json,
)


@pytest.mark.parametrize("value", ["FOO", "foo", "Foo"])
def test_one_of_case_insensitive_accepts_any_casing(value: str):
    validator = OneOfCaseInsensitive(choices=["foo", "bar"])
    assert validator(value) == value


def test_one_of_case_insensitive_accepts_non_string_choices():
    validator = OneOfCaseInsensitive(choices=[1, 2])
    assert validator(1) == 1


def test_one_of_case_insensitive_rejects_unknown_value():
    validator = OneOfCaseInsensitive(choices=["foo"])
    with pytest.raises(ValidationError):
        validator("baz")


def test_one_of_case_insensitive_rejects_unhashable_value():
    validator = OneOfCaseInsensitive(choices=["foo"])
    with pytest.raises(ValidationError):
        validator(None)


@pytest.mark.parametrize("value", ['{"a": 1}', b'{"a": 1}', "[]"])
def test_validate_json_accepts_valid_payloads(value):
    validate_json(value)


def test_validate_json_rejects_invalid_payload():
    with pytest.raises(ValidationError):
        validate_json("{invalid")


@pytest.mark.parametrize(
    "value",
    ["http://example.com", "https://example.com/path?a=1", "HTTPS://EXAMPLE.COM"],
)
def test_validate_external_url_accepts_http_urls(value: str):
    validate_external_url(value)


@pytest.mark.parametrize("value", [None, ""])
def test_validate_external_url_allows_empty_values(value):
    validate_external_url(value)


@pytest.mark.parametrize(
    "value",
    ["javascript:alert(1)", "data:text/html;base64,PHNjcmlwdD4=", "vbscript:msgbox"],
)
def test_validate_external_url_rejects_dangerous_schemes(value: str):
    with pytest.raises(ValidationError):
        validate_external_url(value)


def test_validate_external_url_rejects_relative_url():
    with pytest.raises(ValidationError):
        validate_external_url("https:foo")
