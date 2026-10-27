/**
 * Letter Boxed Cubed - Google Drive Sync Bridge
 *
 * Authorship: Nathan Burgdorff + Ari (ChatGPT)
 * License: GPL-3.0-or-later
 *
 * Deploy this Apps Script project as a Web App that:
 *   - Executes as: Me
 *   - Who has access: Anyone
 *
 * Required appsscript.json scopes: drive.file and script.external_request.
 * Required advanced service: Drive API v3. The script can only manage Drive
 * files created by this OAuth application (or explicitly opened with it).
 * Do not use DriveApp: it requires a much broader Drive authorization.
 *
 * The public endpoint is protected by a high-entropy shared secret generated
 * by Setup(). The secret is never stored in Letter Boxed Cubed exports.
 */

const ProtocolVersion = 1;
const BackupFolderName = "Letter Boxed Cubed";
const BackupFileName = "LetterBoxedCubedCloudBackup.json";
const SecretProperty = "LBC_SYNC_SECRET";
const BackupFileIdProperty = "LBC_BACKUP_FILE_ID";
const BackupFolderIdProperty = "LBC_BACKUP_FOLDER_ID";

function Setup() {
  const Properties = PropertiesService.getScriptProperties();
  let Secret = Properties.getProperty(SecretProperty);

  if (!Secret) {
    Secret = (Utilities.getUuid() + Utilities.getUuid()).replace(/-/g, "");
    Properties.setProperty(SecretProperty, Secret);
  }

  const File = GetOrCreateBackupFile_();

  console.log("Letter Boxed Cubed Google Drive bridge is ready.");
  console.log("Sync secret: " + Secret);
  console.log("Backup file: " + (File.webViewLink ||
    "https://drive.google.com/file/d/" + File.id + "/view"));
  console.log("After deployment, copy the Web App /exec URL into LBC's Drive setup dialog.");

  return Secret;
}

function doPost(Event) {
  try {
    const Request = ParseRequest_(Event);
    ValidateRequest_(Request);

    switch (Request.Action) {
      case "Read":
        return JsonResponse_(ReadEnvelope_());

      case "Write":
        return JsonResponse_(WriteEnvelope_(Request));

      default:
        throw new Error("Unknown action.");
    }
  } catch (Error) {
    return JsonResponse_({
      ProtocolVersion,
      Status: "error",
      Message: Error && Error.message ? Error.message : String(Error)
    });
  }
}

function ParseRequest_(Event) {
  const Contents = Event && Event.postData && Event.postData.contents
    ? Event.postData.contents
    : "";

  if (!Contents) {
    throw new Error("Empty request body.");
  }

  return JSON.parse(Contents);
}

function ValidateRequest_(Request) {
  if (!Request || typeof Request !== "object") {
    throw new Error("Invalid request.");
  }

  if (Number(Request.ProtocolVersion) !== ProtocolVersion) {
    throw new Error("Unsupported sync protocol version.");
  }

  const ExpectedSecret = PropertiesService
    .getScriptProperties()
    .getProperty(SecretProperty);

  if (!ExpectedSecret) {
    throw new Error("Bridge Setup() has not been run yet.");
  }

  if (String(Request.Secret || "") !== ExpectedSecret) {
    throw new Error("Invalid sync secret.");
  }
}

function ReadEnvelope_() {
  const File = GetOrCreateBackupFile_();
  const Contents = ReadBackupText_(File.id).trim();

  if (!Contents) {
    return EmptyEnvelope_();
  }

  try {
    const Parsed = JSON.parse(Contents);

    if (
      Parsed &&
      Number(Parsed.ProtocolVersion) === ProtocolVersion &&
      Object.prototype.hasOwnProperty.call(Parsed, "Revision")
    ) {
      return {
        ProtocolVersion,
        Status: "ok",
        Revision: Number(Parsed.Revision) || 0,
        UpdatedAt: Parsed.UpdatedAt || null,
        LastWriteId: Parsed.LastWriteId || null,
        LastWriterSessionId: Parsed.LastWriterSessionId || null,
        Data: Parsed.Data || null
      };
    }

    /*
     * Recovery convenience: if the Drive file contains a bare LBC backup from
     * an early/manual experiment, expose it as revision 0 rather than discarding
     * it. The next successful write wraps it in the current cloud envelope.
     */
    if (Parsed && Parsed.Format === "LetterBoxedCubedBackup") {
      return {
        ProtocolVersion,
        Status: "ok",
        Revision: 0,
        UpdatedAt: null,
        LastWriteId: null,
        LastWriterSessionId: null,
        Data: Parsed
      };
    }
  } catch (Error) {
    throw new Error("The Google Drive backup file contains invalid JSON.");
  }

  throw new Error("The Google Drive backup file has an unknown format.");
}

function WriteEnvelope_(Request) {
  if (!Request.Data || Request.Data.Format !== "LetterBoxedCubedBackup") {
    throw new Error("Write request did not contain an LBC backup payload.");
  }

  const Lock = LockService.getScriptLock();
  Lock.waitLock(15000);

  try {
    const Current = ReadEnvelope_();
    const ExpectedRevision = Number(Request.ExpectedRevision) || 0;
    const WriteId = String(Request.WriteId || "").trim() || null;
    const WriterSessionId =
      String(Request.WriterSessionId || "").trim() || null;

    if (WriteId && Current.LastWriteId === WriteId) {
      console.log(
        `LBC Drive write replay accepted: ${WriteId} @ revision ${Current.Revision}`
      );
      return {
        ProtocolVersion,
        Status: "ok",
        Revision: Current.Revision,
        UpdatedAt: Current.UpdatedAt || null,
        LastWriteId: Current.LastWriteId || null,
        LastWriterSessionId: Current.LastWriterSessionId || null,
        Replayed: true
      };
    }

    if (ExpectedRevision !== Current.Revision) {
      console.log(
        `LBC Drive revision conflict: expected ${ExpectedRevision}, current ${Current.Revision}, write ${WriteId || "(legacy)"}`
      );
      return {
        ProtocolVersion,
        Status: "conflict",
        Revision: Current.Revision,
        UpdatedAt: Current.UpdatedAt || null,
        LastWriteId: Current.LastWriteId || null,
        LastWriterSessionId: Current.LastWriterSessionId || null
      };
    }

    const Next = {
      ProtocolVersion,
      Revision: Current.Revision + 1,
      UpdatedAt: new Date().toISOString(),
      LastWriteId: WriteId,
      LastWriterSessionId: WriterSessionId,
      Data: Request.Data
    };

    const File = GetOrCreateBackupFile_();
    Drive.Files.update(
      {},
      File.id,
      Utilities.newBlob(JSON.stringify(Next), "text/plain", BackupFileName),
      { fields: "id" }
    );

    console.log(
      `LBC Drive write committed: revision ${Next.Revision}, write ${WriteId || "(legacy)"}`
    );

    return {
      ProtocolVersion,
      Status: "ok",
      Revision: Next.Revision,
      UpdatedAt: Next.UpdatedAt,
      LastWriteId: Next.LastWriteId,
      LastWriterSessionId: Next.LastWriterSessionId
    };
  } finally {
    Lock.releaseLock();
  }
}

function EmptyEnvelope_() {
  return {
    ProtocolVersion,
    Status: "ok",
    Revision: 0,
    UpdatedAt: null,
    LastWriteId: null,
    LastWriterSessionId: null,
    Data: null
  };
}

/**
 * Apps Script's Advanced Drive.Files.get({alt:'media'}) does not reliably
 * return raw text. Google's documented Apps Script download method uses
 * UrlFetchApp with the same restricted script OAuth token instead.
 * The only outbound destination used here is the Google Drive API.
 */
function ReadBackupText_(FileId) {
  const Response = UrlFetchApp.fetch(
    "https://www.googleapis.com/drive/v3/files/" +
      encodeURIComponent(FileId) + "?alt=media",
    {
      method: "get",
      headers: { Authorization: "Bearer " + ScriptApp.getOAuthToken() },
      muteHttpExceptions: true
    }
  );
  const Code = Response.getResponseCode();
  if (Code < 200 || Code >= 300) {
    throw new Error("Drive backup download failed (HTTP " + Code + ").");
  }
  return Response.getContentText("UTF-8");
}

/**
 * Only reuse an ID that this app can already access. Never silently replace
 * an inaccessible legacy backup with a blank new file: that could make
 * LBC think remote history has disappeared.
 */
function GetOrCreateBackupFile_() {
  const Properties = PropertiesService.getScriptProperties();
  const SavedFileId = Properties.getProperty(BackupFileIdProperty);
  if (SavedFileId) {
    try {
      const File = Drive.Files.get(SavedFileId, {
        fields: "id,name,mimeType,trashed,webViewLink"
      });
      if (File.trashed) {
        throw new Error("Backup file is in Drive trash.");
      }
      return File;
    } catch (ErrorValue) {
      throw new Error(
        "The previous backup is not accessible under the narrower drive.file " +
        "permission. Your existing Drive file has NOT been modified. " +
        "First export a full backup from LBC, then run " +
        "StartFreshLimitedScopeBackupAfterExport() in this Apps Script " +
        "project to create a new private backup. Original problem: " +
        String(ErrorValue.message || ErrorValue)
      );
    }
  }

  let FolderId = Properties.getProperty(BackupFolderIdProperty);
  if (FolderId) {
    try {
      const Folder = Drive.Files.get(FolderId, {
        fields: "id,mimeType,trashed"
      });
      if (Folder.trashed) {
        throw new Error("Folder was trashed.");
      }
    } catch (Error) {
      throw new Error(
        "The stored folder is inaccessible under drive.file. " +
        "Run StartFreshLimitedScopeBackupAfterExport() after exporting " +
        "your current LBC data."
      );
    }
  } else {
    const Folder = Drive.Files.create({
      name: BackupFolderName,
      mimeType: "application/vnd.google-apps.folder"
    }, null, {fields: "id"});
    FolderId = Folder.id;
    Properties.setProperty(BackupFolderIdProperty, FolderId);
  }

  const File = Drive.Files.create(
    {
      name: BackupFileName,
      mimeType: "text/plain",
      parents: [FolderId]
    },
    Utilities.newBlob("", "text/plain", BackupFileName),
    {fields: "id,name,webViewLink"}
  );
  Properties.setProperty(BackupFileIdProperty, File.id);
  return File;
}

/**
 * Explicit migration for older bridge installations only. Export from LBC
 * first, and keep the original Drive backup; this never deletes anything.
 * After running Setup() again, LBC will merge its locally stored history
 * into a fresh, limited-scope cloud backup on first synchronization.
 */
function StartFreshLimitedScopeBackupAfterExport() {
  const Properties = PropertiesService.getScriptProperties();
  Properties.deleteProperty(BackupFileIdProperty);
  Properties.deleteProperty(BackupFolderIdProperty);
  console.log(
    "Previous Drive files were left untouched. " +
    "Now run Setup(), then reconnect/sync LBC to seed the new backup."
  );
}

function JsonResponse_(Value) {
  return ContentService
    .createTextOutput(JSON.stringify(Value))
    .setMimeType(ContentService.MimeType.JSON);
}
