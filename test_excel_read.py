"""
Test script to read and analyze the DEPLANT Excel file
"""
import pandas as pd
import sys

def analyze_excel(file_path):
    """Analyze an Excel file to see its structure"""
    try:
        excel_file = pd.ExcelFile(file_path)
        
        print(f"File: {file_path}")
        print(f"Number of sheets: {len(excel_file.sheet_names)}")
        print(f"Sheet names: {excel_file.sheet_names}\n")
        
        for sheet_name in excel_file.sheet_names:
            print(f"\n{'='*60}")
            print(f"Sheet: {sheet_name}")
            print('='*60)
            
            # Try different header rows
            for header_row in range(6):
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
                    
                    if df.empty:
                        continue
                    
                    print(f"\nHeader row {header_row}:")
                    print(f"  Columns ({len(df.columns)}): {list(df.columns)[:10]}")
                    print(f"  Rows: {len(df)}")
                    print(f"  First row data: {df.iloc[0].tolist()[:5] if len(df) > 0 else 'No data'}")
                    
                except Exception as e:
                    print(f"\nHeader row {header_row}: Error - {e}")
        
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == '__main__':
    # Test with the DEPLANT file
    file_path = '../sample_data/DEPLANT DEPCAP.xlsx'
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    analyze_excel(file_path)
