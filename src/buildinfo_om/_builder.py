#
# SPDX-Identifier: Apache 2.0 OR MIT
#
# Copyright (C) 2024 Carsten Igel
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
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import collections
from abc import ABC, abstractmethod
from dataclasses import Field, fields, is_dataclass
from functools import partial
from inspect import isclass
from os import environ
from types import new_class
from typing import (Any, Callable, Generic, Mapping, Self, Sequence, TypeAlias,
                    TypeVar, Union, cast, get_args, get_origin)

from makefun import create_function  # type: ignore

from ._model import (AffectedIssue, Agent, Artifact, BuildAgent, Dependency,
                     Issues, Module, Tracker)
from ._vcs import VCS, BuildInfo

TModel = TypeVar(
    "TModel",
    Agent,
    BuildAgent,
    Issues,
    AffectedIssue,
    Module,
    Tracker,
    Artifact,
    Dependency,
    BuildInfo,
    VCS,
)


class _BuildArguments(dict[str, Any]):
    def get_build_items(self) -> Mapping[str, Any]:
        ro_copy: dict[str, Any] = {}
        ro_copy.update(self)
        return ro_copy


class _Builder(ABC, Generic[TModel]):
    @abstractmethod
    def build(self) -> TModel:
        raise NotImplementedError()


_BuilderCollection = dict[str, type[_Builder[TModel]]]
__all_builders: _BuilderCollection = {}


_FluentFunctArgsType = Any | tuple[Any, ...] | Mapping[Any, Any]
_FluentFunctionType = Callable[[Any, str, _FluentFunctArgsType], Any]


def _make_non_optional_type(t: type) -> type:
    if get_origin(t) is Union and type(None) in get_args(t):
        return cast(type, tuple([a for a in get_args(t) if a is not type(None)]))

    return t


def _determine_fluent_function(
    field: Field, additional_builders: _BuilderCollection
) -> tuple[_FluentFunctionType, str, type]:
    def with_scalar(self, field_name: str, value: Any):
        my_args: _BuildArguments = self.__args
        my_args[field_name] = value
        return self

    def with_builder(self, field_name: str, builder: _Builder):
        my_args: _BuildArguments = self.__args
        my_args[field_name] = builder.build()
        return self

    def with_sequence(self, field_name: str, *values: Any):
        my_args: _BuildArguments = self.__args
        seq: Sequence = [v for v in values]
        my_args[field_name] = seq
        return self

    def with_mapping(self, field_name: str, **values: Any):
        my_args: _BuildArguments = self.__args
        mapping: Mapping[str, Any] = values
        my_args[field_name] = mapping
        return self

    def with_builder_sequence(self, field_name: str, *builders: _Builder):
        my_args: _BuildArguments = self.__args
        seq: Sequence = [b.build() for b in builders]
        my_args[field_name] = seq
        return self

    field_type = field.type
    # Strange behavior: dataclass removes all inspections from field type
    # So: Make type non-optional
    from typing import get_origin, get_args
    field_type = _make_non_optional_type(field_type)

    if is_dataclass(field_type):
        arg_type = _create_builder(field.type, additional_builders)
        arg_name = "builder"
        return cast(_FluentFunctionType, with_builder), arg_name, arg_type
    elif get_origin(field_type) is collections.abc.Mapping or (
        isclass(field_type) and issubclass(field_type, collections.abc.Mapping)
    ):
        args = get_args(field_type)
        return cast(_FluentFunctionType, with_mapping), "**values", args[-1]
    elif get_origin(field_type) is collections.abc.Sequence or (
        isclass(field_type)
        and issubclass(field_type, collections.abc.Sequence)
        and field_type not in (str, bytes, bytearray)
    ):
        args = get_args(field_type)
        if len(args) == 1:
            field_type = args[0]
            if is_dataclass(field_type):
                arg_type = _create_builder(field_type, additional_builders)
                arg_name = "*builders"
                return (
                    cast(_FluentFunctionType, with_builder_sequence),
                    arg_name,
                    arg_type,
                )
            else:
                arg_name = "*values"
                return cast(_FluentFunctionType, with_sequence), arg_name, field_type
        return cast(_FluentFunctionType, with_sequence), "*values", Any  # type: ignore
    else:
        return cast(_FluentFunctionType, with_scalar), "value", field_type


def _create_builder(
    entity_type: type[TModel], additional_builders: _BuilderCollection
) -> type[_Builder[TModel]]:
    if not is_dataclass(entity_type):
        raise TypeError("Not a dataclass type")

    entity_name: str = entity_type.__name__
    builder_name: str = f"{entity_name}Builder"
    if entity_name in __all_builders:
        return __all_builders[entity_name]

    update_ns: dict = {}

    def __init__(self) -> None:
        self.__args: _BuildArguments = _BuildArguments()  # type: ignore

    def build(self) -> TModel:
        my_builder_args: _BuildArguments = self.__args
        return cast(TModel, entity_type(**my_builder_args.get_build_items()))

    for field in fields(entity_type):
        function_name: str = f"with_{field.name}"

        target_func, arg_name, arg_type = _determine_fluent_function(
            field, additional_builders
        )

        arg: str = (
            f"{arg_name}: {arg_type.__qualname__ if isclass(arg_type) else str(arg_type)}"
        )
        if field.name == "requestedBy":
            arg = f"{arg_name}: tuple[str]"

        signature: str = f"{function_name}(self, {arg}) -> Self"

        target_func = partial(target_func, field_name=field.name)

        update_ns[function_name] = create_function(signature, target_func)

    update_ns[__init__.__name__] = create_function("__init__(self) -> None", __init__)
    update_ns[build.__name__] = create_function(
        f"build(self) -> {entity_type.__qualname__}", build
    )

    builder_class = new_class(
        builder_name, [_Builder[TModel]], None, lambda ns: ns.update(update_ns)
    )
    concrete_class = cast(type[_Builder[TModel]], builder_class)
    additional_builders[entity_name] = cast(type[_Builder], concrete_class)
    return concrete_class


def _make_builder(entity_type: type[TModel]) -> type[_Builder[TModel]]:
    global __all_builders
    return _create_builder(entity_type, __all_builders)


BuildAgentBuilder: TypeAlias = _make_builder(BuildAgent)  # type: ignore
AgentBuilder: TypeAlias = _make_builder(Agent)  # type: ignore
ArtifactBuilder: TypeAlias = _make_builder(Artifact)  # type: ignore
DependencyBuilder: TypeAlias = _make_builder(Dependency)  # type: ignore
ModuleBuilder: TypeAlias = _make_builder(Module)  # type: ignore
TrackerBuilder: TypeAlias = _make_builder(Tracker)  # type: ignore
AffectedIssueBuilder: TypeAlias = _make_builder(AffectedIssue)  # type: ignore
IssuesBuilder: TypeAlias = _make_builder(Issues)  # type: ignore
VCSBuilder: TypeAlias = _make_builder(VCS)  # type: ignore
_BuildInfoBuilder: TypeAlias = _make_builder(BuildInfo)  # type: ignore


class BuildInfoBuilder(_BuildInfoBuilder):
    def collect_env(self, **additional_properties: Any) -> Self:
        properties: dict[str, str] = additional_properties
        properties.update(environ)
        return self.with_properties(**properties)
