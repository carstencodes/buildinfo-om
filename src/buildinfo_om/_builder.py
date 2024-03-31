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

import collections
from abc import ABC, abstractmethod
from dataclasses import Field, asdict, fields, is_dataclass
from functools import partial
from inspect import isclass
from os import environ
from re import sub as _substitute
from types import UnionType, new_class
from typing import (
    Any,
    Callable,
    Generic,
    Mapping,
    Self,
    Sequence,
    TypeAlias,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)

from makefun import create_function  # type: ignore

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

TModel = TypeVar(  # pylint: disable=C0103
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


def _to_lower_snake_case(value: str) -> str:
    """

    Parameters
    ----------
    value: str

    Returns
    -------

    """
    return _substitute(r'(?<!^)(?=[A-Z])', '_', value).lower()


class _BuildArguments(dict[str, Any]):
    """ """

    def get_build_items(self) -> Mapping[str, Any]:
        """

        Returns
        -------

        """
        ro_copy: dict[str, Any] = {}
        ro_copy.update(self)
        return ro_copy


class _Builder(ABC, Generic[TModel]):  # pylint: disable=R0903
    """ """

    def __init__(self, existing_items: dict[str, Any] | None = None) -> None:
        """

        Parameters
        ----------
            existing_items : dict[str, Any], optional

        Returns
        -------

        """
        self._args: _BuildArguments = _BuildArguments(existing_items or {})

    @classmethod
    def from_instance(cls, instance: TModel) -> Self:
        """
        Creates a new instance of the builder class initializing it with data
        taken from an existing instance.

        Parameters
        ----------
        instance: TModel
            The existing instance.

        Returns
        -------
            The new instance

        """
        data: dict[str, Any] = asdict(instance)
        builder = cls(data)

        return builder

    @abstractmethod
    def build(self) -> TModel:
        """

        Returns
        -------

        """
        raise NotImplementedError()


_BuilderCollection = dict[str, type[_Builder[TModel]]]
__all_builders: _BuilderCollection = {}


_FluentFunctArgsType = Any | tuple[Any, ...] | Mapping[Any, Any]
_FluentFunctionType = Callable[[Any, str, _FluentFunctArgsType], Any]


def _make_non_optional_type(t: type) -> type:
    """

    Parameters
    ----------
    t

    Returns
    -------

    """

    if get_origin(t) in (Union, UnionType) and type(None) in get_args(t):
        types: tuple[type, ...] = get_args(t)
        if len(types) == 2:
            if types[0] is type(None):
                return types[1]
            return types[0]
        return cast(type, tuple(a for a in get_args(t) if a is not type(None)))

    return t


def _determine_fluent_function(
    field: Field, additional_builders: _BuilderCollection
) -> tuple[_FluentFunctionType, str, type]:
    """

    Parameters
    ----------
    field
    additional_builders

    Returns
    -------

    """

    def with_scalar(self, value: Any, *, field_name: str):
        my_args: _BuildArguments = self._args  # pylint: disable=W0212
        my_args[field_name] = value
        return self

    def with_builder(self, builder: _Builder, *, field_name: str):
        my_args: _BuildArguments = self._args  # pylint: disable=W0212
        my_args[field_name] = builder.build()
        return self

    def with_sequence(self, *values: Any, field_name: str):
        my_args: _BuildArguments = self._args  # pylint: disable=W0212
        seq: Sequence = list(values)
        my_args[field_name] = seq
        return self

    def with_mapping(self, field_name: str, **values: Any):
        my_args: _BuildArguments = self._args  # pylint: disable=W0212
        mapping: Mapping[str, Any] = values
        my_args[field_name] = mapping
        return self

    def with_builder_sequence(self, *builders: _Builder, field_name: str):
        my_args: _BuildArguments = self._args  # pylint: disable=W0212
        seq: Sequence = [b.build() for b in builders]
        my_args[field_name] = seq
        return self

    field_type: type = field.type
    field_type = _make_non_optional_type(field_type)

    if is_dataclass(field_type):
        arg_type = _make_builder(
            field_type,  # type: ignore
            additional_builders,
        )
        arg_name = "builder"
        return cast(_FluentFunctionType, with_builder), arg_name, arg_type
    if get_origin(field_type) is collections.abc.Mapping or (
        isclass(field_type) and issubclass(field_type, collections.abc.Mapping)
    ):
        args = get_args(field_type)
        return cast(_FluentFunctionType, with_mapping), "**values", args[-1]
    if get_origin(field_type) is collections.abc.Sequence or (
        isclass(field_type)
        and issubclass(field_type, collections.abc.Sequence)
        and field_type not in (str, bytes, bytearray)
    ):
        args = get_args(field_type)
        if len(args) == 1:
            field_type = args[0]
            if is_dataclass(field_type):
                arg_type = _make_builder(
                    field_type,  # type: ignore
                    additional_builders,
                )
                arg_name = "*builders"
                return (
                    cast(_FluentFunctionType, with_builder_sequence),
                    arg_name,
                    arg_type,
                )

            arg_name = "*values"
            return (
                cast(_FluentFunctionType, with_sequence),
                arg_name,
                field_type,
            )
        return (
            cast(_FluentFunctionType, with_sequence),
            "*values",
            Any,
        )  # type: ignore

    return cast(_FluentFunctionType, with_scalar), "value", field_type


def _make_builder(
    entity_type: type[TModel], additional_builders: _BuilderCollection
) -> type[_Builder[TModel]]:
    """

    Parameters
    ----------
    entity_type
    additional_builders

    Returns
    -------

    """
    if not is_dataclass(entity_type):
        raise TypeError("Not a dataclass type")

    entity_name: str = entity_type.__name__
    builder_name: str = f"{entity_name}Builder"
    if entity_name in additional_builders:
        return additional_builders[entity_name]

    update_ns: dict = {}

    def build(self) -> TModel:
        my_builder_args: _BuildArguments = self._args  # pylint: disable=W0212
        return cast(TModel, entity_type(**my_builder_args.get_build_items()))

    for field in fields(entity_type):
        function_name, target_func = _generate_field_setter_function(
            entity_name,
            field,
            additional_builders,
        )

        update_ns[function_name] = target_func

    update_ns[build.__name__] = create_function(
        f"build(self) -> {entity_type.__qualname__}", build
    )

    builder_class = new_class(
        builder_name, [_Builder[TModel]], None, lambda ns: ns.update(update_ns)
    )
    concrete_class = cast(type[_Builder[TModel]], builder_class)
    additional_builders[entity_name] = cast(type[_Builder], concrete_class)
    concrete_class.__doc__ = _gen_class_doc(builder_name, entity_name)
    return concrete_class


def _gen_class_doc(builder_name: str, entity_name: str) -> str:
    """

    Parameters
    ----------
    builder_name: str
    entity_name: str

    Returns
    -------
    str

    """
    return f"""
        The {builder_name} represents an implementation of the builder pattern
        for the {entity_name} dataclass.
    """


def _gen_method_doc(
    class_name: str, field: Field, arg_name: str, arg_type: type
) -> str:
    """

    Parameters
    ----------
    class_name: str
    field: Field
    arg_name: str
    arg_type: type

    Returns
    -------
    str

    """

    arg_type_name: str = (
        arg_type.__name__ if isclass(arg_type) else str(arg_type)
    )
    if arg_name.startswith("*"):
        arg_type_name = f"collections.abc.Sequence[{arg_type_name}]"
        if arg_name.startswith("**"):
            arg_type_name = f"collections.abc.Mapping[str, {arg_type_name}]"
        arg_name = arg_name.lstrip("*")

    doc_str = f"""
        Sets the value of the '{field.name}' attribute of the resulting
        {class_name} instance to the specified argument
        and returns the modified instance of the builder itself.

        In case the argument is an instance of the Builder base class or a
        sequence of this, the builder will be invoked to create a new instance
        of the new class before setting the attribute.

        Parameters
        ----------
            {arg_name}: {arg_type_name}
                The value of the property / attribute to set or
                the builder to create these values.

        Returns
        -------
            The modified instance of this builder.
    """
    return doc_str


def _generate_field_setter_function(
    class_name: str, field: Field, additional_builders: _BuilderCollection
) -> tuple[str, _FluentFunctionType]:
    """

    Parameters
    ----------
    class_name: str
    field: Field
    additional_builders: _BuilderCollection

    Returns
    -------

    """
    lower_snake_case_name: str = _to_lower_snake_case(field.name)
    function_name: str = f"with_{lower_snake_case_name}"
    target_func, arg_name, arg_type = _determine_fluent_function(
        field, additional_builders
    )
    arg_type_name = (
        arg_type.__name__ if isclass(arg_type) else str(arg_type)
    )
    arg: str = f"{arg_name}: {arg_type_name}"
    if field.name == "requestedBy":
        arg = f"{arg_name}: tuple[str]"
    signature: str = f"{function_name}(self, {arg}) -> Self"
    target_func = partial(target_func, field_name=field.name)
    doc = _gen_method_doc(class_name, field, arg_name, arg_type)
    target_func = create_function(signature, target_func, doc=doc)
    return function_name, target_func


_BuildAgentBuilder: TypeAlias = _make_builder(  # type: ignore
    BuildAgent, __all_builders
)


class BuildAgentBuilder(_BuildAgentBuilder):  # pylint: disable=R0903
    """ """
    pass  # pylint: disable=W0107


_AgentBuilder: TypeAlias = _make_builder(Agent, __all_builders)  # type: ignore


class AgentBuilder(_AgentBuilder):  # pylint: disable=R0903
    """ """
    pass  # pylint: disable=W0107


_ArtifactBuilder: TypeAlias = _make_builder(  # type: ignore
    Artifact, __all_builders
)


class ArtifactBuilder(_ArtifactBuilder):  # pylint: disable=R0903
    """ """
    def with_hash_composite_value(self, hash_value: str) -> Self:
        """

        Parameters
        ----------
        hash_value: str

        Returns
        -------
        Self

        """
        composite_parts: list[str] = hash_value.split(":", 2)
        return self.with_hash_value(composite_parts[0], composite_parts[1])

    def with_hash_value(self, algorithm: str, hash_value: str) -> Self:
        """

        Parameters
        ----------
        algorithm: str
        hash_value: str

        Returns
        -------
        Self

        """

        if algorithm not in ("md5", "sha1", "sha256"):
            return Self

        if algorithm == "sha256":
            return self.with_sha256(hash_value)
        elif algorithm == "sha1":
            return self.with_sha1(hash_value)
        else:
            return self.with_md5(hash_value)


_DependencyBuilder: TypeAlias = _make_builder(  # type: ignore
    Dependency, __all_builders
)


class DependencyBuilder(_DependencyBuilder):  # pylint: disable=R0903
    """ """
    """ """

    def with_hash_composite_value(self, hash_value: str) -> Self:
        """

        Parameters
        ----------
        hash_value: str

        Returns
        -------
        Self

        """
        composite_parts: list[str] = hash_value.split(":", 2)
        return self.with_hash_value(composite_parts[0], composite_parts[1])

    def with_hash_value(self, algorithm: str, hash_value: str) -> Self:
        """

        Parameters
        ----------
        algorithm: str
        hash_value: str

        Returns
        -------
        Self

        """

        if algorithm not in ("md5", "sha1", "sha256"):
            return Self

        if algorithm == "sha256":
            return self.with_sha256(hash_value)
        elif algorithm == "sha1":
            return self.with_sha1(hash_value)
        else:
            return self.with_md5(hash_value)


_ModuleBuilder: TypeAlias = _make_builder(  # type: ignore
    Module, __all_builders
)


class ModuleBuilder(_ModuleBuilder):  # pylint: disable=R0903
    """ """
    pass


_TrackerBuilder: TypeAlias = _make_builder(  # type: ignore
    Tracker, __all_builders
)


class TrackerBuilder(_TrackerBuilder):  # pylint: disable=R0903
    """ """
    pass  # pylint: disable=W0107


_AffectedIssueBuilder: TypeAlias = _make_builder(  # type: ignore
    AffectedIssue, __all_builders
)


class AffectedIssueBuilder(_AffectedIssueBuilder):  # pylint: disable=R0903
    """ """
    pass  # pylint: disable=W0107


_IssuesBuilder: TypeAlias = _make_builder(  # type: ignore
    Issues, __all_builders
)


class IssuesBuilder(_IssuesBuilder):  # pylint: disable=R0903
    """ """
    pass  # pylint: disable=W0107


_VCSBuilder: TypeAlias = _make_builder(VCS, __all_builders)  # type: ignore


class VCSBuilder(_VCSBuilder):  # pylint: disable=R0903
    """ """
    pass  # pylint: disable=W0107


_BuildInfoBuilder: TypeAlias = _make_builder(  # type: ignore
    BuildInfo, __all_builders
)


class BuildInfoBuilder(_BuildInfoBuilder):
    """ """

    def collect_env(self, **additional_properties: Any) -> Self:
        """

        Parameters
        ----------
        additional_properties: Mapping[str, Any]

        Returns
        -------
        Self

        """
        properties: dict[str, str] = additional_properties
        properties.update(environ)
        return self.with_properties(**properties)

    def collect_env_without_keys(
        self, *keys: str, **additional_properties: Any
    ) -> Self:
        """

        Parameters
        ----------
        keys: tuple[str, ...]
        additional_properties: Mapping[str, Any]

        Returns
        -------
        Self

        """
        properties: dict[str, str] = additional_properties
        properties.update(environ)
        properties = {k: v for k, v in properties.items() if k not in keys}
        return self.with_properties(**properties)


del __all_builders
