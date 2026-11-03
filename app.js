"use strict";
const $=id=>document.getElementById(id);
const state={index:0,exam:null};
const create=(tag,cls,text)=>{const el=document.createElement(tag);if(cls)el.className=cls;if(text!==undefined)el.textContent=text;return el};
function showQuestion(idx,updateHash=true){
 if(idx<0||idx>=state.exam.questions.length)return;
 state.index=idx;
 for(const c of $("questions").children)c.classList.toggle("active",Number(c.dataset.number)===idx+1);
 $("current-label").textContent=`שאלה ${idx+1} מתוך ${state.exam.questions.length}`;
 $("current-points").textContent=`${state.exam.questions[idx].points} נקודות`;
 $("progress-fill").style.width=`${100*(idx+1)/state.exam.questions.length}%`;
 document.querySelector('[role="progressbar"]').setAttribute("aria-valuenow",idx+1);
 $("dock-number").textContent=idx+1;
 for(const button of [$("prev-btn"),$("dock-prev")])button.disabled=idx===0;
 for(const button of [$("next-btn"),$("dock-next")])button.disabled=idx===state.exam.questions.length-1;
 const grid=$("question-grid");
 for(const button of grid.children){const active=Number(button.dataset.number)===idx+1;button.classList.toggle("selected",active);button.setAttribute("aria-current",active?"step":"false")}
 if(updateHash)history.replaceState(null,"",`#q${idx+1}`);
 const panel=document.querySelector(".exam-panel").getBoundingClientRect();
 if(panel.top<0||panel.top>window.innerHeight*.5)document.querySelector(".exam-panel").scrollIntoView({behavior:window.matchMedia("(prefers-reduced-motion: reduce)").matches?"instant":"smooth",block:"start"});
}
function blockNode(block){
 if(block.type==="table"){const wrap=create("div","math-table-wrap");const table=create("table","math-table");table.setAttribute("aria-label","טבלת ערכי הפונקציה");for(const [ri,row] of block.rows.entries()){const tr=create("tr");for(const [ci,v] of row.entries()){const cell=create(ci===0?"th":"td","",v);if(ci===0)cell.scope="row";tr.append(cell)}table.append(tr)}wrap.append(table);return wrap}
 if(block.type==="image"){const fig=create("figure","figure");const img=create("img");img.src=block.src;img.alt=block.alt;img.loading="lazy";img.decoding="async";fig.append(img);return fig}
 const txt=block.text||"";const isFormula=/^[\d\sxXfFgGkKABCDEF()+−×÷=.,:·%°∠∥<>₪\-]+$/u.test(txt)&&/[=+−×÷∠]/.test(txt);
 const isSubpart=/^[אבגדהוזחט]\./u.test(txt);
 return create("p","q-block"+(isFormula?" formula":"")+(isSubpart?" subpart":""),txt);
}
async function start(){
 try{
 const response=await fetch("exam.json",{cache:"no-cache"});
 if(!response.ok)throw new Error("HTTP "+response.status);
 const exam=await response.json();
 if(exam.questions.length!==17||exam.questions.reduce((s,q)=>s+q.points,0)!==100)throw new Error("נתוני המבחן אינם תקינים");
 state.exam=exam;
 document.title=exam.title;
 $("exam-title").textContent=exam.title;
 $("timing").textContent=exam.durationMinutes+" דקות";
 $("points").textContent=exam.totalPoints+" נקודות";
 $("count").textContent=exam.questions.length+" שאלות";
 $("disclaimer").textContent=exam.disclaimer;
 $("instructions").replaceChildren(...exam.instructions.map(t=>create("li","",t)));
 $("footer-lines").replaceChildren(...exam.footer.map(t=>create("div","",t)));
 const area=$("questions"),grid=$("question-grid");
 for(const q of exam.questions){
   const article=create("article","question-card");article.id="question-"+q.number;article.dataset.number=q.number;article.setAttribute("aria-label","שאלה "+q.number);
   article.append(create("div","q-meta",q.points+" נקודות"),create("h2","q-heading","שאלה "+q.number));
   for(const block of q.blocks)article.append(blockNode(block));
   area.append(article);
   const b=create("button","",String(q.number));b.type="button";b.dataset.number=q.number;b.title="שאלה "+q.number;b.append(create("small","",q.points+" נק׳"));b.addEventListener("click",()=>{$("questions-dialog").close();showQuestion(q.number-1)});grid.append(b);
 }
 $("menu-btn").addEventListener("click",()=>$("questions-dialog").showModal());
 $("dock-menu").addEventListener("click",()=>$("questions-dialog").showModal());
 $("dialog-close").addEventListener("click",()=>$("questions-dialog").close());
 $("questions-dialog").addEventListener("click",e=>{if(e.target===$("questions-dialog"))$("questions-dialog").close()});
 $("prev-btn").addEventListener("click",()=>showQuestion(state.index-1));
 $("next-btn").addEventListener("click",()=>showQuestion(state.index+1));
 $("dock-prev").addEventListener("click",()=>showQuestion(state.index-1));
 $("dock-next").addEventListener("click",()=>showQuestion(state.index+1));
 $("print-btn").addEventListener("click",()=>window.print());
 window.addEventListener("hashchange",()=>{const match=/^#q(\d+)$/.exec(location.hash);if(match)showQuestion(Number(match[1])-1,false)});
 const initial=/^#q(\d+)$/.exec(location.hash);showQuestion(initial?Math.min(16,Math.max(0,Number(initial[1])-1)):0,false);
 $("loading").hidden=true;$("app").hidden=false;
 }catch(err){console.error(err);$("loading").textContent="לא ניתן לטעון את המבחן. נסו לרענן את הדף."}
}
start();
