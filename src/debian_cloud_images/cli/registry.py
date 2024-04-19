# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import argparse
import dataclasses
from collections.abc import (
    Callable,
)
from typing import (
    Any,
    ClassVar,
    TypeVar,
)


@dataclasses.dataclass
class _ActionWrapper:
    args: tuple
    kw: dict


class CliCommand:
    argparser: argparse.ArgumentParser | None
    __argparser: ClassVar[argparse.ArgumentParser]

    def __init__(self, *, argparser: argparse.ArgumentParser | None = None) -> None:
        self.argparser = argparser

    def __call__(self) -> None:
        if self.argparser is not None:
            self.argparser.print_help()
        raise NotImplementedError

    def error(self, message: str) -> None:
        if self.argparser is not None:
            self.argparser.error(message)
        raise NotImplementedError


CliCommandT = TypeVar('CliCommandT', bound=type[CliCommand])


class CliRegistry:
    name: str
    parser: argparse.ArgumentParser
    subparsers: argparse._SubParsersAction
    arguments: list[_ActionWrapper]

    def __init__(
        self,
        parser: argparse.ArgumentParser,
        arguments: list[_ActionWrapper] = [],
    ) -> None:
        self.parser = parser
        self.arguments = arguments[:]

        parser.set_defaults(__cls=CliCommand, argparser=parser)
        self.subparsers = parser.add_subparsers()

    @staticmethod
    def prepare_argument(*args, **kw) -> _ActionWrapper:
        return _ActionWrapper(args, kw)

    def register(
        self,
        name: str,
        help: str,
        arguments: list[_ActionWrapper] = [],
        usage: str = '%(prog)s',
        epilog: str | None = None,
    ) -> Callable[[CliCommandT], CliCommandT]:
        parser = self.subparsers.add_parser(
            prog=f'{self.parser.prog}.{name}',
            name=name,
            help=help,
            usage=usage,
            epilog=epilog or self.parser.epilog,
            formatter_class=argparse.RawTextHelpFormatter,
        )

        for w in arguments + self.arguments:
            parser.add_argument(*w.args, **w.kw)

        def wrap(cls: CliCommandT) -> CliCommandT:
            parser.set_defaults(__cls=cls, argparser=parser)
            cls.__argparser = parser
            return cls

        return wrap

    def register_subparsers(
        self,
        name: str,
        help: str,
        arguments: list[_ActionWrapper] = [],
        usage: str = '%(prog)s',
        epilog: str | None = None,
    ) -> CliRegistry:
        # Workaround: add_parser uses the existence of the argument instead of it's value
        kw: dict[str, Any] = {}
        if help:
            kw['help'] = help
        parser = self.subparsers.add_parser(
            prog=f'{self.parser.prog}.{name}',
            name=name,
            usage=usage,
            epilog=epilog,
            formatter_class=argparse.RawTextHelpFormatter,
            **kw,
        )
        return self.__class__(parser, arguments + self.arguments)

    def main(self, cls: CliCommandT | None = None) -> None:
        parser = cls.__argparser if cls else self.parser
        args = parser.parse_args()
        kw = vars(args)
        realcls = kw.pop('__cls')
        realcls(**kw)()
