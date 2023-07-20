from __future__ import annotations

from typing import Callable

from mypy.nodes import ARG_POS, TypeInfo
from mypy.plugin import FunctionSigContext, MethodSigContext, Plugin
from mypy.types import CallableType, FunctionLike, Instance


def replace_transaction_atomic_sig_callback(ctx: FunctionSigContext) -> CallableType:
    signature = ctx.default_signature

    using_arg = signature.argument_by_name("using")
    if not using_arg:
        # No using arg in the signature, bail
        return signature

    # We care about context managers.
    ret_type = signature.ret_type
    if not isinstance(ret_type, Instance):
        return signature

    # Replace the type and remove the default value of using.
    str_type = ctx.api.named_generic_type("builtins.str", [])

    arg_types = signature.arg_types[1:]
    arg_kinds = signature.arg_kinds[1:]

    return signature.copy_modified(
        arg_kinds=[ARG_POS, *arg_kinds],
        arg_types=[str_type, *arg_types],
    )


def replace_get_connection_sig_callback(ctx: FunctionSigContext) -> CallableType:
    signature = ctx.default_signature
    using_arg = signature.argument_by_name("using")
    if not using_arg:
        ctx.api.fail("The using parameter is required", ctx.context)

    str_type = ctx.api.named_generic_type("builtins.str", [])

    return signature.copy_modified(arg_kinds=[ARG_POS], arg_types=[str_type])


def replace_trailing_using_sig_callback(ctx: FunctionSigContext) -> CallableType:
    signature = ctx.default_signature
    using_arg = signature.argument_by_name("using")
    if not using_arg:
        ctx.api.fail("The using parameter is required", ctx.context)

    # Update the parameter type to be required and str
    str_type = ctx.api.named_generic_type("builtins.str", [])
    arg_kinds = signature.arg_kinds[0:-1]
    arg_types = signature.arg_types[0:-1]

    return signature.copy_modified(
        arg_kinds=[*arg_kinds, ARG_POS], arg_types=[*arg_types, str_type]
    )


_FUNCTION_SIG_OVERRIDES: dict[str, Callable[[FunctionSigContext], FunctionLike]] = {
    "django.db.transaction.atomic": replace_transaction_atomic_sig_callback,
    "django.db.transaction.get_connection": replace_get_connection_sig_callback,
    "django.db.transaction.on_commit": replace_trailing_using_sig_callback,
    "django.db.transaction.set_rollback": replace_trailing_using_sig_callback,
}


def field_descriptor_no_overloads(ctx: MethodSigContext) -> FunctionLike:
    # ignore the class / non-model instance descriptor overloads
    signature = ctx.default_signature
    # replace `def __get__(self, inst: Model, owner: Any) -> _GT:`
    # with `def __get__(self, inst: Any, owner: Any) -> _GT:`
    if str(signature.arg_types[0]) == "django.db.models.base.Model":
        return signature.copy_modified(arg_types=[signature.arg_types[1]] * 2)
    else:
        return signature


class SentryMypyPlugin(Plugin):
    def get_function_signature_hook(
        self, fullname: str
    ) -> Callable[[FunctionSigContext], FunctionLike] | None:
        return _FUNCTION_SIG_OVERRIDES.get(fullname)

    def get_method_signature_hook(
        self, fullname: str
    ) -> Callable[[MethodSigContext], FunctionLike] | None:
        if fullname == "django.db.models.fields.Field":
            return field_descriptor_no_overloads

        clsname, _, methodname = fullname.rpartition(".")
        if methodname != "__get__":
            return None

        clsinfo = self.lookup_fully_qualified(clsname)
        if clsinfo is None or not isinstance(clsinfo.node, TypeInfo):
            return None

        fieldinfo = self.lookup_fully_qualified("django.db.models.fields.Field")
        if fieldinfo is None:
            return None

        if fieldinfo.node in clsinfo.node.mro:
            return field_descriptor_no_overloads
        else:
            return None


def plugin(version: str) -> type[SentryMypyPlugin]:
    return SentryMypyPlugin
