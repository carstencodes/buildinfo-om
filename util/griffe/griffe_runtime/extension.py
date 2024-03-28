import ast
import collections.abc

import inspect
from typing import Optional, Self, Union

from griffe import Extension, Class, Function, Docstring, Object, ObjectNode

from importlib import import_module

from griffe.dataclasses import Parameters, Parameter
from griffe.enumerations import ParameterKind


def _make_member(name: str, m: collections.abc.Callable, parent: Class) -> Object:
    docstring = Docstring(m.__doc__ or "")
    sig: inspect.Signature = inspect.signature(m)

    return_type: Optional[str] = None
    if sig.return_annotation is not None:
        return_type = sig.return_annotation.__name__
        if sig.return_annotation == Self:
            return_type = parent.name

    args = Parameters()
    for arg_name, signature in inspect.signature(m).parameters.items():
        kind: ParameterKind = ParameterKind.positional_or_keyword
        if signature.kind == inspect.Parameter.POSITIONAL_ONLY:
            kind = ParameterKind.positional_only
        elif signature.kind == inspect.Parameter.KEYWORD_ONLY:
            kind = ParameterKind.keyword_only
        elif signature.kind == inspect.Parameter.VAR_KEYWORD:
            kind = ParameterKind.var_keyword
        elif signature.kind == inspect.Parameter.VAR_POSITIONAL:
            kind = ParameterKind.var_positional

        default: Optional[str] = None
        if signature.default is not signature.empty:
            default = str(signature.default)

        annotation: Optional[str] = None
        if signature.annotation is not None:
            annotation = signature.annotation.__name__

        args.add(Parameter(arg_name,
                           annotation=annotation,
                           default=default,
                           kind=kind))

    f: Function = Function(
        name=name,
        docstring=docstring,
        parameters=args,
        returns=return_type,
    )

    return f


def _make_new_member(cls: Class, member: Function) -> Function:
    f: Function = Function(
        name=member.name,
        parameters=member.parameters,
        returns=member.returns,
        docstring=member.docstring,
        runtime=True,
        lines_collection=cls.lines_collection,
        modules_collection=cls.modules_collection,
        parent=cls,
        lineno=cls.lineno,
        endlineno=cls.endlineno,
    )

    return f


def _make_class(t: type) -> Class:
    c: Class = Class(name=t.__name__)
    c.docstring = Docstring(c.__doc__)

    for member_name in (m for m in dir(t) if not m.startswith("_")):
        member = getattr(t, member_name)
        if not isinstance(member, collections.abc.Callable):
            continue
        print(member_name)
        o: Object = _make_member(member_name, member, c)
        o.parent = c
        c.members[member_name] = o

    return c


class RuntimeDocstringsExtension(Extension):
    def __init__(self):
        self.__items: dict[str, Class] = {}
        module = import_module("buildinfo_om")
        self.__fill_items(module)

    def on_class_members(self, *, node: Union[ast.AST, ObjectNode], cls: Class) -> None:
        if cls.name.startswith("_"):
            return

        if cls.name in self.__items.keys():
            existing = self.__items[cls.name]
            cls.docstring = existing.docstring
            for key, member in existing.members.items():
                if not isinstance(member, Function):
                    continue
                cls[key] = _make_new_member(cls, member)

    def __fill_items(self, module) -> None:
        elements = [x for x in dir(module) if not x.startswith("__")]

        for key in elements:
            runtime_member = getattr(module, key)
            if not runtime_member.__name__.endswith('Builder'):
                continue

            self.__items[runtime_member.__name__] = _make_class(runtime_member)
