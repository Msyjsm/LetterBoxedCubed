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
 * The public endpoint is protected by a high-entropy shared secret generated
 * by Setup(). The secret is never stored in Letter Boxed Cubed exports.
 */

const ProtocolVersion = 1;
const BackupFolderName = "Letter Boxed Cubed";
const BackupFileName = "LetterBoxedCubedCloudBackup.json";
const SecretProperty = "LBC_SYNC_SECRET";
const BackupFileIdProperty = "LBC_BACKUP_FILE_ID";

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
  console.log("Backup file: " + File.getUrl());
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
  const Contents = File.getBlob().getDataAsString("UTF-8").trim();

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

    if (ExpectedRevision !== Current.Revision) {
      return {
        ProtocolVersion,
        Status: "conflict",
        Revision: Current.Revision,
        UpdatedAt: Current.UpdatedAt || null
      };
    }

    const Next = {
      ProtocolVersion,
      Revision: Current.Revision + 1,
      UpdatedAt: new Date().toISOString(),
      Data: Request.Data
    };

    const File = GetOrCreateBackupFile_();
    File.setContent(JSON.stringify(Next, null, 2));

    return {
      ProtocolVersion,
      Status: "ok",
      Revision: Next.Revision,
      UpdatedAt: Next.UpdatedAt
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
    Data: null
  };
}

function GetOrCreateBackupFile_() {
  const Properties = PropertiesService.getScriptProperties();
  const SavedFileId = Properties.getProperty(BackupFileIdProperty);

  if (SavedFileId) {
    try {
      return DriveApp.getFileById(SavedFileId);
    } catch (Error) {
      Properties.deleteProperty(BackupFileIdProperty);
    }
  }

  let Folder;
  const Folders = DriveApp.getFoldersByName(BackupFolderName);

  if (Folders.hasNext()) {
    Folder = Folders.next();
  } else {
    Folder = DriveApp.createFolder(BackupFolderName);
  }

  let File;
  const Files = Folder.getFilesByName(BackupFileName);

  if (Files.hasNext()) {
    File = Files.next();
  } else {
    File = Folder.createFile(
      BackupFileName,
      "",
      MimeType.PLAIN_TEXT
    );
  }

  Properties.setProperty(
    BackupFileIdProperty,
    File.getId()
  );

  return File;
}

function JsonResponse_(Value) {
  return ContentService
    .createTextOutput(JSON.stringify(Value))
    .setMimeType(ContentService.MimeType.JSON);
}
