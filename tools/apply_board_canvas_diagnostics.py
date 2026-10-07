from pathlib import Path

RUNTIME = Path("tools/preview_runtime.js")
TESTS = Path("tests/final-polish-tests.js")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)

runtime = RUNTIME.read_text(encoding="utf-8")

runtime = replace_once(
    runtime,
    '''    let PreviewTransientAnimationHandler = null;\n    let PreviewTransientTraceActive = false;\n''',
    '''    let PreviewTransientAnimationHandler = null;\n    let PreviewTransientTraceActive = false;\n\n    const PreviewBoardCanvasTrace = [];\n    let PreviewBoardCanvasTraceActive = false;\n    let PreviewBoardCanvasHookInstalled = false;\n    let PreviewNativeBoardFillText = null;\n    let PreviewNativeBoardStrokeText = null;\n''',
    "board trace state"
)

anchor = '''    function GetBoundedPreviewOuterHtml(Selector, MaximumLength = 6000) {\n'''
insert = r'''    function IsPreviewBoardCanvas(Canvas) {
        return Boolean(
            Canvas &&
            typeof Canvas.closest === "function" &&
            Canvas.closest(".lb-game-container .lb-square-container")
        );
    }

    function GetPreviewBoardCanvasSnapshot() {
        const Canvas = document.querySelector(
            ".lb-game-container .lb-square-container canvas"
        );
        const Square = Canvas?.closest(".lb-square-container");
        const Game = Canvas?.closest(".lb-game-container");
        const Matrix = document.getElementById("lb-cubed-board-theme-matrix");

        if (!Canvas) {
            return {
                CapturedAt: new Date().toISOString(),
                Found: false
            };
        }

        const CanvasStyle = getComputedStyle(Canvas);
        const SquareStyle = Square ? getComputedStyle(Square) : null;
        const GameStyle = Game ? getComputedStyle(Game) : null;
        const RootStyle = getComputedStyle(document.documentElement);
        const Result = {
            CapturedAt: new Date().toISOString(),
            Found: true,
            Width: Canvas.width,
            Height: Canvas.height,
            CssWidth: CanvasStyle.width,
            CssHeight: CanvasStyle.height,
            Filter: CanvasStyle.filter,
            MatrixValues: Matrix?.getAttribute("values") || null,
            ThemeVariables: {
                Background: RootStyle.getPropertyValue("--lb-cubed-lb-bg").trim(),
                Board: RootStyle.getPropertyValue("--lb-cubed-lb-board").trim(),
                Foreground: RootStyle.getPropertyValue("--lb-cubed-lb-fg").trim(),
                Active: RootStyle.getPropertyValue("--lb-cubed-lb-active").trim()
            },
            RendererInputs: {
                GameColor: GameStyle?.color || null,
                GameTextVariable: GameStyle?.getPropertyValue("--text")?.trim() || null,
                SquareColor: SquareStyle?.color || null,
                SquareTextVariable: SquareStyle?.getPropertyValue("--text")?.trim() || null,
                SquareBackground: SquareStyle?.backgroundColor || null
            },
            SourcePixelHistogram: []
        };

        try {
            const Context = Canvas.getContext("2d", { willReadFrequently: true });
            const Image = Context?.getImageData(0, 0, Canvas.width, Canvas.height);
            if (!Image) {
                return Result;
            }

            const Counts = new Map();
            let NonTransparentPixels = 0;
            const Data = Image.data;

            for (let Offset = 0; Offset < Data.length; Offset += 4) {
                const Alpha = Data[Offset + 3];
                if (!Alpha) {
                    continue;
                }
                NonTransparentPixels++;
                const Key = `${Data[Offset]},${Data[Offset + 1]},${Data[Offset + 2]},${Alpha}`;
                Counts.set(Key, (Counts.get(Key) || 0) + 1);
            }

            Result.NonTransparentPixels = NonTransparentPixels;
            Result.SourcePixelHistogram = [...Counts.entries()]
                .sort((A, B) => B[1] - A[1])
                .slice(0, 40)
                .map(([Rgba, Count]) => ({
                    Rgba,
                    Count,
                    PercentOfNonTransparent: NonTransparentPixels
                        ? Math.round((Count / NonTransparentPixels) * 100000) / 1000
                        : 0
                }));
        } catch (ErrorValue) {
            Result.PixelReadError = String(ErrorValue?.message || ErrorValue);
        }

        return Result;
    }

    function RecordPreviewBoardCanvasTextDraw(Method, Context, ArgumentsValue) {
        if (!PreviewBoardCanvasTraceActive || !IsPreviewBoardCanvas(Context?.canvas)) {
            return;
        }

        const [Text, X, Y, MaxWidth] = ArgumentsValue;
        const Transform = typeof Context.getTransform === "function"
            ? Context.getTransform()
            : null;
        PreviewBoardCanvasTrace.push({
            Timestamp: new Date().toISOString(),
            Method,
            Text: String(Text),
            X: RoundPreviewNumber(X),
            Y: RoundPreviewNumber(Y),
            MaxWidth: Number.isFinite(Number(MaxWidth))
                ? RoundPreviewNumber(MaxWidth)
                : null,
            FillStyle: String(Context.fillStyle),
            StrokeStyle: String(Context.strokeStyle),
            GlobalAlpha: Context.globalAlpha,
            Font: Context.font,
            TextAlign: Context.textAlign,
            TextBaseline: Context.textBaseline,
            Transform: Transform
                ? {
                    A: RoundPreviewNumber(Transform.a),
                    B: RoundPreviewNumber(Transform.b),
                    C: RoundPreviewNumber(Transform.c),
                    D: RoundPreviewNumber(Transform.d),
                    E: RoundPreviewNumber(Transform.e),
                    F: RoundPreviewNumber(Transform.f)
                }
                : null
        });

        if (PreviewBoardCanvasTrace.length > 500) {
            PreviewBoardCanvasTrace.splice(
                0,
                PreviewBoardCanvasTrace.length - 500
            );
        }
        UpdatePreviewDiagnosticsStatus();
    }

    function InstallPreviewBoardCanvasTraceHook() {
        if (PreviewBoardCanvasHookInstalled) {
            return true;
        }

        const Prototype = PageWindow.CanvasRenderingContext2D?.prototype;
        if (!Prototype) {
            return false;
        }

        PreviewNativeBoardFillText = Prototype.fillText;
        PreviewNativeBoardStrokeText = Prototype.strokeText;

        if (typeof PreviewNativeBoardFillText === "function") {
            Prototype.fillText = function (...ArgumentsValue) {
                RecordPreviewBoardCanvasTextDraw(
                    "fillText",
                    this,
                    ArgumentsValue
                );
                return PreviewNativeBoardFillText.apply(this, ArgumentsValue);
            };
        }

        if (typeof PreviewNativeBoardStrokeText === "function") {
            Prototype.strokeText = function (...ArgumentsValue) {
                RecordPreviewBoardCanvasTextDraw(
                    "strokeText",
                    this,
                    ArgumentsValue
                );
                return PreviewNativeBoardStrokeText.apply(this, ArgumentsValue);
            };
        }

        PreviewBoardCanvasHookInstalled = true;
        return true;
    }

    function StartPreviewBoardCanvasTrace() {
        PreviewBoardCanvasTrace.length = 0;
        if (!InstallPreviewBoardCanvasTraceHook()) {
            alert("Could not install the board Canvas2D trace hook.");
            return;
        }

        PreviewBoardCanvasTraceActive = true;
        UpdatePreviewDiagnosticsStatus();
        console.info(
            "[Letter Boxed Cubed][preview] Board canvas text trace started. " +
            "Type/delete at least one board letter so NYT redraws the canvas."
        );
    }

    function StopPreviewBoardCanvasTrace() {
        PreviewBoardCanvasTraceActive = false;
        UpdatePreviewDiagnosticsStatus();
        return {
            CapturedAt: new Date().toISOString(),
            SourceSnapshot: GetPreviewBoardCanvasSnapshot(),
            TextDraws: structuredClone(PreviewBoardCanvasTrace)
        };
    }

'''
runtime = replace_once(runtime, anchor, insert + anchor, "canvas diagnostics functions")

runtime = replace_once(
    runtime,
    '''            BootstrapTrace: BootstrapDiagnostics.slice(-100),\n            TransientTrace: structuredClone(PreviewTransientTrace)\n''',
    '''            BootstrapTrace: BootstrapDiagnostics.slice(-100),\n            TransientTrace: structuredClone(PreviewTransientTrace),\n            BoardCanvas: {\n                SourceSnapshot: GetPreviewBoardCanvasSnapshot(),\n                TextTraceActive: PreviewBoardCanvasTraceActive,\n                TextDraws: structuredClone(PreviewBoardCanvasTrace)\n            }\n''',
    "debug bundle board canvas"
)

runtime = replace_once(
    runtime,
    '''        Status.textContent = PreviewTransientTraceActive\n            ? `Transient trace: RECORDING (${PreviewTransientTrace.length} events)`\n            : `Transient trace: stopped (${PreviewTransientTrace.length} events retained)`;\n''',
    '''        const TransientStatus = PreviewTransientTraceActive\n            ? `Transient: RECORDING (${PreviewTransientTrace.length})`\n            : `Transient: stopped (${PreviewTransientTrace.length})`;\n        const BoardStatus = PreviewBoardCanvasTraceActive\n            ? `Board canvas: RECORDING (${PreviewBoardCanvasTrace.length})`\n            : `Board canvas: stopped (${PreviewBoardCanvasTrace.length})`;\n        Status.textContent = `${TransientStatus} · ${BoardStatus}`;\n''',
    "diagnostics status"
)

runtime = replace_once(
    runtime,
    '''        AddButton(\n            "Copy Bootstrap Trace",\n            () => CopyPreviewDiagnostic(\n                BootstrapDiagnostics.slice(-100),\n                "Bootstrap trace"\n            )\n        );\n''',
    '''        AddButton(\n            "Copy Board Source Snapshot",\n            () => CopyPreviewDiagnostic(\n                GetPreviewBoardCanvasSnapshot(),\n                "Board source snapshot"\n            )\n        );\n        AddButton(\n            "Start Board Canvas Trace",\n            StartPreviewBoardCanvasTrace\n        );\n        AddButton(\n            "Stop + Copy Board Trace",\n            () => CopyPreviewDiagnostic(\n                StopPreviewBoardCanvasTrace(),\n                "Board canvas trace"\n            )\n        );\n        AddButton(\n            "Copy Bootstrap Trace",\n            () => CopyPreviewDiagnostic(\n                BootstrapDiagnostics.slice(-100),\n                "Bootstrap trace"\n            )\n        );\n''',
    "diagnostic buttons"
)

RUNTIME.write_text(runtime, encoding="utf-8")

tests = TESTS.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    '''  'Stop + Copy Trace',\n  'Copy Bootstrap Trace',\n''',
    '''  'Stop + Copy Trace',\n  'Copy Board Source Snapshot',\n  'Start Board Canvas Trace',\n  'Stop + Copy Board Trace',\n  'Copy Bootstrap Trace',\n''',
    "diagnostic labels"
)
needle = "assert(preview.includes('PreviewTransientTrace'), 'transient trace state missing');\n"
addition = (
    "assert(preview.includes('GetPreviewBoardCanvasSnapshot'), 'board source snapshot diagnostic missing');\n"
    "assert(preview.includes('InstallPreviewBoardCanvasTraceHook'), 'board Canvas2D trace hook missing');\n"
    "assert(preview.includes('SourcePixelHistogram'), 'board source pixel histogram missing');\n"
    "assert(preview.includes('TextDraws: structuredClone(PreviewBoardCanvasTrace)'), 'board trace missing from full debug bundle');\n"
)
if addition not in tests:
    tests = replace_once(tests, needle, needle + addition, "board diagnostic tests")
TESTS.write_text(tests, encoding="utf-8")
