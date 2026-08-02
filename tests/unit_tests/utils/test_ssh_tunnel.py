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

from superset.constants import PASSWORD_MASK
from superset.databases.ssh_tunnel.models import SSHTunnel
from superset.utils.ssh_tunnel import (
    get_default_port,
    mask_password_info,
    unmask_password_info,
)


def test_mask_password_info_masks_all_secrets():
    assert mask_password_info(
        {
            "server_address": "localhost",
            "password": "secret",
            "private_key": "-----BEGIN RSA-----",
            "private_key_password": "another-secret",
        }
    ) == {
        "server_address": "localhost",
        "password": PASSWORD_MASK,
        "private_key": PASSWORD_MASK,
        "private_key_password": PASSWORD_MASK,
    }


def test_mask_password_info_leaves_absent_and_none_keys_out():
    assert mask_password_info({"server_address": "localhost", "password": None}) == {
        "server_address": "localhost"
    }


def test_unmask_password_info_restores_values_from_model():
    model = SSHTunnel(
        password="secret",  # noqa: S106
        private_key="-----BEGIN RSA-----",
        private_key_password="another-secret",  # noqa: S106
    )
    assert unmask_password_info(
        {
            "server_address": "localhost",
            "password": PASSWORD_MASK,
            "private_key": PASSWORD_MASK,
            "private_key_password": PASSWORD_MASK,
        },
        model,
    ) == {
        "server_address": "localhost",
        "password": "secret",
        "private_key": "-----BEGIN RSA-----",
        "private_key_password": "another-secret",
    }


def test_unmask_password_info_keeps_new_values():
    model = SSHTunnel(password="old")  # noqa: S106
    assert unmask_password_info({"password": "new"}, model) == {"password": "new"}


@pytest.mark.parametrize(
    "backend,expected",
    [
        ("postgresql", 5432),
        ("mysql", 3306),
        ("oracle", 1521),
        ("mssql", 1433),
        ("sqlite", None),
    ],
)
def test_get_default_port(backend: str, expected: int | None):
    assert get_default_port(backend) == expected
