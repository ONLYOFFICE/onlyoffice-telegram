# ONLYOFFICE bot for Telegram

ONLYOFFICE bot for Telegram allows working with office files directly within [Telegram](https://web.telegram.org).

## Getting started

To start the bot, follow the given link and click the **Start** button. Then, enter the **/start** command.

## Creating files

Using the bot, you can create new files in docx, xlsx, and pptx formats.

1. Click the **Create** button in the menu.
2. Select the desired file format (Document, Spreadsheet, Presentation).
3. Enter the file name.

Once done, a message from the bot will come with the link to the created file. By clicking on this link, the corresponding ONLYOFFICE editor will open. For mobile devices and desktops, the mobile version of ONLYOFFICE Docs is used.

After the editing session is over, the bot will send the file with all the changes made.

## Collaborating on files

To co-edit the created file, forward the message with the link to other Telegram users.

The link is valid for 24 hours. If someone clicks on it within 24 hours, the counter is reset and is valid for another 24 hours. When opening an expired link, an error is displayed.

After everyone who followed the link has closed the editor, the file will be immediately sent to all the participants (in case the changes were made).

## Opening local files

You can send files from your device to the bot to open them via ONLYOFFICE.

There are 2 ways:

* To send a file to the chat without selecting any command.
* To select options via the bot menu: **/start** -> **Open** -> Upload a file from device.

In both cases, the bot will send a message with the link to open. If you send several files in one message, the link will be generated for the first file in the message.

File formats available for editing:

* **WORD**: DOCM, DOCX, DOTM, DOTX
* **CELL**: XLSM, XLSX, XLTM, XLTX
* **SLIDE**: POTM, POTX, PPSM, PPSX, PPTM, PPTX
* **PDF**: PDF

File formats available for viewing:

* **WORD**: DOC, DOT, EPUB, FB2, FODT, HTM, HTML, MHT, MHTML, ODT, OTT, RTF, STW, SXW, TXT, WPS, WPT, XML
* **CELL**: CSV, ET, ETT, FODS, ODS, OTS, SXC, XLS, XLSB, XLT
* **SLIDE**: DPS, DPT, FODP, ODP, OTP, POT, PPS, PPT, SXI
* **PDF**: DJVU, DOCXF, OFORM, OXPS, XPS

File formats available for conveting:

* **WORD**: DOC, DOCM, DOCX, DOT, DOTM, DOTX, EPUB, FB2, FODT, HTM, HTML, MHT, MHTML, ODT, OTT, RTF, STW, SXW, TXT, WPS, WPT, XML
* **CELL**: CSV, ET, ETT, FODS, ODS, OTS, SXC, XLS, XLSB, XLSM, XLSX, XLT, XLTM, XLTX
* **SLIDE**: DPS, DPT, FODP, ODP, OTP, POT, POTM, POTX, PPS, PPSM, PPSX, PPT, PPTM, PPTX, SXI
* **PDF**: DJVU, DOCXF, OFORM, OXPS, PDF, XPS

## Converting files

1. **/start**
2. **Convert**
3. Send the file from the device to the bot.
4. Select the file format to which the sent file should be converted.

After these steps, the bot will send a message to the chat with the file converted to the selected format. A message with a link is not generated in this case.

## Changing bot language

By default, the bot uses the language of the Telegram user profile. If such a language is not available in the bot translations, English is used. The user can change the language themselves by entering the **/lang** command.

## Project info

Official website: [www.onlyoffice.com](https://www.onlyoffice.com/)

Code repository: [github.com/ONLYOFFICE/onlyoffice-telegram](https://github.com/ONLYOFFICE/onlyoffice-telegram)

## User feedback and support

In case of technical problems, the best way to get help is to submit your issues [here](https://github.com/ONLYOFFICE/onlyoffice-telegram/issues).
Alternatively, you can contact ONLYOFFICE team on [forum.onlyoffice.com](https://forum.onlyoffice.com/).
