"""
Excel Export Service for Weekly Reports
Generates professional Excel reports with formatting and charts
"""
import os
from runtime_paths import data_directory
import json
import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import PieChart, Reference, BarChart
from openpyxl.utils import get_column_letter
from logger_config import get_logger

logger = get_logger('app')


class ExcelReportGenerator:
    """Generate Excel reports from test data"""
    
    def __init__(self):
        self.report_dir = str(data_directory() / 'reports')
        if not os.path.exists(self.report_dir):
            try:
                os.makedirs(self.report_dir)
                logger.info(f"Created reports directory: {self.report_dir}")
            except Exception as e:
                logger.error(f"Failed to create reports directory: {e}")
                raise
    
    def generate_weekly_report(self, weekly_data, stats, calibration_settings):
        """
        Generate a comprehensive weekly Excel report
        
        Args:
            weekly_data: List of test results from the week
            stats: Statistics dictionary with total tests count
            calibration_settings: Current calibration settings
            
        Returns:
            str: Path to generated Excel file or None on error
        """
        try:
            logger.info("Starting weekly Excel report generation")
            
            # Create workbook
            wb = Workbook()
            
            # Remove default sheet
            wb.remove(wb.active)
            
            # Add worksheets
            self._create_summary_sheet(wb, weekly_data, stats)
            self._create_detailed_data_sheet(wb, weekly_data)
            self._create_statistics_sheet(wb, weekly_data)
            self._create_calibration_sheet(wb, calibration_settings)
            
            # Generate filename with timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"Weekly_Report_{timestamp}.xlsx"
            filepath = os.path.join(self.report_dir, filename)
            
            # Save workbook
            wb.save(filepath)
            logger.info(f"Excel report generated successfully: {filepath}")
            
            # Get file size for logging
            file_size = os.path.getsize(filepath)
            logger.info(f"Report file size: {file_size:,} bytes ({file_size/1024:.2f} KB)")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating Excel report: {e}", exc_info=True)
            return None
    
    def _create_summary_sheet(self, wb, weekly_data, stats):
        """Create summary overview sheet"""
        ws = wb.create_sheet('Summary', 0)
        
        # Title
        ws['A1'] = 'Light Transmission Tester - SYNTHETIC DEMO - Weekly Report'
        ws['A1'].font = Font(size=16, bold=True, color='FFFFFF')
        ws['A1'].fill = PatternFill(start_color='0066CC', end_color='0066CC', fill_type='solid')
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws.merge_cells('A1:F1')
        ws.row_dimensions[1].height = 30
        
        # Report info
        row = 3
        ws[f'A{row}'] = 'Report Date:'
        ws[f'B{row}'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ws[f'A{row}'].font = Font(bold=True)
        
        row += 1
        ws[f'A{row}'] = 'Report Period:'
        if weekly_data:
            start_date = datetime.datetime.fromisoformat(weekly_data[0]['timestamp']).strftime('%Y-%m-%d')
            end_date = datetime.datetime.fromisoformat(weekly_data[-1]['timestamp']).strftime('%Y-%m-%d')
            ws[f'B{row}'] = f"{start_date} to {end_date}"
        else:
            ws[f'B{row}'] = 'No data'
        ws[f'A{row}'].font = Font(bold=True)
        
        row += 1
        ws[f'A{row}'] = 'Total Tests (All Time):'
        ws[f'B{row}'] = stats.get('total_tests_count', 0)
        ws[f'A{row}'].font = Font(bold=True)
        
        # Weekly statistics
        row += 2
        ws[f'A{row}'] = 'This Week\'s Results'
        ws[f'A{row}'].font = Font(size=14, bold=True)
        row += 1
        
        # Calculate statistics
        total_tests = len(weekly_data)
        pass_count = sum(1 for entry in weekly_data if 'PASS' in entry['result'])
        fail_count = sum(1 for entry in weekly_data if 'FAIL' in entry['result'])
        
        pass_rate = (pass_count / total_tests * 100) if total_tests > 0 else 0
        
        # Results table
        headers = ['Result', 'Count', 'Percentage']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=row, column=col)
            cell.value = header
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
            cell.alignment = Alignment(horizontal='center')
        
        row += 1
        
        # Data rows
        data_rows = [
            ('PASS', pass_count, f"{pass_count/total_tests*100:.1f}%" if total_tests > 0 else "0%"),
            ('FAIL', fail_count, f"{fail_count/total_tests*100:.1f}%" if total_tests > 0 else "0%"),
            ('TOTAL', total_tests, '100%')
        ]
        
        for data_row in data_rows:
            for col, value in enumerate(data_row, start=1):
                cell = ws.cell(row=row, column=col)
                cell.value = value
                cell.alignment = Alignment(horizontal='center')
                
                # Color code results
                if col == 1:
                    if value == 'PASS':
                        cell.fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
                    elif value == 'FAIL':
                        cell.fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
                    elif value == 'TOTAL':
                        cell.font = Font(bold=True)
            row += 1
        
        # Key metrics
        row += 2
        ws[f'A{row}'] = 'Key Metrics'
        ws[f'A{row}'].font = Font(size=12, bold=True)
        row += 1
        
        metrics = [
            ('Pass Rate:', f"{pass_rate:.1f}%"),
            ('Fail Rate:', f"{fail_count/total_tests*100:.1f}%" if total_tests > 0 else "0%"),
            ('Tests This Week:', total_tests),
        ]
        
        for metric_label, metric_value in metrics:
            ws[f'A{row}'] = metric_label
            ws[f'B{row}'] = metric_value
            ws[f'A{row}'].font = Font(bold=True)
            row += 1
        
        # Column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 15
        
        logger.debug("Summary sheet created")
    
    def _create_detailed_data_sheet(self, wb, weekly_data):
        """Create detailed test data sheet"""
        ws = wb.create_sheet('Detailed Data')
        
        # Headers
        headers = ['#', 'Date', 'Time', 'Result', 'Cavity', 'Front (lx)', 'Left (lx)', 'Back (lx)', 'Right (lx)', 'Notes']
        
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill(start_color='0066CC', end_color='0066CC', fill_type='solid')
            cell.alignment = Alignment(horizontal='center')
        
        # Data rows
        for idx, entry in enumerate(weekly_data, start=1):
            row = idx + 1
            
            # Parse timestamp
            try:
                dt = datetime.datetime.fromisoformat(entry['timestamp'])
                date_str = dt.strftime('%Y-%m-%d')
                time_str = dt.strftime('%H:%M:%S')
            except:
                date_str = 'N/A'
                time_str = 'N/A'
            
            # Parse result
            result_str = entry['result']
            result_type = 'UNKNOWN'
            cavity = ''
            readings = {'front': None, 'left': None, 'back': None, 'right': None}
            
            if 'PASS' in result_str:
                result_type = 'PASS'
            elif 'FAIL' in result_str:
                result_type = 'FAIL'
            else:
                result_type = 'UNKNOWN'
            
            # Extract cavity information from result (format: "PASS (A+2)")
            try:
                result_part = result_str.split(' | ')[0]  # Get part before first |
                if '(' in result_part and ')' in result_part:
                    cavity_start = result_part.find('(')
                    cavity_end = result_part.find(')')
                    if cavity_start < cavity_end:
                        cavity = result_part[cavity_start + 1:cavity_end]
            except:
                cavity = ''
            
            # Parse sensor readings (format: "F98, L215, B82, R162")
            try:
                parts = result_str.split('|')
                if len(parts) > 1:
                    readings_part = parts[1].strip()
                    for token in readings_part.split(','):
                        token = token.strip()
                        if not token:
                            continue
                        sensor = token[0].lower()
                        value_str = token[1:].removeprefix("-")
                        try:
                            value = float(value_str)
                            if sensor == 'f':
                                readings['front'] = value
                            elif sensor == 'l':
                                readings['left'] = value
                            elif sensor == 'b':
                                readings['back'] = value
                            elif sensor == 'r':
                                readings['right'] = value
                        except ValueError:
                            pass
            except Exception as e:
                logger.debug(f"Could not parse readings from: {result_str}")
            
            # Write row
            ws.cell(row=row, column=1).value = idx
            ws.cell(row=row, column=2).value = date_str
            ws.cell(row=row, column=3).value = time_str
            ws.cell(row=row, column=4).value = result_type
            ws.cell(row=row, column=5).value = cavity
            ws.cell(row=row, column=6).value = readings['front']
            ws.cell(row=row, column=7).value = readings['left']
            ws.cell(row=row, column=8).value = readings['back']
            ws.cell(row=row, column=9).value = readings['right']
            ws.cell(row=row, column=10).value = result_str  # Full original string
            
            # Format result cell
            result_cell = ws.cell(row=row, column=4)
            result_cell.alignment = Alignment(horizontal='center')
            
            if result_type == 'PASS':
                result_cell.fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
                result_cell.font = Font(color='006100')
            elif result_type == 'FAIL':
                result_cell.fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
                result_cell.font = Font(color='9C0006')
            
            # Center align numeric columns
            for col in range(1, 11):
                ws.cell(row=row, column=col).alignment = Alignment(horizontal='center')
        
        # Column widths
        ws.column_dimensions['A'].width = 6
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 10
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 10  # Cavity column
        ws.column_dimensions['F'].width = 12
        ws.column_dimensions['G'].width = 12
        ws.column_dimensions['H'].width = 12
        ws.column_dimensions['I'].width = 12
        ws.column_dimensions['J'].width = 40
        
        # Freeze header row
        ws.freeze_panes = 'A2'
        
        logger.debug("Detailed data sheet created")
    
    def _create_statistics_sheet(self, wb, weekly_data):
        """Create statistics and charts sheet"""
        ws = wb.create_sheet('Statistics')
        
        # Title
        ws['A1'] = 'Weekly Statistics'
        ws['A1'].font = Font(size=14, bold=True)
        
        # Calculate daily statistics
        daily_stats = {}
        for entry in weekly_data:
            try:
                dt = datetime.datetime.fromisoformat(entry['timestamp'])
                date_key = dt.strftime('%Y-%m-%d')
                
                if date_key not in daily_stats:
                    daily_stats[date_key] = {'pass': 0, 'fail': 0}
                
                result = entry['result']
                if 'PASS' in result and 'FAIL' not in result:
                    daily_stats[date_key]['pass'] += 1
                elif 'FAIL' in result:
                    daily_stats[date_key]['fail'] += 1
            except Exception as e:
                logger.debug(f"Error processing entry for statistics: {e}")
        
        # Write daily statistics
        row = 3
        ws[f'A{row}'] = 'Daily Breakdown'
        ws[f'A{row}'].font = Font(size=12, bold=True)
        row += 1
        
        headers = ['Date', 'PASS', 'FAIL', 'Total', 'Pass Rate']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=row, column=col)
            cell.value = header
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')
            cell.alignment = Alignment(horizontal='center')
        
        row += 1
        start_data_row = row
        
        for date_key in sorted(daily_stats.keys()):
            stats = daily_stats[date_key]
            total = stats['pass'] + stats['fail']
            pass_rate = (stats['pass'] / total * 100) if total > 0 else 0
            
            ws.cell(row=row, column=1).value = date_key
            ws.cell(row=row, column=2).value = stats['pass']
            ws.cell(row=row, column=3).value = stats['fail']
            ws.cell(row=row, column=4).value = total
            ws.cell(row=row, column=5).value = f"{pass_rate:.1f}%"
            
            for col in range(1, 6):
                ws.cell(row=row, column=col).alignment = Alignment(horizontal='center')
            
            row += 1
        
        # Column widths
        for col in range(1, 6):
            ws.column_dimensions[get_column_letter(col)].width = 15
        
        logger.debug("Statistics sheet created")
    
    def _create_calibration_sheet(self, wb, calibration_settings):
        """Create calibration settings sheet"""
        ws = wb.create_sheet('Calibration')
        
        # Title
        ws['A1'] = 'Calibration Settings'
        ws['A1'].font = Font(size=14, bold=True)
        
        # Threshold settings
        row = 3
        ws[f'A{row}'] = 'Sensor Thresholds'
        ws[f'A{row}'].font = Font(size=12, bold=True)
        row += 1
        
        # Headers
        ws.cell(row=row, column=1).value = 'Sensor'
        ws.cell(row=row, column=2).value = 'Threshold (lx)'
        for col in range(1, 3):
            cell = ws.cell(row=row, column=col)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')
        row += 1
        
        sensors = ['Front', 'Left', 'Back', 'Right']
        for sensor in sensors:
            ws.cell(row=row, column=1).value = sensor
            ws.cell(row=row, column=2).value = calibration_settings.get(sensor.lower(), 100.0)
            row += 1
        
        # Master sample readings
        row += 2
        ws[f'A{row}'] = 'Master Sample Reference'
        ws[f'A{row}'].font = Font(size=12, bold=True)
        row += 1
        
        master_readings = calibration_settings.get('master_readings', {})
        master_locked = calibration_settings.get('master_locked', False)
        master_date = calibration_settings.get('master_locked_date', 'Not set')
        
        ws[f'A{row}'] = 'Status:'
        ws[f'B{row}'] = 'Locked' if master_locked else 'Not Locked'
        ws[f'B{row}'].font = Font(color='006100' if master_locked else '9C0006')
        row += 1
        
        ws[f'A{row}'] = 'Last Updated:'
        ws[f'B{row}'] = master_date
        row += 2
        
        # Headers
        ws.cell(row=row, column=1).value = 'Sensor'
        ws.cell(row=row, column=2).value = 'Reference Reading (lx)'
        for col in range(1, 3):
            cell = ws.cell(row=row, column=col)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')
        row += 1
        
        for sensor in sensors:
            ws.cell(row=row, column=1).value = sensor
            reading = master_readings.get(sensor.lower())
            ws.cell(row=row, column=2).value = reading if reading is not None else 'Not set'
            row += 1
        
        # Column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 25
        
        logger.debug("Calibration sheet created")


def create_weekly_excel_report(weekly_history_file, stats_file, calibration_file):
    """
    Convenience function to generate weekly report from file paths
    
    Args:
        weekly_history_file: Path to weekly_history.json
        stats_file: Path to stats.json
        calibration_file: Path to calibration_settings.json
        
    Returns:
        str: Path to generated Excel file or None
    """
    try:
        # Load data
        weekly_data = []
        if os.path.exists(weekly_history_file):
            with open(weekly_history_file, 'r') as f:
                weekly_data = json.load(f)
        
        stats = {}
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                stats = json.load(f)
        
        calibration = {}
        if os.path.exists(calibration_file):
            with open(calibration_file, 'r') as f:
                calibration = json.load(f)
        
        # Generate report
        generator = ExcelReportGenerator()
        return generator.generate_weekly_report(weekly_data, stats, calibration)
        
    except Exception as e:
        logger.error(f"Error creating weekly Excel report: {e}", exc_info=True)
        return None
