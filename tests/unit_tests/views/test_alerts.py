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
"""Tests for the access control of the alerts & reports HTML views."""

from unittest.mock import MagicMock, patch

import pytest
from werkzeug.exceptions import NotFound

from superset.views.alerts import BaseAlertReportView


def _call_log(pk: str, *, report: object | None) -> object:
    with (
        patch("superset.views.alerts.is_feature_enabled", return_value=True),
        patch("superset.views.alerts.ReportScheduleDAO") as mock_dao,
        patch.object(
            BaseAlertReportView, "render_app_template", return_value="rendered"
        ),
    ):
        mock_dao.find_by_id.return_value = report
        result = BaseAlertReportView().log(pk)
        mock_dao.find_by_id.assert_called_once_with(pk)
        return result


def test_log_renders_for_visible_report() -> None:
    """A report schedule the user is entitled to see renders the SPA."""
    assert _call_log("1", report=MagicMock()) == "rendered"


def test_log_aborts_when_report_not_visible() -> None:
    """The DAO base filter hides other users' reports, which 404s."""
    with pytest.raises(NotFound):
        _call_log("1", report=None)


def test_log_aborts_when_feature_disabled() -> None:
    """The route stays hidden while the feature flag is off."""
    with (
        patch("superset.views.alerts.is_feature_enabled", return_value=False),
        patch("superset.views.alerts.ReportScheduleDAO") as mock_dao,
        pytest.raises(NotFound),
    ):
        BaseAlertReportView().log("1")
    mock_dao.find_by_id.assert_not_called()
