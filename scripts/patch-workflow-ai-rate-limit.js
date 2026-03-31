/**
 * One-shot patch: ruleSeverity in parse node, gate before AI, 120s throttle, gpt-4o-mini.
 * Run: node scripts/patch-workflow-ai-rate-limit.js
 */
const fs = require("fs");
const path = require("path");

const workflowPath = path.join(__dirname, "..", "n8n", "workflows", "hvac-ai-kultek-controller.json");
const w = JSON.parse(fs.readFileSync(workflowPath, "utf8"));

const evaluateRuleSeveritySrc = `function evaluateRuleSeverity(payload, H) {
  let sev = 'normal';
  const issues = [];
  function bump(level, msg) {
    issues.push(msg);
    if (level === 'critical') sev = 'critical';
    else if (level === 'warning' && sev !== 'critical') sev = 'warning';
  }
  const room = payload.room || {};
  const ch = payload.chiller || {};
  const nh3 = payload.coolant || {};
  const cond = payload.condenser || {};
  const R = H.room;
  const C = H.chiller_r22;
  const N = H.coolant_nh3_20pct;

  if (room.temp_c != null) {
    const t = Number(room.temp_c);
    if (!Number.isNaN(t)) {
      if (t < R.temp_critical_below || t > R.temp_critical_above) bump('critical', 't помещения ' + t + '°C');
      else if (t < R.temp_warning_below || t > R.temp_warning_above) bump('warning', 't помещения ' + t + '°C вне комфорта');
    }
  }
  if (room.rh_pct != null) {
    const rh = Number(room.rh_pct);
    if (!Number.isNaN(rh)) {
      if (rh < R.rh_critical_below || rh > R.rh_critical_above) bump('critical', 'RH ' + rh + '%');
      else if (rh < R.rh_warning_below || rh > R.rh_warning_above) bump('warning', 'RH ' + rh + '%');
    }
  }
  if (room.co2_ppm != null) {
    const co2 = Number(room.co2_ppm);
    if (!Number.isNaN(co2)) {
      if (co2 >= R.co2_ppm_critical) bump('critical', 'CO2 ' + co2 + ' ppm');
      else if (co2 >= R.co2_ppm_warning) bump('warning', 'CO2 ' + co2 + ' ppm');
    }
  }
  if (room.air_speed_ms != null) {
    const v = Number(room.air_speed_ms);
    if (!Number.isNaN(v) && v > R.air_speed_ms_warning_above) bump('warning', 'скорость воздуха ' + v + ' м/с');
  }

  if (ch.t_evap_c != null) {
    const te = Number(ch.t_evap_c);
    if (!Number.isNaN(te)) {
      if (te < C.t_evap_c_range[0] || te > C.t_evap_c_range[1]) bump('critical', 'T исп ' + te + '°C вне диапазона');
      else if (te < C.t_evap_warning_below || te > C.t_evap_warning_above) bump('warning', 'T исп ' + te + '°C');
    }
  }
  if (ch.p_suction_bar_abs != null) {
    const p = Number(ch.p_suction_bar_abs);
    if (!Number.isNaN(p)) {
      if (p < C.p_suction_bar_abs_range[0] || p > C.p_suction_bar_abs_range[1]) bump('critical', 'P всас ' + p + ' бар вне диапазона');
      else if (p < C.p_suction_critical_below) bump('critical', 'P всас ' + p + ' бар');
      else if (p < C.p_suction_warn_below) bump('warning', 'P всас ' + p + ' бар');
    }
  }
  if (ch.p_discharge_bar_abs != null) {
    const p = Number(ch.p_discharge_bar_abs);
    if (!Number.isNaN(p)) {
      if (p < C.p_discharge_bar_abs_range[0] || p > C.p_discharge_bar_abs_range[1]) bump('critical', 'P нагн ' + p + ' бар вне диапазона');
      else if (p >= C.p_discharge_critical_above) bump('critical', 'P нагн ' + p + ' бар');
      else if (p >= C.p_discharge_warn_above) bump('warning', 'P нагн ' + p + ' бар');
    }
  }
  if (ch.superheat_k != null) {
    const sh = Number(ch.superheat_k);
    if (!Number.isNaN(sh)) {
      if (sh < C.superheat_crit_below || sh > C.superheat_crit_above) bump('critical', 'перегрев ' + sh + ' K');
      else if (sh < C.superheat_warn_below || sh > C.superheat_warn_above) bump('warning', 'перегрев ' + sh + ' K');
    }
  }
  if (ch.t_discharge_c != null) {
    const td = Number(ch.t_discharge_c);
    if (!Number.isNaN(td)) {
      if (td >= C.t_discharge_critical_c) bump('critical', 'T нагн ' + td + '°C');
      else if (td >= C.t_discharge_warn_c) bump('warning', 'T нагн ' + td + '°C');
    }
  }
  if (ch.t_oil_c != null) {
    const to = Number(ch.t_oil_c);
    if (!Number.isNaN(to)) {
      if (to >= C.t_oil_critical_c) bump('critical', 'T масла ' + to + '°C');
      else if (to >= C.t_oil_warn_c) bump('warning', 'T масла ' + to + '°C');
    }
  }
  if (ch.oil_dp_bar != null) {
    const od = Number(ch.oil_dp_bar);
    if (!Number.isNaN(od)) {
      if (od < C.oil_dp_critical_below) bump('critical', 'ΔP масла ' + od + ' бар');
      else if (od < C.oil_dp_warn_below) bump('warning', 'ΔP масла ' + od + ' бар');
    }
  }

  const tin = nh3.t_in_c ?? nh3.coolant_t_in;
  const tout = nh3.t_out_c ?? nh3.coolant_t_out;
  const flow = nh3.flow_m3h ?? nh3.coolant_flow;
  const press = nh3.pressure_mpa ?? nh3.coolant_pressure;
  if (tout != null) {
    const t = Number(tout);
    if (!Number.isNaN(t)) {
      if (t < N.t_out_critical_below_c) bump('critical', 'T вых хладоносителя ' + t + '°C');
      else if (t < N.t_out_c_range[0] || t > N.t_out_c_range[1]) bump('warning', 'T вых хладоносителя ' + t + '°C');
    }
  }
  if (tin != null) {
    const t = Number(tin);
    if (!Number.isNaN(t) && (t < N.t_in_c_range[0] || t > N.t_in_c_range[1])) bump('warning', 'T вх хладоносителя ' + t + '°C');
  }
  if (flow != null) {
    const f = Number(flow);
    if (!Number.isNaN(f) && f < N.flow_warn_below) bump('warning', 'расход ' + f + ' м³/ч');
  }
  if (press != null) {
    const pr = Number(press);
    if (!Number.isNaN(pr) && pr > N.pressure_warn_above_mpa) bump('warning', 'давление ' + pr + ' МПа');
  }
  if (cond.t_out_c != null && H.condenser_water) {
    const t = Number(cond.t_out_c);
    if (!Number.isNaN(t) && t > H.condenser_water.t_out_c_nominal + 5) bump('warning', 'T вых конденсатора ' + t + '°C');
  }
  return { ruleSeverity: sev, ruleIssues: issues, ruleSummary: issues.length ? issues.join('; ') : 'в пределах правил' };
}

`;

const parse = w.nodes.find((n) => n.id === "node-parse-thresholds");
if (!parse) throw new Error("node-parse-thresholds not found");

let code = parse.parameters.jsCode;
if (!code.includes("function evaluateRuleSeverity")) {
  code = code.replace("const META = {", `${evaluateRuleSeveritySrc}\nconst META = {`);
}

const oldReturn = `return [
  {
    json: {
      topic: raw.topic || payload.topic || 'unknown',
      receivedAt: new Date().toISOString(),
      sensorPayload: payload,
      thresholds: THRESHOLDS,
      meta: META,
    },
  },
];`;

const newReturn = `const ruleEval = evaluateRuleSeverity(payload, THRESHOLDS);
return [
  {
    json: {
      topic: raw.topic || payload.topic || 'unknown',
      receivedAt: new Date().toISOString(),
      sensorPayload: payload,
      thresholds: THRESHOLDS,
      meta: META,
      ruleSeverity: ruleEval.ruleSeverity,
      ruleIssues: ruleEval.ruleIssues,
      ruleSummary: ruleEval.ruleSummary,
    },
  },
];`;

if (!code.includes(oldReturn)) {
  throw new Error("parse node return block not found (workflow changed?)");
}
code = code.replace(oldReturn, newReturn);
parse.parameters.jsCode = code;

const gateId = "node-gate-ai-rules";
if (!w.nodes.find((n) => n.id === gateId)) {
  w.nodes.push({
    parameters: {
      jsCode:
        "const j = $input.first().json;\nif (j.parseError) return [];\nif (j.ruleSeverity === 'normal' || !j.ruleSeverity) return [];\nreturn $input.all();",
    },
    id: gateId,
    name: "К AI только при отклонении",
    type: "n8n-nodes-base.code",
    typeVersion: 2,
    position: [-430, 220],
  });
}

const th = w.nodes.find((n) => n.id === "node-throttle-30s");
if (th) {
  th.name = "Окно 120 сек для AI";
  th.parameters.jsCode = `// Не передавать AI невалидные сообщения (parseError из предыдущей ноды)
const base = $input.first().json;
if (base.parseError) return [];

try {
  const g = $getWorkflowStaticData('global');
  const now = Date.now();
  if (!g.lastAiMs) g.lastAiMs = 0;
  if (now - g.lastAiMs < 120000) return [];
  g.lastAiMs = now;
} catch (e) {
  // Если static data недоступен, AI вызывается на каждое сообщение (редко: только после gate отклонений)
}
return $input.all();`;
}

const oa = w.nodes.find((n) => n.id === "node-openai-chat");
if (oa) oa.parameters.model.value = "gpt-4o-mini";

const pg = w.nodes.find((n) => n.id === "node-pg-ai-decisions");
if (pg) {
  pg.parameters.options.queryReplacement = pg.parameters.options.queryReplacement.replace(
    /'gpt-4o'/g,
    "'gpt-4o-mini'",
  );
}

w.connections["Разбор MQTT + пороги"].main[0] = [
  { node: "Развернуть сенсоры в строки БД", type: "main", index: 0 },
  { node: "К AI только при отклонении", type: "main", index: 0 },
];
w.connections["К AI только при отклонении"] = {
  main: [[{ node: "Окно 120 сек для AI", type: "main", index: 0 }]],
};
delete w.connections["Окно 30 сек для AI"];
w.connections["Окно 120 сек для AI"] = {
  main: [[{ node: "AI Agent HVAC", type: "main", index: 0 }]],
};

const sticky = w.nodes.find((n) => n.id === "sticky-readme");
if (sticky && sticky.parameters.content) {
  sticky.parameters.content = sticky.parameters.content
    .replace(
      "**Цепочка:** `MQTT Trigger` → `Разбор + пороги` → **параллельно:** `Развернуть сенсоры` → `PostgreSQL sensor_readings` **и** `Окно 30 сек для AI` → `AI Agent`",
      "**Цепочка:** `MQTT Trigger` → `Разбор + пороги` → **параллельно:** сенсоры в БД **и** `К AI только при отклонении` → `Окно 120 сек` → `AI Agent`",
    )
    .replace("Окно 30 сек для AI", "Окно 120 сек (после gate)");
}

w.meta.description =
  "План: MQTT hvac/# → парсинг + ruleSeverity → sensor_readings; только warning/critical → окно 120с → AI (gpt-4o-mini) → ai_decisions → Switch → Telegram + MQTT.";

fs.writeFileSync(workflowPath, JSON.stringify(w, null, 2) + "\n", "utf8");
console.log("Patched", workflowPath);
