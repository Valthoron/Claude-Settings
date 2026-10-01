---
name: microsoft-style
description: Write and review text a person reads, by the Microsoft Writing Style Guide and the Win32 error message guidelines. Use it whenever you write, change, or review such text, including in passing during a code change: log lines, error strings (errors.New, fmt.Errorf, raise, throw), flag and command help, UI and web page strings, and error, warning, and confirmation messages. Use it for Markdown documents too, such as READMEs and files under docs/, and for requests to proofread or polish text for tone, capitalization, punctuation, or wording. String literals that reach a person are in scope even inside source code. Don't use it for commit messages, pull request text, code comments, identifiers, or chat replies.
---

# Microsoft style for user-facing text

`references/` holds pages from the Microsoft Writing Style Guide and the Win32 error message guidelines. You already write clear, plain, friendly text. This file lists the specific conventions of the guide that you're likely to miss, and tells you which reference to open for each kind of task.

## Scope and precedence

These rules govern text that a person reads: UI, messages, and documentation. They don't govern commit messages, pull request text, code comments, identifiers, or chat replies.

When sources disagree, the higher one wins:

1. The user's explicit instructions, including their CLAUDE.md.
2. The repository's own style guide or established conventions, such as the wording and casing of strings the product already ships, or a language convention for error strings.
3. This skill.

When text refers to a UI label, quote the label as the UI shows it. The guide is written for Microsoft, so read "Microsoft" as whoever owns the product, and skip rules that only fit Microsoft's brand, such as the Segoe font or the Microsoft trademark list.

## Rewriting versus writing

Decide first which task you have. The two handle missing information differently.

**Rewriting existing text** (polishing, fixing, reviewing, or reformatting) changes how the text says things, never what it says. It adds no knowledge and removes none.

- Keep every piece of information the source gives, including details that look minor, such as an error code, a keyboard shortcut, a time limit, or a button label. Reword it, move it, or reformat it, but don't drop it.
- Add nothing the source doesn't state. That covers causes, examples, limits, product behavior, keyboard shortcuts, and advice like "try again" or "free up space", even when it's generic or almost certainly true.
- When the guide asks for something the source doesn't provide, such as a solution in an error message or the location of a setting, leave it out of the text and name the gap in your summary. It's the developer's job to supply it.

**Writing new text** from a developer's description means producing complete text that meets the guide.

- Make messages actionable. Tell the user what they can do, as far as the description supports it. For example, "Photo.tif can't be opened because it's larger than 2 GB. Open a smaller file." The action doesn't repeat the limit, because the first sentence already gives it.
- Don't invent product specifics the description doesn't give, such as features, causes, workarounds, or examples like "a copy exported at a lower resolution". If a good message needs one, name it in your summary.

**Both tasks**

- State each fact once. If a sentence already gives a limit, don't repeat it in the next one.
- Some rules depend on context the text doesn't show. For example, whether a label takes a colon depends on its layout. When you can't see that context, keep the original and name the open question in your summary.

## Order content by what the reader needs first

People scan the start of a page and act on the first steps they see.

- Put warnings, prerequisites, and risks before the steps they apply to, never after.
- State the full scope up front. If a feature supports several formats or cases, list them all at first mention, not only the first one.
- Order steps as the user performs them. Required steps come before optional ones.

## Conventions that are easy to miss

**Words**
- Write *checkbox* and *dialog*. Don't write *check box*, *dialog box*, or *pop-up window*.
- Use verbs that work with any input method: *select*, *enter*, *open*, *close*, *go to*, *clear* (a checkbox), and *turn on*/*turn off* (a toggle). Avoid *click*, *hit*, *press*, *check*, and *tap* unless the text is specific to one device (`procedures-instructions--describing-interactions-with-ui.md`).
- Use *in* for a box, dialog, pane, list, or window. Use *on* for a tab, menu, toolbar, ribbon, or page (`grammar--prepositions.md`).
- Don't write *please* in messages or *and/or* anywhere. Don't use a slash to mean *or*. Write *for example* and *that is*, not *e.g.* and *i.e.*
- Use *stop responding*, not *hang*. Use *primary/subordinate*, not *master/slave*. Don't use violent terms like *kill* (`bias-free-communication.md`, `militaristic-language.md`).
- Don't mix *can't* and *cannot* in the same UI. Avoid *it'll*, *there'd*, and noun-plus-verb contractions.

**Capitalization and punctuation**
- Use sentence-style capitalization for every heading, title, label, button, menu item, and table header.
- Start every sentence with a capital letter. If a sentence would start with a lowercase name or command, rewrite it (`capitalization.md`).
- Don't end headings, checkbox labels, or button labels with a period or colon. The guide also drops the colon from input labels, but a label placed beside its field may need one. Remove it only if you know the layout.
- Before a table, image, or code sample, end the introduction with a period, not a colon (`punctuation--colons.md`).
- Don't end list items with semicolons, commas, or *and*. Put a period on a list item only if it's a complete sentence or completes the introduction (`scannable-content--lists.md`).
- In instructions, drop a label's trailing colon or ellipsis. Write **Save as**, not **Save as...**
- Keep semicolons and exclamation points rare. Split the sentence instead.

**Numbers** (`numbers.md`)
- Spell out zero through nine in running text. Always use numerals in UI and for measurements, sizes, percentages, and values the user must type.
- Use a comma in numbers with four or more digits: *1,250*, *10,000*. For years, pixels, and baud, use a comma only from five digits: *4096 × 4096 pixels*.
- Write dimensions with a spaced multiplication sign (×) for screen resolutions, tiles, and paper. Put a space between a number and its unit: *2 GB*.
- Write ranges as *from 1 through 5*, or with an en dash and no *from*: *1–5*.
- Lowercase file name extensions: *.enex*, *.docx*.

**Headings** (`scannable-content--headings.md`)
- Use an imperative or infinitive phrase for a task heading, such as "Import notes". Use a noun phrase for other headings.

## Error, warning, and confirmation messages

Read `error-messages.md` in full before you write or review one.

- Say what happened and why, what it means for the user, and what the user can do. When you rewrite, use only what the source tells you, and name a missing cause or solution in your summary. When you write new text, include the action the description supports (see "Rewriting versus writing"). Write one message per known cause.
- Keep an error code the source gives, as a trailing supplement: "(Error code: 0x80070002)".
- If the source writes button labels into the message text, keep them there and fix only the pairing: "[OK] [Cancel]" under a question becomes "[Yes] [No]". If the dialog defines its buttons separately, note in your summary that the labels probably belong there.
- In a dialog title bar, show only the product, component, or wizard name. Don't summarize the problem there, and don't write "Error".
- When the body asks a yes-or-no question, such as "Save changes to Photo.jpg?", use *Yes* and *No*, plus *Cancel* if the user can back out. Don't swap in verb buttons like *Save* and *Don't save*. Use *Yes* and *No* only as a pair, and only after a question. Don't put *OK* under a question. Use *OK* when the message states a user action, *Cancel* to stop an operation, and *Close* to dismiss the message.
- Don't write *bad*. Say what's wrong, as far as the source tells you.
- Don't blame the user. Describe the condition, and use the passive voice if you need to: "The file can't be opened."
- When documentation quotes an error message, put the message in quotation marks.

## Procedures

- Use numbered steps. Make each step one complete, imperative sentence that ends with a period.
- Give each step one action in one place. When the user moves to a new screen, tab, or dialog, start a new step. Merging "go to Settings, open the tab, and select the button" into one step makes it easy to lose your place.
- Tell the reader where to act before you say what to do: "On the **Design** tab, select **Header row**."
- Bold UI labels in documentation. Write menu paths with spaced, unbolded `>` characters: "Select **File** > **Save as**."
- Include the step that finishes the procedure, such as selecting **OK**.

## Developer text

In documentation, format code elements by the table in `developer-content--formatting-developer-text-elements.md`. Commands, flags, parameters, types, paths, file names, and environment variables go in code style. User input is bold. Placeholders go in angle brackets inside code, or in italics in UI text.

## Reference map

| Task | Open |
| --- | --- |
| Errors, warnings, confirmations | `error-messages.md` |
| Step-by-step instructions | `procedures-instructions--*.md`, `checklists--procedures-and-instructions-checklist.md` |
| Formatting UI labels, names, and code in docs | `procedures-instructions--formatting-text-in-instructions.md`, `developer-content--formatting-developer-text-elements.md` |
| API reference or code samples | `developer-content--reference-documentation.md`, `developer-content--code-examples.md` |
| Headings, lists, tables, and long pages | `scannable-content*.md`, `responsive-content.md` |
| Numbers, dates, ranges, and units | `numbers.md` |
| Punctuation | `punctuation--<mark>.md`, `checklists--punctuation-checklist.md` |
| Word choice, jargon, and acronyms | `word-choice--*.md`, `acronyms.md` |
| Inclusive language | `bias-free-communication.md`, `militaristic-language.md` |
| Links and web addresses | `urls-web-addresses.md` |

## Reviewing existing text

1. Check the repository for its own style guide and for the conventions its existing strings follow. Those take precedence.
2. Open the `checklists--*.md` files that match the text, plus the references the text calls for.
3. Report only real deviations. For each one, quote the original, give the fix, and name the reference file. Group the findings by kind. Don't flag text that already complies.
4. When the user asks for a rewrite, return the corrected text itself, not only the findings.
