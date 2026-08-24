// ==UserScript==
// @name         NYT Letter Boxed Cubed
// @namespace    https://www.nytimes.com/puzzles/letter-boxed
// @version      1.3.0
// @description  Tracks Letter Boxed words and puzzle statistics.
// @author       Nathan Burgdorff + Ari (ChatGPT)
// @match        https://www.nytimes.com/puzzles/letter-boxed*
// @grant        unsafeWindow
// @grant        GM_getValue
// @grant        GM_setValue
// @run-at       document-idle
// ==/UserScript==

/*
    HISTORICAL RECONSTRUCTION

    The original generated artifact for this pre-v1.6 release was not retained
    as a downloadable file. This snapshot was reconstructed from the chat
    requirements and preserves the feature progression, but is not guaranteed
    to be byte-for-byte identical to the original generated source.
*/

(function () {
    "use strict";

    const PageWindow = typeof unsafeWindow !== "undefined" ? unsafeWindow : window;
    const PanelId = "lbc-panel";
    const StyleId = "lbc-styles";

    let GameData = null;
    let Dictionary = [];
    let FoundWords = new Set();
    let StorageKey = null;

    async function Initialize() {
        AddStyles();
        if (!(await WaitForGame())) return;

        GameData = PageWindow.gameData;
        Dictionary = [...new Set(GameData.dictionary.map(NormalizeWord).filter(Boolean))].sort();
        StorageKey = "LetterBoxedTracker_" + String(GameData.id || GameData.printDate || "UnknownPuzzle");
        FoundWords = new Set(GM_getValue(StorageKey, []).map(NormalizeWord).filter(Boolean));
        CreatePanel();
        ScanGameState(true);

        const WordContainer = document.querySelector(".lb-word-container") || document.querySelector("#pz-game-root");
        new MutationObserver(() => ScanGameState()).observe(WordContainer, {
            childList: true,
            subtree: true,
            characterData: true
        });

        window.addEventListener("resize", PositionPanel);
    }

    function WaitForGame() {
        return new Promise(Resolve => {
            const Started = Date.now();
            const Timer = setInterval(() => {
                if (PageWindow.gameData?.dictionary && document.querySelector("#pz-game-root")) {
                    clearInterval(Timer);
                    Resolve(true);
                } else if (Date.now() - Started > 20000) {
                    clearInterval(Timer);
                    Resolve(false);
                }
            }, 250);
        });
    }

    function ScanGameState(Force = false) {
        const Chain = [...document.querySelectorAll("#pz-game-root .lb-word-list__word")]
            .map(Element => NormalizeWord(Element.textContent))
            .filter(Boolean);

        let Changed = false;
        for (const Word of Chain) {
            if (!FoundWords.has(Word)) {
                FoundWords.add(Word);
                Changed = true;
            }
        }

        if (Changed) GM_setValue(StorageKey, [...FoundWords].sort());
        if (Changed || Force) RenderPanel();
    }

    function NormalizeWord(Value) {
        return String(Value || "").replace(/\s+/g, "").trim().toUpperCase();
    }

    function CreatePanel() {
        if (document.getElementById(PanelId)) return;
        const Game = document.querySelector(".lb-game-container") || document.querySelector("#pz-game-root");
        const Panel = document.createElement("section");
        Panel.id = PanelId;
        Game.appendChild(Panel);
        PositionPanel();
    }

    function PositionPanel() {
        const Panel = document.getElementById(PanelId);
        const Game = document.querySelector(".lb-game-container");
        if (!Panel || !Game) return;
        Game.classList.add("lbc-side-layout");
        const Board = Game.querySelector(".lb-square-container");
        if (Board) {
            const GameRect = Game.getBoundingClientRect();
            const BoardRect = Board.getBoundingClientRect();
            Panel.style.left = `${Math.round(BoardRect.right - GameRect.left + 24)}px`;
            Panel.style.right = "auto";
        }
    }

    function RenderPanel() {
        const Panel = document.getElementById(PanelId);
        if (!Panel) return;

        const FoundList = Dictionary.filter(Word => FoundWords.has(Word)).sort();
        const UnfoundList = Dictionary.filter(Word => !FoundWords.has(Word)).sort();
        const Percent = Dictionary.length ? FoundList.length / Dictionary.length * 100 : 0;
        const PuzzleLetters = new Set((GameData.sides || []).join(""));
        const Covered = new Set(FoundList.join(""));
        const LongestLength = FoundList.length ? Math.max(...FoundList.map(Word => Word.length)) : 0;
        const Longest = FoundList.filter(Word => Word.length === LongestLength).join(", ");

        Panel.replaceChildren();

        const Header = document.createElement("div");
        Header.innerHTML = `<h2>Word Log</h2><small>${GameData.date || GameData.printDate || ""}</small>`;
        Panel.appendChild(Header);

        const StatGrid = document.createElement("div");
        StatGrid.className = "lbc-stats";

        AddStat(StatGrid, "Completion", `${FoundList.length} / ${Dictionary.length} (${Percent.toFixed(1)}%)`);
        AddStat(StatGrid, "Longest Found", Longest || "-");
        Panel.appendChild(StatGrid);

        const Length = document.createElement("details");
        Length.className = "lbc-tree";
        const LengthSummary = document.createElement("summary");
        LengthSummary.textContent = "Words by Length";
        Length.append(LengthSummary, MakeLengthBody(FoundList));
        Panel.appendChild(Length);

        const Columns = document.createElement("div");
        Columns.className = "lbc-word-columns";
        Columns.appendChild(MakeWordTree(`Found Words (${FoundList.length})`, FoundList, false, true));
        Columns.appendChild(MakeWordTree(`Unfound Words (${UnfoundList.length})`, UnfoundList, true, true));
        Panel.appendChild(Columns);
    }

    function AddStat(Container, Label, Value) {
        const Card = document.createElement("div");
        Card.className = "lbc-stat";
        Card.innerHTML = `<strong>${Value}</strong><small>${Label}</small>`;
        Container.appendChild(Card);
    }

    function MakeLengthBody(FoundList) {
        const Body = document.createElement("div");
        for (const Bucket of [3, 4, 5, 6, 7]) {
            const Total = Dictionary.filter(Word => Bucket === 7 ? Word.length >= 7 : Word.length === Bucket).length;
            const Found = FoundList.filter(Word => Bucket === 7 ? Word.length >= 7 : Word.length === Bucket).length;
            const Row = document.createElement("div");
            Row.textContent = `${Bucket === 7 ? "7+" : Bucket} letters: ${Found} / ${Total}`;
            Body.appendChild(Row);
        }
        return Body;
    }

    function MakeWordTree(Title, Words, Redacted, Open) {
        const Details = document.createElement("details");
        Details.className = "lbc-tree";
        Details.open = Open;
        const Summary = document.createElement("summary");
        Summary.textContent = Title;
        Details.appendChild(Summary);

        for (const Word of Words) {
            const Row = document.createElement("div");
            Row.className = Redacted ? "lbc-word redacted" : "lbc-word";
            Row.textContent = Word;
            Details.appendChild(Row);
        }

        return Details;
    }

    function AddStyles() {
        if (document.getElementById(StyleId)) return;
        const Style = document.createElement("style");
        Style.id = StyleId;
        Style.textContent = `
            #lbc-panel {
                box-sizing: border-box;
                padding: 14px;
                background: rgb(216, 132, 130);
                color: rgb(48, 24, 24);
                border: 1px solid rgba(76, 34, 34, .58);
                border-radius: 4px;
                font-family: Arial, sans-serif;
                overflow: auto;
            }
            .lbc-stats { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; }
            .lbc-stat { padding:8px; text-align:center; background:rgba(255,255,255,.18); border:1px solid rgba(78,34,34,.3); }
            .lbc-stat strong, .lbc-stat small { display:block; }
            .lbc-word { padding:4px 6px; margin:3px; background:rgba(255,255,255,.24); font-family:Consolas,monospace; }
            .redacted { background:#000 !important; color:#000 !important; user-select:none; }
            .lbc-hints { margin:8px; padding:8px; background:rgba(255,255,255,.12); }

            .lb-game-container.lbc-side-layout { position: relative !important; }
            #lbc-panel { position:absolute; right:18px; top:0; width:420px; max-height:560px; overflow:auto; }
            .lbc-word-columns { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
            .lbc-tree { border:1px solid rgba(70,30,30,.4); margin-top:8px; }
            .lbc-tree > summary { padding:8px; font-weight:700; cursor:pointer; }
        `;
        document.head.appendChild(Style);
    }

    Initialize();
})();
