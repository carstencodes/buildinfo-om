#!/usr/bin/env python3

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

from inspect import getmembers, isclass, signature, Parameter
from pathlib import Path

from buildinfo_om import _builder as builder_module


def is_relevant(m) -> bool:
    if not hasattr(m, "__module__"):
        return False
    return (m.__module__ == 'buildinfo_om._builder'
            and isclass(m) and not m.__name__.startswith('_'))


members = getmembers(builder_module, is_relevant)

cur_path = Path(__file__).parent.resolve()
project_path = cur_path.parent.parent
out_dir = project_path / 'src' / 'buildinfo_om'

out_file = out_dir / '_builder.pyi'

lines: list[str] = []
class_types: list[str] = []
model_types: set[str] = set()

for member in members:
    member_name, member_instance = member
    class_types.append(member_name)
    if isclass(member_instance):
        model_type = "Any"
        lines.append(f"class {member_name}:")
        for function in [f for f in getmembers(member_instance)
                         if not f[0].startswith("_")]:
            sig = signature(function[1])
            if function[0] == "build":
                model_type = sig.return_annotation.__name__
            elif function[0] == "from_instance":
                lines.append("    @staticmethod")

            params = sig.parameters
            def_line = "    def "
            def_line += function[0]
            def_line += "("
            for key, value in params.items():
                if value.kind == Parameter.VAR_POSITIONAL:
                    def_line += "*"
                elif value.kind == Parameter.VAR_KEYWORD:
                    def_line += "**"

                def_line += key
                if key != "self":
                    if function[0] == "from_instance" and key == "instance":
                        def_line += f": {model_type}"
                    else:
                        def_line += f": {value.annotation.__name__}"
                def_line += ", "
            def_line = def_line[:-2]
            def_line += ")"
            if function[0] == "build":
                def_line += f" -> {model_type}"
            elif function[0] == "from_instance":
                def_line += f" -> {member_name}"
            else:
                def_line += f" -> {sig.return_annotation.__name__}"
            def_line += ": ..."
            lines.append(def_line)

        model_types.add(model_type)

    lines.append("\n")


model_types.remove("VCS")
sorted_model_types = sorted(list(model_types))

with open(__file__, "r") as input:
    license_lines = input.readlines()
    license_lines = [l for l in license_lines if l.startswith("#")]
    license_lines = license_lines[1:]


with out_file.open('w') as stream:
    print("".join(license_lines), file=stream)

    print("\n", file=stream)

    print('"""', file=stream)
    print("   File stubs for runtime generated types: ", file=stream)
    print("\n".join([f"     * {c}" for c in class_types]), file=stream)
    print('"""', file=stream)

    print("\n", file=stream)

    print("from typing import Any, Self", file=stream)

    print("from ._model import (", file=stream)
    for model in sorted_model_types:
        print(f"    {model},", file=stream)
    print(")", file=stream)
    print("from ._vcs import VCS", file=stream)

    print("\n\n", file=stream)
    print("\n".join(lines), file=stream)
    print("\n", file=stream)
