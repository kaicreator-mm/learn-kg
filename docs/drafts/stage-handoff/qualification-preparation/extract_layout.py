#!/usr/bin/env python3
"""Private HSK source layout investigation; never infers semantic parentage."""
import argparse, hashlib, json, os
from pathlib import Path
import fitz

def digest(b): return hashlib.sha256(b).hexdigest()
def run(pdf, out):
    raw=pdf.read_bytes();h=digest(raw)
    if h!='ec74ce0439e837bbb15154be13e747ae798903b2fd3a331629df6c3b45504941': raise ValueError('unexpected PDF byte identity')
    if out.exists(): raise ValueError('output exists; preserve prior evidence')
    os.umask(0o077);out.mkdir(parents=True,mode=0o700)
    doc=fitz.open(pdf);assert len(doc)==406
    records=[];summary=[]
    for section,pages,columns in [('TOPIC',range(56,76),3),('GRAMMAR',range(383,404),4)]:
        for page in pages:
            index=page+2;pdf_page=doc[index];tables=pdf_page.find_tables().tables
            record={'source':'RHSK01','source_sha256':h,'section':section,'printed_page':page,'pdf_index_zero_based':index,'pdf_page_box':list(pdf_page.rect),'tables':[],'status':'LAYOUT_CANDIDATE_NOT_SEMANTIC_MAPPING'}
            for table in tables:
                raw_cells=table.extract()
                assert len(raw_cells)==table.row_count==len(table.rows)
                rr=[]
                for rownum,(row,texts) in enumerate(zip(table.rows,raw_cells,strict=True)):
                    assert len(texts)==len(row.cells)==table.col_count
                    row_cells=[]
                    for colnum,(box,txt) in enumerate(zip(row.cells,texts,strict=True)):
                        row_cells.append({'row':rownum,'column':colnum,'bbox':list(box) if box is not None else None,'raw_extracted_text':txt,'state':'MERGED_OR_UNDETECTED_CELL' if box is None else 'CELL_GEOMETRY_DETECTED'})
                    rr.append(row_cells)
                record['tables'].append({'bbox':list(table.bbox),'row_count':table.row_count,'column_count':table.col_count,'rows':rr})
            record_bytes=(json.dumps(record,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
            records.append(record_bytes)
            summary.append({'printed_page':page,'pdf_index':index,'section':section,'expected_columns':columns,'tables':[{'rows':t['row_count'],'columns':t['column_count'],'missing_boxes':sum(c['bbox'] is None for r in t['rows'] for c in r)} for t in record['tables']], 'record_sha256':digest(record_bytes),'shape_status':'EXPECTED_ONE_TABLE_COLUMNS' if len(tables)==1 and tables[0].col_count==columns else 'HOLD_TABLE_SHAPE'})
    sidecar=b''.join(records);f=out/'private-layout.jsonl';f.write_bytes(sidecar)
    assert f.read_bytes()==sidecar and len(sidecar.splitlines())==41
    s={'status':'PRIVATE_LAYOUT_INVESTIGATION_ONLY','pdf_sha256':h,'pymupdf':fitz.VersionBind,'pages':summary,'total_pages':len(summary),'shape_matches':sum(p['shape_status']=='EXPECTED_ONE_TABLE_COLUMNS' for p in summary),'sidecar_bytes':len(sidecar),'sidecar_sha256':digest(sidecar),'limits':['Grid positions and extracted strings only. Missing boxes are not empty values, and never forward filled across merged cells or page breaks. No row hierarchy or semantic grammar inferred.','Private transient output; no public data export, no claim of durable backup or full visual accuracy.']}
    (out/'safe-summary.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(s,ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('pdf',type=Path);p.add_argument('out',type=Path);args=p.parse_args();run(args.pdf,args.out)
