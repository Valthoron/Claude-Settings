<!-- retrieved from https://learn.microsoft.com/en-us/style-guide/developer-content/formatting-developer-text-elements on Sep 30 2026 -->

# Formatting developer text elements - Microsoft Style Guide | Microsoft Learn

Consistent text formatting helps readers locate and interpret information. Follow these formatting conventions for text elements that are commonly used in content for developers.

In general, use code style for programmatic or code-related elements. The following table lists examples of common programming elements, and some exceptions to the code style convention. Consider localization needs for the text elements that you're formatting.

The capitalization of developer text elements varies depending on the programming language or operating environment. When you're documenting code, capitalization should follow what the code uses.

| **Element** | **Convention** | **Example** |
| --- | --- | --- |
| **AI prompts** | Quotation marks, if you're referencing prompts in text. If prompts appear in a list and the introductory text makes clear what those items are, special formatting isn't necessary. | "List all of my subscriptions." |
| **Attributes** | Code style. | `IfOutputPrecision` |
| **Classes (predefined or user-defined)** | Code style. | `ios``filebuf``BitArray``BlueTimerControl` |
| **Code samples, including keywords and variables within text and as separate paragraphs, and user-defined program elements within text** | Code style. | `#include <iostream.h>``void main ()` |
| **Command-line commands** | Code style. | `copy` |
| **Command-line options (also known as switches or flags)** | Code style. Capitalize the way the option must be typed. | `/a``/Aw` |
| **Constants** | Code style. | `INT_MAX``bDenyWrite``CS_DBLCLKS` |
| **Control classes** | Code style. All uppercase. | `EDIT` control class |
| **Data formats** | Code style. All uppercase. | `CF_DIB` format |
| **Data structures and their members (predefined)** | Code style. | `BITMAP``bmBits``CREATESTRUCT``hInstance` |
| **Data types** | Code style. Capitalization follows the API. | `DWORD``float``HANDLE` |
| **Database names** | Bold. Code style if using in code syntax. | **Contoso** database`USE ContosoSalesDatabase;` |
| **Directives** | Code style. | `\#include``\#define` |
| **Environment variables** | Code style. | `INCLUDE``SESSIONNAME` |
| **Error messages** | Sentence-style capitalization. Enclose in quotation marks when you're referencing error messages in text. If error messages appear in a list and the introductory text makes clear what those items are, special formatting isn't necessary. | An error occurred during report processing. If you see the error message "Placeholder text in a content control contains items that aren't valid," remove floating objects, revision marks, or content controls from placeholder text, and try again. |
| **Event names** | Code style. | In the `OnClick` event procedure .... |
| **Fields (members of a class or structure)** | Code style. | `IfHeight``biPlanes` |
| **File attributes** | All lowercase. | The `attrib` command displays, sets, or removes the read-only, archive, system, and hidden attributes assigned to files or directories. |
| **File name extensions** | All lowercase. | .mdb.doc |
| **File names (user-defined examples)** | Apply code style if used in code. Use bold or plain text if referencing UI. | `MyTaxesFor2025` My Taxes for 2025 |
| **Folder and directory names (user-defined examples)** | Apply code style if used in code. Use bold or plain text if referencing UI. | `MyFiles\Accounting\Payroll\VacPay`Vacation and sick pay |
| **Functions (predefined)** | Code style. | `CompactDatabase``CWnd::CreateEx``FadePic` |
| **Handles** | Code style. All uppercase. | `HWND` |
| **Keywords (language and operating system)** | Code style. Capitalization follows the API. | `main``True``void` |
| **Logical operators** | Code style. | `AND``XOR` |
| **Macros** | Code style. | `LOWORD``MASKROP` |
| **Markup language elements (tags)** | Code style. | `<img>``<input type="text">``<!DOCTYPE html>` |
| **Mathematical constants and variables** | Italic. | *a2 + b2 = c2* |
| **Members** | Code style. | `ulNumCharsAllowed` |
| **Methods** | Code style. | `OpenForm()``GetPrevious()` |
| **New terms** | Italicize the first mention of a new term if you're going to define it immediately in text. | Microsoft Exchange consists of both *server* and *client* components. |
| **Operators** | Bold. Use code style for code-related operators. | **+, -**`sizeof` |
| **Parameters** | Code style. | `Hdc``grfFlagClientBinding` |
| **Placeholders (in syntax and in user input)** | Italic when placeholder element is UI text. Use angle brackets for code placeholders when angle brackets aren't part of the language syntax. | Enter *password*.`/v: <version>` |
| **Ports** | All uppercase. | LPT1 |
| **Products, services, apps, and trademarks** | Usually title-style capitalization. Check the Microsoft trademark list for capitalization of trademarked names. | Microsoft Arc Touch MouseMicrosoft WordSurface ProNotepadNetwork ConnectionsMakefileRC program |
| **Properties** | Code style. | `M_bClipped``AbsolutePosition``Message ID` |
| **Registers** | Code style. | `DS` |
| **Registry settings** | Subtrees (first-level items) all uppercase. Separated by underscores. Usually code style.Registry keys (second-level items) follow the capitalization of the UI.Registry subkeys (below the second level) follow the capitalization of the Regedit UI. | `HKEY_CLASSES_ROOT``HKEY_LOCAL_MACHINE``SOFTWARE``ApplicationIdentifier` |
| **Statements** | Code style. | `IMPORTS``LIBRARY` |
| **Structures** | Code style. | `ACCESSTIMEOUT` |
| **Switches** | Code style. Usually lowercase. | `build: commands` |
| **UI text or strings** | Treatment varies. Sentence-style capitalization. | Import from fileCreate a new resourceSee all your resourcesManually trigger a flowReport a bug |
| **URLs** | All lowercase for complete URLs. If necessary, line-break long URLs before a slash. Don't hyphenate. Use code style if referring to URLs in code. | www.microsoft.comwww.microsoft.com/download`const url = "https://www.microsoft.com"` |
| **User input** | Usually lowercase, unless case sensitive. Bold. Use italic only for placeholders. | Enter **hello world**Enter *password* |
| **Values** | Code style. All uppercase. | `DIB_PAL_COLORS` |
| **Variables** | Usually code style. | `bEmpty``m_nParams``file_name` |
| **XML schema elements** | Code style. Usually surrounded with angle brackets. | `<configuration>``ElementType` element |
