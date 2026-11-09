"use strict";
const $ = (id) => document.getElementById(id);
const views = ["login", "welcome", "training", "processing", "result"];
let currentState = null;
let busy = false;

function show(name) {
  for (const view of views) $("view-" + view).hidden = view !== name;
  window.scrollTo({ top: 0, behavior: "instant" });
}

function notify(message) {
  $("alert").textContent = message;
  $("alert").hidden = !message;
}

function setBusy(value) {
  busy = value;
  for (const id of ["start-button", "restart-button", "answer-submit"]) {
    $(id).disabled = value;
  }
  $("login-form").querySelector("button").disabled = value;
}

async function api(path, options = {}) {
  const response = await fetch("/api/" + path, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  let data;
  try { data = await response.json(); } catch { throw new Error("Réponse du serveur invalide."); }
  if (!response.ok) throw new Error(data.error || "Une erreur est survenue.");
  return data;
}

function render(data) {
  currentState = data;
  notify("");
  if (!data.authorized) {
    show("login");
    return;
  }
  if (!data.stage || data.stage === "welcome") {
    show("welcome");
    return;
  }
  if (data.stage === "processing") {
    show("processing");
    return;
  }
  if (data.stage === "done") {
    $("score-value").textContent = (data.result.score || "").replace("/3", "").trim();
    const score = Number(($("score-value").textContent || "0").replace(",", "."));
    $("score-legend").textContent = score >= 2.5 ? "Une belle maîtrise. Continue sur cette lancée !" : score >= 1.5 ? "De bonnes bases, quelques réflexes à affiner." : "Chaque situation est une occasion de progresser.";
    $("feedback-text").textContent = data.result.feedback || "";
    $("example-text").textContent = data.result.example || "";
    show("result");
    return;
  }
  $("situation-text").textContent = data.situation || "";
  const second = data.stage === "second";
  $("phase-pill").textContent = second ? "ÉTAPE 2 / 2" : "ÉTAPE 1 / 2";
  $("training-heading").innerHTML = second ? "Le spectateur <em>insiste.</em>" : "À toi <em>de jouer.</em>";
  $("relance-card").hidden = !second;
  $("first-answer-summary").hidden = !second;
  if (second) {
    $("relance-text").textContent = data.relance || "";
    $("first-answer-text").textContent = data.first_answer || "";
  }
  $("answer-label").textContent = second ? "Et maintenant, que lui réponds-tu ?" : "Que réponds-tu au spectateur ?";
  $("answer-text").value = "";
  $("character-count").textContent = "0 / 1800";
  $("answer-submit").textContent = second ? "Obtenir mon débrief →" : "Envoyer ma réponse →";
  show("training");
}

async function launch() {
  if (busy) return;
  setBusy(true);
  notify("");
  try { render(await api("start", { method: "POST", body: "{}" })); }
  catch (error) { notify(error.message); }
  finally { setBusy(false); }
}

$("start-button").addEventListener("click", launch);
$("restart-button").addEventListener("click", launch);
$("answer-text").addEventListener("input", () => {
  $("character-count").textContent = $("answer-text").value.length + " / 1800";
});
$("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy) return;
  setBusy(true);
  notify("");
  try {
    const code = $("access-code").value;
    const data = await api("login", { method: "POST", body: JSON.stringify({ code }) });
    $("access-code").value = "";
    render(data);
  } catch (error) { notify(error.message); }
  finally { setBusy(false); }
});
$("answer-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy) return;
  const answer = $("answer-text").value.trim();
  if (!answer) return;
  setBusy(true);
  notify("");
  if (currentState.stage === "second") show("processing");
  try {
    render(await api("answer", { method: "POST", body: JSON.stringify({ answer }) }));
  } catch (error) {
    if (currentState.stage === "second") show("training");
    notify(error.message);
  } finally { setBusy(false); }
});
api("state").then(render).catch((error) => { show("login"); notify(error.message); });