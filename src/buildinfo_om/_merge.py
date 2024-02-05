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


from datetime import datetime, timedelta
from enum import IntEnum, auto
from os import pathsep
from typing import Mapping, Sequence, TypeVar

from ._model import AffectedIssue, Agent, BuildAgent, Issues, Module
from ._vcs import VCS, BuildInfo


class NonUniqueBuilds(IntEnum):
    """ """

    IGNORE = auto()
    """
    """
    CANCEL = auto()
    """
    """
    SKIP = auto()
    """
    """


class NonSameSetsOfProperties(IntEnum):
    """ """

    IGNORE = auto()
    """
    """
    CANCEL = auto()
    """
    """
    SKIP = auto()
    """
    """
    DELETE = auto()
    """
    """
    JOIN = auto()
    """
    """


def merge_build_info(
    *items: BuildInfo,
    different_data: NonUniqueBuilds = NonUniqueBuilds.SKIP,
    different_props: NonSameSetsOfProperties = NonSameSetsOfProperties.SKIP,
) -> BuildInfo:
    """

    Parameters
    ----------
    items: tuple[BuildInfo, ...]
    different_data: NonUniqueBuilds
    different_props: NonSameSetsOfProperties

    Returns
    -------
    BuildInfo

    """

    filtered_items = _verify_builds(different_data, *items)

    result: BuildInfo = BuildInfo()

    result.name = _select_name(*filtered_items)
    result.number = _select_number(*filtered_items)
    result.version = _select_version(*filtered_items)
    result.vcs = _select_vcs(*filtered_items)
    result.buildAgent = _unify_build_agent(*filtered_items)
    result.agent = _unify_agent(*filtered_items)
    result.started, result.durationMillis = _sum_up_build_duration(
        *filtered_items
    )
    result.modules = _combine_modules(*filtered_items)
    result.url = _select_url(*filtered_items)
    result.type = _select_type(*filtered_items)
    result.issues = _combine_issues(*filtered_items)
    result.properties = _combine_properties(different_props, *filtered_items)
    result.principal = _select_principal(*filtered_items)

    return result


_T = TypeVar("_T")


def __unique_or_first(*items: _T) -> _T | None:
    """

    Parameters
    ----------
    items

    Returns
    -------

    """
    if len(items) == 0:
        return None

    return items[0]


def __unique_or_combined(*items: _T, separator: str = ", ") -> str | None:
    """

    Parameters
    ----------
    items: tuple[_T, ...]
    separator: str
        (the default value is ", ")

    Returns
    -------
    str | None

    """
    if len(items) == 0:
        return None

    return separator.join({str(i) for i in items})


def __combine_sequence(*items: Sequence[_T]) -> Sequence[_T] | None:
    """

    Parameters
    ----------
    items: tuple[Sequence[_T], ...]

    Returns
    -------
    Sequence[_T] | None

    """
    if len(items) == 0:
        return None

    new_items: set[_T] = set()
    for item in items:
        new_items = new_items.union(item)

    return list(new_items)


def _select_name(*items: BuildInfo) -> str | None:
    """

    Parameters
    ----------
    items: tuple[BuildInfo, ...]

    Returns
    -------
    str | None

    """
    return __unique_or_first(
        *tuple({b.name for b in items if b.name is not None})
    )


def _select_number(*items: BuildInfo) -> str | None:
    """

    Parameters
    ----------
    items: tuple[BuildInfo, ...]

    Returns
    -------
    str | None

    """
    return __unique_or_first(
        *tuple({b.number for b in items if b.number is not None})
    )


def _select_version(*items: BuildInfo) -> str | None:
    """

    Parameters
    ----------
    items: tuple[BuildInfo, ...]

    Returns
    -------
    str | None

    """
    return __unique_or_first(
        *tuple({b.version for b in items if b.version is not None})
    )


def _select_vcs(*items: BuildInfo) -> Sequence[VCS] | None:
    """

    Parameters
    ----------
    items: tuple[BuildInfo, ...]

    Returns
    -------
    Sequence[VCS] | None

    """
    return __combine_sequence(
        *tuple(b.vcs for b in items if b.vcs is not None)
    )


def _unify_build_agent(*items: BuildInfo) -> BuildAgent | None:
    """

    Parameters
    ----------
    items: tuple[BuildInfo, ...]

    Returns
    -------
    BuildAgent | None

    """
    build_agents: tuple[BuildAgent, ...] = tuple(
        b.buildAgent for b in items if b.buildAgent is not None
    )
    agent: BuildAgent = BuildAgent()
    agent.name = __unique_or_combined(
        *tuple(a.name for a in build_agents if a.name is not None)
    )
    agent.version = __unique_or_combined(
        *tuple(a.version for a in build_agents if a.version is not None)
    )

    return agent


def _unify_agent(*items: BuildInfo) -> Agent | None:
    """

    Parameters
    ----------
    items: tuple[BuildInfo, ...]

    Returns
    -------
    Agent | None

    """
    agents: tuple[Agent, ...] = tuple(
        b.agent for b in items if b.agent is not None
    )
    agent: Agent = Agent()
    agent.name = __unique_or_combined(
        *tuple(a.name for a in agents if a.name is not None)
    )
    agent.version = __unique_or_combined(
        *tuple(a.version for a in agents if a.version is not None)
    )

    return agent


def _combine_modules(*items: BuildInfo) -> Sequence[Module] | None:
    """

    Parameters
    ----------
    items: tuple[BuildInfo, ...]

    Returns
    -------
    Sequence[Module] | None

    """
    # TODO merge module inner values
    return __combine_sequence(
        *tuple(b.modules for b in items if b.modules is not None)
    )


def _select_url(*items: BuildInfo) -> str | None:
    """

    Parameters
    ----------
    items: tuple[BuildInfo, ...]

    Returns
    -------
    str | None

    """
    return __unique_or_combined(
        *tuple({b.url for b in items if b.url is not None})
    )


def _select_type(*items: BuildInfo) -> str | None:
    """

    Parameters
    ----------
    items: tuple[BuildInfo, ...]

    Returns
    -------
    str | None

    """
    return __unique_or_combined(
        *tuple({b.type for b in items if b.type is not None})
    )


def _combine_issues(*items: BuildInfo) -> Issues | None:
    """

    Parameters
    ----------
    items: tuple[BuildInfo, ...]

    Returns
    -------
    Issues | None

    """
    if len(items) == 0:
        return None

    issues: Issues = Issues()
    issue_list: list[AffectedIssue] = []
    status_list: set[str] = set()

    for item in items:
        if item.issues is not None:
            __push_to_new_issue(issues, item.issues, issue_list, status_list)

    issues.aggregationBuildStatus = (
        "\n".join(status_list) if len(status_list) > 0 else None
    )
    issues.affectedIssues = issue_list if len(issue_list) > 0 else None

    return issues


def __push_to_new_issue(
    new_issues: Issues,
    current_issue: Issues,
    all_affected_issues: list[AffectedIssue],
    all_aggregated_states: set[str],
) -> None:
    """

    Parameters
    ----------
    new_issues: Issues

    current_issue: Issues

    all_affected_issues: list[AffectedIssue]

    all_aggregated_states: set[str}

    Returns
    -------
    None

    """
    if current_issue.aggregateBuildIssues is not None:
        new_issues.aggregateBuildIssues = (
            current_issue.aggregateBuildIssues
            and new_issues.aggregateBuildIssues
            if new_issues.aggregateBuildIssues is not None
            else current_issue.aggregateBuildIssues
        )
    if new_issues.tracker is None:
        new_issues.tracker = current_issue.tracker
    if current_issue.affectedIssues is not None:
        all_affected_issues.extend(current_issue.affectedIssues)
    if current_issue.aggregationBuildStatus is not None:
        all_aggregated_states.add(current_issue.aggregationBuildStatus)


def _combine_properties(
    different_properties: NonSameSetsOfProperties, *items: BuildInfo
) -> Mapping[str, str] | None:
    """

    Parameters
    ----------
    different_properties: NonSameSetsOfProperties
    items: tuple[BuildInfo, ...]

    Returns
    -------
    Mapping[str, str] | None

    """
    if len(items) == 0:
        return None

    deleted: set[str] = set()
    properties: dict[str, set[str]] = {}
    for item in items:
        if item.properties is None:
            continue

        for key in item.properties.keys():
            if key in deleted:
                continue

            if key not in properties:
                properties[key] = set()
                properties[key].add(item.properties[key])
            elif __can_combine_current_property_set(
                different_properties,
                key,
                properties[key],
                item.properties[key],
            ):
                deleted.add(key)
                _ = properties.pop(key, None)

    return {k: pathsep.join(v) for k, v in properties.items()}


def __can_combine_current_property_set(
    different_properties: NonSameSetsOfProperties,
    identifier: str,
    items: set[str],
    current: str,
) -> bool:
    """

    Parameters
    ----------
    different_properties: NonSameSetsOfProperties
    identifier: str
    items: tuple[set[str], ...]
    current: str

    Returns
    -------
    bool

    """
    if different_properties == NonSameSetsOfProperties.IGNORE:
        items.add(current)
    elif different_properties == NonSameSetsOfProperties.JOIN:
        items.add(current)
    elif different_properties != NonSameSetsOfProperties.SKIP:
        if current not in items:
            if different_properties == NonSameSetsOfProperties.CANCEL:
                raise ValueError(
                    "Cannot combine properties", identifier, items, current
                )
            return different_properties != NonSameSetsOfProperties.DELETE

    return True


def _select_principal(*items: BuildInfo) -> str | None:
    """

    Parameters
    ----------
    items: tuple[BuildInfo, ...]

    Returns
    -------
    str | None

    """
    return __unique_or_combined(
        *tuple({b.principal for b in items if b.principal is not None})
    )


def _sum_up_build_duration(*items: BuildInfo) -> tuple[str | None, int | None]:
    """

    Parameters
    ----------
    items: tuple[BuildInfo, ...]

    Returns
    -------
    tuple[str | None, int | None]

    """
    starts_and_durations: list[tuple[datetime | None, timedelta | None]] = [
        (
            (
                datetime.fromisoformat(build.started)
                if build.started is not None
                else None
            ),
            (
                timedelta(milliseconds=build.durationMillis)
                if build.durationMillis is not None
                else None
            ),
        )
        for build in items
    ]
    starts_and_ends: list[tuple[datetime | None, datetime | None]] = [
        (
            start if start is not None else None,
            (
                start + duration
                if start is not None and duration is not None
                else None
            ),
        )
        for start, duration in starts_and_durations
    ]

    starts = [start for start, _ in starts_and_ends if start is not None]
    ends = [end for _, end in starts_and_ends if end is not None]

    start: str | None = None
    duration: int | None = None

    if len(starts) > 0:
        start_time: datetime = min(starts)
        start = start_time.isoformat()
        if len(ends) > 0:
            end_time: datetime = max(ends)
            duration_delta = end_time - start_time
            duration_seconds: float = duration_delta.total_seconds()
            duration_milliseconds: float = duration_seconds * 1000
            duration = int(duration_milliseconds)

    return start, duration


def _verify_builds(
    different_builds: NonUniqueBuilds, *items: BuildInfo
) -> tuple[BuildInfo, ...]:
    """

    Parameters
    ----------
    different_builds: NonUniqueBuilds
    items: tuple[BuildInfo, ...]

    Returns
    -------
    tuple[BuildInfo, ...]

    """
    if different_builds == NonUniqueBuilds.IGNORE:
        return ()

    names: set[str] = set()
    numbers: set[str] = set()

    for build in items:
        if build.name is not None:
            names.add(build.name)
        if build.number is not None:
            numbers.add(build.number)

    if different_builds == NonUniqueBuilds.CANCEL:
        if len(names) != 1:
            raise ValueError("Multiple names")
        if len(numbers) != 1:
            raise ValueError("Multiple numbers")

    if different_builds != NonUniqueBuilds.SKIP:
        raise ValueError("Invalid configuration:", different_builds)

    first_build: BuildInfo = tuple(
        filter(lambda b: b.name is not None and b.number is not None, items)
    )[0]

    return tuple(
        build
        for build in items
        if build.name == first_build.name
        and build.number == first_build.number
    )
