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


from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass
class BuildAgent:
    """
    Build tool information
    """

    name: str | None = None
    """
    Build tool type
    """
    version: str | None = None
    """
    Build tool version
    """


@dataclass
class Agent:
    """
    CI server information
    """

    name: str | None = None
    """
    CI server type
    """
    version: str | None = None
    """
    CI server version
    """


@dataclass
class Artifact:
    type: str | None = None
    name: str | None = None
    path: str | None = None
    sha256: str | None = None
    sha1: str | None = None
    md5: str | None = None


@dataclass
class Dependency:
    type: str | None = None
    id: str | None = None
    sha256: str | None = None
    sha1: str | None = None
    md5: str | None = None
    scopes: Sequence[str] | None = None
    requestedBy: Sequence[Sequence[str]] | None = None
    """
    List of ancestor dependencies, which caused this dependency to be imported into the build
    """


@dataclass
class Module:
    properties: Mapping[str, str] | None = None
    """
    Module properties
    """
    id: str | None = None
    """
    Module ID
    """
    type: str | None = None
    """
    Module type
    """
    artifacts: Sequence[Artifact] | None = None
    """
    List of module artifacts
    """
    dependencies: Sequence[Dependency] | None = None
    """
    List of module dependencies
    """


@dataclass
class Tracker:
    name: str
    version: str


@dataclass
class AffectedIssue:
    key: str | None = None
    url: str | None = None
    summary: str | None = None
    aggregated: bool | None = None
    """
    Whether this specific issue already appeared in previous builds
    """


@dataclass
class Issues:
    """
    List of issues related to the build
    """

    tracker: Tracker | None = None
    aggregateBuildIssues: bool | None = None
    """
    Whether issues have appeared in previous builds
    """
    aggregationBuildStatus: str | None = None
    affectedIssues: Sequence[AffectedIssue] | None = None


@dataclass
class BuildInfo:
    """
    build-info
    """

    properties: Mapping[str, str] | None = None
    """
    Environment variables and properties collected from the CI server
    """
    version: str | None = None
    """
    Build info schema version
    """
    name: str | None = None
    """
    Build name
    """
    number: str | None = None
    """
    Build number
    """
    type: str | None = None
    """
    Build type
    """
    buildAgent: BuildAgent | None = None
    """
    Build tool information
    """
    agent: Agent | None = None
    """
    CI server information
    """
    started: str | None = None
    """
    Build start time
    """
    durationMillis: int | None = None
    """
    Build duration in milliseconds
    """
    principal: str | None = None
    url: str | None = None
    """
    CI server URL
    """
    vcs: Sequence[Any] | None = None
    """
    List of VCS used for the build
    """
    modules: Sequence[Module] | None = None
    """
    Build-info modules
    """
    issues: Issues | None = None
    """
    List of issues related to the build
    """
