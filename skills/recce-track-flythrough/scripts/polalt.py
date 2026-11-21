import json,sys,subprocess
an=json.load(open(sys.argv[1])); out=sys.argv[2]; r=an['res']
S=json.load(open('userstd.json')); S['exc_dig_m3hr']=round(1200/35.32,1)
secs=[{"from":a,"to":b,"type":t,"width_ft":14,"thick_in":0,"lead_km":0,"loader":"Excavator","grader":False,"level":True} for a,b,t in an['secs'] if t!='road']
rock=r['bench_m3']+r['grade_m3']
nx=an['xing']; major=sum(1 for x in nx if x[1]>5); med=sum(1 for x in nx if 1<x[1]<=5)
exc=[{"desc":"Rock cutting (grade reduction / bench)","nos":1,"len":1000,"top":4.27,"bot":4.27,"depth":round(rock/1000/4.27,3),"unit":"m","mach":"Excavator"}]
other=[{"name":"Dozer – dozing / disposal of cut rock","hrs":round(rock/95),"lph":27,"rem":""}]
for fleet,fbt,sc,civ,tag in [(1,2,8,4,'1'),(2,4,10,5,'F')]:
    p={"sections":secs,"exc":exc,"other":other,"veh":{"fbt_trips":fbt,"fbt_km":300,"sc_trips":sc,"sc_km":200,"dc_trips":4,"dc_km":200,"civ_trips":civ,"civ_km":150},"S":S}
    json.dump(p,open(f'proj_{out}_{tag}.json','w'))
    o=subprocess.run(['node','polrun.js',f'proj_{out}_{tag}.json',f'pol_{out}_{tag}.json'],capture_output=True,text=True).stdout
    print(tag,o.splitlines()[0])
    R=json.load(open(f'pol_{out}_{tag}.json')); exh=sum(x['q'] for x in R['rows'] if x['g']=='exc'); dz=sum(x['q'] for x in R['rows'] if x['d'].startswith('Dozer'))
    print('   exc hrs',exh,'dozer hrs',dz,'days 1+1',max(exh,dz)/8, 'days 1exc+2doz', max(exh/8,dz/16),'rock',round(rock),'major nx',major,'med',med)
