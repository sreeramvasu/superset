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

from superset.views.alerts import AlertView, BaseAlertReportView, ReportView


@pytest.mark.parametrize("view", [BaseAlertReportView, AlertView, ReportView])
def test_route_methods_are_scoped(view: type[BaseAlertReportView]) -> None:
    assert view.include_route_methods == {"list", "log"}


@pytest.mark.parametrize("view", [BaseAlertReportView, AlertView, ReportView])
def test_method_permissions(view: type[BaseAlertReportView]) -> None:
    assert view.class_permission_name == "ReportSchedule"
    assert view.method_permission_name == {"list": "read", "log": "read"}
