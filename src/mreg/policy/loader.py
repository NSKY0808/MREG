from pathlib import Path
from typing import Any

import yaml


class UniqueSafeLoader(yaml.SafeLoader):
    """Safe YAML without aliases, duplicate keys, or merge-key ambiguity."""

    def compose_node(self, parent: Any, index: Any) -> Any:
        if self.check_event(yaml.AliasEvent):
            raise ValueError("YAML aliases are unsupported")
        return super().compose_node(parent, index)

    def construct_mapping(self, node: Any, deep: bool = False) -> dict[Any, Any]:
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ValueError("YAML mapping keys must be strings")
            if key in mapping:
                raise ValueError("duplicate YAML key")
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def read_policy(path: Path) -> Any:
    if path.stat().st_size > 1_000_000:
        raise ValueError("policy exceeds 1 MB limit")
    loader = UniqueSafeLoader(path.read_text(encoding="utf-8"))
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()
