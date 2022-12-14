# -*- coding: bccelerator-transform-UTF-8 -*-
# library management

import bpy as _bpy
import types as _types
import typing as _typing

from .. import util as _util
from ..util import data as _util_data
from ..util import enums as _util_enums
from ..util import polyfill as _util_polyfill
from ..util import types as _util_types
from ..util import utils as _util_utils


class RemapUserToLibraryByName(_bpy.types.Operator):
    """Remap selected local data-block(s) to library data-block(s) by name"""

    __slots__: _typing.ClassVar = ()
    bl_idname: _typing.ClassVar[  # type: ignore
        str
    ] = "object.remap_user_to_library_by_name"
    bl_label: _typing.ClassVar[  # type: ignore
        str
    ] = "Remap User(s) to Library Data-Block(s) by Name"
    bl_options: _typing.ClassVar[  # type: ignore
        _typing.AbstractSet[_util_enums.OperatorTypeFlag]
    ] = frozenset(
        {_util_enums.OperatorTypeFlag.REGISTER, _util_enums.OperatorTypeFlag.UNDO}
    )

    @classmethod
    def poll(  # type: ignore
        cls: type[_util_polyfill.Self], context: _bpy.types.Context
    ) -> bool:
        return (
            context.space_data is not None
            and context.space_data.type == _util_enums.SpaceType.OUTLINER
            and any(id.library is None for id in context.selected_ids)
        )

    def execute(  # type: ignore
        self: _util_polyfill.Self, context: _bpy.types.Context
    ) -> _typing.AbstractSet[_util_enums.OperatorReturn]:
        processed: int = 0
        local_users: _typing.Mapping[
            tuple[type[_bpy.types.ID], str], _bpy.types.ID
        ] = _types.MappingProxyType(
            {
                (type(id), id.name): id
                for id in context.selected_ids
                if _typing.cast(_bpy.types.Library | None, id.library) is None
            }
        )
        lib_user: _bpy.types.ID
        local_user: _bpy.types.ID
        for lib_user, local_user in (
            (user, local_users[type(user), user.name])
            for lib in _util.intersection2(context.blend_data.libraries)[1]
            for user in _typing.cast(_typing.Collection[_bpy.types.ID], lib.users_id)
            if (type(user), user.name) in local_users
        ):
            local_user.user_remap(lib_user)
            processed += 1
            self.report(
                {_util_enums.WMReport.INFO},
                f'Remapped "{local_user.name_full}" to "{lib_user.name_full}"',
            )
        self.report({_util_enums.WMReport.INFO}, f"Remapped {processed} data-block(s)")
        return (
            {_util_enums.OperatorReturn.FINISHED}
            if processed > 0
            else {_util_enums.OperatorReturn.CANCELLED}
        )


class RemapUserToLocalByName(_bpy.types.Operator):
    """Remap selected library data-block(s) to local data-block(s) by name"""

    __slots__: _typing.ClassVar = ()
    bl_idname: _typing.ClassVar[  # type: ignore
        str
    ] = "object.remap_user_to_local_by_name"
    bl_label: _typing.ClassVar[  # type: ignore
        str
    ] = "Remap User(s) to Local Data-Block(s) by Name"
    bl_options: _typing.ClassVar[  # type: ignore
        _typing.AbstractSet[_util_enums.OperatorTypeFlag]
    ] = frozenset(
        {_util_enums.OperatorTypeFlag.REGISTER, _util_enums.OperatorTypeFlag.UNDO}
    )

    @classmethod
    def poll(  # type: ignore
        cls: type[_util_polyfill.Self], context: _bpy.types.Context
    ) -> bool:
        return (
            context.space_data is not None
            and context.space_data.type == _util_enums.SpaceType.OUTLINER
            and any(id.library is not None for id in context.selected_ids)
        )

    def execute(  # type: ignore
        self: _util_polyfill.Self, context: _bpy.types.Context
    ) -> _typing.AbstractSet[_util_enums.OperatorReturn]:
        processed: int = 0
        all_data: _typing.Mapping[
            type[_bpy.types.ID], _bpy.types.bpy_prop_collection[_bpy.types.ID]
        ] = _util_data.all(context)
        lib_user: _bpy.types.ID
        local_user: _bpy.types.ID
        for lib_user, local_user in (
            (id, all_data[type(id)][_typing.cast(_typing.Any, (id.name, None))])
            for id in context.selected_ids
            if id.library is not None
            and _typing.cast(_typing.Any, (id.name, None)) in all_data[type(id)]
        ):
            lib_user.user_remap(local_user)
            processed += 1
            self.report(
                {_util_enums.WMReport.INFO},
                f'Remapped "{lib_user.name_full}" to "{local_user.name_full}"',
            )
        self.report({_util_enums.WMReport.INFO}, f"Remapped {processed} data-block(s)")
        return (
            {_util_enums.OperatorReturn.FINISHED}
            if processed > 0
            else {_util_enums.OperatorReturn.CANCELLED}
        )


class LocalizeLibrary(_bpy.types.Operator):
    """Make all data-blocks of selected library(s) local"""

    __slots__: _typing.ClassVar = ()
    bl_idname: _typing.ClassVar[str] = "outliner.localize_library"  # type: ignore
    bl_label: _typing.ClassVar[str] = "Localize Library"  # type: ignore
    bl_options: _typing.ClassVar[  # type: ignore
        _typing.AbstractSet[_util_enums.OperatorTypeFlag]
    ] = frozenset(
        {_util_enums.OperatorTypeFlag.REGISTER, _util_enums.OperatorTypeFlag.UNDO}
    )

    @classmethod
    def poll(  # type: ignore
        cls: type[_util_polyfill.Self], context: _bpy.types.Context
    ) -> bool:
        return (
            context.space_data is not None
            and context.space_data.type == _util_enums.SpaceType.OUTLINER
            and any(isinstance(id, _bpy.types.Library) for id in context.selected_ids)
        )

    def execute(  # type: ignore
        self: _util_polyfill.Self, context: _bpy.types.Context
    ) -> _typing.AbstractSet[_util_enums.OperatorReturn]:
        users: _typing.Collection[_bpy.types.ID] = tuple(
            user
            for lib in context.selected_ids
            if isinstance(lib, _bpy.types.Library)
            for user in _typing.cast(_typing.Collection[_bpy.types.ID], lib.users_id)
        )
        to_be_processed: int = len(users)
        while users:
            retry_users: _typing.MutableSequence[_bpy.types.ID] = []
            user: _bpy.types.ID
            for user in (user.make_local() for user in users):
                if user.library is None:
                    self.report(
                        {_util_enums.WMReport.INFO}, f'Made "{user.name_full}" local'
                    )
                else:
                    retry_users.append(user)
            if len(retry_users) == len(users):
                for user in users:
                    self.report(
                        {_util_enums.WMReport.WARNING},
                        f'Cannot make "{user.name_full}" local',
                    )
                self.report(
                    {_util_enums.WMReport.WARNING},
                    f'Cannot make "{len(users)}" data-block(s) local',
                )
                break
            users = retry_users
        processed = to_be_processed - len(users)
        self.report(
            {_util_enums.WMReport.INFO}, f"Made {processed} data-block(s) local"
        )
        return (
            {_util_enums.OperatorReturn.FINISHED}
            if processed > 0
            else {_util_enums.OperatorReturn.CANCELLED}
        )


class CleanUpLibraryWeakReference(_bpy.types.Operator):
    """Clean up unused weak reference(s) to external library(s)"""

    __slots__: _typing.ClassVar = ()
    bl_idname: _typing.ClassVar[  # type: ignore
        str
    ] = "wm.clean_up_library_weak_reference"
    bl_label: _typing.ClassVar[str] = "Clean Up Library Weak References"  # type: ignore
    bl_options: _typing.ClassVar[  # type: ignore
        _typing.AbstractSet[_util_enums.OperatorTypeFlag]
    ] = frozenset(
        {_util_enums.OperatorTypeFlag.REGISTER, _util_enums.OperatorTypeFlag.UNDO}
    )

    def execute(  # type: ignore
        self: _util_polyfill.Self, context: _bpy.types.Context
    ) -> _typing.AbstractSet[_util_enums.OperatorReturn]:
        data: _typing.Collection[_bpy.types.ID] = tuple(
            datum
            for data in _util_data.all(context).values()
            for datum in data
            if datum.library_weak_reference is not None
            and _typing.cast(_bpy.types.Library | None, datum.library) is None
        )
        datum: _bpy.types.ID
        for datum in data:
            new_datum: _bpy.types.ID = datum.copy()
            asset_data: _bpy.types.AssetMetaData | None = datum.asset_data
            if asset_data is not None:
                new_datum.asset_mark()
                new_asset_data: _bpy.types.AssetMetaData = new_datum.asset_data
                attr: str
                for attr in (
                    "active_tag",
                    "author",
                    "catalog_id",
                    "description",
                ):
                    setattr(new_asset_data, attr, getattr(asset_data, attr))
                tag: _bpy.types.AssetTag
                for tag in asset_data.tags:
                    _util.intersection2(new_asset_data.tags)[0].new(tag.name)
            datum.user_remap(new_datum)
            datum.asset_clear()
            new_datum.name = datum.name
            self.report(
                {_util_enums.WMReport.INFO},
                f'Removed library weak reference of "{datum.name}": "{datum.library_weak_reference.filepath}"',
            )
        processed: int = len(data)
        self.report(
            {_util_enums.WMReport.INFO},
            f"Removed {processed} library weak reference(s)",
        )
        return (
            {_util_enums.OperatorReturn.FINISHED}
            if processed > 0
            else {_util_enums.OperatorReturn.CANCELLED}
        )


@_util_types.draw_func_class
@_util_types.internal_operator(uuid="2947869a-43a8-4f91-bb19-20ffca18edce")
class DrawFunc(_bpy.types.Operator):
    __slots__: _typing.ClassVar = ()

    @classmethod
    def OUTLINER_MT_context_menu_draw_func(
        cls: type[_util_polyfill.Self], self: _typing.Any, context: _bpy.types.Context
    ) -> None:
        layout: _bpy.types.UILayout = self.layout
        lambdas: _typing.MutableSequence[_typing.Callable[[], _typing.Any | None]] = []
        if RemapUserToLibraryByName.poll(context):
            lambdas.append(lambda: layout.operator(RemapUserToLibraryByName.bl_idname))
        if RemapUserToLocalByName.poll(context):
            lambdas.append(lambda: layout.operator(RemapUserToLocalByName.bl_idname))
        if LocalizeLibrary.poll(context):
            lambdas.append(lambda: layout.operator(LocalizeLibrary.bl_idname))
        if lambdas:
            layout.separator()
            lamb: _typing.Callable[[], _typing.Any | None]
            for lamb in lambdas:
                lamb()

    @classmethod
    def TOPBAR_MT_file_cleanup_draw_func(
        cls: type[_util_polyfill.Self], self: _typing.Any, context: _bpy.types.Context
    ) -> None:
        layout: _bpy.types.UILayout = self.layout
        layout.separator()
        layout.operator(
            CleanUpLibraryWeakReference.bl_idname, text="Library Weak References"
        )

    @classmethod
    def OUTLINER_MT_collection_draw_func(
        cls: type[_util_polyfill.Self], self: _typing.Any, context: _bpy.types.Context
    ) -> None:
        cls.OUTLINER_MT_context_menu_draw_func(self, context)

    @classmethod
    def OUTLINER_MT_object_draw_func(
        cls: type[_util_polyfill.Self], self: _typing.Any, context: _bpy.types.Context
    ) -> None:
        cls.OUTLINER_MT_context_menu_draw_func(self, context)


register: _typing.Callable[[], None]
unregister: _typing.Callable[[], None]
register, unregister = _util_utils.register_classes_factory(
    (
        RemapUserToLibraryByName,
        RemapUserToLocalByName,
        LocalizeLibrary,
        CleanUpLibraryWeakReference,
        DrawFunc,
    )
)
