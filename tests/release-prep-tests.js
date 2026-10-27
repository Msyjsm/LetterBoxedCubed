const Fs = require("node:fs");
const Path = require("node:path");
const Vm = require("node:vm");
const Assert = require("node:assert/strict");
const Root = Path.resolve(__dirname, "..");
const Bridge = Fs.readFileSync(
    Path.join(Root, "integrations/google-drive/Code.gs"), "utf8"
);
const Manifest = JSON.parse(Fs.readFileSync(
    Path.join(Root, "integrations/google-drive/appsscript.json"), "utf8"
));
const Lbc = Fs.readFileSync(Path.join(Root, "LetterBoxedCubed.user.js"), "utf8");

Assert(!Bridge.includes("DriveApp."), "Bridge must not request full DriveApp scope");
Assert.deepEqual([...Manifest.oauthScopes].sort(), [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/script.external_request"
].sort(), "Bridge must request exactly Drive file and Google API fetch scopes");
Assert(Manifest.dependencies.enabledAdvancedServices.some(
    X => X.serviceId === "drive" && X.version === "v3"
), "Drive v3 advanced service must be declared");
Assert(Lbc.includes("https://nathanburgdorff.com/lbc/google-drive-sync/"),
    "LBC Setup help link missing");
Assert(Lbc.includes("Don't have this? See nathanburgdorff.com/lbc/google-drive-sync"),
    "LBC Setup prompt help missing");
Assert(Lbc.includes('const LocalRecoveryKey = "LetterBoxedCubed_WordsRecovery_v1";'),
    "local catastrophic recovery mirror missing");
Assert(Lbc.includes("QueueLocalRecoveryBackup(0);"),
    "cloud success must update local backup");
Assert(Lbc.includes("QueueLocalRecoveryBackup();"),
    "local changes must update backup even without Drive");
Assert(Lbc.includes("MergeBackupIntoStorage(Backup, {"),
    "local recovery must use merge, not overwrite");

// Simulate the real Apps Script public request shape and Google Drive storage.
{
    let Id = 0;
    const Files = new Map();
    const Props = new Map();
    const HttpRequests = [];
    const Store = {
        getProperty: Key => Props.get(Key) ?? null,
        setProperty: (Key, Value) => Props.set(Key, Value),
        deleteProperty: Key => Props.delete(Key)
    };
    const Mime = {PLAIN_TEXT:"text/plain"};
    const Utilities = {
        getUuid: () => "stable-random-uuid-" + (++Id),
        newBlob: (Text, MimeType, Name) => ({
            Text: String(Text),
            MimeType, Name
        })
    };
    const Drive = {
        Files: {
            create: (Body, Blob, Options) => {
                const FileId = "file-" + (++Id);
                const File = {
                    id: FileId,
                    name: Body.name,
                    mimeType: Body.mimeType,
                    parents: Body.parents || [],
                    webViewLink: "https://drive.google.com/file/d/" + FileId + "/view",
                    trashed: false,
                    Text: Blob?.Text || ""
                };
                Files.set(FileId, File);
                return File;
            },
            get: (FileId, Options) => {
                if (!Files.has(FileId)) throw Error("File not found");
                return Files.get(FileId);
            },
            update: (Body, FileId, Blob) => {
                if (!Files.has(FileId)) throw Error("File not found");
                Files.get(FileId).Text = Blob.Text;
                return Files.get(FileId);
            }
        }
    };
    const UrlFetchApp = {
        fetch: (Url, Options) => {
            HttpRequests.push(Url);
            const Match = Url.match(/^https:\/\/www\.googleapis\.com\/drive\/v3\/files\/([^?]+)\?alt=media$/);
            Assert(Match, "Unexpected outbound destination " + Url);
            const File = Files.get(decodeURIComponent(Match[1]));
            return {
                getResponseCode: () => File ? 200 : 404,
                getContentText: () => File ? File.Text : "File not found"
            };
        }
    };
    const Google = {
        PropertiesService: {getScriptProperties: () => Store},
        Drive, UrlFetchApp, Utilities,
        ScriptApp: {getOAuthToken: () => "test-drive-file-token"},
        LockService: {getScriptLock: () => ({
            waitLock: () => {}, releaseLock: () => {}
        })},
        ContentService: {
            MimeType: {JSON: "application/json"},
            createTextOutput: Text => ({
                Content: Text, setMimeType() { return this; }
            })
        },
        console: {log: () => {}},
        Date, JSON, Number, String, Object, Error, encodeURIComponent
    };
    Vm.createContext(Google);
    Vm.runInContext(Bridge, Google);
    const Secret = Vm.runInContext("Setup()", Google);
    Assert(Secret && Secret.length >= 30, "Setup must generate a strong secret");
    Assert.equal(Files.size, 2, "Setup creates one folder and one backup file");
    const Request = (Action, Payload = {}) => {
        const Data = {ProtocolVersion:1,Secret,Action,...Payload};
        const Response = Vm.runInContext(
            "doPost(JSON.parse(" + JSON.stringify(JSON.stringify({
                postData: {contents: JSON.stringify(Data)}
            })) + "))",
            Google
        );
        return JSON.parse(Response.Content);
    };
    const Start = Request("Read");
    Assert.equal(Start.Revision, 0, "initial backup revision must be zero");
    Assert.equal(Start.Data, null, "empty backup must have no payload");
    const Snapshot = {Format: "LetterBoxedCubedBackup", StorageSnapshot: {
        LetterBoxedTracker_123: ["CURIE"]
    }};
    const Written = Request("Write", {
        Data: Snapshot, ExpectedRevision:0,
        WriteId: "test-write-1", WriterSessionId: "test"
    });
    Assert.equal(Written.Status, "ok", "write must succeed");
    Assert.equal(Written.Revision, 1, "first write revision");
    const ReadBack = Request("Read");
    Assert.equal(ReadBack.Data.StorageSnapshot.LetterBoxedTracker_123[0], "CURIE",
        "backup content should survive Drive API fetch");
    const Replay = Request("Write", {
        Data: Snapshot, ExpectedRevision:0,
        WriteId: "test-write-1", WriterSessionId: "test"
    });
    Assert.equal(Replay.Replayed, true, "idempotent write replay must succeed");
    const Invalid = Request("Write", {
        Data: Snapshot, ExpectedRevision:0, WriteId:"new-write"
    });
    Assert.equal(Invalid.Status, "conflict", "stale revision must conflict");
    Assert(HttpRequests.length >= 3, "Read must use Google Drive API");
    Assert(HttpRequests.every(Url => Url.startsWith("https://www.googleapis.com/drive/v3/")),
        "Bridge must never send content to external non-Google destinations");

    // Migrating a legacy file cannot silently create a blank backup.
    Props.set("LBC_BACKUP_FILE_ID", "old-legacy-inaccessible");
    const CountBeforeMigration = Files.size;
    Assert.throws(() => Vm.runInContext("Setup()", Google), /previous backup is not accessible/,
        "Legacy inaccessible backup must stop before any data loss");
    Assert.equal(Files.size, CountBeforeMigration, "No implicit empty-file recreation");
    Vm.runInContext("StartFreshLimitedScopeBackupAfterExport()", Google);
    Vm.runInContext("Setup()", Google);
    Assert.equal(Files.size, CountBeforeMigration + 2,
        "Explicit migration creates separate new folder and file");
}
console.log("PASS: narrow Drive bridge protocol and safe migration mock integration checks");


// Verify the extra browser backup contains only word-related records, never
// cloud credentials, and restores via a merge instead of replacing state.
{
    const Start = Lbc.indexOf('    const LocalRecoveryKey = "LetterBoxedCubed_WordsRecovery_v1";');
    const End = Lbc.indexOf('    function GetHistoricalProjectionForExport(', Start);
    Assert(Start >= 0 && End > Start, "local recovery helpers unavailable");
    const Storage = new Map();
    let Merged = null;
    let Reloads = 0;
    const Browser = {
        Date, JSON, Object, String, Number, Math,
        localStorage: {
            setItem: (Key, Value) => Storage.set(Key, Value),
            getItem: Key => Storage.get(Key) || null
        },
        BuildStorageSnapshot: () => ({
            LetterBoxedTracker_123: ["CURIE"],
            LetterBoxedCubed_FoundTwofers_123: ["CURIE\u001fEAT"],
            LetterBoxedCubed_CustomWords_123: ["EXAMPLE"],
            LBC_SYNC_SECRET: "MUST_NOT_APPEAR",
            "LetterBoxedCubed_Drive_Config": { Secret: "MUST_NOT_APPEAR" }
        }),
        CustomWordsPrefix: "LetterBoxedCubed_CustomWords_",
        CustomDictionaryStorageKey: "LetterBoxedCubed_CustomDictionary",
        GlobalWordHistoryStorageKey: "LetterBoxedCubed_GlobalWordHistory",
        ExportFormatName: "LetterBoxedCubedBackup",
        ExportFormatVersion: 4,
        MigrateBackupToCurrent: X => X,
        MergeBackupIntoStorage: X => { Merged = X; return { ChangedKeys: 3 }; },
        confirm: () => true,
        alert: () => {},
        location: {reload: () => { Reloads++; }},
        clearTimeout: () => {},
        setTimeout: () => 1,
        console: {log: () => {}, warn: () => {}, error: () => {}}
    };
    Vm.createContext(Browser);
    Vm.runInContext(
        Lbc.slice(Start, End) +
        '\nglobalThis.LocalRecoveryHooks = {' +
        'WriteLocalRecoveryBackup, RecoverLocalBackup};',
        Browser
    );
    Assert(Browser.LocalRecoveryHooks.WriteLocalRecoveryBackup(), "mirror should write");
    const Saved = Storage.get("LetterBoxedCubed_WordsRecovery_v1");
    Assert(Saved && Saved.includes("CURIE"), "word data must be mirrored");
    Assert(!Saved.includes("MUST_NOT_APPEAR"), "sync credentials must never enter localStorage");
    Browser.LocalRecoveryHooks.RecoverLocalBackup();
    Assert(Merged && Merged.StorageSnapshot.LetterBoxedTracker_123,
        "local recovery must merge word snapshot");
    Assert.equal(Reloads, 1, "successful merge reloads once");
}
console.log("PASS: localStorage credential exclusion and explicit recovery merge");
