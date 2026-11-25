import json; from geo import R
M={t['name']:t for t in json.load(open(f'{R}/work/metrics.json'))['tracks']}; MC=json.load(open(f'{R}/work/mcda.json')); P=json.load(open(f'{R}/work/pol.json'))
T=dict(zip(MC['ids'],MC['total'])); D={'T1':'Direct climb - S spur','T2':'Graded S spur 1:7','T3':'W spur/ ridge','T4':'E flank','T5':'Rear/ N foothill'}
t4,t5,t1=M['T4'],M['T5'],M['T1']
rows='\n'.join(f"| {k} | {D[k]} | {m['new_const_m']/1000:.2f} | {m['max_grade_pct']:.1f} | {m['pct_gt_1in10']:.0f} | {m['pct_gt_1in5']:.0f} | {m['hairpins']} | {m['nala_xings']} | {m['cut_m3']:,.0f} | {m['expo_dominating_pct']:.0f} / {m['expo_plain_road_pct']:.0f} | {P[k]['total']:,} | {P[k]['dur']} | {T[k]:.2f} |" for k,m in M.items())
pr='\n'.join(f"| {c} | {r['d']} | {r['au']} | {r['q']:,} | {r['rate']} | {r['l']:,} | {r['rm']} |" for c,r in zip('abcdefg',P['T5']['rows']))
md=f"""**<u>Anx A</u>**

**<u>RECCE REPORT - TR TO KHABRI-1 HILL POST (RL 133) - SELECTION OF ALN</u>**

1. **<u>Gen</u>**. **Khabri-1 hill post** (25°25'38.6"N 63°26'23.2"E, RL 133 m) is located on the SW nose of **Taloband Rg**, above the **Shadi Kaur**. An existing tr runs from **CHW** to the foot of the old climb at CH 3.92 km. A new tr CH 3.92 - 5.23 km and a kacha tr CH 5.23 - 5.92 km have been planned to the plain pad (KMZ Opt 1 rev). In continuation, a desk study (terrain analysis) of all feasible alns from the existing/ planned tr to the **hill post** has been carried out.

2. **<u>Aim</u>**. To put fwd the desk study report for the tr to Khabri-1 hill post alongwith analysis of **5 x alns**, req of POL/ work days, and recom on the aln to be pegged.

3. **<u>Seq</u>**. This report shall unfold in fol seq: -
   a. Methodology.
   b. Terrain.
   c. Alns Consd.
   d. Comparison and Analysis.
   e. POL and Work Days.
   f. Maj Findings and Recom.

4. **<u>Methodology</u>**. The study was carried out on Cop GLO-30 DEM (30 m), Esri imagery (0.6 m), the user KMZ, drone footage (848x480, no telemetry) and recce photographs. Alns were derived by least-cost analysis (grade limit 1:7, side-hill and N penalties), each forced to arrive at the post from a different side. Fol were the key consds: -
   a. Gradient against the permissible 1:10 (ruling) and 1:7 (max pitch).
   b. Cut/ fill, N xings, slope stability and maint liability.
   c. Exposure to dominating ground and to W/ NW low gr (OPs assumed, ***to be confirmed***).

5. **<u>Terrain</u>**. Salient are as fol: -
   a. <u>Ridge</u>. The post crest is narrow, aligned ENE - WSW. The S face is steep (avg **21°** over 250 m, scarp); the N side falls at about 8° into a strike hollow (RL about 85 m).
   b. <u>Strata</u>. Bedding strikes ENE - WSW and crops out on both faces (drone 01:03, S face; recce oblique, N side). Beds are assessed gently dipping/ near-horizontal. No dip-slope face has been identified ***(to be confirmed by gr recce)***.
   c. <u>Drainage</u>. Nalas drain both flanks; the N foothill is crossed by {t5['nala_xings']} x nalas with catchment > 5 ha.
   d. <u>Existing tr to post</u>. No veh tr to the post is visible on imagery. A faint footpath runs W along the ridge spine (unconfirmed).

6. **<u>Alns Consd and Comparison</u>**. Details are as given below: -

| Tr | Aln | New const (km) | Max grade (%) | > 1:10 (%) | > 1:5 (%) | Hairpins | N xings | Cut (cu M, assessed) | Exposure crest / low gr (%) | POL (lit) | Work days | MCDA |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
{rows}

   a. <u>T1</u>. Max grade **{t1['max_grade_pct']:.1f} %** against the permissible 1:7 (14 %); {t1['pct_gt_1in5']:.0f} % of its length is steeper than 1:5. It is **not tech feasible** for veh mov ({P['T1']['dur']} work days).
   b. <u>T4 and T5</u>. MCDA ranks T4 ({T['T4']:.2f}) and T5 ({T['T5']:.2f}) equal within desk-study accuracy. With ± 20 % on each of the 8 weights, T4 stays first in {MC['sens_winners'].get('T4',0)}/ 16 runs. If the KMZ new tr is built regardless, the two are level.
   c. <u>T5</u>. Gentlest grades (max **{t5['max_grade_pct']:.1f} %**, 0 % > 1:5, {t5['pct_gt_1in10']:.0f} % > 1:10); least cut ({t5['cut_m3']:,.0f} cu M); lowest exposure to dominating crests ({t5['expo_dominating_pct']:.0f} %). It is the longest ({t5['new_const_m']/1000:.2f} km incl {t5['kmz_newtr_used_m']/1000:.2f} km of the KMZ new tr) with **{t5['nala_xings']} x N xings**.
   d. <u>T4</u>. Shortest of the graded alns ({t4['new_const_m']/1000:.2f} km), nil N xings; however, {t4['pct_gt_1in10']:.0f} % > 1:10 with {t4['hairpins']} x hairpins and {t4['expo_dominating_pct']:.0f} % exposure to the crests.

7. **<u>POL and Work Days (T5)</u>**. Worked out using the user's saved POL/ plt stds (hidden safety margin of {10} % incl): -

| Ser | Description | A/U | Qty | KMPL/ LPH | Lits | Remarks |
|---|---|---|---|---|---|---|
{pr}
| | **Total** | | | | **{P['T5']['total']:,}** | |

   Duration: **{P['T5']['dur']} work days** with 1 x Dozer and 1 x Excavator ({P['T5']['dur_2doz']} work days with 2 x Dozers). T4 for comparison: {P['T4']['total']:,} lit, {P['T4']['dur']} work days.

8. **<u>Maj Findings</u>**. After carrying out the desk study, fol are the maj findings: -
   a. <u>Rear aln exists</u>. A graded aln skirting the mount to the rear, running N along the foothill and climbing to the post from the N (T5) has been found by least-cost analysis and is corroborated by the DEM section and imagery.
   b. <u>Direct climb</u>. T1 is **not tech feasible** ({t1['max_grade_pct']:.1f} % max grade).
   c. <u>T4/ T5</u>. Equal on desk study; T5 is better on grade, cut and crest exposure; T4 on length and N xings.
   d. <u>Accuracy</u>. Figures are based on a 30 m DEM; cut qty are assessed (± 50 %) ***(to be confirmed by gr recce)***.

9. **<u>Recom</u>**. In view of the above, fol is recom: -
   a. <u>Aln</u>. **T5 (rear/ N foothill aln)** be adopted for pegging, being the gentlest for loaded vehs in all weather, with least cut and least exposure to dominating gr. **T4 (E flank)** be held as altn.
   b. <u>Gr Recce</u>. **Engr team be tasked to carry out gr recce of T5 and T4** (dip of strata, N xing sites, OP sites), before a final decision.
   c. <u>N Xings</u>. Protection (Irish xings/ causeways) be planned at the {t5['nala_xings']} x N xings on T5.
   d. <u>Interim</u>. Till the aln is finalised, the existing footpath will continue to be used for foot mov to the post.
"""
open('/home/user/Aftab-Machine/output/Recce_Report.md','w').write(md); print('ok')
