# Recidiviz - a data platform for criminal justice reform
# Copyright (C) 2021 Recidiviz, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# =============================================================================
"""Defines a collection of objects that can collectively be used to build an abstract
syntax tree that can be used to convert an ingest view row into a hydrated entity
tree.
"""

import abc
import json
import re
from enum import Enum
from typing import Callable, Dict, Generic, List, Optional, Type, TypeVar, Union

import attr
from more_itertools import one

from recidiviz.common.constants.enum_overrides import EnumOverrides
from recidiviz.common.constants.enum_parser import EnumParser
from recidiviz.common.constants.strict_enum_parser import StrictEnumParser
from recidiviz.persistence.entity.base_entity import Entity, EnumEntity
from recidiviz.persistence.entity.entity_deserialize import EntityFactory, EntityT
from recidiviz.utils.yaml_dict import YAMLDict

ManifestNodeT = TypeVar("ManifestNodeT")


@attr.s(kw_only=True)
class ManifestNode(Generic[ManifestNodeT]):
    """Abstract interface for all nodes in the manifest abstract syntax tree. Subclasses
    may be leaf nodes (e.g. represent flat fields) or subtree root nodes (e.g. represent
    entity relationships).
    """

    @abc.abstractmethod
    def build_from_row(self, row: Dict[str, str]) -> Optional[ManifestNodeT]:
        """Should be implemented by subclasses to return a recursively hydrated node
        in the entity tree, parsed out of the input row.
        """


@attr.s(kw_only=True)
class EntityTreeManifest(ManifestNode[EntityT]):
    """An abstract syntax tree describing how to convert an input ingest view row into
    all or part of the output entity tree.
    """

    # The class we will recursively hydrate from this entity manifest.
    entity_cls: Type[EntityT] = attr.ib()

    # The factory class for converting a collection of arguments into an instance of
    # the above class.
    entity_factory_cls: Type[EntityFactory[EntityT]] = attr.ib()

    # A collection of manifests for fields that should be recursively hydrated into
    # sub-trees. These may either be manifests for flat fields or relationship fields.
    field_manifests: Dict[str, ManifestNode] = attr.ib()

    # A map of arguments that should be applied to all parsed entities.
    common_args: Dict[str, Optional[Union[str, EnumParser]]] = attr.ib()

    # Optional predicate for filtering out hydrated entities. If returns True,
    # build_for_row() will return null instead of this entity (and any children
    # entities) will be excluded entirely from the result.
    #
    # Currently this is primarily used for enum entities. If the enum value is null or
    # ignored by the mappings, the entire enum entity will be filtered out.
    filter_predicate: Optional[Callable[[EntityT], bool]] = attr.ib(default=None)

    def build_from_row(self, row: Dict[str, str]) -> Optional[EntityT]:
        """Builds a recursively hydrated entity from the given input row."""
        args: Dict[str, Optional[Union[str, EnumParser]]] = self.common_args.copy()

        for field_name, field_manifest in self.field_manifests.items():
            field_value = field_manifest.build_from_row(row)
            if field_value:
                args[field_name] = field_value

        entity = self.entity_factory_cls.deserialize(**args)

        if not isinstance(entity, self.entity_cls):
            raise ValueError(f"Unexpected type for entity: [{type(entity)}]")

        if self.filter_predicate and self.filter_predicate(entity):
            return None

        return entity


@attr.s(kw_only=True)
class ExpandableListItemManifest:
    """A wrapper around an EntityTreeManifest that describes a list item that can be
    expanded into 0 to N entity trees, based on the value of the input column.
    """

    # Key that denotes that a list item should be treated as an expandable list item.
    FOREACH_ITERATOR_KEY = "$foreach"

    # Variable "column name" hydrated with a single list item value. Can only be used
    # within the context of a $foreach loop.
    FOREACH_LOOP_VALUE_NAME = "$iter"

    # Default delimiter used to split list column values.
    DEFAULT_LIST_VALUE_DELIMITER = ","

    # Name of the column that should be treated as a list of values to expand into list
    # items.
    mapped_column: str = attr.ib()

    child_entity_manifest: EntityTreeManifest = attr.ib()

    def expand(self, row: Dict[str, str]) -> List[Entity]:
        column_value = row[self.mapped_column]
        if not column_value:
            return []

        # TODO(#8908): For now, we always split list column values on the default
        #  delimiter. Revisit whether the parser language needs be changed to allow the
        #  delimiter to be configurable.
        values = column_value.split(self.DEFAULT_LIST_VALUE_DELIMITER)
        result = []
        if self.FOREACH_LOOP_VALUE_NAME in row:
            raise ValueError(
                f"Unexpected {self.FOREACH_LOOP_VALUE_NAME} key value in row: {row}. "
                f"Nested loops not supported."
            )
        for value in values:
            row[self.FOREACH_LOOP_VALUE_NAME] = value
            entity = self.child_entity_manifest.build_from_row(row)
            del row[self.FOREACH_LOOP_VALUE_NAME]
            if entity:
                result.append(entity)
        return result


@attr.s(kw_only=True)
class ListRelationshipFieldManifest(ManifestNode[List[Entity]]):
    """Manifest describing a relationship field that will be hydrated with a list of
    entities that have been recursively hydrated based on the provided child tree
    manifests.
    """

    child_manifests: List[
        Union[ExpandableListItemManifest, EntityTreeManifest]
    ] = attr.ib()

    def build_from_row(self, row: Dict[str, str]) -> List[Entity]:
        child_entities = []
        for child_manifest in self.child_manifests:
            if isinstance(child_manifest, ExpandableListItemManifest):
                child_entities.extend(child_manifest.expand(row))
            elif isinstance(child_manifest, EntityTreeManifest):
                child_entity = child_manifest.build_from_row(row)
                if child_entity:
                    child_entities.append(child_entity)
            else:
                raise ValueError(
                    f"Unexpected type for child manifest: {type(child_manifest)}"
                )
        return child_entities


@attr.s(kw_only=True)
class DirectMappingFieldManifest(ManifestNode[str]):
    """Manifest describing a flat field that will be hydrated with the value of a
    specific column.
    """

    mapped_column: str = attr.ib()

    def build_from_row(self, row: Dict[str, str]) -> str:
        return row[self.mapped_column]


@attr.s(kw_only=True)
class StringLiteralFieldManifest(ManifestNode[str]):
    """Manifest describing a flat field that will be hydrated with a string literal
    value for all input rows.
    """

    # String literals are denoted like $literal("MY_STR")
    STRING_LITERAL_VALUE_REGEX = re.compile(r"^\$literal\(\"(.+)\"\)$")

    literal_value: str = attr.ib()

    def build_from_row(self, row: Dict[str, str]) -> str:
        return self.literal_value


@attr.s(kw_only=True)
class EnumFieldManifest(ManifestNode[StrictEnumParser]):
    """Manifest describing a flat field that will be hydrated into a parsed enum value."""

    # Raw manifest key whose value describes where to look for the raw text value to
    # parse this enum from.
    RAW_TEXT_KEY = "$raw_text"

    # Raw manifest key whose value describes the direct string mappings for this enum
    # field.
    MAPPINGS_KEY = "$mappings"

    # Raw manifest key whose value describes the string raw text values that should
    # be ignored when parsing this enum field.
    IGNORES_KEY = "$ignore"

    enum_cls: Type[Enum] = attr.ib()
    enum_overrides: EnumOverrides = attr.ib()
    raw_text_field_manifest: ManifestNode[str] = attr.ib()

    def build_from_row(self, row: Dict[str, str]) -> StrictEnumParser:
        return StrictEnumParser(
            raw_text=self.raw_text_field_manifest.build_from_row(row),
            enum_cls=self.enum_cls,
            enum_overrides=self.enum_overrides,
        )

    @classmethod
    def raw_text_field_name(cls, enum_field_name: str) -> str:
        return f"{enum_field_name}{EnumEntity.RAW_TEXT_FIELD_SUFFIX}"

    @classmethod
    def from_raw_manifest(
        cls, *, enum_cls: Type[Enum], field_enum_mappings_manifest: YAMLDict
    ) -> "EnumFieldManifest":
        """Factory method for building an enum field manifest."""

        raw_text_field_manifest = build_manifest_from_raw(
            pop_raw_flat_field_manifest(
                EnumFieldManifest.RAW_TEXT_KEY, field_enum_mappings_manifest
            )
        )

        enum_overrides = cls._build_field_enum_overrides(
            enum_cls,
            ignores_list=field_enum_mappings_manifest.pop_list(
                EnumFieldManifest.IGNORES_KEY, str
            ),
            raw_mappings_manifest=field_enum_mappings_manifest.pop_dict(
                EnumFieldManifest.MAPPINGS_KEY
            ),
        )

        if len(field_enum_mappings_manifest):
            raise ValueError(
                f"Found unused keys in field enum mappings manifest: "
                f"{field_enum_mappings_manifest.keys()}"
            )
        return EnumFieldManifest(
            enum_cls=enum_cls,
            enum_overrides=enum_overrides,
            raw_text_field_manifest=raw_text_field_manifest,
        )

    @staticmethod
    def _build_field_enum_overrides(
        enum_cls: Type[Enum], ignores_list: List[str], raw_mappings_manifest: YAMLDict
    ) -> EnumOverrides:
        """Builds the enum mappings object that should be used to parse the enum value."""

        enum_overrides_builder = EnumOverrides.Builder()

        for enum_value_str in raw_mappings_manifest.keys():
            enum_cls_name, enum_name = enum_value_str.split(".")
            if enum_cls_name != enum_cls.__name__:
                raise ValueError(
                    f"Declared enum class in manifest [{enum_cls_name}] does "
                    f"not match expected enum class type [{enum_cls.__name__}]."
                )
            value_manifest_type = raw_mappings_manifest.peek_type(enum_value_str)
            if value_manifest_type is str:
                mappings_raw_text_list: List[str] = [
                    raw_mappings_manifest.pop(enum_value_str, str)
                ]
            elif value_manifest_type is list:
                mappings_raw_text_list = []
                for raw_text in raw_mappings_manifest.pop(enum_value_str, list):
                    if not isinstance(raw_text, str) or not raw_text:
                        raise ValueError(f"Unexpected value for raw_text: {raw_text}")
                    mappings_raw_text_list.append(raw_text)
            else:
                raise ValueError(
                    f"Unexpected mapping values manifest type: {value_manifest_type}"
                )
            for raw_text in mappings_raw_text_list:
                enum_overrides_builder.add(
                    raw_text, enum_cls[enum_name], normalize_label=False
                )

        for raw_text_value in ignores_list:
            enum_overrides_builder.ignore(
                raw_text_value, enum_cls, normalize_label=False
            )

        return enum_overrides_builder.build()


@attr.s(kw_only=True)
class SerializedJSONDictFieldManifest(ManifestNode[str]):
    """Manifest describing the value for a flat field that will be hydrated with
    serialized JSON, derived from the values in 1 or more columns.
    """

    # Function name used to identify raw manifests of this type.
    JSON_DICT_KEY = "$json_dict"

    # Maps JSON dict keys to values they should be hydrated wtih
    key_to_manifest_map: Dict[str, ManifestNode[str]] = attr.ib()

    def build_from_row(self, row: Dict[str, str]) -> str:
        result_dict = {
            key: manifest.build_from_row(row)
            for key, manifest in self.key_to_manifest_map.items()
        }
        return json.dumps(result_dict, sort_keys=True)


@attr.s(kw_only=True)
class ConcatenatedStringsManifest(ManifestNode[str]):
    """Manifest describing a value that is hydrated by concatenating 0-N values, with
    a separator.
    """

    # Function name used to identify raw manifests of this type.
    CONCATENATE_KEY = "$concat"

    # Optional function argument key for string separator.
    SEPARATOR_ARG_KEY = "$separator"

    # Function argument key for the list of raw manifests for values to concatenate.
    VALUES_ARG_KEY = "$values"

    # Separator that will be used by default when concatenating values, if one is not
    # specified.
    DEFAULT_SEPARATOR = "-"

    # List of manifest nodes that can be evaluated to get the list of values to
    # concatenate.
    value_manifests: List[ManifestNode[str]] = attr.ib()

    # The string separator that will be inserted between concatenated values.
    separator: str = attr.ib()

    def build_from_row(self, row: Dict[str, str]) -> Optional[str]:
        return self.separator.join(
            value_manifest.build_from_row(row) or str(None).upper()
            for value_manifest in self.value_manifests
        )

    @classmethod
    def from_raw_manifest(
        cls, *, raw_function_manifest: YAMLDict
    ) -> "ConcatenatedStringsManifest":
        concat_manifests: List[Union[str, YAMLDict]] = []
        for raw_manifest in raw_function_manifest.pop(cls.VALUES_ARG_KEY, list):
            if isinstance(raw_manifest, str):
                concat_manifests.append(raw_manifest)
            elif isinstance(raw_manifest, dict):
                concat_manifests.append(YAMLDict(raw_manifest))
            else:
                raise ValueError(
                    f"Unexpected raw manifest type in $concat list: [{type(raw_manifest)}]"
                )

        separator = raw_function_manifest.pop_optional(cls.SEPARATOR_ARG_KEY, str)
        return ConcatenatedStringsManifest(
            separator=(separator if separator is not None else cls.DEFAULT_SEPARATOR),
            value_manifests=[
                build_manifest_from_raw(raw_manifest)
                for raw_manifest in concat_manifests
            ],
        )


def _get_complex_flat_field_manifest(
    raw_field_manifest: YAMLDict,
) -> ManifestNode[str]:
    """Returns the manifest node for a flat field that should be hydrated with
    the result of some function.

    The input raw manifest must follow this structure:
    $<function_name>:
        <dict with function args>
    """
    function_name = one(raw_field_manifest.keys())
    function_arguments = raw_field_manifest.pop_dict(function_name)
    manifest: ManifestNode[str]
    if function_name == SerializedJSONDictFieldManifest.JSON_DICT_KEY:
        manifest = SerializedJSONDictFieldManifest(
            key_to_manifest_map={
                key: build_manifest_from_raw(
                    pop_raw_flat_field_manifest(key, function_arguments)
                )
                for key in function_arguments.keys()
            }
        )
    elif function_name == ConcatenatedStringsManifest.CONCATENATE_KEY:
        manifest = ConcatenatedStringsManifest.from_raw_manifest(
            raw_function_manifest=function_arguments,
        )
    else:
        # TODO(#9086): Add support for building a string physical address from parts
        raise ValueError(
            f"Unexpected format for function field manifest: [{raw_field_manifest}]"
        )

    if len(raw_field_manifest):
        raise ValueError(
            f"Found unused keys in field manifest: {raw_field_manifest.keys()}"
        )
    return manifest


def _get_simple_flat_field_manifest(raw_field_manifest: str) -> ManifestNode[str]:
    # If the value in the manifest for this field is a string, it is either
    #  a) A literal string value to hydrate the field with, or
    #  b) The name of a column whose value we should hydrate the field with
    match = re.match(
        StringLiteralFieldManifest.STRING_LITERAL_VALUE_REGEX,
        raw_field_manifest,
    )
    if match:
        return StringLiteralFieldManifest(literal_value=match.group(1))
    return DirectMappingFieldManifest(mapped_column=raw_field_manifest)


def pop_raw_flat_field_manifest(
    field_name: str, raw_parent_manifest: YAMLDict
) -> Union[str, YAMLDict]:
    raw_field_manifest_type = raw_parent_manifest.peek_type(field_name)
    if raw_field_manifest_type is dict:
        return raw_parent_manifest.pop_dict(field_name)
    if raw_field_manifest_type is str:
        return raw_parent_manifest.pop(field_name, str)
    raise ValueError(
        f"Unexpected field manifest type [{raw_field_manifest_type}] for "
        f"field [{field_name}]."
    )


def build_manifest_from_raw(
    raw_field_manifest: Union[str, YAMLDict]
) -> ManifestNode[str]:
    if isinstance(raw_field_manifest, str):
        return _get_simple_flat_field_manifest(raw_field_manifest)
    if isinstance(raw_field_manifest, YAMLDict):
        return _get_complex_flat_field_manifest(raw_field_manifest)
    raise ValueError(
        f"Unexpected flat field manifest type: [{type(raw_field_manifest)}]"
    )