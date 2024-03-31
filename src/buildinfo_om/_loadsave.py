#
#
# SPDX-Identifier: Apache 2.0 OR MIT
#
# Copyright (c) 2024 Carsten Igel.
#
# This file is part of pdm-bump
# (see https://github.com/carstencodes/pdm-bump).
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#  == OR ==
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#

"""
"""
from collections.abc import Sequence
from dataclasses import asdict
from json import dumps, loads
from os import PathLike
from typing import Any, Mapping, TextIO, cast, AnyStr, IO

from dacite import Config, from_dict  # type: ignore

from ._vcs import BuildInfo


def load_from_file(path: PathLike) -> BuildInfo:
    """

    Parameters
    ----------
    path: PathLike

    Returns
    -------
    BuildInfo

    """
    with open(path, "r", encoding="utf-8") as buffer:
        return load_from_buffer(buffer)


def load_from_buffer(buf: TextIO) -> BuildInfo:
    """

    Parameters
    ----------
    buf: TextIO

    Returns
    -------
    BuildInfo

    """
    data: str | bytes = buf.read()
    return load_from_str(data)


def load_from_str(value: str | bytes | bytearray) -> BuildInfo:
    """

    Parameters
    ----------
    value: str | bytes | bytearray

    Returns
    -------
    BuildInfo

    """
    data: Any = loads(value)
    transformable_data: Mapping[str, Any] = (
        cast(dict, data) if isinstance(data, dict) else vars(data)
    )
    return load_from_dict(transformable_data)


def load_from_dict(data: Mapping[str, Any]) -> BuildInfo:
    """

    Parameters
    ----------
    data: Mapping[str, Any]

    Returns
    -------
    BuildInfo

    """
    cfg: Config = Config()
    cfg.check_types = True
    cfg.strict = True
    cfg.strict_unions_match = True

    return from_dict(BuildInfo, data, cfg)


def save_to_file(bi: BuildInfo, path: PathLike) -> None:
    """

    Parameters
    ----------
    bi: BuildInfo
    path: PathLike

    Returns
    -------
    None

    """
    with open(path, "w+", encoding="utf-8") as buffer:
        save_to_buffer(bi, buffer)


def save_to_text_buffer(bi: BuildInfo, buffer: TextIO) -> None:
    """

    Parameters
    ----------
    bi: BuildInfo
    buffer: TextIO

    Returns
    -------
    None

    """
    data: str = transform_to_str(bi)
    buffer.write(data)


def save_to_buffer(bi: BuildInfo, buffer: IO[AnyStr]) -> None:
    """

    Parameters
    ----------
    bi: BuildInfo
    buffer: IO[AnyStr]

    Returns
    -------
    None

    """
    data: str = transform_to_str(bi)
    buffer.write(data)


def transform_to_str(bi: BuildInfo) -> str:
    """

    Parameters
    ----------
    bi: BuildInfo

    Returns
    -------
    str

    """
    data: Mapping[str, Any] = transform_to_mapping(bi)
    return dumps(data)


def _remove_empty_values(data: Mapping[str, Any]) -> Mapping[str, Any]:
    for key, value in list(data.items()):
        if value is None:
            del data[key]
        elif isinstance(value, dict):
            _ = _remove_empty_values(value)
        elif isinstance(value, Sequence):
            for inner_value in list(value):
                if isinstance(inner_value, dict):
                    _ = _remove_empty_values(inner_value)

    return data


def transform_to_mapping(bi: BuildInfo) -> Mapping[str, Any]:
    """

    Parameters
    ----------
    bi: BuildInfo

    Returns
    -------
    Mapping[str, Any]

    """
    data: Mapping[str, Any] = asdict(bi)
    _remove_empty_values(data)
    return data
