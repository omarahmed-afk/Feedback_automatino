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
        return self.sheet.batch_update.call_args.args[0]

    def test_new_sheet_deduplicates_input(self):
        updates = self.write([], [self.row, self.row])
        self.assertEqual(updates, [
            {'range': 'A1:F1', 'values': [self.header[:6]]},
            {'range': 'A2:G2', 'values': [self.row]},
        ])

    def test_previous_date_and_stale_phone_removed(self):
        today = self.row.copy()
        today[4] = '09/24/2026'
        updates = self.write([self.header, self.row[:6] + ['555-0100'], self.row], [today])
        self.assertEqual(updates[1]['values'], [today, [''] * 7])
        self.assertEqual(updates[1]['range'], 'A2:G3')

    def test_phone_follows_matching_visit_and_status_refreshes(self):
        another = self.row.copy()
        another[0] = '002'
        changed = self.row.copy()
        changed[5] = 'Checked Out'
        updates = self.write([self.header, self.row[:6] + ['555-0100'], another],
                             [another, changed])
        self.assertEqual(updates[1]['values'], [another, changed[:6] + ['555-0100']])

    def test_empty_report_clears_data(self):
        updates = self.write([self.header, self.row], [])
        self.assertEqual(updates[1]['values'], [[''] * 7])

    def test_custom_phone_header_is_not_written(self):
        updates = self.write([self.header[:6] + ['Contact Phone'], self.row], [self.row])
        self.assertEqual(updates[0], {'range': 'A1:F1', 'values': [self.header[:6]]})

    def test_unexpected_header_fails_without_writing(self):
        with self.assertRaises(RuntimeError):
            self.write([['Different header']], [self.row])
        self.sheet.update.assert_not_called()
        self.sheet.batch_update.assert_not_called()


if __name__ == '__main__':
    unittest.main()
