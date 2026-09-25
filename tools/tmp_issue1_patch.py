from pathlib import Path

path = Path("LetterBoxedCubed.user.js")
source = path.read_text(encoding="utf-8")
start_marker = "    function WaitForGame() {\n"
end_marker = "    function LoadPuzzleData() {\n"
start = source.find(start_marker)
end = source.find(end_marker, start)

if start < 0 or end < 0 or end <= start:
    raise SystemExit("Could not locate WaitForGame block")

replacement = '''    function WaitForGame() {
        RecordBootstrapDiagnostic("wait-for-game-start");

        return new Promise((Resolve) => {
            const StartTime = Date.now();
            const LongWaitDiagnosticMs = 20000;
            const PollIntervalMs = 1000;
            let SawGameData = false;
            let SawWordContainer = false;
            let SawSquareContainer = false;
            let LoggedLongWait = false;
            let Observer = null;
            let Timer = null;

            const Cleanup = () => {
                if (Timer) {
                    clearInterval(Timer);
                    Timer = null;
                }

                Observer?.disconnect();
                Observer = null;

                window.removeEventListener("focus", CheckReadiness);
                window.removeEventListener("pageshow", CheckReadiness);
                document.removeEventListener(
                    "visibilitychange",
                    CheckReadiness
                );
            };

            const CheckReadiness = () => {
                const HasGameData = Boolean(
                    PageWindow.gameData &&
                    Array.isArray(PageWindow.gameData.dictionary)
                );
                const HasWordContainer = Boolean(document.querySelector(
                    ".lb-game-container .lb-word-container"
                ));
                const HasSquareContainer = Boolean(document.querySelector(
                    ".lb-game-container .lb-square-container"
                ));

                if (HasGameData && !SawGameData) {
                    SawGameData = true;
                    RecordBootstrapDiagnostic("game-data-seen");
                }
                if (HasWordContainer && !SawWordContainer) {
                    SawWordContainer = true;
                    RecordBootstrapDiagnostic("word-container-seen");
                }
                if (HasSquareContainer && !SawSquareContainer) {
                    SawSquareContainer = true;
                    RecordBootstrapDiagnostic("square-container-seen");
                }

                if (HasGameData && HasWordContainer && HasSquareContainer) {
                    Cleanup();
                    RecordBootstrapDiagnostic("wait-for-game-ready", {
                        ElapsedMs: Date.now() - StartTime
                    });
                    Resolve(true);
                    return;
                }

                if (
                    !LoggedLongWait &&
                    Date.now() - StartTime >= LongWaitDiagnosticMs
                ) {
                    LoggedLongWait = true;
                    RecordBootstrapDiagnostic("wait-for-game-still-waiting", {
                        HasGameData,
                        HasWordContainer,
                        HasSquareContainer
                    });

                    console.info(
                        "[Letter Boxed Cubed] Waiting for NYT to start Letter Boxed."
                    );
                }
            };

            /*
                NYT can legitimately leave Letter Boxed on its pre-game splash
                screen indefinitely. gameData may already exist while the word
                and square containers do not appear until Start Game is clicked.
                A fixed timeout therefore turns a valid NYT state into a fatal
                Cubed bootstrap failure. Watch DOM creation instead, while a
                low-frequency poll covers gameData changes that need not mutate
                the DOM. Focus/visibility/pageshow checks make restored tabs
                react immediately when Chrome wakes them.
            */
            Observer = new MutationObserver(CheckReadiness);
            Observer.observe(
                document.documentElement,
                {
                    childList: true,
                    subtree: true
                }
            );

            Timer = setInterval(
                CheckReadiness,
                PollIntervalMs
            );

            window.addEventListener("focus", CheckReadiness);
            window.addEventListener("pageshow", CheckReadiness);
            document.addEventListener(
                "visibilitychange",
                CheckReadiness
            );

            CheckReadiness();
        });
    }

'''

updated = source[:start] + replacement + source[end:]
path.write_text(updated, encoding="utf-8")
