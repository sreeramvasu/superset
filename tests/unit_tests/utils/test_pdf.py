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

from io import BytesIO

import pytest
from PIL import Image

from superset.commands.report.exceptions import ReportSchedulePdfFailedError
from superset.utils.pdf import build_pdf_from_screenshots


def create_screenshot(mode: str = "RGB") -> bytes:
    buffer = BytesIO()
    Image.new(mode, (10, 10), "red").save(buffer, "PNG")
    return buffer.getvalue()


def test_build_pdf_from_screenshots_single_image():
    pdf = build_pdf_from_screenshots([create_screenshot()])

    assert pdf.startswith(b"%PDF")


def test_build_pdf_from_screenshots_converts_rgba_images():
    pdf = build_pdf_from_screenshots([create_screenshot("RGBA"), create_screenshot()])

    assert pdf.startswith(b"%PDF")


def test_build_pdf_from_screenshots_raises_on_empty_list():
    with pytest.raises(ReportSchedulePdfFailedError):
        build_pdf_from_screenshots([])
