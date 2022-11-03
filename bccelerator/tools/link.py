# using libraries

import bpy as _bpy
import itertools as _itertools
import types as _types
import typing as _typing

from .. import util as _util
from ..util import enums as _util_enums
from ..util import props as _util_props
from ..util import types as _util_types
from ..util import utils as _util_utils


class LinkModifierByName(_bpy.types.Operator):
    '''Link modifiers from active modifier to modifiers of selected object(s) by name'''
    bl_idname: _typing.ClassVar[str] = (  # type: ignore
        'object.link_modifier_by_name'
    )
    bl_label: _typing.ClassVar[str] = (  # type: ignore
        'Link Modifier By Name'
    )
    bl_options: _typing.ClassVar[_typing.AbstractSet[_util_enums.OperatorTypeFlag]] = (  # type: ignore
        frozenset({
            _util_enums.OperatorTypeFlag.REGISTER, _util_enums.OperatorTypeFlag.UNDO, })
    )
    exclude_attrs: _typing.ClassVar[_typing.AbstractSet[str]] = frozenset({
        '__doc__', '__module__', '__slots__',
        'bl_rna', 'rna_type',
        'is_active', 'is_override_data',
        'name', 'show_expanded', 'type',
    })

    @classmethod
    def poll(  # type: ignore
            cls: type[_typing.Self], context: _bpy.types.Context
    ) -> bool:
        active_object: _bpy.types.Object = context.active_object
        return (len(context.selected_objects) >= 2
                and active_object is not None
                and _util.intersection2(active_object.modifiers)[0].active is not None)

    def execute(  # type: ignore
        self: _typing.Self, context: _bpy.types.Context
    ) -> _typing.AbstractSet[_util_enums.OperatorReturn]:
        modifiers: int = 0
        drivers: int = 0

        from_object: _bpy.types.Object = context.active_object
        from_modifier: _bpy.types.Modifier = _util.intersection2(from_object.modifiers)[
            0].active
        modifier_name: str = from_modifier.name
        modifier_type: _util_enums.ObjectModifierType = _util_enums.ObjectModifierType(
            from_modifier.type)
        modifier_attrs: _typing.Collection[str] = tuple(filter(lambda attr: attr not in self.exclude_attrs,
                                                               dir(from_modifier)))
        for to_object in filter(
                lambda obj: obj != from_object and modifier_name in _util.intersection2(obj.modifiers)[
                    0],
                context.selected_objects
        ):
            to_modifier = to_object.modifiers[modifier_name]
            if to_modifier.type == modifier_type:
                to_drivers: int = 0
                for modifier_attr in modifier_attrs:
                    data_path: str = f'modifiers["{modifier_name}"].{modifier_attr}'
                    if _util_utils.has_driver(to_object, data_path):
                        continue
                    try:
                        curves: _bpy.types.FCurve | _typing.Collection[_bpy.types.FCurve] = to_object.driver_add(
                            data_path)
                    except TypeError:
                        continue
                    multiple: bool = isinstance(curves, _typing.Collection)
                    curves = _typing.cast(
                        _typing.Collection[_bpy.types.FCurve], curves) if multiple else (curves,)
                    index: int
                    curve: _bpy.types.FCurve
                    for index, curve in enumerate(curves):
                        _util_utils.configure_driver(curve.driver,
                                                     id_type=_util_enums.IDType.OBJECT, id=from_object,
                                                     data_path=f'{data_path}[{index}]' if multiple else data_path,
                                                     )
                        curve.lock = True
                    to_drivers += len(curves)
                modifiers += 1
                drivers += to_drivers
                self.report({str(_util_enums.WMReport.INFO)},
                            f'Linked modifier of "{to_object.name_full}" using {to_drivers} driver(s)')
        self.report({str(_util_enums.WMReport.INFO)},
                    f'Linked {modifiers} modifier(s) using {drivers} driver(s)')
        return {_util_enums.OperatorReturn.FINISHED} if drivers > 0 else {_util_enums.OperatorReturn.CANCELLED}


class ChangeLibraryOverrideEditable(_bpy.types.Operator):
    '''Change editability of selected library override(s)'''
    bl_idname: _typing.ClassVar[str] = (  # type: ignore
        'outliner.liboverride_editable_operation'
    )
    bl_label: _typing.ClassVar[str] = (  # type: ignore
        'Change Library Override(s) Editability'
    )
    bl_options: _typing.ClassVar[_typing.AbstractSet[_util_enums.OperatorTypeFlag]] = (  # type: ignore
        frozenset({
            _util_enums.OperatorTypeFlag.REGISTER, _util_enums.OperatorTypeFlag.UNDO, })
    )

    editable: _typing.ClassVar[_typing.Annotated[bool,
                                                 (_bpy.props.BoolProperty  # type: ignore
                                                  )(
                                                     name='Editable',
                                                     description='Editability',
                                                     default=False,
                                                     options={
                                                         _util_enums.PropertyFlagEnum.SKIP_SAVE},
                                                 )]]
    selection_set_items: _typing.ClassVar[_typing.Mapping[str, _util_props.EnumPropertyItem[str]]] = _types.MappingProxyType({
        'SELECTED': _util_props.EnumPropertyItem[str](
            'SELECTED',
            'Selected',
            'Apply the operation over selected data-block(s) only',
            number=0
        ),
        'CONTENT': _util_props.EnumPropertyItem[str](
            'CONTENT',
            'Content',
            'Apply the operation over content of the selected item(s) only (the data-block(s) in their sub-tree(s))',
            number=1
        ),
        'SELECTED_AND_CONTENT': _util_props.EnumPropertyItem[str](
            'SELECTED_AND_CONTENT',
            'Selected & Content',
            'Apply the operation over selected data-block(s) and all their dependency(s)',
            number=2
        ),
    })
    selection_set: _typing.ClassVar[_typing.Annotated[str,
                                                      (_bpy.props.EnumProperty  # type: ignore
                                                       )(
                                                          name='Selection Set',
                                                          items=selection_set_items.values(),  # type: ignore
                                                          description='Over which part of the tree item(s) to apply the operation',
                                                          default='SELECTED',
                                                          options={
                                                              _util_enums.PropertyFlagEnum.SKIP_SAVE}
                                                      )]]

    @classmethod
    def poll(  # type: ignore
            cls: type[_typing.Self], context: _bpy.types.Context
    ) -> bool:
        return (context.space_data.type == _util_enums.SpaceType.OUTLINER
                and any(id.override_library is not None for id in context.selected_ids))

    def execute(  # type: ignore
        self: _typing.Self, context: _bpy.types.Context
    ) -> _typing.AbstractSet[_util_enums.OperatorReturn]:
        processed: int = 0

        if self.selection_set == 'SELECTED':
            data: _typing.Iterable[_bpy.types.ID] = context.selected_ids
        elif self.selection_set == 'CONTENT':
            def lamb(id: _bpy.types.ID) -> _typing.Iterable[_bpy.types.ID]:
                return (_util.intersection2(id.objects)[1]
                        if isinstance(id, _bpy.types.Collection)
                        else (id,))
            data = _util.flatmap(lamb, context.selected_ids)
        elif self.selection_set == 'SELECTED_AND_CONTENT':
            def lamb(id: _bpy.types.ID) -> _typing.Iterable[_bpy.types.ID]:
                return (_itertools.chain((id,), _util.intersection2(id.objects)[1])
                        if isinstance(id, _bpy.types.Collection)
                        else (id,))
            data = _util.flatmap(lamb, context.selected_ids)
        else:
            self.report({str(_util_enums.WMReport.ERROR_INVALID_INPUT)},
                        f'Invalid selection set "{self.selection_set}"')
            return {_util_enums.OperatorReturn.CANCELLED}

        datum: _bpy.types.ID
        for datum in data:
            if datum.override_library is not None:
                datum.override_library.is_system_override = not self.editable
                processed += 1
                self.report({str(_util_enums.WMReport.INFO)},
                            f'Changed editability of library override "{datum.name_full}"')

        self.report({str(_util_enums.WMReport.INFO)},
                    f'Changed editability of {processed} data-block(s)')
        return {_util_enums.OperatorReturn.FINISHED} if processed > 0 else {_util_enums.OperatorReturn.CANCELLED}


class _LibraryOverrideEditableMenu(_bpy.types.Menu):
    __editable: _typing.ClassVar[bool]

    def __init_subclass__(cls: type[_typing.Self], editable: bool, **kwargs: _typing.Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.__editable = editable
        cls.bl_idname: _typing.ClassVar[str] = (  # type: ignore
            f'OUTLINER_MT_liboverride_editable_{"editable" if editable else "noneditable"}'
        )
        cls.bl_label: _typing.ClassVar[str] = (  # type: ignore
            'Editable' if editable else 'Non-Editable'
        )

    def draw(self: _typing.Self, context: _bpy.types.Context) -> None:
        for selection_set in ChangeLibraryOverrideEditable.selection_set_items.values():
            op = self.layout.operator(ChangeLibraryOverrideEditable.bl_idname,
                                      text=selection_set[1])
            setattr(op, 'editable', self.__editable)
            setattr(op, 'selection_set', selection_set[0])


@_util_types.draw_func_class
@_util_types.internal_operator(uuid='06211866-d898-46d8-b253-14e4cd41dd77')
class DrawFunc(_bpy.types.Operator):
    editable_menu: _typing.ClassVar[type[_LibraryOverrideEditableMenu]]
    noneditable_menu: _typing.ClassVar[type[_LibraryOverrideEditableMenu]]
    editable_menu, noneditable_menu = (
        type('', (_LibraryOverrideEditableMenu,), dict(), editable=editable)
        for editable in (True, False)
    )

    register: _typing.ClassVar[_typing.Callable[[], None]]
    unregister: _typing.ClassVar[_typing.Callable[[], None]]
    register, unregister = _util_utils.register_classes_factory((
        editable_menu,
        noneditable_menu
    ), class_method=True)

    @classmethod
    def VIEW3D_MT_make_links_draw_func(cls: type[_typing.Self], self: _typing.Any, context: _bpy.types.Context) -> None:
        layout: _bpy.types.UILayout = self.layout
        layout.separator()
        layout.operator(LinkModifierByName.bl_idname)

    @classmethod
    def OUTLINER_MT_liboverride_draw_func(cls: type[_typing.Self], self: _typing.Any, context: _bpy.types.Context) -> None:
        layout: _bpy.types.UILayout = self.layout
        layout.separator()
        layout.menu(cls.editable_menu.bl_idname)
        layout.menu(cls.noneditable_menu.bl_idname)


register: _typing.Callable[[], None]
unregister: _typing.Callable[[], None]
register, unregister = _util_utils.register_classes_factory((
    LinkModifierByName,
    ChangeLibraryOverrideEditable,
    DrawFunc,
))