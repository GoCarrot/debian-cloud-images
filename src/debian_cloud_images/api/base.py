# SPDX-License-Identifier: GPL-2.0-or-later

from marshmallow import Schema, post_dump


class SchemaNonempty(Schema):
    @post_dump
    def remove_empty(self, data: dict, **kw) -> dict:
        return {i: j for i, j in data.items() if j not in (None, [], {})}
