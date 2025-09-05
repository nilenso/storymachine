import marimo

__generated_with = "0.15.2"
app = marimo.App(width="columns")

with app.setup(hide_code=True):
    import marimo as mo
    from dataclasses import dataclass, field
    from typing import List, Optional
    import uuid
    import random
    from markdown import markdown
    from fasthtml.common import Div, H3, P, Strong, Ul, Li, NotStr

    # Base cards
    CARD_STYLE = "border:1px solid #e0e0e0;border-radius:8px;margin:8px 0;padding:16px;"
    CARD_WITH_META = (
        CARD_STYLE  # remove extra top padding; we'll use a header row instead
    )
    HEADER_ROW_STYLE = "display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin:0 0 10px 0;"
    META_BOX_STYLE = (
        "display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:#6b6b6b;"
    )

    # Markdown box
    MD_BOX_STYLE = (
        "background:#f9f9f9;padding:14px;border-radius:6px;overflow:auto;"
        "font-size:14px;line-height:1.55;color:#1f2328;"
    )

    # Sticky-note + story styles
    STICKY_STYLE = (
        "background:#fff9a9;border:1px solid #e6d95c;border-radius:6px;"
        "padding:18px 18px 38px;width:340px;min-height:160px;"
        "box-shadow:0 10px 18px rgba(0,0,0,.15), inset 0 -10px 20px rgba(0,0,0,.06);"
        "margin:16px 12px;position:relative;"
    )
    TAPE_STYLE = (
        "position:absolute;top:-12px;left:50%;transform:translateX(-50%) rotate(2deg);"
        "width:120px;height:22px;background:linear-gradient(180deg,rgba(255,255,255,.85),rgba(255,255,255,.6));"
        "box-shadow:0 2px 6px rgba(0,0,0,.25);border-radius:3px;"
    )
    TITLE_STYLE = "margin:0 0 8px 0;font-size:18px;font-weight:700;color:#2b2b2b;"
    # bullets for acceptance criteria
    LIST_STYLE = (
        "margin:8px 0 0 18px;line-height:1.5;list-style:disc;padding-left:18px;"
    )
    LI_STYLE = "margin:2px 0;list-style:inherit;"
    META_CONTAINER_STYLE = (
        "position:absolute;bottom:8px;right:10px;text-align:right;line-height:1.1;"
    )
    META_LINE_STYLE = "margin:0;padding:0;font-size:11px;color:#6b6b6b;"

    # Markdown config
    MD_EXTS = ["extra", "sane_lists", "fenced_code", "codehilite"]
    MD_CFG = {
        "codehilite": {
            "noclasses": True,
            "guess_lang": False,
            "pygments_style": "default",
        }
    }


@app.cell(hide_code=True)
def _():
    mo.md(r"""# Eval Entity Previews""")
    return


@app.cell(hide_code=True)
def _():
    # Example
    example_project = Project(
        name="Example Project",
        description="An example project for StoryMachine evals.",
    )
    example_prd_doc = PRD(
        project_id=example_project.id,
        content="""# This is an example **PRD** content.
    Some text here.

    - Requirement 1
    - Requirement 2
    - Requirement 3
    """,
    )
    example_tech_doc = TechSpec(
        project_id=example_project.id,
        content="""# This is an example _technical specification_.
    This is some text.

    ```python
    def add(a, b):
        return a + b
    print(add(2, 3))
    ```
    """,
    )

    example_stories = [
        Story(
            project_id=example_project.id,
            title="Example Story",
            acceptance_criteria=[
                "Given some precondition, when some action is taken, then expect some outcome.",
                "Given another precondition, when another action is taken, then expect another outcome.",
                "Criteria 3",
            ],
        ),
        Story(
            project_id=example_project.id,
            title="Another Story",
            acceptance_criteria=["Criteria A", "Criteria B"],
        ),
        Story(
            project_id=example_project.id,
            title="Third Story",
            acceptance_criteria=[
                "Criteria X",
                "Criteria Y",
                "Criteria Z",
            ],
        ),
    ]

    mo.vstack(
        [
            example_project,
            example_prd_doc,
            example_tech_doc,
            mo.hstack(example_stories),
        ]
    )
    return example_prd_doc, example_project, example_stories, example_tech_doc


@app.cell(hide_code=True)
def _(example_prd_doc, example_project, example_stories, example_tech_doc):
    # Create example evaluation items using our existing example entities
    example_story_card_eval = StoryCardEvalItem(
        eval_criteria="Is this a good User Story?",
        project_id=example_project.id,
        prd=example_prd_doc,
        tech_spec=example_tech_doc,
        story=example_stories[0],
        notes="This is an example evaluation note for a story card",
        good_story=None,
    )

    example_story_set_eval = StorySetEvalItem(
        project_id=example_project.id,
        prd=example_prd_doc,
        tech_spec=example_tech_doc,
        story_set=example_stories,
        notes="This is an example evaluation note for a story set",
        good_story_set=None,
    )

    # Display them
    mo.vstack([example_story_card_eval, example_story_set_eval])
    return


@app.cell(column=1, hide_code=True)
def _():
    mo.md(r"""# Eval Entity Definitions""")
    return


@app.function
# helper for markdown rendering
def md_block(html: str, dom_id: str):
    # Scoped CSS so headings, lists, quotes, and code render predictably
    css = f"""
<style>
#{dom_id} h1, #{dom_id} h2, #{dom_id} h3, #{dom_id} h4, #{dom_id} h5, #{dom_id} h6 {{
  font-weight:700; margin:0.3em 0 0.4em;
}}
#{dom_id} ul {{ list-style: disc; margin:6px 0 6px 22px; padding-left:18px; }}
#{dom_id} ol {{ list-style: decimal; margin:6px 0 6px 22px; padding-left:18px; }}
#{dom_id} li {{ margin:2px 0; }}
#{dom_id} blockquote {{
  margin:8px 0; padding:8px 12px; border-left:4px solid #d0d7de; color:#57606a; background:#fafbfc;
}}
#{dom_id} pre {{ margin:6px 0; }}
#{dom_id} code {{ font-size:13px; }}
</style>
"""
    return Div(
        NotStr(css),
        Div(NotStr(html), id=dom_id, style=MD_BOX_STYLE),
    )


@app.class_definition
@dataclass
class Project:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""

    def _repr_html_(self):
        return str(
            Div(
                H3("Project: ", self.name),
                P(Strong("ID:"), f" {self.id}"),
                P(Strong("Description:"), f" {self.description}"),
                style=CARD_STYLE,
            )
        )


@app.class_definition
@dataclass
class PRD:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    content: str = ""

    def _repr_html_(self):
        html = markdown(
            self.content or "", extensions=MD_EXTS, extension_configs=MD_CFG
        )
        md_id = f"md-{self.id}"
        return str(
            Div(
                # header row: title left, meta right
                Div(
                    H3(
                        "Product Requirements Document",
                        style="margin:0;padding:0;",
                    ),
                    Div(
                        P(f"ID: {self.id}"),
                        P(f"Project ID: {self.project_id}"),
                        style=META_BOX_STYLE,
                    ),
                    style=HEADER_ROW_STYLE,
                ),
                md_block(html, md_id),
                style=CARD_WITH_META,
            )
        )


@app.class_definition
@dataclass
class TechSpec:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    content: str = ""

    def _repr_html_(self):
        html = markdown(
            self.content or "", extensions=MD_EXTS, extension_configs=MD_CFG
        )
        md_id = f"md-{self.id}"
        return str(
            Div(
                Div(
                    H3("Technical Specification", style="margin:0;padding:0;"),
                    Div(
                        P(f"ID: {self.id}"),
                        P(f"Project ID: {self.project_id}"),
                        style=META_BOX_STYLE,
                    ),
                    style=HEADER_ROW_STYLE,
                ),
                md_block(html, md_id),
                style=CARD_WITH_META,
            )
        )


@app.class_definition
@dataclass
class Story:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    title: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)

    def _repr_html_(self):
        rotation = random.uniform(-1.5, 1.5)
        return str(
            Div(
                Div(style=TAPE_STYLE),
                H3(self.title or "User Story", style=TITLE_STYLE),
                P(Strong("Acceptance Criteria:")),
                Ul(
                    *(Li(c, style=LI_STYLE) for c in self.acceptance_criteria),
                    style=LIST_STYLE,
                ),
                Div(
                    P(f"Project: {self.project_id}", style=META_LINE_STYLE),
                    P(f"Card: {self.id}", style=META_LINE_STYLE),
                    style=META_CONTAINER_STYLE,
                ),
                style=STICKY_STYLE + f"transform:rotate({rotation}deg);",
            )
        )


@app.class_definition
@dataclass
class StoryCardEvalItem:
    project_id: str
    prd: PRD
    tech_spec: TechSpec
    story: Story
    notes: str = ""
    good_story: Optional[bool] = None
    eval_criteria: str = ""

    def _repr_html_(self):
        project_html = (
            self.prd._repr_html_() if self.prd else "<div>PRD not available</div>"
        )
        tech_spec_html = (
            self.tech_spec._repr_html_()
            if self.tech_spec
            else "<div>Tech Spec not available</div>"
        )
        story_html = (
            self.story._repr_html_() if self.story else "<div>Story not available</div>"
        )

        # Build eval criteria section only if exists
        eval_criteria_html = (
            f"""
            <div style="margin-top: 20px; padding: 15px; background-color: #ebf8ff; border-left: 4px solid #4299e1;">
                <h3 style="margin: 0; color: #2c5282; font-size: 1em;">Evaluation Criteria:</h3>
                <p style="margin: 10px 0 0 0; font-size: 1.2em; font-weight: 500;">{self.eval_criteria}</p>
            </div>
            """
            if self.eval_criteria
            else ""
        )

        notes_html = (
            f"""
            <div style="margin-top: 20px; padding: 10px; background-color: #f7fafc;">
                <strong>Notes:</strong> {self.notes}
            </div>
            """
            if self.notes
            else ""
        )

        good_story_html = (
            f"""
            <div style="margin-top: 10px;">
                <strong>Good Story?</strong> {"Yes" if self.good_story else "No"}
            </div>
            """
            if self.good_story is not None
            else ""
        )

        return f"""
        <div style="border: 2px solid #2c5282; border-radius: 10px; padding: 20px; margin: 10px 0;">
            <h2 style="color: #2c5282; margin-top: 0;">Story Card Evaluation</h2>
            <div style="margin-bottom: 20px;">
                <strong>Project ID:</strong> {self.project_id}
            </div>
            <div style="display: flex; flex-direction: column; gap: 20px;">
                <details>
                    <summary style="cursor: pointer; font-weight: bold; padding: 10px; background-color: #e2e8f0; border-radius: 5px;">PRD Details</summary>
                    {project_html}
                </details>
                <details>
                    <summary style="cursor: pointer; font-weight: bold; padding: 10px; background-color: #e2e8f0; border-radius: 5px;">Tech Spec Details</summary>
                    {tech_spec_html}
                </details>
                {story_html}
            </div>
            {eval_criteria_html}
            {notes_html}
            {good_story_html}
        </div>
        """


@app.class_definition
@dataclass
class StorySetEvalItem:
    project_id: str
    prd: PRD
    tech_spec: TechSpec
    story_set: List[Story]
    notes: str = ""
    good_story_set: Optional[bool] = None
    eval_criteria: str = ""

    def _repr_html_(self):
        project_html = (
            self.prd._repr_html_() if self.prd else "<div>PRD not available</div>"
        )
        tech_spec_html = (
            self.tech_spec._repr_html_()
            if self.tech_spec
            else "<div>Tech Spec not available</div>"
        )

        stories_html = ""
        if self.story_set:
            stories_html = "".join([story._repr_html_() for story in self.story_set])
        else:
            stories_html = "<div>No stories available</div>"

        eval_criteria_html = (
            f"""
            <div style="margin-top: 20px; padding: 15px; background-color: #ebf8ff; border-left: 4px solid #4299e1;">
                <h3 style="margin: 0; color: #2c5282; font-size: 1em;">Evaluation Criteria:</h3>
                <p style="margin: 10px 0 0 0; font-size: 1.2em; font-weight: 500;">{self.eval_criteria}</p>
            </div>
            """
            if self.eval_criteria
            else ""
        )

        notes_html = (
            f"""
            <div style="margin-top: 20px; padding: 10px; background-color: #f7fafc;">
                <strong>Notes:</strong> {self.notes}
            </div>
            """
            if self.notes
            else ""
        )

        good_story_set_html = (
            f"""
            <div style="margin-top: 10px;">
                <strong>Good Story Set?</strong> {"Yes" if self.good_story_set else "No"}
            </div>
            """
            if self.good_story_set is not None
            else ""
        )

        return f"""
        <div style="border: 2px solid #38a169; border-radius: 10px; padding: 20px; margin: 10px 0;">
            <h2 style="color: #38a169; margin-top: 0;">Story Set Evaluation</h2>
            <div style="margin-bottom: 20px;">
                <strong>Project ID:</strong> {self.project_id}
                <div style="margin-top: 5px;"><strong>Story Count:</strong> {len(self.story_set)}</div>
            </div>
            <div style="display: flex; flex-direction: column; gap: 20px;">
                <details>
                    <summary style="cursor: pointer; font-weight: bold; padding: 10px; background-color: #e2e8f0; border-radius: 5px;">PRD Details</summary>
                    {project_html}
                </details>
                <details>
                    <summary style="cursor: pointer; font-weight: bold; padding: 10px; background-color: #e2e8f0; border-radius: 5px;">Tech Spec Details</summary>
                    {tech_spec_html}
                </details>
            </div>
            <div>
                <div style="display: flex; flex-wrap: wrap;">
                    {stories_html}
                </div>
            </div>
            {eval_criteria_html}
            {notes_html}
            {good_story_set_html}
        </div>
        """


if __name__ == "__main__":
    app.run()
