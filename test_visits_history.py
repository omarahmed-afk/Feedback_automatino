import unittest
from unittest.mock import MagicMock, patch

import visits


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.header = ['EMR ID', 'Clinic Name', 'Patient Name', 'Appointment Type',
                       'Appointment Date', 'Visit Status', 'Phone']
        self.row = ['001', 'Clinic', 'Sample', 'Follow Up', '09/23/2026', 'Checked In', '']
        self.sheet = MagicMock(row_count=100, col_count=7)
        self.book = MagicMock()
        self.book.worksheet.return_value = self.sheet
        self.logging = patch.object(visits, 'log')
        self.logging.start()
        self.addCleanup(self.logging.stop)

    def write(self, existing, rows):
        self.sheet.get.return_value = existing
        visits._write_google_tab(self.book, 'All', [self.header] + rows)
        self.sheet.batch_clear.assert_not_called()
        for call in self.sheet.update.call_args_list:
            self.assertNotIn('G', call.kwargs['range_name'])
            self.assertTrue(all(len(row) == 6 for row in call.kwargs['values']))

    def test_new_sheet_writes_header_and_deduplicates_input(self):
        self.write([], [self.row, self.row])
        self.sheet.update.assert_called_once_with(
            values=[self.header[:6], self.row[:6]], range_name='A1:F2', value_input_option='RAW')

    def test_rerun_preserves_manual_phone(self):
        saved = self.row[:6] + ['555-0100']
        self.write([self.header, saved], [self.row])
        self.sheet.update.assert_not_called()

    def test_new_date_appends_and_status_updates_in_place(self):
        changed = self.row.copy()
        changed[5] = 'Checked Out'
        tomorrow = self.row.copy()
        tomorrow[4] = '09/24/2026'
        self.write([self.header, self.row[:6] + ['555-0100']], [self.row, changed, tomorrow])
        self.sheet.update.assert_called_once_with(
            values=[tomorrow[:6]], range_name='A3:F3', value_input_option='RAW')
        self.sheet.batch_update.assert_called_once_with(
            [{'range': 'F2', 'values': [['Checked Out']]}], value_input_option='RAW')

    def test_status_only_does_not_append(self):
        changed = self.row.copy()
        changed[5] = 'Checked Out'
        self.write([self.header, self.row], [changed])
        self.sheet.update.assert_not_called()
        self.sheet.batch_update.assert_called_once_with(
            [{'range': 'F2', 'values': [['Checked Out']]}], value_input_option='RAW')

    def test_phone_header_can_be_customized(self):
        self.write([self.header[:6] + ['Contact Phone'], self.row], [self.row])
        self.sheet.update.assert_not_called()
        self.sheet.batch_update.assert_not_called()

    def test_empty_report_preserves_history(self):
        self.write([self.header, self.row], [])
        self.sheet.update.assert_not_called()

    def test_trailing_blank_phone_omitted_by_sheets(self):
        self.write([self.header, self.row[:6]], [self.row])
        self.sheet.update.assert_not_called()

    def test_unexpected_header_fails_without_writing(self):
        with self.assertRaises(RuntimeError):
            self.write([['Different header']], [self.row])
        self.sheet.update.assert_not_called()


if __name__ == '__main__':
    unittest.main()
