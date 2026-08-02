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
"""Tests for the access control of the alert/report log view."""

from unittest.mock import MagicMock, patch

import pytest
from werkzeug.exceptions import NotFound


def _call_log(
    *, feature_enabled: bool, report: object | None
) -> tuple[object, MagicMock]:
    from superset.views import alerts as alerts_module

    with (
        patch.object(alerts_module, "is_feature_enabled", return_value=feature_enabled),
        patch.object(
            alerts_module.ReportScheduleDAO, "find_by_id", return_value=report
        ) as find_by_id,
        patch.object(
            alerts_module.BaseSupersetView,
            "render_app_template",
            return_value="rendered",
        ),
    ):
        response = alerts_module.ReportView().log(1)
        return response, find_by_id


def test_log_aborts_when_feature_disabled() -> None:
    with pytest.raises(NotFound):
        _call_log(feature_enabled=False, report=MagicMock())


def test_log_aborts_when_report_not_visible_to_user() -> None:
    """The DAO base filter scopes reports, so an inaccessible id yields a 404."""
    with pytest.raises(NotFound):
        _call_log(feature_enabled=True, report=None)


def test_log_renders_for_accessible_report() -> None:
    response, find_by_id = _call_log(feature_enabled=True, report=MagicMock())
    assert response == "rendered"
    find_by_id.assert_called_once_with(1)
