import asyncio

from django.db import transaction

from document.models import Document
from document import prosemirror
from prosemirror.transform import ReplaceStep
from prosemirror.model import Slice, Fragment
from document.consumers import WebsocketConsumer


class DhdDocumentContentUpdate:
    class DocumentOpenedInSession(Exception):
        pass

    ORCID_ID_UNKNOWN = "<ORCID: N/A>"

    def __init__(self):
        self.title = ""
        self.abstract = ""
        self.contribution_type = ""
        self.keywords = []
        self.topics = []
        self.contributors = []
        self.orcid_ids = []

    def set_title(self, title: str):
        self.title = title

    def set_abstract(self, abstract: str):
        self.abstract = abstract

    def set_contribution_type(self, contribution_type: str):
        self.contribution_type = contribution_type

    def set_keywords(self, keywords: list[str]):
        self.keywords = keywords

    def set_topics(self, topics: list[str]):
        self.topics = topics

    def add_contributor(self, firstname, lastname, email, institution, orcid):
        self.contributors.append({key: value for key, value in dict(
            firstname=firstname,
            lastname=lastname,
            email=email,
            institution=institution,
        ).items() if value})
        self.orcid_ids.append(orcid if orcid else self.ORCID_ID_UNKNOWN)

    @classmethod
    def _update_part(cls, parts: list, part_type: str, part_id: str=None, content=None):
        for part in parts:
            try:
                if (
                    content
                    and (part["type"] == part_type)
                    and (part_id is None or part["attrs"]["id"] == part_id)
                ):
                    part["content"] = content
                    break
            except (KeyError, AttributeError):
                pass

    def _find_part_position(self, node, part_type: str, part_id: str = None):
        if not hasattr(node, 'content') or not node.content:
            return None
        pos = 1  # Start after doc node
        for i, child in enumerate(node.content.content):
            child_data = prosemirror.to_mini_json(child)
            if (child_data.get("type") == part_type and
                (part_id is None or child_data.get("attrs", {}).get("id") == part_id)):
                return pos
            pos += child.node_size
        return None

    def _build_updates(self):
        ctype = [{"type": "tag", "attrs": {"tag": self.contribution_type}}]
        keywords = [{"type": "tag", "attrs": {"tag": i}} for i in sorted(self.keywords)]
        topics = [{"type": "tag", "attrs": {"tag": i}} for i in sorted(self.topics)]
        contributors = [{"type": "contributor", "attrs": i} for i in self.contributors]
        orcid_ids = [{"type": "tag", "attrs": {"tag": i}} for i in self.orcid_ids]
        title = []
        visible_title = []
        abstract = []

        if self.title:
            title = [{"type": "text", "text": self.title}]
            visible_title = [
                {"type": "heading1", "content": [{"type": "text", "text": self.title}]}
            ]
        if self.abstract:
            abstract = [
                {"type": "paragraph", "content": [
                    {"type": "text", "text": self.abstract}
                ]}
            ]
        return [
            ("richtext_part", "abstract", abstract),
            ("tags_part", "topics", topics),
            ("tags_part", "keywords", keywords),
            ("tags_part", "contributionTypes", ctype),
            ("tags_part", "orcidIds", orcid_ids),
            ("contributors_part", None, contributors),
            ("heading_part", "visibleTitle", visible_title),
            ("title", None, title),
        ]

    def _create_content_fragment(self, content_data):
        """Create a prosemirror Fragment from content data."""
        if not content_data:
            return Fragment.empty
        nodes = []
        for item in content_data:
            node = prosemirror.from_json(item)
            if node:
                nodes.append(node)

        return Fragment.from_(nodes) if nodes else Fragment.empty

    def _create_transform_steps(self, document_id, updates):
        """Create prosemirror transform steps for the content updates."""
        session = WebsocketConsumer.sessions[document_id]
        current_node = session["node"]
        steps = []
        for part_type, part_id, content in updates:
            pos = self._find_part_position(current_node, part_type, part_id)
            if pos is not None:
                content_fragment = self._create_content_fragment(content)
                part_size = 0
                for child in current_node.content.content:
                    child_data = prosemirror.to_mini_json(child)
                    if (child_data.get("type") == part_type and
                        (part_id is None or child_data.get("attrs", {}).get("id") == part_id)):
                        # Get the content size (exclude the wrapper node)
                        if hasattr(child, 'content') and child.content:
                            part_size = sum(c.node_size for c in child.content.content)
                        break

                if part_size > 0 or content_fragment.size > 0:
                    steps.append(
                        ReplaceStep(
                            from_=pos,
                            to=pos + part_size,
                            slice=Slice(content_fragment, 0, 0)
                        )
                    )
        # Sort in descending order of range, such that steps can be applied in order
        steps = sorted(steps, key=lambda s: s.to, reverse=True)
        for s1, s2 in zip(steps, steps[1:]):
            assert s1.to >= s2.from_  # the document template does not allow overlaps
        return [step.to_json() for step in steps]

    def ensure_no_active_session(self, document_id):
        if document_id in WebsocketConsumer.sessions:
            raise self.DocumentOpenedInSession

    def set_on(self, document=None, doc_id=None):
        updates = self._build_updates()
        try:
            self.set_in_database(document=document, doc_id=doc_id, updates=updates)
        except self.DocumentOpenedInSession:
            self.set_in_session(document=document, doc_id=doc_id, updates=updates)

    def set_in_database(self, *, document=None, doc_id=None, updates=None):
        if doc_id is None:
            doc_id = document.pk
        if updates is None:
            updates = self._build_updates()
        with transaction.atomic():
            if locked := Document.objects.select_for_update().filter(pk=doc_id).first():
                self.ensure_no_active_session(doc_id)
                parts = locked.content.get("content", list())
                for part_type, part_id, content in updates:
                    self._update_part(parts, part_type, part_id, content)
                locked.content["content"] = parts
                locked.save()
        if document:
            document.refresh_from_db(fields=('content',))

    def set_in_session(self, *, document=None, doc_id=None, updates=None):
        async def run():
            return await self.aset_in_session(
                document=document, doc_id=doc_id, updates=updates
            )
        asyncio.run(run())

    async def aset_in_session(self, *, document=None, doc_id=None, updates=None):
        if doc_id is None:
            doc_id = document.pk

        session = WebsocketConsumer.sessions[doc_id]

        # Create prosemirror transform steps
        if updates is None:
            updates = self._build_updates()
        steps = self._create_transform_steps(doc_id, updates)

        if not steps:
            return None

        # Apply the steps to the session node
        current_node = session["node"]
        updated_node = prosemirror.apply(steps, current_node)

        # Update other session state
        session["node"] = updated_node
        session["node_updates"] = True
        session["doc"].version += 1

        # Create the necessary diffs and broadcast to participants
        diff_message = {
            "type": "diff",
            "v": session["doc"].version - 1,  # Previous version
            "ds": steps,
            "rid": f"dhd_content_update_{doc_id}_{session['doc'].version}",
        }
        # The title needs some special handling
        if self.title:
            diff_message["ti"] = self.title
            session["doc"].title = self.title[-255:]
        session["doc"].diffs.append(diff_message)
        session["doc"].diffs = session["doc"].diffs[-WebsocketConsumer.history_length:]
        await WebsocketConsumer.send_updates(diff_message, doc_id)
        return None
