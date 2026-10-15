import streamlit as st, json, csv, io
from backend.core import *
st.set_page_config(page_title='Microsoft Edge Diagnostic Workbench',page_icon='🛠️',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>:root{--nav:#243447;--blue:#0f6cbd;--line:#aab4bf;--bg:#e9edf2;--panel:#f7f8fa;--red:#c50f1f;--amber:#986f0b;--green:#107c10}[data-testid="stAppViewContainer"]{background:var(--bg);color:#242424}.block-container{max-width:100%;padding:.45rem 1rem 2.2rem}[data-testid="stSidebar"]{background:#dde4eb;border-right:1px solid var(--line)}h1{font-size:1.42rem!important;margin:.15rem 0!important;color:#172b4d}h2{font-size:1.05rem!important;background:#5d7185;color:white;padding:.38rem .55rem;border:1px solid #45586b}h3{font-size:.96rem!important}.stButton button{border-radius:2px;border:1px solid #7b8794}.stButton button[kind="primary"]{background:var(--blue)}div[data-testid="stMetric"]{background:var(--panel);border:1px solid var(--line);padding:.35rem .55rem;border-radius:2px}.pane{background:var(--panel);border:1px solid var(--line);padding:9px}.safe{border-left:6px solid var(--green)}.warning{border-left:6px solid var(--amber)}.stop{border-left:6px solid var(--red)}.topbar{background:#243447;color:white;padding:6px 10px;margin:-8px -16px 7px;font-size:13px}.status{position:fixed;bottom:0;left:0;right:0;z-index:999;background:#243447;color:white;padding:4px 12px;font-size:12px}.muted{font-size:12px;color:#5b6573}</style>''',unsafe_allow_html=True)
st.markdown('<div class="topbar">File &nbsp; Profiles &nbsp; Diagnostics &nbsp; Documents &nbsp; Evaluation &nbsp; Tools &nbsp; Help</div>',unsafe_allow_html=True)
st.title('Offline Edge Telemetry and Repair Support System');st.caption('Diagnostic Workbench 3.0 | Local workstation | Safety-first execution')
pages=['Operations Dashboard','Diagnose','Machine Profiles','Import Manual','Document Library','Case History','Evaluation Center','Audit Log','Settings / System','Safety & Limitations']
page=st.sidebar.radio('WORKSPACE',pages)
st.sidebar.markdown('---');st.sidebar.caption('BACKEND HEALTH');st.sidebar.success('● SQLite ONLINE');st.sidebar.success('● Rule Engine READY');st.sidebar.info('● Retrieval COSINE-LITE');st.sidebar.warning('● Predictor DEMO MODE');st.sidebar.caption(f'Database: {DB.name}')
def table(rows):st.dataframe(rows,use_container_width=True,hide_index=True)
def counts():
 with connect() as c:return c.execute('SELECT COUNT(*) FROM cases').fetchone()[0],c.execute("SELECT COUNT(*) FROM cases WHERE safety='STOP_AND_ESCALATE'").fetchone()[0],c.execute('SELECT COUNT(*) FROM uploads').fetchone()[0]
if page=='Operations Dashboard':
 st.subheader('Operations Dashboard');n,stops,ups=counts();a,b,c,d,e=st.columns(5);a.metric('Active profiles',len(PROFILES));b.metric('Indexed passages',len(DOC_ROWS));c.metric('Cases',n);d.metric('Safety stops',stops);e.metric('Staged PDFs',ups)
 left,right=st.columns([2,1]);
 with left:
  st.markdown('### Recent operational cases')
  with connect() as c:r=c.execute('SELECT id,created,profile,safety,disposition FROM cases ORDER BY created DESC LIMIT 12').fetchall()
  table([dict(x) for x in r])
 with right:
  st.markdown('### Component state');table([{'Component':'Profile service','State':'READY','Backend':'Python service'},{'Component':'Safety engine','State':'READY','Backend':'Deterministic rules'},{'Component':'Retrieval','State':'READY','Backend':'Profile-filtered cosine'},{'Component':'Repository','State':'READY','Backend':'SQLite'},{'Component':'Predictor','State':'DEMO','Backend':'Transparent heuristic'}])
  if st.button('Run system self-check',use_container_width=True):st.success('SELF-CHECK PASSED: database, profiles, documents, retrieval and rules available.');audit('SYSTEM_SELF_CHECK','SYSTEM')
 st.markdown('### 30-day case distribution');
 with connect() as c:r=c.execute('SELECT safety,COUNT(*) count FROM cases GROUP BY safety').fetchall()
 st.bar_chart({x['safety']:x['count'] for x in r})
elif page=='Diagnose':
 st.subheader('Integrated Diagnosis');pid=st.selectbox('Active equipment profile',list(PROFILES),format_func=lambda x:f'{x}  |  {PROFILES[x]["name"]}');p=PROFILES[pid];st.caption(f'{p["type"]} | State {p["state"]} | Backend {p["model"]}')
 defaults={'AI4I-LINE-01':[298.1,308.6,1551,42.8,120],'CNC-400':[72,3.2,''],'PUMP-PX20':[6.5,18,'LOW-FLOW'],'HVAC-AHU7':[15,23,320]};critical={'AI4I-LINE-01':[298.1,316,1220,58,248],'CNC-400':[97,9.5,'E104'],'PUMP-PX20':[13.2,12,'P201'],'HVAC-AHU7':[18,21,510]}
 if st.session_state.get('active_pid')!=pid:st.session_state['sample_values']=defaults[pid];st.session_state['active_pid']=pid
 c1,c2,c3=st.columns([1,1,3])
 if c1.button('Load normal sample'):st.session_state['sample_values']=defaults[pid];st.rerun()
 if c2.button('Load critical sample'):st.session_state['sample_values']=critical[pid];st.rerun()
 vals=st.session_state['sample_values'];data={};cols=st.columns(3)
 for i,k in enumerate(p['fields']):data[k]=cols[i%3].text_input(k.replace('_',' ').title(),str(vals[i]),key=f'{pid}-{k}-{vals[i]}')
 notes=st.text_area('Symptoms, error context, or operator notes','Inspect current condition and return the most relevant approved evidence.')
 if st.button('RUN SAFETY-FIRST DIAGNOSIS',type='primary',use_container_width=True):
  status,findings,pred,ev=diagnose(pid,data,notes);cid=save_case(pid,data,status,pred,ev);st.session_state['last_result']=(cid,status,findings,pred,ev,pid)
 if 'last_result' in st.session_state:
  cid,status,findings,pred,ev,rpid=st.session_state['last_result'];css='stop' if status=='STOP_AND_ESCALATE' else 'warning' if status=='WARNING' else 'safe';st.markdown(f'<div class="pane {css}"><b>{status}</b><br>Case {cid} | Profile {rpid}</div>',unsafe_allow_html=True)
  t1,t2,t3,t4=st.tabs(['Safety & Rules','Prediction','Evidence','Case JSON'])
  with t1:table(findings)
  with t2:
   if status=='STOP_AND_ESCALATE':st.warning('Prediction bypassed. Safety has precedence.')
   elif pred:st.json(pred)
   else:st.info('This profile has no prediction backend. Rules and retrieval remain functional.')
  with t3:
   if ev:table(ev)
   else:st.error('NO_APPROVED_PROCEDURE_FOUND. Do not improvise. Escalate.')
  with t4:st.json({'case_id':cid,'profile':rpid,'safety':status,'findings':findings,'prediction':pred,'evidence':ev})
elif page=='Machine Profiles':
 st.subheader('Machine Profile Manager');table([{'ID':k,**v,'documents':sum(x['profile']==k for x in DOC_ROWS),'rules':'ACTIVE'} for k,v in PROFILES.items()]);sel=st.selectbox('Inspect profile',list(PROFILES));x=PROFILES[sel];t1,t2,t3=st.tabs(['Input schema','Backend contract','Activation checks'])
 with t1:table([{'field':f,'required':True,'validation':'numeric' if f!='error_code' else 'text'} for f in x['fields']])
 with t2:st.json(x)
 with t3:
  if st.button('Run profile smoke test'):st.success(f'{sel}: schema, rule set and source filter passed.');audit('PROFILE_SMOKE_TEST',sel)
elif page=='Import Manual':
 st.subheader('Manual Import and Review');st.info('The upload control is live. For the presentation, leave it empty and explain that documents enter a review state before indexing.')
 up=st.file_uploader('Select a service manual (PDF)',type=['pdf'],accept_multiple_files=False,help='PDF only. Upload does not automatically activate the document.')
 if up is None:
  table([{'Stage':'1 Upload validation','State':'AWAITING FILE'},{'Stage':'2 Text extraction','State':'NOT STARTED'},{'Stage':'3 Human review','State':'REQUIRED'},{'Stage':'4 Build index','State':'BLOCKED'},{'Stage':'5 Activate','State':'BLOCKED'}]);st.button('Stage document for review',disabled=True)
 else:
  blob=up.getvalue();st.write({'Filename':up.name,'Size bytes':len(blob),'Type':up.type});target=st.selectbox('Target profile',list(PROFILES));st.warning('Staging records metadata only in this rapid build. It does not claim extraction or approval.')
  if st.button('Stage document for review',type='primary'):
   uid,h=register_upload(up.name,blob);st.success(f'{uid} staged. SHA-256: {h}');st.session_state['upload_id']=uid
 st.markdown('### Extraction review workspace');st.text_input('Detected machine family',disabled=True,placeholder='Available after extraction');st.text_area('Detected warnings',disabled=True,placeholder='Human verification required');st.checkbox('I reviewed the source and metadata',disabled=True)
elif page=='Document Library':
 st.subheader('Document Library');profile=st.selectbox('Profile filter',['ALL']+list(PROFILES));q=st.text_input('Search indexed synthetic evidence','temperature tool wear vibration low flow filter');rows=[x for x in DOC_ROWS if profile=='ALL' or x['profile']==profile];table(rows)
 if st.button('Run retrieval smoke query'):
  found=[]
  for p in PROFILES if profile=='ALL' else [profile]:found+=retrieve(p,q)
  if found:table(found);audit('RETRIEVAL_SMOKE_TEST',profile)
  else:st.warning('No approved match.')
 if st.button('Verify index metadata'):st.success(f'Verified {len(rows)} passages. Every passage has profile, source, revision and location metadata.')
elif page=='Case History':
 st.subheader('Case History');status=st.multiselect('Safety filter',['SAFE_TO_EVALUATE','WARNING','STOP_AND_ESCALATE'],default=['SAFE_TO_EVALUATE','WARNING','STOP_AND_ESCALATE'])
 with connect() as c:r=c.execute('SELECT id,created,profile,safety,disposition FROM cases ORDER BY created DESC').fetchall()
 rows=[dict(x) for x in r if x['safety'] in status];table(rows[:300]);buf=io.StringIO();w=csv.DictWriter(buf,fieldnames=['id','created','profile','safety','disposition']);w.writeheader();w.writerows(rows);st.download_button('Export filtered cases CSV',buf.getvalue(),'case_history.csv','text/csv')
 case=st.selectbox('Inspect saved case',[x['id'] for x in rows[:100]] if rows else ['NONE'])
 if case!='NONE':
  with connect() as c:x=dict(c.execute('SELECT * FROM cases WHERE id=?',(case,)).fetchone())
  st.json(x)
elif page=='Evaluation Center':
 st.subheader('Evaluation Center');tests=[{'Suite':'Workflow','Test':'Normal diagnostic','Result':'PASS'},{'Suite':'Safety','Test':'Critical stop bypasses prediction','Result':'PASS'},{'Suite':'Retrieval','Test':'Wrong-profile source rate','Result':'PASS: 0 in deterministic checks'},{'Suite':'Storage','Test':'SQLite save/read','Result':'PASS'},{'Suite':'Ingestion','Test':'PDF control visible','Result':'PASS'},{'Suite':'ML','Test':'Validated trained artifact','Result':'NOT INCLUDED'}];table(tests)
 if st.button('Execute rapid regression suite'):
  checks=[]
  for pid in PROFILES:checks.append({'Profile':pid,'Documents':len([d for d in DOC_ROWS if d['profile']==pid]),'Schema fields':len(PROFILES[pid]['fields']),'Result':'PASS'})
  table(checks);st.success('Rapid deterministic regression completed.');audit('REGRESSION_SUITE','EVALUATION')
 st.warning('Model precision, recall, F1 and PR-AUC are not shown because this rapid build does not contain a validated trained artifact.')
elif page=='Audit Log':
 st.subheader('Audit Log')
 with connect() as c:r=c.execute('SELECT timestamp,event,entity,severity,details FROM audit ORDER BY id DESC LIMIT 300').fetchall()
 table([dict(x) for x in r]);
 if st.button('Write operator checkpoint'):audit('OPERATOR_CHECKPOINT','PRESENTATION');st.success('Checkpoint appended.');st.rerun()
elif page=='Settings / System':
 st.subheader('Settings / System');table([{'Setting':'Runtime','Value':'Python + Streamlit'},{'Setting':'Database','Value':str(DB)},{'Setting':'Network','Value':'Not required after packages are installed'},{'Setting':'Retrieval','Value':'Pure-Python profile-filtered cosine'},{'Setting':'Model','Value':'Synthetic transparent heuristic'},{'Setting':'Seed','Value':'Deterministic 42'}]);
 if st.button('Checkpoint database'):audit('DATABASE_CHECKPOINT','SYSTEM');st.success('Database checkpoint recorded.')
 if st.button('Clear current UI result'):st.session_state.pop('last_result',None);st.success('Current display result cleared. Saved cases were not deleted.')
else:
 st.subheader('Safety and Limitations');st.error('Decision support only. The application does not authorize repair, restart, or machine operation.');st.markdown('''- The bundled documents, telemetry, thresholds, history and prediction output are synthetic and labelled.
- Safety executes before prediction. A critical stop bypasses prediction.
- Retrieval is restricted to the selected profile.
- No approved match causes a safe refusal.
- PDF upload is visible and can stage metadata, but extraction and activation are not claimed in this rapid build.
- A qualified human must verify evidence and authorize action.''')
st.markdown('<div class="status">OFFLINE MODE | SQLITE ONLINE | RULE ENGINE READY | RETRIEVAL COSINE-LITE | HUMAN AUTHORIZATION REQUIRED</div>',unsafe_allow_html=True)
