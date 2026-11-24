# WoW Forever Japanese → Anki

An [Anki](https://apps.ankiweb.net/) add-on that imports your saved words from the [WoW Forever Japanese](https://foreverjapanese.com) World of Warcraft addon directly into Anki as flashcards.

## How it works

1. **In WoW**: Save words to your word bank while playing (click/Ctrl-click/Shift-click on highlighted words)
2. **Log out or /reload**: WoW writes your word bank to `WoWForeverJapanese.lua` (SavedVariables)
3. **In Anki**: Go to **Tools → WoW Forever Japanese: Import Words** to create flashcards from your saved words

Each banked word creates one card (Recognition: JP → EN):
- **Front**: The Japanese word with furigana on top + the example sentence from the game
- **Back**: The front content + the English meaning/translation underneath

## Installation (Quick & Easy)

1. **Download the add-on**:
   - Download the `wow_forever_japanese_anki.zip` file (or click **Code → Download ZIP** on GitHub).
   - If downloaded as a ZIP from GitHub, unzip it and rename the folder inside to `wow_forever_japanese_anki`.

2. **Open the Anki Add-ons folder**:
   - Open Anki.
   - In the top menu bar, click **Tools → Add-ons** (or press `Ctrl+Shift+A` on Windows / `Cmd+Shift+A` on Mac).
   - In the window that appears, click the **View Files** button at the bottom right.
   - *(This will instantly open your Anki add-ons folder in File Explorer or Finder!)*

3. **Copy the folder into place**:
   - Drag or paste the `wow_forever_japanese_anki` folder directly into that folder.
   - It should look like this:
     ```
     addons21/
       wow_forever_japanese_anki/
         __init__.py
         main.py
         gui.py
         importer.py
         note_type.py
         lua_parser.py
         config.json
         manifest.json
     ```

4. **Restart Anki**:
   - Close Anki completely and reopen it.
   - You will now see **WoW Forever Japanese: Import Words** and **WoW Forever Japanese: Settings…** under your **Tools** menu!

## Configuration

Go to **Tools → WoW Forever Japanese: Settings…**

| Setting | Description |
|---|---|
| **SavedVariables path** | Path to your `WoWForeverJapanese.lua` in your account's WTF folder (required). |
| **Target Deck** | Dropdown list of your Anki decks to choose where cards will go. |
| **Auto-import on profile open** | Automatically import new words every time you open your Anki profile. |

### Finding your SavedVariables file

The file is typically at:
```
World of Warcraft/_classic_/WTF/Account/<ACCOUNT_NAME>/SavedVariables/WoWForeverJapanese.lua
```

> **Note**: WoW only writes SavedVariables when you log out or `/reload`. If you just saved words, do one of those before importing into Anki.

## Card fields

Each note contains these fields:

| Field | Description |
|---|---|
| Key | Unique identifier (`kind:id:word`) — used for duplicate detection |
| Reading | Target word with furigana HTML (`<ruby>用心<rt>ようじん</rt></ruby>`) |
| Sentence | Example sentence from the game with the word highlighted in bold |
| Back / Meaning | English translation / definition |
| Kanji / Word | The bare word without furigana |
| DictionaryForm | Dictionary / lemma form |
| Source | Where the word came from: quest, gossip, book, window |
| QuestTitle | Quest title in Japanese (if from a quest) |
| SavedDate | When the word was saved |

## License

MIT — see [LICENSE](LICENSE).
