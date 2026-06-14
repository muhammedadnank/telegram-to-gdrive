class BotCommands:
    Authorize = ["auth", "authorize"]
    SetFolder = ["setfolder", "setfl"]
    Revoke = ["revoke"]
    Accounts = ["accounts", "myaccounts"]
    SwitchAccount = ["switch", "switchaccount"]


class Messages:
    START_MSG = "**Hi there {}. 🎵**\n__I'm Music to Google Drive Bot. Send me any music/audio file and I'll upload it directly to your Google Drive.__\n__You'll need to setup /auth first.__"

    HELP_MSG = [
        ".",
        "**🎵 Music to Google Drive Bot**\n__Send me any audio file (mp3, flac, wav, m4a, ogg etc.) and I will upload it to your Google Drive.__\n\nBefore using, you need to authenticate your Google Drive account.",
        f"**Authenticating Google Drive**\n__Send the /{BotCommands.Authorize[0]} command and you will receive a URL, visit the URL, follow the steps and send the received code here.__\n__Use /{BotCommands.Revoke[0]} to revoke your currently logged Google Drive Account.__\n\n**Note: Authorization is mandatory before I can upload files!**",
        f"**Custom Upload Folder**\n__Want to upload to a specific folder?__\n__Use /{BotCommands.SetFolder[0]} (Folder URL) to set a custom upload folder.__",
    ]

    RATE_LIMIT_EXCEEDED_MESSAGE = (
        "❗ **Rate Limit Exceeded.**\n__User rate limit exceeded try after 24 hours.__"
    )

    FILE_NOT_FOUND_MESSAGE = "❗ **File/Folder not found.**\n__File id - {} Not found. Make sure it's exists and accessible by the logged account.__"

    INVALID_GDRIVE_URL = "❗ **Invalid Google Drive URL**\nMake sure the Google Drive URL is in valid format."

    COPIED_SUCCESSFULLY = "✅ **Copied successfully.**\n[{}]({}) __({})__"

    NOT_AUTH = f"🔑 **You have not authenticated me to upload to any account.**\n__Send /{BotCommands.Authorize[0]} to authenticate.__"

    DOWNLOADED_SUCCESSFULLY = (
        "📤 **Uploading File...**\n**Filename:** `{}`\n**Size:** `{}`"
    )

    UPLOADED_SUCCESSFULLY = "✅ **Uploaded Successfully.**\n[{}]({}) __({})__"

    DOWNLOAD_ERROR = "❗**Downloader Failed**\n{}\n__Link - {}__"

    DOWNLOADING = "📥 **Downloading File...\nLink:** `{}`"

    ALREADY_AUTH = (
        "🔒 **You already have {count} Google Drive account(s) linked.**\n"
        "__Use /accounts to manage them, or /auth again to add another account.__"
    )

    FLOW_IS_NONE = f"❗ **Invalid Code**\n__Run {BotCommands.Authorize[0]} first.__"

    AUTH_SUCCESSFULLY = "🔐 **Google Drive account #{index} authorized successfully.**\n__Label: `{label}`__\n__Use /accounts to view all linked accounts.__"

    INVALID_AUTH_CODE = "❗ **Invalid Code**\n__The code you have sent is invalid or already used before. Generate new one by the Authorization URL__"

    AUTH_TEXT = "⛓️ **To Authorize your Google Drive account visit this [URL]({}) and copy the code & send it here.**\n__Visit the URL > Allow permissions >  copy code  > Send it here__"

    NO_ACCOUNTS = (
        f"❗ **No Google Drive accounts linked.**\n"
        f"__Use /{BotCommands.Authorize[0]} to connect one.__"
    )

    ACCOUNTS_LIST_HEADER = "🗂️ **Your linked Google Drive accounts:**\n\n{entries}\n\n__Use /switch `<number>` to switch active account.__\n__Use /revoke `<number>` to remove an account.__"

    SWITCHED = "✅ **Switched to account #{index}:** `{label}`"

    REVOKED = (
        f"🔓 **Account removed successfully.**\n"
        f"__Use /{BotCommands.Authorize[0]} to add a new account.__"
    )

    DOWNLOAD_TG_FILE = "📥 **Downloading File...**\n**Filename:** `{}`\n**Size:** `{}`\n**MimeType:** `{}`"

    PARENT_SET_SUCCESS = "🆔✅ **Custom Folder link set successfully.**\n__Your custom folder id - {}\nUse__ `/{} clear` __to clear it.__"
    
    PARENT_CLEAR_SUCCESS = f"🆔🚮 **Custom Folder ID Cleared Successfuly.**\n__Use__ `/{BotCommands.SetFolder[0]} (Folder Link)` __to set it back__."

    CURRENT_PARENT = "🆔 **Your Current Custom Folder ID - {}**\n__Use__ `/{} (Folder link)` __to change it.__"

    NOT_FOLDER_LINK = (
        "❗ **Invalid folder link.**\n__The link you send its not belong to a folder.__"
    )

    CLONING = "🗂️ **Cloning into Google Drive...**\n__G-Drive Link - {}__"

    PROVIDE_GDRIVE_URL = "**❗ Provide a valid Google Drive URL along with commmand.**\n__Usage - /{} (GDrive Link)__"

    INSUFFICIENT_PERMISSONS = (
        "❗ **You have insufficient permissions for this file.**\n__File id - {}__"
    )

    DELETED_SUCCESSFULLY = "🗑️✅ **File Deleted Successfully.**\n__File deleted permanently !\nFile id - {}__"

    WENT_WRONG = "⁉️ **ERROR: SOMETHING WENT WRONG**\n__Please try again later.__"

    EMPTY_TRASH = "🗑️🚮**Trash Emptied Successfully !**"

    PROVIDE_YTDL_LINK = "❗**Provide a valid YouTube-DL supported link.**"

    NO_FOLDER_SET = (
        "📁 **No custom folder set.**\n"
        "__Files will be uploaded to your Drive root by default.__\n"
        f"__Use /{BotCommands.SetFolder[0]} (Folder Link) to set a custom folder.__"
    )
