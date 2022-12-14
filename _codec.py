# -*- coding: UTF-8 -*-
import bpy as _bpy
import codecs as _codecs
import io as _io
import itertools as _itertools
import json as _json
import re as _re
import token as _token
import tokenize as _tokenize
import typing as _typing

_T = _typing.TypeVar("_T")
_Self: _typing.TypeAlias = _typing.Annotated[_T, "Self"]


class BcceleratorTransform(_codecs.Codec):
    __slots__: _typing.ClassVar = ("__codec",)
    __SeralizedType: _typing.TypeAlias = _typing.Sequence[str]
    __format: str = "# bccelerator-transform: {}\n"
    __regex: _re.Pattern[str] = _re.compile(
        r"^# bccelerator-transform: (.+)$", flags=_re.MULTILINE
    )

    def __init__(self: _Self["BcceleratorTransform"], codec: _codecs.CodecInfo) -> None:
        super().__init__()
        self.__codec: _codecs.CodecInfo = codec

    def encode(
        self: _Self["BcceleratorTransform"], input: str, errors: str = "strict"
    ) -> tuple[bytes, int]:
        match: _re.Match[str] | None = self.__regex.search(input)
        if match:
            serialized: self.__SeralizedType = _json.loads(
                input[match.start(1) : match.end(1)]
            )
        else:
            serialized = ()

        def gen_tokens() -> _typing.Iterator[tuple[int, str]]:
            inserts: _typing.Iterator[str] = _itertools.chain(
                iter(serialized), _itertools.repeat("")
            )
            token: _tokenize.TokenInfo
            for token in _tokenize.generate_tokens(
                iter(input.splitlines(keepends=True)).__next__
            ):
                yield token[:2]
                if (
                    token.exact_type == _token.NAME
                    and token.string == _bpy.types.bpy_prop_collection.__name__
                ):
                    yield from map(
                        lambda token: token[:2],
                        _tokenize.generate_tokens(
                            iter(next(inserts).splitlines(keepends=True)).__next__
                        ),
                    )

        return self.__codec.encode(_tokenize.untokenize(gen_tokens()), errors=errors)

    def decode(
        self: _Self["BcceleratorTransform"], input: bytes, errors: str = "strict"
    ) -> tuple[str, int]:
        inter: str
        consumed: int
        inter, consumed = self.__codec.decode(input, errors=errors)

        def gen_tokens() -> _typing.Iterator[tuple[int, str]]:
            level: int | None = None
            deleted: _typing.MutableSequence[_io.StringIO] = []
            token: _tokenize.TokenInfo
            for token in _tokenize.generate_tokens(
                iter(inter.splitlines(keepends=True)).__next__
            ):
                if level is None:
                    if token.exact_type == _token.ENDMARKER:
                        yield (_token.NEWLINE, "\n")
                        seralized: self.__SeralizedType = tuple(
                            map(_io.StringIO.getvalue, deleted)
                        )
                        yield (
                            _token.COMMENT,
                            self.__format.format(
                                _json.dumps(seralized, ensure_ascii=True)
                            ),
                        )
                    yield token[:2]
                    if (
                        token.exact_type == _token.NAME
                        and token.string == _bpy.types.bpy_prop_collection.__name__
                    ):
                        level = 0
                        deleted.append(_io.StringIO())
                else:
                    if token.exact_type == _token.LSQB:
                        level += 1
                        deleted[-1].write(token.string)
                    elif token.exact_type == _token.RSQB:
                        level -= 1
                        deleted[-1].write(token.string)
                        if level == 0:
                            level = None
                    elif level == 0:
                        level = None
                        yield token[:2]
                    else:
                        deleted[-1].write(token.string)

        return (_tokenize.untokenize(gen_tokens()), consumed)


def lookup(name: str) -> _codecs.CodecInfo | None:
    codec0: _codecs.CodecInfo | None = None
    if name.startswith("bccelerator_transform"):
        encoding: str = name[len("bccelerator_transform") :]
        if not encoding.startswith("_"):
            encoding = "_UTF-8"
        try:
            codec0 = _codecs.lookup(encoding[1:])
        except LookupError:
            pass
    if codec0 is None:
        return None
    codec: _codecs.Codec = BcceleratorTransform(codec0)
    return _codecs.CodecInfo(encode=codec.encode, decode=codec.decode, name=name)
