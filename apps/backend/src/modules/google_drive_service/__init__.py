from integrations.google_drive_service import GoogleDriveService


async def init(deps: dict = None) -> GoogleDriveService:
    return GoogleDriveService()
