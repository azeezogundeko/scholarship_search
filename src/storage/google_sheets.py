"""Google Sheets storage backend using service account authentication."""

import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Any, Optional
from datetime import datetime


class GoogleSheetsStorage:
    """Storage backend for Google Sheets."""

    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    def __init__(self, service_account_info: dict):
        """Initialize Google Sheets storage.

        Args:
            service_account_info: Service account credentials as a dictionary
        """
        credentials = Credentials.from_service_account_info(
            service_account_info,
            scopes=self.SCOPES
        )
        self.client = gspread.authorize(credentials)

    def get_or_create_sheet(
        self,
        spreadsheet_id: str,
        sheet_name: str,
    ) -> gspread.Worksheet:
        """Get or create a worksheet in a spreadsheet.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the worksheet

        Returns:
            Worksheet object
        """
        spreadsheet = self.client.open_by_key(spreadsheet_id)

        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=sheet_name,
                rows=1000,
                cols=20
            )

        return worksheet

    def append_rows(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        rows: List[List[Any]],
        headers: Optional[List[str]] = None,
    ) -> None:
        """Append rows to a Google Sheet.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the worksheet
            rows: List of rows to append (each row is a list of values)
            headers: Optional headers to add if sheet is empty
        """
        worksheet = self.get_or_create_sheet(spreadsheet_id, sheet_name)

        # Check if we need to add headers
        if headers and worksheet.row_count == 0:
            worksheet.append_row(headers)

        # Append all rows
        if rows:
            worksheet.append_rows(rows)

    def append_dicts(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        data: List[Dict[str, Any]],
        add_timestamp: bool = True,
    ) -> None:
        """Append dictionaries as rows to a Google Sheet.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the worksheet
            data: List of dictionaries to append
            add_timestamp: Whether to add a timestamp column
        """
        if not data:
            return

        # Get all unique keys from all dictionaries
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())

        # Sort keys for consistent column order
        keys = sorted(all_keys)

        # Add timestamp column if requested
        if add_timestamp:
            keys = ['timestamp'] + keys

        worksheet = self.get_or_create_sheet(spreadsheet_id, sheet_name)

        # Add headers if sheet is empty
        if worksheet.row_count == 0:
            worksheet.append_row(keys)

        # Convert dicts to rows
        rows = []
        for item in data:
            row = []
            if add_timestamp:
                row.append(datetime.now().isoformat())

            for key in keys:
                if key != 'timestamp':
                    value = item.get(key, '')
                    # Convert lists/dicts to strings
                    if isinstance(value, (list, dict)):
                        value = str(value)
                    row.append(value)

            rows.append(row)

        # Append all rows
        worksheet.append_rows(rows)

    def update_cell(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        row: int,
        col: int,
        value: Any,
    ) -> None:
        """Update a single cell.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the worksheet
            row: Row number (1-indexed)
            col: Column number (1-indexed)
            value: Value to set
        """
        worksheet = self.get_or_create_sheet(spreadsheet_id, sheet_name)
        worksheet.update_cell(row, col, value)

    def get_all_values(
        self,
        spreadsheet_id: str,
        sheet_name: str,
    ) -> List[List[str]]:
        """Get all values from a worksheet.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the worksheet

        Returns:
            List of rows (each row is a list of values)
        """
        worksheet = self.get_or_create_sheet(spreadsheet_id, sheet_name)
        return worksheet.get_all_values()

    def clear_sheet(
        self,
        spreadsheet_id: str,
        sheet_name: str,
    ) -> None:
        """Clear all content from a worksheet.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the worksheet
        """
        worksheet = self.get_or_create_sheet(spreadsheet_id, sheet_name)
        worksheet.clear()

    def create_spreadsheet(
        self,
        title: str,
        share_with: Optional[List[str]] = None,
    ) -> str:
        """Create a new spreadsheet.

        Args:
            title: Spreadsheet title
            share_with: Optional list of email addresses to share with

        Returns:
            Spreadsheet ID
        """
        spreadsheet = self.client.create(title)

        # Share with specified emails
        if share_with:
            for email in share_with:
                spreadsheet.share(email, perm_type='user', role='writer')

        return spreadsheet.id
