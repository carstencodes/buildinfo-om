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


from ._builder import (
    AffectedIssueBuilder,
    AgentBuilder,
    ArtifactBuilder,
    BuildAgentBuilder,
    BuildInfoBuilder,
    DependencyBuilder,
    IssuesBuilder,
    ModuleBuilder,
    TrackerBuilder,
    VCSBuilder,
)
from ._loadsave import (
    load_from_buffer,
    load_from_dict,
    load_from_file,
    load_from_str,
    save_to_buffer,
    save_to_file,
    transform_to_mapping,
    transform_to_str,
)
from ._merge import merge_build_info
from ._model import (
    AffectedIssue,
    Agent,
    Artifact,
    BuildAgent,
    Dependency,
    Issues,
    Module,
    Tracker,
)
from ._vcs import VCS, BuildInfo

__all__ = [
    Agent.__name__,
    BuildAgent.__name__,
    BuildInfo.__name__,
    Issues.__name__,
    AffectedIssue.__name__,
    Module.__name__,
    Tracker.__name__,
    Artifact.__name__,
    Dependency.__name__,
    VCS.__name__,
    load_from_file.__name__,
    load_from_buffer.__name__,
    save_to_file.__name__,
    save_to_buffer.__name__,
    transform_to_str.__name__,
    transform_to_mapping.__name__,
    load_from_dict.__name__,
    load_from_str.__name__,
    merge_build_info.__name__,
    AffectedIssueBuilder.__name__,
    AgentBuilder.__name__,
    ArtifactBuilder.__name__,
    BuildAgentBuilder.__name__,
    BuildInfoBuilder.__name__,
    DependencyBuilder.__name__,
    IssuesBuilder.__name__,
    ModuleBuilder.__name__,
    TrackerBuilder.__name__,
    VCSBuilder.__name__,
]
