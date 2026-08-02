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

from typing import Any

from superset.models.slice import Slice
from superset.utils import json
from superset.utils.dashboard_filter_scopes_converter import (
    convert_filter_scopes,
    copy_filter_scopes,
)


def filter_box(slice_id: int, params: dict[str, Any]) -> Slice:
    slc = Slice(slice_name=f"filter_box_{slice_id}", params=json.dumps(params))
    slc.id = slice_id
    return slc


def test_convert_filter_scopes_time_filters():
    scopes = convert_filter_scopes(
        {},
        [
            filter_box(
                1,
                {
                    "date_filter": True,
                    "show_sqla_time_column": True,
                    "show_sqla_time_granularity": True,
                },
            )
        ],
    )

    assert scopes == {
        1: {
            "__time_range": {"scope": ["ROOT_ID"], "immune": []},
            "__time_col": {"scope": ["ROOT_ID"], "immune": []},
            "__time_grain": {"scope": ["ROOT_ID"], "immune": []},
        }
    }


def test_convert_filter_scopes_applies_immunity():
    scopes = convert_filter_scopes(
        {
            "filter_immune_slices": [10],
            "filter_immune_slice_fields": {"20": ["gender"]},
        },
        [filter_box(1, {"filter_configs": [{"column": "gender"}]})],
    )

    assert sorted(scopes[1]["gender"]["immune"]) == [10, 20]


def test_convert_filter_scopes_skips_filter_boxes_without_fields():
    assert convert_filter_scopes({}, [filter_box(1, {})]) == {}


def test_convert_filter_scopes_ignores_invalid_columns():
    scopes = convert_filter_scopes(
        {},
        [filter_box(1, {"filter_configs": [{"column": None}, {"column": "gender"}]})],
    )

    assert list(scopes[1]) == ["gender"]


def test_copy_filter_scopes_remaps_ids():
    new_scopes = copy_filter_scopes(
        old_to_new_slc_id_dict={1: 101, 2: 102},
        old_filter_scopes={1: {"gender": {"scope": ["ROOT_ID"], "immune": [2, 3]}}},
    )

    assert new_scopes == {"101": {"gender": {"scope": ["ROOT_ID"], "immune": [102]}}}


def test_copy_filter_scopes_drops_unmapped_filters():
    assert (
        copy_filter_scopes(
            old_to_new_slc_id_dict={},
            old_filter_scopes={1: {"gender": {"scope": ["ROOT_ID"], "immune": []}}},
        )
        == {}
    )
