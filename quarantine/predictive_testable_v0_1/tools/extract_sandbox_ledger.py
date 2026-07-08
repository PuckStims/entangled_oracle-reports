import os
import glob
import csv
from bs4 import BeautifulSoup

def extract_windows_to_csv(output_dir, csv_path):
    html_files = glob.glob(os.path.join(output_dir, '*predictive_sandbox*.html'))
    
    headers = [
        "Report Subject",
        "Window ID",
        "Start",
        "Peak",
        "End",
        "Total Intensity",
        "Prominence",
        "Nearby Historical Event or Chapter",
        "Temporal Match Status",
        "Evidence Source",
        "Evidence Tier",
        "Structural Role / Gradient",
        "Interpretive Tags",
        "Statistical Inclusion",
        "Validation Status",
        "Research Notes"
    ]
    
    rows = []
    
    for filepath in html_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            
        title_tag = soup.find('title')
        if title_tag:
            # "Predictive Sandbox · Querent Name"
            title_text = title_tag.text
            subject = title_text.split('·')[-1].strip() if '·' in title_text else title_text
        else:
            subject = os.path.basename(filepath)
            
        windows_section = soup.find('div', id='windows')
        if not windows_section:
            continue
            
        tables = windows_section.find_all('table')
        if not tables:
            continue
            
        windows_table = tables[0]
        tbody = windows_table.find('tbody')
        if not tbody:
            continue
            
        for tr in tbody.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) < 18:
                continue
                
            window_id = tds[0].text.strip()
            start = tds[1].text.strip()
            peak = tds[2].text.strip()
            end = tds[3].text.strip()
            
            # total intensity is index 6
            total_intensity = tds[6].text.strip()
            # prominence is index 7
            prominence = tds[7].text.strip()
            # gradient is index 8
            gradient = tds[8].text.strip()
            # semantic state is index 11
            semantic_state = tds[11].text.strip()
            
            # structural role combination
            structural_role = f"{gradient} / {semantic_state}" if semantic_state and semantic_state != '—' else gradient
            
            # tags is index 17
            tags = tds[17].text.strip()
            
            row = {
                "Report Subject": subject,
                "Window ID": window_id,
                "Start": start,
                "Peak": peak,
                "End": end,
                "Total Intensity": total_intensity,
                "Prominence": prominence,
                "Nearby Historical Event or Chapter": "",
                "Temporal Match Status": "",
                "Evidence Source": "",
                "Evidence Tier": "",
                "Structural Role / Gradient": structural_role,
                "Interpretive Tags": tags,
                "Statistical Inclusion": "",
                "Validation Status": "",
                "Research Notes": ""
            }
            rows.append(row)
            
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Extraction complete! Saved {len(rows)} windows to {csv_path}")

if __name__ == '__main__':
    OUTPUT_DIR = "C:/entangled_oracle/output"
    CSV_PATH = "C:/entangled_oracle/output/Retrospective_Validation_Ledger.csv"
    extract_windows_to_csv(OUTPUT_DIR, CSV_PATH)
