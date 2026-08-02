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
from werkzeug.exceptions import NotFound
from werkzeug.routing import Map, Rule

from superset.tags.models import ObjectType
from superset.utils.url_map_converters import ObjectTypeConverter, RegexConverter


def test_regex_converter_matches_configured_pattern():
    url_map = Map(
        [Rule("/<regex('[0-9]+'):value>/", endpoint="test")],
        converters={"regex": RegexConverter},
    )
    adapter = url_map.bind("localhost")

    assert adapter.match("/123/") == ("test", {"value": "123"})

    with pytest.raises(NotFound):
        adapter.match("/abc/")


def test_object_type_converter_round_trip():
    converter = ObjectTypeConverter(Map())

    assert converter.to_python("dashboard") == ObjectType.dashboard
    assert converter.to_url(ObjectType.dashboard) == "dashboard"


def test_object_type_converter_rejects_unknown_type():
    converter = ObjectTypeConverter(Map())

    with pytest.raises(KeyError):
        converter.to_python("invalid_type")
