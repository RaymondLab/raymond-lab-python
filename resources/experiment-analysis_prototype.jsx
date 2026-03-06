import { useState, useCallback, useMemo } from "react";

// ═══════════════════════════════════════════════════════════
// THEME
// ═══════════════════════════════════════════════════════════
const T = {
  light: {
    bgApp:"#E8ECF0",bgPanel:"#FFFFFF",bgPanelAlt:"#EFF2F6",bgInput:"#FFFFFF",
    bgTopbar:"#263040",bgTabActive:"#3E6E8C",bgTabInactive:"#324050",
    bgCali:"#EFF4F8",bgParam:"#F3F6F9",bgPlot:"#F8FAFB",
    bd:"#CDD4DC",bdL:"#DFE4EA",bdF:"#3E6E8C",
    t1:"#1A2230",t2:"#4E5A6A",t3:"#8490A0",tI:"#FFFFFF",tTop:"#A8B4C2",
    ac:"#3E6E8C",acD:"#2E5A74",acL:"#E0EDF5",acT:"#2E5A74",
    dPos:"#E8690B",dVel:"#2563EB",dSac:"#D42A2A",dStim:"#8490A0",dFit:"#1A2230",dRaw:"#BCC4CE",dSem:"#D6E4F7",
    bPre:"#0F8A5F",bPreBg:"#D6F0E4",bTrn:"#CF2C4A",bTrnBg:"#FAE0E5",
    qG:"#1A9E50",qW:"#D4930D",qB:"#CF2C2C",qS:"#2D5FD4",
  },
  dark: {
    bgApp:"#141A22",bgPanel:"#1C2430",bgPanelAlt:"#18202A",bgInput:"#243040",
    bgTopbar:"#0E1418",bgTabActive:"#508CB0",bgTabInactive:"#243040",
    bgCali:"#1A2430",bgParam:"#18202A",bgPlot:"#18202A",
    bd:"#304050",bdL:"#243040",bdF:"#508CB0",
    t1:"#DEE4EA",t2:"#90A0B0",t3:"#607080",tI:"#141A22",tTop:"#8094A8",
    ac:"#508CB0",acD:"#3E7898",acL:"#1A2C3C",acT:"#70A8CA",
    dPos:"#F0923C",dVel:"#6BA3F5",dSac:"#F06B6B",dStim:"#607080",dFit:"#DEE4EA",dRaw:"#3A4858",dSem:"#1A2E48",
    bPre:"#3BD48A",bPreBg:"#0F3028",bTrn:"#F27088",bTrnBg:"#3A1422",
    qG:"#2ED06A",qW:"#F0B030",qB:"#F06B6B",qS:"#6BA3F5",
  },
};
const F = "'Segoe UI','SF Pro Text',system-ui,sans-serif";
const M = "'Consolas','SF Mono','Menlo',monospace";

// ═══════════════════════════════════════════════════════════
// PRIMITIVES
// ═══════════════════════════════════════════════════════════
const Btn = ({children,primary,small,disabled,c,onClick,style:s})=>(
  <div onClick={disabled?undefined:onClick} style={{display:"inline-flex",alignItems:"center",justifyContent:"center",gap:4,
    padding:small?"3px 10px":"5px 14px",borderRadius:3,fontFamily:F,cursor:disabled?"default":"pointer",
    border:primary?`1px solid ${c.acD}`:`1px solid ${c.bd}`,
    background:primary?c.ac:c.bgPanel,color:primary?c.tI:c.t2,
    fontSize:small?11:12,fontWeight:600,opacity:disabled?.4:1,userSelect:"none",...s,
  }}>{children}</div>
);

const Inp = ({label,w,value,placeholder,badge,c})=>(
  <div style={{display:"flex",flexDirection:"column",gap:2,width:w}}>
    {label&&<div style={{fontSize:11,color:c.t3,fontWeight:600,display:"flex",alignItems:"center",gap:3,fontFamily:F}}>{label}{badge}</div>}
    <div style={{border:`1px solid ${c.bd}`,borderRadius:3,padding:"4px 7px",fontSize:12,color:value?c.t1:c.t3,background:c.bgInput,fontFamily:F}}>{value||placeholder||""}</div>
  </div>
);

const Cmb = ({label,value,w,badge,c})=>(
  <div style={{display:"flex",flexDirection:"column",gap:2,width:w}}>
    {label&&<div style={{fontSize:11,color:c.t3,fontWeight:600,display:"flex",alignItems:"center",gap:3,fontFamily:F}}>{label}{badge}</div>}
    <div style={{border:`1px solid ${c.bd}`,borderRadius:3,padding:"4px 7px",fontSize:12,color:c.t1,background:c.bgInput,display:"flex",justifyContent:"space-between",alignItems:"center",fontFamily:F}}>{value}<span style={{fontSize:8,color:c.t3}}>▾</span></div>
  </div>
);

const Sld = ({label,value,unit,c,val,onVal})=>{
  const pct = val !== undefined ? val : 40;
  return(
  <div style={{display:"flex",alignItems:"center",gap:8,flex:1}}>
    <div style={{fontSize:11,color:c.t3,fontWeight:600,minWidth:72,textAlign:"right",fontFamily:F}}>{label}</div>
    <div style={{flex:1,height:4,background:c.bd,borderRadius:2,position:"relative",cursor:"pointer"}}
      onClick={e=>{if(onVal){const r=e.currentTarget.getBoundingClientRect();onVal(Math.round((e.clientX-r.left)/r.width*100));}}}>
      <div style={{position:"absolute",left:0,top:0,width:`${pct}%`,height:"100%",background:c.ac,borderRadius:2}}/>
      <div style={{position:"absolute",left:`${pct-2}%`,top:-5,width:14,height:14,borderRadius:7,background:c.ac,border:`2px solid ${c.bgPanel}`}}/>
    </div>
    <div style={{fontSize:11,color:c.t1,fontWeight:600,minWidth:52,fontFamily:M}}>{value}<span style={{fontWeight:400,color:c.t3,fontSize:10}}> {unit}</span></div>
  </div>
);};

const Grp = ({title,children,c,style:s})=>(
  <div style={{background:c.bgPanel,border:`1px solid ${c.bd}`,borderRadius:3,...s}}>
    {title&&<div style={{fontSize:11,fontWeight:700,color:c.t2,padding:"6px 8px",borderBottom:`1px solid ${c.bdL}`,fontFamily:F}}>{title}</div>}
    {children}
  </div>
);

const Plt = ({title,children,c,xLabel,style:s})=>(
  <div style={{background:c.bgPlot,border:`1px solid ${c.bd}`,borderRadius:3,position:"relative",display:"flex",flexDirection:"column",overflow:"hidden",...s}}>
    {title&&<div style={{fontSize:10,fontWeight:600,color:c.t3,padding:"5px 8px 0",fontFamily:F}}>{title}</div>}
    <div style={{flex:1,position:"relative",minHeight:0}}>{children}</div>
    {xLabel&&<div style={{fontSize:9,color:c.t3,textAlign:"center",padding:"2px 0 4px",fontFamily:M}}>{xLabel}</div>}
  </div>
);

const TRow = ({cells,header,c})=>(
  <div style={{display:"flex",borderBottom:`1px solid ${header?c.bd:c.bdL}`,background:header?c.bgPanelAlt:"transparent"}}>
    {cells.map((cl,i)=>(
      <div key={i} style={{flex:cl.flex||1,padding:"5px 5px",fontSize:11,fontWeight:header?700:400,color:header?c.t2:(cl.color||c.t1),fontFamily:(!header&&i>1)?M:F,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{cl.text}</div>
    ))}
  </div>
);

const Bdg = ({children,color,c})=>(
  <span style={{fontSize:9,fontWeight:700,padding:"1px 5px",borderRadius:2,background:color==="green"?c.bPreBg:color==="accent"?c.acL:c.bgPanelAlt,color:color==="green"?c.bPre:color==="accent"?c.acT:c.t3,fontFamily:F}}>{children}</span>
);

const Sec = ({children,c})=><div style={{fontSize:10,fontWeight:700,color:c.t3,textTransform:"uppercase",letterSpacing:".06em",fontFamily:F}}>{children}</div>;
const Req = ({c})=><span style={{color:c.ac,fontWeight:800}}>*</span>;

// Block bands SVG
const BB = ({c})=>(
  <>
    <rect x="45" y="5" width="15" height="90" fill={c.bPre} opacity=".18"/>
    {Array.from({length:20},(_,i)=><rect key={i} x={65+i*20} y="5" width="18" height="90" fill={c.bTrn} opacity=".1"/>)}
    <rect x="465" y="5" width="15" height="90" fill={c.bPre} opacity=".18"/>
  </>
);

// Block navigator
const BNav = ({c,selBlock,onSelBlock,label})=>{
  const bq=[.9,.85,.78,.65,.55,.72,.80,.45,.35,.60,.70,.50,.15,.82,.68,.42,.75,.55,.38,.18,.62,.71,.48,.80,.66,.58,.73,.44,.52,.69,.88];
  const qc=f=>f>=.4?c.qG:f>=.2?c.qW:c.qB;
  const sb = selBlock||0;
  return(
    <div style={{display:"flex",gap:4,alignItems:"stretch",flexShrink:0}}>
      <Btn small c={c} onClick={()=>onSelBlock&&onSelBlock(Math.max(0,sb-1))} style={{padding:"1px 7px"}}>◂</Btn>
      <div style={{flex:1,display:"flex",flexDirection:"column",gap:1}}>
        <div style={{display:"flex",gap:1,height:13}}>
          {Array.from({length:31},(_,i)=>{
            const isPre=i===0||i===30;
            return <div key={i} onClick={()=>onSelBlock&&onSelBlock(i)} style={{
              flex:isPre?0:1,width:isPre?13:undefined,minWidth:3,cursor:"pointer",
              background:isPre?c.bPre:c.bTrn,borderRadius:"2px 2px 0 0",
              opacity:i===sb?1:.4,outline:i===sb?`2px solid ${c.t1}`:"none",outlineOffset:-2,
            }}/>;
          })}
        </div>
        <div style={{display:"flex",gap:1,height:9}}>
          {Array.from({length:31},(_,i)=>(
            <div key={i} onClick={()=>onSelBlock&&onSelBlock(i)} style={{
              flex:(i===0||i===30)?0:1,width:(i===0||i===30)?13:undefined,minWidth:3,cursor:"pointer",
              background:qc(bq[i]),borderRadius:"0 0 2px 2px",
              opacity:i===sb?.9:.65,outline:i===sb?`2px solid ${c.t1}`:"none",outlineOffset:-2,
            }}/>
          ))}
        </div>
      </div>
      <Btn small c={c} onClick={()=>onSelBlock&&onSelBlock(Math.min(30,sb+1))} style={{padding:"1px 7px"}}>▸</Btn>
      <div style={{display:"flex",flexDirection:"column",justifyContent:"center",marginLeft:4,gap:1,flexShrink:0}}>
        <div style={{fontSize:11,color:c.t1,fontWeight:700,fontFamily:F}}>{label||`Block ${sb+1} / 62`} <span style={{fontWeight:400,color:c.t3}}>{sb===0||sb===30?"VORD (Pre/Post)":"OKR (Training)"}</span></div>
        <div style={{display:"flex",gap:6,fontSize:8,color:c.t3}}>
          <span><span style={{display:"inline-block",width:7,height:4,background:c.qG,borderRadius:1,marginRight:2}}/>≥40%</span>
          <span><span style={{display:"inline-block",width:7,height:4,background:c.qW,borderRadius:1,marginRight:2}}/>20-40%</span>
          <span><span style={{display:"inline-block",width:7,height:4,background:c.qB,borderRadius:1,marginRight:2}}/>&lt;20%</span>
        </div>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════
// SCREENS
// ═══════════════════════════════════════════════════════════

function W1Screen({c,onNext,fileLoaded,setFileLoaded,analysisType,setAnalysisType}){
  return(
    <div style={{display:"flex",flexDirection:"column",gap:8,height:"100%"}}>
      <Grp c={c} style={{padding:"8px 12px"}}>
        <div style={{display:"flex",gap:8,alignItems:"flex-end"}}>
          <div style={{flex:1,display:"flex",gap:6,alignItems:"flex-end"}}>
            <Btn c={c} onClick={()=>setFileLoaded(true)}>{fileLoaded?"✓ Loaded":"Browse"}</Btn>
            <Inp w="100%" value={fileLoaded?"/Users/lab/data/experiment_01.smr":""} placeholder="Select .smr / .smrx / .mat file..." c={c}/>
          </div>
          <Cmb label="Analysis Type" value={analysisType} w={155} c={c}/>
          <Btn primary c={c} disabled={!fileLoaded} onClick={onNext}>Next →</Btn>
        </div>
        {fileLoaded&&<div style={{display:"flex",gap:14,fontSize:11,color:c.t3,marginTop:6,fontFamily:M}}>
          <span><b style={{color:c.t2}}>Ch</b> 13</span><span><b style={{color:c.t2}}>Size</b> 245 MB</span>
          <span><b style={{color:c.t2}}>Date</b> 2026-01-15</span><span><b style={{color:c.t2}}>Fmt</b> SMR</span>
        </div>}
      </Grp>

      {fileLoaded ? <>
        <div style={{display:"flex",gap:12,padding:"5px 10px",background:c.bgPanelAlt,borderRadius:3,fontSize:11,color:c.t2,fontWeight:600,flexShrink:0,border:`1px solid ${c.bdL}`}}>
          <span>Duration: <b>3842s</b></span><span>Blocks: <b>62</b></span>
          <span style={{color:c.bPre}}>Pre/Post: <b>1</b></span>
          <span style={{color:c.bTrn}}>Training: <b>60</b></span>
          <span>Freq: <b>1 Hz</b></span>
        </div>
        <div style={{display:"flex",gap:8,flex:1,minHeight:0}}>
          <div style={{flex:1,display:"flex",flexDirection:"column",gap:3}}>
            {[{ch:"htvel",d:"Drum Vel",g:i=>Math.sin(i*.15)*30},{ch:"hhvel",d:"Chair Vel",g:i=>i<15?Math.sin(i*.8)*25:i>420?Math.sin((i-420)*.8)*25:0}].map(({ch,d,g})=>(
              <div key={ch} style={{flex:1,display:"flex",flexDirection:"column"}}>
                <div style={{display:"flex",alignItems:"center",gap:4,marginBottom:2}}><Sec c={c}>Ch:</Sec><Cmb value={ch} w={80} c={c}/><span style={{fontSize:9,color:c.t3}}>{d}</span></div>
                <Plt c={c} style={{flex:1}}>
                  <svg style={{position:"absolute",inset:0,width:"100%",height:"100%"}} viewBox="0 0 500 100" preserveAspectRatio="none">
                    <BB c={c}/><path d={`M 45 50 ${Array.from({length:440},(_,i)=>`L ${45+i} ${50+g(i)}`).join(" ")}`} stroke={c.t1} fill="none" strokeWidth=".8"/>
                  </svg>
                </Plt>
              </div>
            ))}
            <div style={{flex:1,display:"flex",flexDirection:"column"}}>
              <div style={{display:"flex",alignItems:"center",gap:4,marginBottom:2}}>
                <Sec c={c}>Raw Eye Pos — UNCAL</Sec>
                <span style={{fontSize:9,color:c.dPos,fontWeight:700}}>━ h1</span>
                <span style={{fontSize:9,color:c.dVel,fontWeight:700}}>━ h2</span>
              </div>
              <Plt xLabel="Time (s)" c={c} style={{flex:1}}>
                <svg style={{position:"absolute",inset:0,width:"100%",height:"100%"}} viewBox="0 0 500 100" preserveAspectRatio="none">
                  <BB c={c}/>
                  <path d={`M 45 45 ${Array.from({length:440},(_,i)=>`L ${45+i} ${45+Math.sin(i*.04)*15+Math.sin(i*.15)*8}`).join(" ")}`} stroke={c.dPos} fill="none" strokeWidth=".8"/>
                  <path d={`M 45 55 ${Array.from({length:440},(_,i)=>`L ${45+i} ${55+Math.sin(i*.04+.3)*12+Math.sin(i*.15)*6}`).join(" ")}`} stroke={c.dVel} fill="none" strokeWidth=".8"/>
                </svg>
              </Plt>
            </div>
          </div>
          <Grp title="Block Table" c={c} style={{width:195,display:"flex",flexDirection:"column",overflow:"hidden",flexShrink:0}}>
            <TRow header c={c} cells={[{text:"#",flex:.5},{text:"Label",flex:1.2},{text:"Hz",flex:.6},{text:"✓",flex:.4}]}/>
            <div style={{flex:1,overflowY:"auto"}}>
              {[{n:1,l:"VORD",cl:c.bPre},...Array.from({length:9},(_,i)=>({n:i+2,l:"OKR",cl:c.bTrn}))].map(b=>
                <TRow key={b.n} c={c} cells={[{text:b.n,flex:.5},{text:b.l,flex:1.2,color:b.cl},{text:"1",flex:.6},{text:"☑",flex:.4}]}/>
              )}
              <div style={{padding:"4px",fontSize:9,color:c.t3,textAlign:"center"}}>… 52 more</div>
              <TRow c={c} cells={[{text:62,flex:.5},{text:"VORD",flex:1.2,color:c.bPre},{text:"1",flex:.6},{text:"☑",flex:.4}]}/>
            </div>
          </Grp>
        </div>
      </> : <div style={{flex:1,display:"flex",alignItems:"center",justifyContent:"center",color:c.t3,fontSize:13}}>
        <div style={{textAlign:"center"}}>
          <div style={{fontSize:32,marginBottom:8,opacity:.3}}>📂</div>
          <div>Click <b>Browse</b> to load an experiment file</div>
        </div>
      </div>}
    </div>
  );
}

function W2Screen({c,onBack,onStart}){
  const [filled,setFilled]=useState(5);
  const required=8;
  const au=<Bdg color="green" c={c}>auto</Bdg>;
  return(
    <div style={{display:"flex",flexDirection:"column",gap:8,height:"100%"}}>
      <Grp c={c} style={{padding:"8px 12px",flexShrink:0}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
          <div style={{display:"flex",gap:8,alignItems:"flex-end"}}><Btn c={c} onClick={onBack}>← Back</Btn><Sec c={c}>Save to:</Sec><Btn small c={c}>Browse</Btn><Inp w={240} value="/Users/lab/data/experiment_01/" c={c}/></div>
          <div style={{display:"flex",alignItems:"center",gap:10}}>
            {filled<required&&<span style={{fontSize:11,color:c.qB,fontWeight:600}}>{required-filled} required fields remaining</span>}
            {filled>=required&&<span style={{fontSize:11,color:c.qG,fontWeight:600}}>✓ All fields complete</span>}
            <Btn primary c={c} disabled={filled<required} onClick={onStart}>Start Analysis</Btn>
          </div>
        </div>
      </Grp>
      <div style={{flex:1,overflowY:"auto",display:"flex",flexDirection:"column",gap:8}}>
        <Grp title="Subject Information" c={c}>
          <div style={{display:"flex",flexWrap:"wrap",gap:7,padding:"6px 8px"}}>
            <Inp label={<><Req c={c}/> Mouse ID</>} w={125} value="M001" badge={au} c={c}/>
            <Inp label="Species" w={105} value="Mus musculus" c={c}/>
            <Cmb label={<><Req c={c}/> Strain</>} value="C57BL/6J" w={110} c={c}/>
            <Cmb label={<><Req c={c}/> Sex</>} value="Male" w={75} c={c}/>
            <Inp label="Age" w={70} placeholder="P60" c={c}/>
            <Inp label="Wt (g)" w={65} placeholder="25" c={c}/>
            <Cmb label={<><Req c={c}/> Genotype</>} value="WT" w={90} c={c}/>
          </div>
        </Grp>
        <Grp title="Session Information" c={c}>
          <div style={{padding:"6px 8px"}}>
            <div style={{display:"flex",flexWrap:"wrap",gap:7}}>
              <Inp label={<><Req c={c}/> Date</>} w={110} value="2026-01-15" badge={au} c={c}/>
              <Inp label={<><Req c={c}/> Start</>} w={90} value="14:32:05" badge={au} c={c}/>
              <Cmb label={<><Req c={c}/> Experimenter</>} value={filled>=7?"Dr. Smith":"Select..."} w={130} c={c}/>
              <Inp label="Lab" w={125} value="Raymond Lab" c={c}/>
              <Inp label="Institution" w={145} value="Stanford University" c={c}/>
            </div>
          </div>
        </Grp>
        <Grp title="Experiment Details" c={c}>
          <div style={{padding:"6px 8px"}}>
            <div style={{display:"flex",flexWrap:"wrap",gap:7}}>
              <Inp label={<><Req c={c}/> Cohort</>} w={105} value={filled>=8?"Cohort 3":""} placeholder="Cohort 3" c={c}/>
              <Cmb label={<><Req c={c}/> Condition</>} value="WT" w={90} c={c}/>
              <Cmb label={<><Req c={c}/> Task</>} value="Std VOR" w={120} badge={au} c={c}/>
              <Inp label={<><Req c={c}/> Freq</>} w={70} value="1 Hz" badge={au} c={c}/>
              <Cmb label="Eye" value="Right" w={72} c={c}/>
            </div>
          </div>
        </Grp>
        <Grp title="Device Information" c={c}>
          <div style={{display:"flex",flexWrap:"wrap",gap:7,padding:"6px 8px"}}>
            <Cmb label="Rig" value="Rig 1" w={85} c={c}/>
            <Inp label="Rec System" w={185} value="CED Power1401 + Spike2" c={c}/>
            <Inp label="Eye Track" w={165} value="Magnetic (HMC1512)" c={c}/>
            <Inp label={<><Req c={c}/> Rate</>} w={100} value="1000 Hz" badge={au} c={c}/>
          </div>
        </Grp>
        {/* Simulate filling fields */}
        <div style={{padding:"8px 12px",textAlign:"center"}}>
          <Btn c={c} onClick={()=>setFilled(Math.min(required,filled+1))} style={{fontSize:11}}>
            ⚡ Simulate filling a required field ({filled}/{required})
          </Btn>
        </div>
      </div>
    </div>
  );
}

function A1Screen({c,selBlock,onSelBlock,caliOpen,setCaliOpen,lpCut,setLpCut,sgWin,setSgWin,sacTh,setSacTh}){
  return(
    <div style={{display:"flex",flexDirection:"column",gap:7,height:"100%"}}>
      {/* Calibration */}
      <Grp c={c} style={{padding:caliOpen?"7px 10px":"7px 10px",background:c.bgCali,borderColor:c.ac+"40",flexShrink:0}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",cursor:"pointer"}} onClick={()=>setCaliOpen(!caliOpen)}>
          <span style={{fontSize:10,fontWeight:700,color:c.acT,textTransform:"uppercase",letterSpacing:".05em"}}>{caliOpen?"▾":"▸"} Calibration</span>
          {!caliOpen&&<div style={{display:"flex",gap:8,fontSize:10,fontFamily:M,color:c.t2}}>
            <span>Ch1: <b>.0412</b></span><span>Active: <b>Ch1</b></span>
            <Bdg color="green" c={c}>✓ OK</Bdg>
          </div>}
          <div style={{display:"flex",gap:3}}>
            <Btn small primary c={c} style={{fontSize:10,padding:"2px 8px"}}>Load File</Btn>
            <Btn small c={c} style={{fontSize:10,padding:"2px 8px"}}>Manual</Btn>
          </div>
        </div>
        {caliOpen&&<div style={{display:"flex",gap:10,alignItems:"center",marginTop:6}}>
          <Btn small c={c}>Browse</Btn><Inp w={185} value="foldername_cali/cali_workspace.mat" c={c}/>
          <div style={{display:"flex",gap:10,fontSize:10,fontFamily:M,color:c.t2}}><span>Ch1: <b>.0412</b></span><span>Ch2: <b>.0389</b></span><span>Act: <b>Ch1</b></span></div>
          <Bdg color="green" c={c}>✓ OK</Bdg><Btn small primary c={c}>Apply</Btn>
        </div>}
      </Grp>

      <BNav c={c} selBlock={selBlock} onSelBlock={onSelBlock}/>

      <div style={{display:"flex",gap:7,flex:1,minHeight:0}}>
        <Plt title="Eye Position" xLabel="Time (s)" c={c} style={{flex:1}}>
          <svg style={{position:"absolute",inset:0,width:"100%",height:"100%"}} viewBox="0 0 400 180" preserveAspectRatio="none">
            {[120,250,330].map(x=><rect key={x} x={x} y="5" width={x===120?20:x===250?15:18} height="165" fill={c.dSac} opacity=".06"/>)}
            <path d={`M 45 90 ${Array.from({length:340},(_,i)=>`L ${45+i} ${90+Math.sin(i*.04+selBlock*.2)*40+(Math.random()-.5)*18}`).join(" ")}`} stroke={c.dRaw} fill="none" strokeWidth="1"/>
            <path d={`M 45 90 ${Array.from({length:340},(_,i)=>`L ${45+i} ${90+Math.sin(i*.04+selBlock*.2)*(35+lpCut/10)}`).join(" ")}`} stroke={c.dPos} fill="none" strokeWidth="2"/>
            <path d="M 120 55 L 128 25 L 133 65 L 140 60" stroke={c.dSac} fill="none" strokeWidth="1.5"/>
          </svg>
          <div style={{position:"absolute",top:5,left:42,display:"flex",gap:7,fontSize:9}}>
            <span style={{color:c.dRaw}}>━ raw</span><span style={{color:c.dPos}}>━ filt</span><span style={{color:c.dSac}}>━ sacc</span>
          </div>
        </Plt>
        <Plt title="Eye Velocity" xLabel="Time (s)" c={c} style={{flex:1}}>
          <svg style={{position:"absolute",inset:0,width:"100%",height:"100%"}} viewBox="0 0 400 180" preserveAspectRatio="none">
            {[120,250,330].map(x=><rect key={x} x={x} y="5" width={x===120?20:x===250?15:18} height="165" fill={c.dSac} opacity=".06"/>)}
            <path d={`M 45 90 ${Array.from({length:340},(_,i)=>`L ${45+i} ${90+Math.cos(i*.04+selBlock*.2)*50}`).join(" ")}`} stroke={c.dStim} fill="none" strokeWidth="1" strokeDasharray="4,3"/>
            <path d={`M 45 90 ${Array.from({length:340},(_,i)=>`L ${45+i} ${90+Math.cos(i*.04+selBlock*.2)*35+(Math.random()-.5)*35}`).join(" ")}`} stroke={c.dRaw} fill="none" strokeWidth=".8"/>
            <path d={`M 45 90 ${Array.from({length:340},(_,i)=>`L ${45+i} ${90+Math.cos(i*.04+selBlock*.2)*35}`).join(" ")}`} stroke={c.dVel} fill="none" strokeWidth="2"/>
          </svg>
          <div style={{position:"absolute",top:5,left:42,display:"flex",gap:7,fontSize:9}}>
            <span style={{color:c.dStim}}>╌ stim</span><span style={{color:c.dRaw}}>━ raw</span><span style={{color:c.dVel}}>━ filt</span>
          </div>
        </Plt>
      </div>

      <Grp c={c} style={{padding:"8px 12px",background:c.bgParam,flexShrink:0}}>
        <div style={{display:"flex",alignItems:"center"}}>
          <div style={{flex:1,display:"flex",flexDirection:"column",gap:4}}>
            <div style={{display:"flex",alignItems:"center",gap:5}}><Sec c={c}>Pos Filter</Sec><Cmb value="Butterworth" w={105} c={c}/></div>
            <Sld label="LP Cutoff" value={lpCut} unit="Hz" c={c} val={lpCut} onVal={setLpCut}/>
          </div>
          <div style={{width:1,height:32,background:c.bd,margin:"0 12px"}}/>
          <div style={{flex:.65,display:"flex",flexDirection:"column",gap:4}}>
            <Sec c={c}>Differentiation</Sec>
            <Sld label="SG Window" value={sgWin} unit="ms" c={c} val={sgWin} onVal={setSgWin}/>
          </div>
          <div style={{width:1,height:32,background:c.bd,margin:"0 12px"}}/>
          <div style={{flex:1,display:"flex",flexDirection:"column",gap:4}}>
            <div style={{display:"flex",alignItems:"center",gap:5}}><Sec c={c}>Saccade Det</Sec><Cmb value="SVT" w={70} c={c}/></div>
            <Sld label="Threshold" value={sacTh} unit="°/s" c={c} val={sacTh} onVal={setSacTh}/>
          </div>
        </div>
      </Grp>
    </div>
  );
}

function A2Screen({c,selBlock,onSelBlock}){
  const [selCycle,setSelCycle]=useState(4);
  const [dispMode,setDispMode]=useState("SEM");
  const cq=[1,1,1,0,1,1,1,0,1,1,1,1,0,1,1,1,1,0,1,1];
  return(
    <div style={{display:"flex",flexDirection:"column",gap:7,height:"100%"}}>
      <BNav c={c} selBlock={selBlock} onSelBlock={onSelBlock}/>
      <div style={{display:"flex",gap:5,alignItems:"center",flexShrink:0}}>
        <Sec c={c}>Cycles:</Sec>
        <div style={{flex:1,display:"flex",gap:2,height:15}}>
          {cq.map((g,i)=>(
            <div key={i} onClick={()=>setSelCycle(i)} style={{
              flex:1,borderRadius:2,minWidth:7,cursor:"pointer",
              background:i===selCycle?c.qS:g?c.qG:c.qB,
              opacity:i===selCycle?1:.55,
              outline:i===selCycle?`2px solid ${c.t1}`:"none",outlineOffset:-1,
            }}/>
          ))}
        </div>
        <div style={{display:"flex",gap:4,fontSize:8,color:c.t3,flexShrink:0}}>
          <span><span style={{display:"inline-block",width:6,height:6,background:c.qG,borderRadius:1,marginRight:2}}/>good</span>
          <span><span style={{display:"inline-block",width:6,height:6,background:c.qB,borderRadius:1,marginRight:2}}/>sacc</span>
          <span><span style={{display:"inline-block",width:6,height:6,background:c.qS,borderRadius:1,marginRight:2}}/>sel</span>
        </div>
        <div style={{display:"flex",borderRadius:3,overflow:"hidden",border:`1px solid ${c.bd}`,flexShrink:0,marginLeft:4}}>
          {["SEM","All Cycles","Good Cycles"].map(m=>(
            <div key={m} onClick={()=>setDispMode(m)} style={{padding:"4px 10px",fontSize:10,fontWeight:600,cursor:"pointer",background:dispMode===m?c.ac:c.bgPanel,color:dispMode===m?c.tI:c.t3,borderRight:m!=="Good Cycles"?`1px solid ${c.bd}`:"none",fontFamily:F}}>{m}</div>
          ))}
        </div>
      </div>

      <div style={{display:"flex",gap:8,flex:1,minHeight:0}}>
        <Plt title={`Block ${selBlock+1} (${selBlock+1} of 62): ${selBlock===0||selBlock===30?"VORD":"OKR"}`} xLabel="Time (s)" c={c} style={{flex:1}}>
          <svg style={{position:"absolute",inset:0,width:"100%",height:"100%"}} viewBox="0 0 400 200" preserveAspectRatio="none">
            {dispMode==="SEM"&&<path d={`M 30 92 ${Array.from({length:350},(_,i)=>`L ${30+i} ${100+Math.sin(i*.018+selBlock*.1)*40-8}`).join(" ")} ${Array.from({length:350},(_,i)=>`L ${380-i} ${100+Math.sin((350-i)*.018+selBlock*.1)*40+8}`).join(" ")} Z`} fill={c.dSem} stroke="none" opacity=".5"/>}
            {(dispMode==="All Cycles"||dispMode==="Good Cycles")&&Array.from({length:dispMode==="All Cycles"?20:16},(_,ci)=>(
              <path key={ci} d={`M 30 100 ${Array.from({length:350},(_,i)=>`L ${30+i} ${100+Math.sin(i*.018+selBlock*.1+ci*.15)*(36+ci*.3)}`).join(" ")}`} stroke={ci===selCycle?c.qS:c.dVel} fill="none" strokeWidth={ci===selCycle?2:.6} opacity={ci===selCycle?1:.2}/>
            ))}
            <path d={`M 30 100 ${Array.from({length:350},(_,i)=>`L ${30+i} ${100+Math.sin(i*.018+selBlock*.1)*55}`).join(" ")}`} stroke={c.dStim} fill="none" strokeWidth="1.5" strokeDasharray="6,4"/>
            <path d={`M 30 100 ${Array.from({length:350},(_,i)=>`L ${30+i} ${100+Math.sin(i*.018+selBlock*.1+.1)*40}`).join(" ")}`} stroke={c.dVel} fill="none" strokeWidth="2.5"/>
            <path d={`M 30 100 ${Array.from({length:350},(_,i)=>`L ${30+i} ${100+Math.sin(i*.018+selBlock*.1+.08)*38}`).join(" ")}`} stroke={c.dFit} fill="none" strokeWidth="1.5"/>
          </svg>
          <div style={{position:"absolute",top:8,right:10,display:"flex",flexDirection:"column",gap:2,fontSize:9}}>
            <span style={{color:c.dStim}}>╌ stim</span><span style={{color:c.dVel}}>━ avg</span><span style={{color:c.dFit}}>━ fit</span>
            {dispMode==="SEM"&&<span style={{background:c.dSem,padding:"0 4px",borderRadius:1}}>±SEM</span>}
          </div>
        </Plt>
        <Grp title="Block Metrics" c={c} style={{width:168,flexShrink:0}}>
          <div style={{padding:"6px 8px",display:"flex",flexDirection:"column",gap:3}}>
            {[["Gain","0.82"],["Eye Amp","8.2 ± 0.3"],["Eye Ph","3.1° ± 1.2°"],["Stim A","10.0"],["Freq","1 Hz"],["Good Cyc","16/20"],["VarRes","0.04"]].map(([k,v])=>(
              <div key={k} style={{display:"flex",justifyContent:"space-between",fontSize:11}}>
                <span style={{color:c.t3}}>{k}</span>
                <span style={{color:c.t1,fontWeight:600,fontFamily:M}}>{v}</span>
              </div>
            ))}
          </div>
        </Grp>
      </div>
    </div>
  );
}

function A3Screen({c}){
  return(
    <div style={{display:"flex",flexDirection:"column",gap:7,height:"100%"}}>
      <div style={{display:"flex",justifyContent:"flex-end"}}><Cmb value="Y: Gain" w={120} c={c}/></div>
      <Plt title="Gain Time Course" xLabel="Block Number" c={c} style={{height:175,flexShrink:0}}>
        <svg style={{position:"absolute",inset:0,width:"100%",height:"100%"}} viewBox="0 0 400 160" preserveAspectRatio="none">
          {[35,65,95,125].map(y=><line key={y} x1="35" y1={y} x2="390" y2={y} stroke={c.bdL} strokeWidth=".5"/>)}
          <circle cx="48" cy="88" r="5" fill={c.bPre}/>
          {Array.from({length:30},(_,i)=><circle key={i} cx={58+i*10.5} cy={88-i*1+(Math.random()-.5)*8} r="3" fill={c.bTrn} opacity=".55"/>)}
          <circle cx="380" cy="55" r="5" fill={c.bPre}/>
        </svg>
        <div style={{position:"absolute",top:8,right:10,display:"flex",gap:8,fontSize:9}}>
          <span><span style={{display:"inline-block",width:7,height:7,borderRadius:"50%",background:c.bPre,marginRight:3}}/>Pre/Post</span>
          <span><span style={{display:"inline-block",width:7,height:7,borderRadius:"50%",background:c.bTrn,marginRight:3}}/>Train</span>
        </div>
      </Plt>
      <Grp c={c} style={{flex:1,overflow:"hidden",display:"flex",flexDirection:"column",minHeight:0}}>
        <TRow header c={c} cells={[{text:"#",flex:.3},{text:"Label",flex:.5},{text:"Hz",flex:.3},{text:"Start",flex:.5},{text:"End",flex:.5},{text:"Dur",flex:.4},{text:"Amp±SEM",flex:.85},{text:"Ph±SEM",flex:.85},{text:"StmA",flex:.45},{text:"Gain",flex:.4},{text:"GdCyc",flex:.5},{text:"VR",flex:.35}]}/>
        <div style={{flex:1,overflowY:"auto"}}>
          {[{n:1,l:"VORD",cl:c.bPre,s:"27.3",e:"87.3",ea:"8.2±.3",ep:"3.1±1.2",sa:"10",g:".82",gc:"18/20",v:".04"},
            {n:2,l:"OKR",cl:c.bTrn,s:"97.3",e:"157.3",ea:"7.8±.4",ep:"4.2±1.5",sa:"10",g:".78",gc:"19/20",v:".05"},
            {n:3,l:"OKR",cl:c.bTrn,s:"167",e:"227",ea:"8.0±.3",ep:"3.8±1.1",sa:"10",g:".80",gc:"20/20",v:".03"},
            {n:4,l:"OKR",cl:c.bTrn,s:"237",e:"297",ea:"8.4±.2",ep:"3.5±.9",sa:"10",g:".84",gc:"18/20",v:".04"},
            {n:5,l:"OKR",cl:c.bTrn,s:"307",e:"367",ea:"8.6±.3",ep:"3.2±1.0",sa:"10",g:".86",gc:"19/20",v:".03"},
          ].map(r=><TRow key={r.n} c={c} cells={[{text:r.n,flex:.3},{text:r.l,flex:.5,color:r.cl},{text:"1",flex:.3},{text:r.s,flex:.5},{text:r.e,flex:.5},{text:"60",flex:.4},{text:r.ea,flex:.85},{text:r.ep,flex:.85},{text:r.sa,flex:.45},{text:r.g,flex:.4},{text:r.gc,flex:.5},{text:r.v,flex:.35}]}/>)}
          <div style={{padding:"4px",fontSize:9,color:c.t3,textAlign:"center"}}>… 57 more</div>
        </div>
      </Grp>
      <div style={{display:"flex",justifyContent:"flex-end",gap:5,flexShrink:0}}>
        <Btn small c={c}>Excel</Btn><Btn small c={c}>Figures</Btn><Btn small c={c}>Workspace</Btn><Btn small primary c={c}>Export All</Btn>
      </div>
    </div>
  );
}

function S1Panel({c,isDark,onToggle,lpCut,setLpCut,sgWin,setSgWin,sacTh,setSacTh,onClose}){
  const SH=({children})=><div style={{fontSize:10,fontWeight:700,color:c.t3,textTransform:"uppercase",letterSpacing:".06em",marginBottom:7,paddingBottom:4,borderBottom:`1px solid ${c.bd}`,fontFamily:F}}>{children}</div>;
  const SR=({label,val,v,onV})=>(
    <div><div style={{display:"flex",justifyContent:"space-between",marginBottom:3}}><span style={{fontSize:11,color:c.t2}}>{label}</span><span style={{fontSize:11,fontWeight:700,color:c.t1,fontFamily:M}}>{val}</span></div>
    <div style={{height:4,background:c.bd,borderRadius:2,position:"relative",cursor:"pointer"}} onClick={e=>{if(onV){const r=e.currentTarget.getBoundingClientRect();onV(Math.round((e.clientX-r.left)/r.width*100));}}}>
      <div style={{position:"absolute",left:0,top:0,width:`${v}%`,height:"100%",background:c.ac,borderRadius:2}}/><div style={{position:"absolute",left:`${v-2}%`,top:-5,width:14,height:14,borderRadius:7,background:c.ac,border:`2px solid ${c.bgPanel}`}}/></div></div>
  );
  return(
    <div style={{width:265,background:c.bgPanel,borderLeft:`2px solid ${c.bd}`,display:"flex",flexDirection:"column",flexShrink:0}}>
      <div style={{padding:"8px 12px",borderBottom:`1px solid ${c.bd}`,display:"flex",justifyContent:"space-between",alignItems:"center"}}><span style={{fontSize:12,fontWeight:700,color:c.t1}}>⚙ Settings</span><Btn small c={c} onClick={onClose}>✕</Btn></div>
      <div style={{flex:1,overflowY:"auto",padding:"10px 12px",display:"flex",flexDirection:"column",gap:14}}>
        <div><SH>Position Filter</SH><div style={{display:"flex",flexDirection:"column",gap:7}}><Cmb label="Method" value="Butterworth" w="100%" c={c}/><SR label="LP Cutoff (Hz)" val={lpCut} v={lpCut} onV={setLpCut}/></div></div>
        <div><SH>Differentiation</SH><SR label="SG Window (ms)" val={sgWin} v={sgWin} onV={setSgWin}/></div>
        <div><SH>Saccade Detection</SH><div style={{display:"flex",flexDirection:"column",gap:7}}><Cmb label="Method" value="SVT" w="100%" c={c}/><SR label="Threshold (°/s)" val={sacTh} v={sacTh} onV={setSacTh}/><div style={{display:"flex",gap:5}}><Inp label="Min Dur" w="50%" value="10" c={c}/><Inp label="Pad (ms)" w="50%" value="5" c={c}/></div></div></div>
        <div><SH>Eye Channel</SH><Cmb label="Active" value="Auto (Ch1)" w="100%" c={c}/></div>
        <div><SH>Appearance</SH>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
            <span style={{fontSize:11,color:c.t2}}>Dark Theme</span>
            <div onClick={onToggle} style={{width:36,height:18,borderRadius:9,background:isDark?c.ac:c.bd,position:"relative",cursor:"pointer"}}>
              <div style={{width:14,height:14,borderRadius:7,background:c.bgPanel,position:"absolute",top:2,left:isDark?20:2,transition:"left .15s"}}/>
            </div>
          </div>
        </div>
      </div>
      <div style={{padding:"8px 12px",borderTop:`1px solid ${c.bd}`}}><Btn c={c} style={{width:"100%",justifyContent:"center"}} onClick={()=>{setLpCut(40);setSgWin(30);setSacTh(50);}}>Reset to Defaults</Btn></div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// APP
// ═══════════════════════════════════════════════════════════
export default function App(){
  const [isDark,setIsDark]=useState(false);
  const c = isDark?T.dark:T.light;

  // Navigation
  const [phase,setPhase]=useState("wizard"); // "wizard" | "workspace"
  const [wizStep,setWizStep]=useState(1);
  const [wsTab,setWsTab]=useState("A1");
  const [settingsOpen,setSettingsOpen]=useState(false);

  // Shared state
  const [fileLoaded,setFileLoaded]=useState(false);
  const [analysisType]=useState("Standard VOR");
  const [selBlock,setSelBlock]=useState(0);
  const [caliOpen,setCaliOpen]=useState(true);
  const [lpCut,setLpCut]=useState(40);
  const [sgWin,setSgWin]=useState(30);
  const [sacTh,setSacTh]=useState(50);
  const [loading,setLoading]=useState(false);

  const startAnalysis=()=>{
    setLoading(true);
    setTimeout(()=>{setLoading(false);setPhase("workspace");setWsTab("A1");},1200);
  };

  const newAnalysis=()=>{
    if(window.confirm("Start a new analysis? Current workspace will be discarded.")){
      setPhase("wizard");setWizStep(1);setFileLoaded(false);setSelBlock(0);setSettingsOpen(false);
    }
  };

  const isWorkspace = phase==="workspace";

  return(
    <div style={{fontFamily:F,background:c.bgApp,color:c.t1,minHeight:"100vh",display:"flex",flexDirection:"column",transition:"background .2s,color .2s"}}>
      {/* Title bar */}
      <div style={{height:30,background:c.bgTopbar,display:"flex",alignItems:"center",justifyContent:"space-between",padding:"0 14px",flexShrink:0}}>
        <div style={{display:"flex",alignItems:"center",gap:8}}>
          <span style={{fontSize:12,color:"#FFFFFF",fontWeight:700}}>Behavioral Experiment Analysis</span>
          <span style={{fontSize:10,color:c.tTop,opacity:.6}}>
            {isWorkspace?`— ${wsTab==="A1"?"Signal Explorer":wsTab==="A2"?"Block Analysis":"Results Summary"}`
              :`— Step ${wizStep} of 2: ${wizStep===1?"Load & Review":"Metadata & Output"}`}
          </span>
        </div>
        <span style={{fontSize:9,color:c.tTop,opacity:.4,fontFamily:M}}>Phase 4 Interactive Prototype</span>
      </div>

      {/* Workspace top bar */}
      {isWorkspace&&<div style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"6px 14px",background:c.bgPanel,borderBottom:`1px solid ${c.bd}`,flexShrink:0}}>
        <div style={{display:"flex",gap:10,alignItems:"center"}}>
          <span style={{fontSize:14,fontWeight:700}}>M001</span>
          <span style={{fontSize:11,color:c.t3,fontFamily:M}}>2026-01-15</span>
          <Bdg color="accent" c={c}>Standard VOR</Bdg>
        </div>
        <div style={{display:"flex",gap:6,alignItems:"center"}}>
          <Btn small c={c} onClick={newAnalysis} style={{color:c.t3,fontSize:11}}>↺ New Analysis</Btn>
          <div style={{display:"flex",borderRadius:3,overflow:"hidden",border:`1px solid ${c.bd}`}}>
            {[["A1","Signal Explorer"],["A2","Block Analysis"],["A3","Results Summary"]].map(([id,label])=>(
              <div key={id} onClick={()=>{setWsTab(id);setSettingsOpen(false);}} style={{
                padding:"6px 14px",fontSize:11,fontWeight:600,cursor:"pointer",fontFamily:F,
                background:wsTab===id?c.ac:c.bgPanel,color:wsTab===id?c.tI:c.t3,
                borderRight:id!=="A3"?`1px solid ${c.bd}`:"none",
              }}>{label}</div>
            ))}
          </div>
          <div onClick={()=>setSettingsOpen(!settingsOpen)} style={{
            width:30,height:30,borderRadius:3,display:"flex",alignItems:"center",justifyContent:"center",cursor:"pointer",
            border:`1px solid ${settingsOpen?c.ac:c.bd}`,background:settingsOpen?c.acL:c.bgPanel,fontSize:14,color:settingsOpen?c.ac:c.t2,
          }}>⚙</div>
        </div>
      </div>}

      {/* Loading overlay */}
      {loading&&<div style={{position:"fixed",inset:0,background:"rgba(0,0,0,0.4)",display:"flex",alignItems:"center",justifyContent:"center",zIndex:100}}>
        <div style={{background:c.bgPanel,border:`1px solid ${c.bd}`,borderRadius:6,padding:"24px 40px",textAlign:"center"}}>
          <div style={{fontSize:14,fontWeight:700,color:c.t1,marginBottom:8}}>Processing...</div>
          <div style={{width:200,height:4,background:c.bd,borderRadius:2,overflow:"hidden"}}>
            <div style={{width:"60%",height:"100%",background:c.ac,borderRadius:2,animation:"loading 1.2s ease-in-out infinite"}}/>
          </div>
          <div style={{fontSize:11,color:c.t3,marginTop:8}}>Segmenting blocks, preparing workspace...</div>
        </div>
      </div>}

      {/* Main content */}
      <div style={{flex:1,display:"flex",overflow:"hidden"}}>
        <div style={{flex:1,padding:isWorkspace?"10px 14px":"12px 16px",overflow:"hidden",display:"flex",flexDirection:"column"}}>
          {phase==="wizard"&&wizStep===1&&<W1Screen c={c} onNext={()=>setWizStep(2)} fileLoaded={fileLoaded} setFileLoaded={setFileLoaded} analysisType={analysisType} setAnalysisType={()=>{}}/>}
          {phase==="wizard"&&wizStep===2&&<W2Screen c={c} onBack={()=>setWizStep(1)} onStart={startAnalysis}/>}
          {isWorkspace&&wsTab==="A1"&&<A1Screen c={c} selBlock={selBlock} onSelBlock={setSelBlock} caliOpen={caliOpen} setCaliOpen={setCaliOpen} lpCut={lpCut} setLpCut={setLpCut} sgWin={sgWin} setSgWin={setSgWin} sacTh={sacTh} setSacTh={setSacTh}/>}
          {isWorkspace&&wsTab==="A2"&&<A2Screen c={c} selBlock={selBlock} onSelBlock={setSelBlock}/>}
          {isWorkspace&&wsTab==="A3"&&<A3Screen c={c}/>}
        </div>

        {/* Settings panel */}
        {isWorkspace&&settingsOpen&&<S1Panel c={c} isDark={isDark} onToggle={()=>setIsDark(!isDark)} lpCut={lpCut} setLpCut={setLpCut} sgWin={sgWin} setSgWin={setSgWin} sacTh={sacTh} setSacTh={setSacTh} onClose={()=>setSettingsOpen(false)}/>}
      </div>

      {/* Status bar */}
      {isWorkspace&&<div style={{height:22,background:c.ac,display:"flex",alignItems:"center",padding:"0 12px",gap:16,flexShrink:0}}>
        <span style={{fontSize:10,color:c.tI,fontWeight:600}}>M001 · 2026-01-15</span>
        <span style={{fontSize:10,color:c.tI,opacity:.7,fontFamily:M}}>Standard VOR</span>
        <div style={{flex:1}}/>
        <span style={{fontSize:10,color:c.tI,opacity:.7,fontFamily:M}}>LP:{lpCut}Hz · SG:{sgWin}ms · Sac:{sacTh}°/s</span>
        <span style={{fontSize:10,color:c.tI,opacity:.5,fontFamily:M}}>1000Hz · 62 blocks</span>
      </div>}
    </div>
  );
}
