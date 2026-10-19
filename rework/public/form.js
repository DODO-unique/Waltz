(() => {
  "use strict";

  /*
   * Server injection contract (v1): replace every token below while serving
   * this file for a Redis key with base64url(JSON.stringify(value)) in UTF-8,
   * without padding. Never replace with raw JSON/JavaScript. In Node:
   * Buffer.from(JSON.stringify(value), "utf8").toString("base64url")
   */
  const TRANSACTION_ID_SLOT = "__EXPRESS_FROM_TRANSACTION_ID_STRING_V1"
  const CONTRACT_SLOT = "__EXPRESS_FORM_CONTRACT_B64URL_V1__";
  const CONTRACT_TYPE_SLOT = "__EXPRESS_FORM_CONTRACT_TYPE_B64URL_V1__";
  const SCHEMA_SLOT = "__EXPRESS_FORM_SCHEMA_B64URL_V1__";

  // Shared by every rendered form. Change only if the common route differs.
  const SUBMIT_URL = "/waltz/submit";

  const FIELD = {
    username: { label: "Username", autocomplete: "username" },
    email: { label: "Email address", type: "email", autocomplete: "email" },
    fullname: { label: "Full name", autocomplete: "name" },
    age: { label: "Age", type: "number", inputMode: "numeric", min: 0 },
    address: { label: "Address", autocomplete: "street-address" },
    password: { label: "Password", type: "password", autocomplete: "current-password" }
  };
  const form = document.querySelector("#account-form");
  const root = document.querySelector("#form-fields");
  const title = document.querySelector("#form-title");
  const loading = document.querySelector("#form-loading");
  const error = document.querySelector("#form-error");
  const attempts = document.querySelector("#form-attempts");
  const success = document.querySelector("#form-success");
  const submit = document.querySelector("#form-submit");
  let activeFields = [];
  let authenticationLocked = false;

  function injectedJson(slot, name) {
    if (!slot || /^__EXPRESS_FORM_[A-Z_]+_B64URL_V1__$/.test(slot)) throw new Error(`The server did not inject ${name}.`);
    if (!/^[A-Za-z0-9_-]+$/.test(slot)) throw new Error(`Invalid ${name} encoding.`);
    try {
      const padded = slot.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((slot.length + 3) % 4);
      const bytes = Uint8Array.from(atob(padded), char => char.charCodeAt(0));
      return JSON.parse(new TextDecoder().decode(bytes));
    } catch { throw new Error(`The injected ${name} is not valid JSON.`); }
  }
  function object(value) { return value && typeof value === "object" && !Array.isArray(value) ? value : {}; }
  function properties(value) { const source = object(value); return object(source.properties || source.fields || source); }
  function setting(name, ...sources) {
    for (const source of sources) { const value = properties(source)[name]; if (value !== undefined) return value; }
  }
  function enabled(value) { return value !== undefined && value !== false && value?.enabled !== false; }
  function showError(message) { error.textContent = message; error.hidden = false; }
  function clearMessages() {
    error.hidden = true; error.textContent = "";
    attempts.hidden = true; attempts.textContent = "";
    success.hidden = true; success.textContent = "";
  }

  function formType(contract, type) {
    const candidate = String(type || contract?.type || contract?.contractType || contract?.kind || contract?.name || "").toLowerCase();
    if (candidate.includes("registration") || candidate.includes("register")) return "registration";
    if (candidate.includes("auth") || candidate.includes("login")) return "auth";
    throw new Error("The injected contract type must be Auth or Registration.");
  }
  function descriptor(name, config, path) {
    const metadata = object(config), defaults = FIELD[name];
    return { name, path, label: metadata.label || defaults.label, type: metadata.type || defaults.type || "text",
      autocomplete: metadata.autocomplete || defaults.autocomplete || "off", inputMode: metadata.inputMode || defaults.inputMode,
      required: metadata.required !== false,
      placeholder: metadata.placeholder || "", min: metadata.min ?? defaults.min, max: metadata.max,
      minLength: metadata.minLength, maxLength: metadata.maxLength, pattern: metadata.pattern };
  }
  function fieldsFor(type, contract, schema) {
    const fromContract = properties(contract), fromSchema = properties(schema);
    if (type === "auth") {
      const contractIdentifier = properties(fromContract.identifier), schemaIdentifier = properties(fromSchema.identifier);
      const fields = ["email", "username"].map(name => [name, setting(name, schemaIdentifier, contractIdentifier)])
        .filter(([, value]) => enabled(value)).map(([name, value]) => descriptor(name, value, ["identifier", name]));
      const password = setting("password", fromSchema, fromContract);
      if (enabled(password)) fields.push(descriptor("password", password, ["password"]));
      return fields;
    }
    return ["username", "email", "fullname", "age", "address", "password"]
      .map(name => [name, setting(name, fromSchema, fromContract)]).filter(([, value]) => enabled(value))
      .map(([name, value]) => descriptor(name, value, [name]));
  }
  function render(fields) {
    root.replaceChildren();
    for (const field of fields) {
      const input = document.createElement("input"), label = document.createElement("label"), wrapper = document.createElement("div");
      input.id = `field-${field.name}`; input.name = field.name; input.type = field.type; input.autocomplete = field.autocomplete;
      input.required = field.required; input.placeholder = field.placeholder;
      for (const key of ["inputMode", "min", "max", "minLength", "maxLength", "pattern"]) if (field[key] !== undefined) input[key] = field[key];
      label.htmlFor = input.id; label.textContent = field.label; wrapper.className = "form-field"; wrapper.append(label, input); root.append(wrapper);
    }
  }
  function payload() {
    const result = {}, values = new FormData(form);
    for (const field of activeFields) { let cursor = result; for (const key of field.path.slice(0, -1)) cursor = cursor[key] ||= {}; cursor[field.path.at(-1)] = values.get(field.name); }
    return result;
  }
  async function responseJson(response) { const text = await response.text(); if (!text) return null; try { return JSON.parse(text); } catch { return text; } }

  function initialise() {
    clearMessages();
    try {
      const contract = injectedJson(CONTRACT_SLOT, "contract");
      const type = formType(contract, injectedJson(CONTRACT_TYPE_SLOT, "contract type"));
      activeFields = fieldsFor(type, contract, injectedJson(SCHEMA_SLOT, "schema"));
      if (!activeFields.length) throw new Error("The injected schema has no enabled fields.");
      const registration = type === "registration"; title.textContent = registration ? "Create account" : "Sign in";
      submit.textContent = registration ? "Create account" : "Sign in"; render(activeFields); loading.hidden = true; form.hidden = false;
    } catch (cause) { loading.hidden = true; showError(cause instanceof Error ? cause.message : "Unable to prepare the form."); }
  }
  form.addEventListener("submit", async event => {
    event.preventDefault(); clearMessages(); if (!form.reportValidity()) return;
    submit.disabled = true; const originalText = submit.textContent; submit.textContent = "Submitting.";
    try {
      const response = await fetch(SUBMIT_URL, { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify({ tkey: TRANSACTION_ID_SLOT, body: payload() }) });
      const result = await responseJson(response);
      if (response.status === 401 && Number.isInteger(result?.attemptsRemaining)) {
        showError(result.message || "Invalid credentials.");
        if (result.attemptsRemaining <= 0) {
          authenticationLocked = true;
          attempts.textContent = "No attempts remaining. This sign-in form is locked.";
          form.querySelectorAll("input").forEach(input => { input.disabled = true; });
        } else {
          attempts.textContent = result.attemptsRemaining === 1
            ? "1 attempt remaining."
            : `${result.attemptsRemaining} attempts remaining.`;
        }
        attempts.hidden = false;
        if (!authenticationLocked) {
          const password = form.querySelector('input[name="password"]');
          if (password) { password.value = ""; password.focus(); }
        }
        return;
      }
      if (response.status === 429) {
        authenticationLocked = true;
        showError(result?.message || "The authentication attempt limit has been reached.");
        attempts.textContent = "No attempts remaining. This sign-in form is locked.";
        attempts.hidden = false;
        form.querySelectorAll("input").forEach(input => { input.disabled = true; });
        return;
      }
      if (!response.ok) throw new Error(result?.message || `Submission failed (${response.status}).`);
      success.textContent = result?.message || "Submitted successfully."; success.hidden = false;
    } catch (cause) { showError(cause instanceof Error ? cause.message : "Unable to submit the form."); }
    finally { submit.disabled = authenticationLocked; submit.textContent = originalText; }
  });
  initialise();
})();
