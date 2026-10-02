"""Reproducible educational examples. All operational data below is hypothetical."""
from pathlib import Path
import json, csv, math, random, statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT=Path(__file__).parent
OUT=ROOT/'output'; OUT.mkdir(exist_ok=True)
FIG=OUT/'figures'; FIG.mkdir(exist_ok=True)
DEMAND=[420,460,500,480]
HISTORY=[380,400,390,420,410,430,440,450]
def forecasts():
    rows=[]
    smooth=HISTORY[0]
    for i,x in enumerate(HISTORY):
        if i>=3: rows.append({'period':i+1,'actual':x,'moving_average_3':sum(HISTORY[i-3:i])/3,'exponential_smoothing':smooth})
        if i>0:smooth=.3*x+.7*smooth
    return rows
def mrp():
    stock=80; rows=[]
    for i,d in enumerate(DEMAND):
        q=max(0,d+60-stock)
        rows.append(dict(week=i+1,opening=stock,demand=d,receipt=q,ending=stock+q-d,assembly_hours=.096*q,machine_hours=.12*q))
        stock=stock+q-d
    return rows
def capacity_scenarios():
    results=[]
    for hours in [40,44,48]:
        stock=80; backlog=0; made=0; stocks=[]; backs=[]
        for d in DEMAND:
            need=max(0,d+backlog+60-stock)
            q=min(need,math.floor(hours/.096))
            supply=stock+q; required=d+backlog
            shipped=min(supply,required);backlog=required-shipped;stock=supply-shipped
            made+=q;stocks.append(stock);backs.append(backlog)
        results.append(dict(weekly_assembly_hours=hours,produced=made,ending_inventory=stock,ending_backlog=backlog,backlog_by_week=backs,inventory_by_week=stocks))
    return results

def monte_carlo(replications=2000,seed=20261002):
    rng=random.Random(seed)
    draws=[[(max(0,round(rng.gauss(465,40))),max(0,rng.gauss(0,3))) for _ in range(4)] for _ in range(replications)]
    results=[]
    for base in [40,44,48]:
        costs=[];backlogs=[];served=0
        for trace in draws:
            stock=80;backlog=0;cost=4*(base-40)*80
            for demand,loss in trace:
                available=max(0,base-loss)
                need=max(0,demand+backlog+60-stock)
                made=min(need,math.floor(available/.096))
                supply=stock+made;required=demand+backlog
                shipped=min(required,supply);backlog=required-shipped;stock=supply-shipped
                cost+=2*stock+20*backlog
            costs.append(cost);backlogs.append(backlog);served+=backlog==0
        ordered=sorted(backlogs)
        results.append(dict(hours=base,mean_end_backlog=statistics.mean(backlogs),p90_end_backlog=ordered[math.ceil(.9*len(ordered))-1],probability_zero_end_backlog=served/replications,mean_cost_units=statistics.mean(costs)))
    return results

def savefig(name):
    plt.savefig(FIG/name,dpi=180,bbox_inches='tight');plt.close()

def flow(name,nodes,edges):
    fig,ax=plt.subplots(figsize=(7,5));ax.set_xlim(0,10);ax.set_ylim(0,10);ax.axis('off')
    coords={}
    for key,label,x,y in nodes:
        coords[key]=(x,y)
        ax.add_patch(FancyBboxPatch((x-1.35,y-.48),2.7,.96,boxstyle='round,pad=.10',facecolor='#eff3f6',edgecolor='#677989'))
        ax.text(x,y,label,ha='center',va='center',fontsize=9,wrap=True)
    for start,end,label in edges:
        x1,y1=coords[start];x2,y2=coords[end]
        if x1 == x2:
            a,b=(x1,y1-.58),(x2,y2+.58)
            if label: ax.text(x1+.35,(y1+y2)/2,label,fontsize=8)
        elif y1 == y2:
            a,b=(x1-1.45,y1),(x2+1.45,y2)
            if label: ax.text((a[0]+b[0])/2,y1+.28,label,fontsize=8,ha='center')
        else:
            a,b=(x1,y1+.58),(x2-1.45,y2)
            ax.plot([a[0],a[0]],[a[1],y2],color='#475569',lw=1)
            a=(a[0],y2)
        ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=13,color='#475569'))
    fig.tight_layout();savefig(name)

def create_figures():
    flow('pp_process.png',[
      ('d','Demand review\nand approved PIR',5,9),('m','MRP and material\nexception review',5,7),
      ('c','Capacity review\nand scheduling',5,5),('o','Production order\nrelease and execution',5,3),('r','Receipt and\nperformance review',5,1),
      ('e','Revise dates\nor supply plan',1.55,5)],
      [('d','m',''),('m','c',''),('c','o','Feasible'),('c','e','Overload'),('e','m',''),('o','r','')])
    flow('change.png',[
      ('a','Assess work\nand stakeholder impact',5,9),('b','Co-design process\nand readiness criteria',5,7),('c','Train and test\nwith representative cases',5,5),('d','Pilot and review\nreadiness evidence',5,3),('e','Adopt and monitor\nwith named owners',5,1),('f','Resolve gaps\nand repeat pilot',1.55,3)],
      [('a','b',''),('b','c',''),('c','d',''),('d','e','Pass'),('d','f','Gap'),('f','c','')])
    rows=mrp();plt.figure(figsize=(7,3.8));plt.plot(range(1,5),[r['assembly_hours'] for r in rows],marker='o',label='Required assembly hours');plt.axhline(40,color='#ba4a4a',ls='--',label='Baseline available 40 hours');plt.axhline(48,color='#377f62',ls=':',label='Alternative available 48 hours');plt.xticks(range(1,5));plt.xlabel('Week');plt.ylabel('Hours');plt.title('Hypothetical capacity comparison');plt.legend(fontsize=8);plt.grid(alpha=.2);savefig('capacity.png')
    plt.figure(figsize=(7,3.6));plt.plot(range(1,9),HISTORY,marker='o',label='Hypothetical actual demand');plt.plot(range(4,9),[r['moving_average_3'] for r in forecasts()],marker='s',label='Three period moving average');plt.plot(range(4,9),[r['exponential_smoothing'] for r in forecasts()],marker='^',label='Exponential smoothing alpha 0.3');plt.xlabel('Period');plt.ylabel('Units');plt.title('Rolling one period forecast comparison');plt.legend(fontsize=8);plt.grid(alpha=.2);savefig('forecast.png')
    fig,ax=plt.subplots(figsize=(7,3.6));jobs=[('A lot 1 machining',0,3),('A lot 1 assembly',3,2),('B lot 1 machining',3,4),('B lot 1 assembly',7,3),('A lot 2 machining',7,3),('A lot 2 assembly',10,2)]
    for i,(label,start,dur) in enumerate(jobs):ax.barh(i,dur,left=start,color='#59768d' if 'machining' in label else '#70967e')
    ax.set_yticks(range(len(jobs)),[j[0] for j in jobs],fontsize=8);ax.invert_yaxis();ax.set_xlabel('Elapsed working hours');ax.set_title('Hypothetical finite schedule with precedence');ax.grid(axis='x',alpha=.2);savefig('gantt.png')
    plt.figure(figsize=(7,3.6));plt.plot(range(1,7),[390,420,430,440,470,480],marker='o',label='Good output');plt.plot(range(1,7),[420,460,500,480,490,500],marker='s',label='Period demand');plt.title('Hypothetical post implementation performance');plt.xlabel('Review period');plt.ylabel('Units');plt.legend(fontsize=8);plt.grid(alpha=.2);savefig('improvement.png')

def main():
    forecast=forecasts(); fr=[]
    for model in ['moving_average_3','exponential_smoothing']:
        errors=[r['actual']-r[model] for r in forecast]
        fr.append(dict(model=model,mae=sum(abs(e) for e in errors)/len(errors),bias=sum(errors)/len(errors),next_forecast=(sum(HISTORY[-3:])/3 if model=='moving_average_3' else .3*HISTORY[-1]+.7*forecast[-1]['exponential_smoothing'])))
    data=dict(disclaimer='All operational observations are hypothetical educational data; these are external Python calculations, not executed SAP transactions.',history=HISTORY,demand=DEMAND,mrp=mrp(),forecast=forecast,forecast_metrics=fr,capacity=capacity_scenarios(),monte_carlo=monte_carlo())
    (OUT/'analysis_results.json').write_text(json.dumps(data,indent=2))
    create_figures()
    print(json.dumps({'forecast_metrics':fr,'capacity':data['capacity'],'monte_carlo':data['monte_carlo']},indent=2))
if __name__=='__main__':main()
