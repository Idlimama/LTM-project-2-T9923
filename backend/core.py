import sqlite3, json, math, re, uuid, random, hashlib
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DB=ROOT/'edge_support.db'
PROFILES={
 'AI4I-LINE-01':{'name':'AI4I Production Line','family':'Predictive maintenance','type':'Predictive','model':'DemoRiskModel 1.2','state':'ACTIVE','fields':['air_temp_K','process_temp_K','rpm','torque_Nm','tool_wear_min']},
 'CNC-400':{'name':'CNC-400 Machining Centre','family':'CNC','type':'Rule / manual','model':'NoModel','state':'ACTIVE','fields':['spindle_temp_C','vibration_mm_s','error_code']},
 'PUMP-PX20':{'name':'PX-20 Process Pump','family':'Fluid handling','type':'Repair guide','model':'NoModel','state':'ACTIVE','fields':['pressure_bar','flow_L_min','error_code']},
 'HVAC-AHU7':{'name':'AHU-7 Air Handler','family':'HVAC','type':'Rule / manual','model':'NoModel','state':'ACTIVE','fields':['supply_temp_C','return_temp_C','filter_dp_Pa']}}
DOCS=[
 ('AI4I-LINE-01','AI4I Operations Handbook','DEMO-1','p. 7','Tool wear','tool wear elevated inspection replace tool wear threshold maintenance'),
 ('AI4I-LINE-01','AI4I Operations Handbook','DEMO-1','p. 4','Thermal condition','process temperature air temperature cooling load inspect thermal difference'),
 ('AI4I-LINE-01','AI4I Operations Handbook','DEMO-1','p. 9','Torque and speed','high torque low rotational speed inspect drive load power condition'),
 ('CNC-400','CNC-400 Service Manual','DEMO-2','p. 12','E104 spindle overtemperature','E104 spindle temperature high stop isolate ventilation qualified maintenance'),
 ('CNC-400','CNC-400 Service Manual','DEMO-2','p. 18','Abnormal vibration','vibration mounting alignment tool condition bearings keep stopped'),
 ('CNC-400','CNC-400 Service Manual','DEMO-2','p. 23','E211 lubrication','E211 lubrication pressure inspect reservoir line qualified technician'),
 ('PUMP-PX20','PX-20 Repair Guide','DEMO-1','Step 3','Low flow','low flow normal pressure inlet strainer inspect obstruction'),
 ('PUMP-PX20','PX-20 Repair Guide','DEMO-1','Step 5','High pressure','high pressure stop isolate discharge obstruction valve'),
 ('PUMP-PX20','PX-20 Repair Guide','DEMO-1','Step 7','Seal leakage','seal leakage isolate spill control qualified technician'),
 ('HVAC-AHU7','AHU-7 Maintenance Manual','DEMO-3','p. 16','Filter differential pressure','filter differential pressure high replace inspect airflow'),
 ('HVAC-AHU7','AHU-7 Maintenance Manual','DEMO-3','p. 21','Temperature split','supply return temperature inspect coil controls sensor'),
]
DOC_ROWS=[{'id':f'DOC-{i+1:03}','profile':x[0],'title':x[1],'revision':x[2],'location':x[3],'section':x[4],'text':x[5],'source_status':'SYNTHETIC REVIEWED','index_status':'READY'} for i,x in enumerate(DOCS)]
def connect():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
 c.executescript('''CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY,created TEXT,profile TEXT,inputs TEXT,safety TEXT,prediction TEXT,evidence TEXT,disposition TEXT DEFAULT 'UNREVIEWED');CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,timestamp TEXT,event TEXT,entity TEXT,severity TEXT,details TEXT);CREATE TABLE IF NOT EXISTS uploads(id TEXT PRIMARY KEY,filename TEXT,size INTEGER,sha256 TEXT,status TEXT,created TEXT);''');c.commit();return c
def audit(event,entity,severity='INFO',details=None):
 with connect() as c:c.execute('INSERT INTO audit(timestamp,event,entity,severity,details) VALUES(?,?,?,?,?)',(datetime.now().isoformat(timespec='seconds'),event,entity,severity,json.dumps(details or {})))
def seed():
 with connect() as c:
  if c.execute('SELECT COUNT(*) FROM cases').fetchone()[0]:return
  rng=random.Random(42);start=datetime.now()-timedelta(days=30)
  for i in range(180):
   pid=list(PROFILES)[i%4];status=rng.choices(['SAFE_TO_EVALUATE','WARNING','STOP_AND_ESCALATE'],[.68,.24,.08])[0];cid=f'SEED-{i+1:04}';created=(start+timedelta(hours=i*4)).isoformat(timespec='seconds');pred={'label':'NO FAILURE INDICATED','probability':round(rng.uniform(.03,.42),3),'model':'SYNTHETIC'} if pid=='AI4I-LINE-01' and status!='STOP_AND_ESCALATE' else None
   c.execute('INSERT INTO cases VALUES(?,?,?,?,?,?,?,?)',(cid,created,pid,json.dumps({'synthetic':True,'sample':i+1}),status,json.dumps(pred),json.dumps([]),rng.choice(['UNREVIEWED','MONITOR','ESCALATED','CLOSED'])))
  for i in range(36):
   c.execute('INSERT INTO audit(timestamp,event,entity,severity,details) VALUES(?,?,?,?,?)',((start+timedelta(hours=i*18)).isoformat(timespec='seconds'),rng.choice(['PROFILE_ACTIVATED','INDEX_VERIFIED','DIAGNOSIS_COMPLETED','EXPORT_CREATED']),f'OBJ-{i+1:03}',rng.choice(['INFO','INFO','WARNING']),json.dumps({'synthetic_seed':True})))
  c.commit()
def toks(s):return re.findall(r'[a-z0-9]+',str(s).lower())
def retrieve(pid,q,top=3):
 a=Counter(toks(q));out=[]
 for d in DOC_ROWS:
  if d['profile']!=pid:continue
  b=Counter(toks(d['section']+' '+d['text']));den=math.sqrt(sum(v*v for v in a.values())*sum(v*v for v in b.values())) or 1;score=sum(a[k]*b[k] for k in a)/den
  if score>0.04:out.append(d|{'score':round(score,3)})
 return sorted(out,key=lambda x:x['score'],reverse=True)[:top]
def diagnose(pid,data,notes):
 def num(k):
  try:return float(data.get(k,''))
  except:return None
 nums=[k for k in PROFILES[pid]['fields'] if k!='error_code']
 if any(str(data.get(k,'')).strip()=='' for k in nums):return 'INSUFFICIENT_INFORMATION',[{'severity':'ERROR','finding':'Required reading missing','action':'Enter all required readings.'}],None,[]
 if any(num(k) is None for k in nums):return 'INVALID_INPUT',[{'severity':'ERROR','finding':'Invalid numeric reading','action':'Correct the highlighted value.'}],None,[]
 status='SAFE_TO_EVALUATE';f=[];pred=None
 if pid=='AI4I-LINE-01':
  air,proc,rpm,tq,wear=[num(k) for k in PROFILES[pid]['fields']]
  if wear>=240:status='STOP_AND_ESCALATE';f.append({'severity':'CRITICAL','finding':'Prototype critical tool-wear threshold reached','action':'Stop and request qualified review.'})
  elif wear>=180:status='WARNING';f.append({'severity':'WARNING','finding':'Elevated tool wear','action':'Schedule tool inspection.'})
  if proc-air>15 and status!='STOP_AND_ESCALATE':status='WARNING';f.append({'severity':'WARNING','finding':'High process-to-air temperature difference','action':'Inspect cooling and load.'})
  if status!='STOP_AND_ESCALATE':
   risk=max(.01,min(.98,.025+max(0,wear-90)/290+max(0,tq-45)/100+max(0,1450-rpm)/2600+max(0,proc-air-10)/70));pred={'label':'FAILURE RISK' if risk>=.5 else 'NO FAILURE INDICATED','probability':round(risk,3),'backend':'DemoRiskModel 1.2','disclosure':'Synthetic transparent heuristic'}
 elif pid=='CNC-400':
  t,v=num('spindle_temp_C'),num('vibration_mm_s');code=str(data.get('error_code','')).upper()
  if t>=90 or code=='E104':status='STOP_AND_ESCALATE';f.append({'severity':'CRITICAL','finding':'E104 or high spindle temperature','action':'Stop, isolate and escalate.'})
  elif v>=8:status='WARNING';f.append({'severity':'WARNING','finding':'Abnormal vibration','action':'Keep stopped and inspect alignment.'})
 elif pid=='PUMP-PX20':
  p,flow=num('pressure_bar'),num('flow_L_min')
  if p>=12:status='STOP_AND_ESCALATE';f.append({'severity':'CRITICAL','finding':'Prototype over-pressure stop','action':'Stop and isolate.'})
  elif flow<20:status='WARNING';f.append({'severity':'WARNING','finding':'Low flow','action':'Review low-flow guide.'})
 else:
  dp=num('filter_dp_Pa');delta=num('return_temp_C')-num('supply_temp_C')
  if dp>=450:status='WARNING';f.append({'severity':'WARNING','finding':'High filter differential pressure','action':'Inspect filter and airflow.'})
  if delta<4:status='WARNING';f.append({'severity':'WARNING','finding':'Low temperature split','action':'Inspect coil, controls and sensors.'})
 if not f:f=[{'severity':'INFO','finding':'No deterministic warning rule triggered','action':'Review evidence and record disposition.'}]
 q=notes+' '+str(data.get('error_code',''))+' '+' '.join(x['finding'] for x in f);ev=retrieve(pid,q)
 return status,f,pred,ev
def save_case(pid,data,status,pred,ev):
 cid='CASE-'+uuid.uuid4().hex[:10].upper();now=datetime.now().isoformat(timespec='seconds')
 with connect() as c:c.execute('INSERT INTO cases(id,created,profile,inputs,safety,prediction,evidence) VALUES(?,?,?,?,?,?,?)',(cid,now,pid,json.dumps(data),status,json.dumps(pred),json.dumps(ev)))
 audit('DIAGNOSIS_COMPLETED',cid,'CRITICAL' if status=='STOP_AND_ESCALATE' else 'INFO',{'profile':pid,'safety':status});return cid
def register_upload(name,blob):
 uid='UPL-'+uuid.uuid4().hex[:8].upper();h=hashlib.sha256(blob).hexdigest()
 with connect() as c:c.execute('INSERT INTO uploads VALUES(?,?,?,?,?,?)',(uid,name,len(blob),h,'REQUIRES_REVIEW',datetime.now().isoformat(timespec='seconds')))
 audit('DOCUMENT_STAGED',uid,'INFO',{'filename':name,'bytes':len(blob)});return uid,h
seed()
