/**
 * family.js — Couple / family shared budgeting page.
 */

let _household = null;

async function loadFamily() {
  try {
    const data = await api.getHousehold();
    _household = data;
    renderFamily(data);
  } catch (err) {
    document.getElementById("familyContent").innerHTML =
      `<div class="empty-state">Error loading family data.</div>`;
    showToast(err.message, "error");
  }
}

function renderFamily(data) {
  const container = document.getElementById("familyContent");

  if (!data) {
    // Not in a household
    container.innerHTML = `
      <div class="family-empty-wrap">
        <div class="family-empty-icon"><i data-feather="users"></i></div>
        <h2>Create your household</h2>
        <p>Share budgets, goals, and spending insights with your partner or family members.</p>
        <div class="family-create-form">
          <input type="text" id="householdNameInput" class="form-control"
                 placeholder="Household name (e.g. Smith Family)" maxlength="60"/>
          <button class="btn btn-primary" id="createHouseholdBtn">
            <i data-feather="plus"></i> Create Household
          </button>
        </div>
        <div class="family-divider">— or join an existing one —</div>
        <div class="family-join-form">
          <input type="text" id="inviteTokenInput" class="form-control"
                 placeholder="Paste your invite token here"/>
          <button class="btn btn-ghost" id="joinHouseholdBtn">Join</button>
        </div>
      </div>`;

    if (window.feather) feather.replace();

    document.getElementById("createHouseholdBtn").addEventListener("click", createHousehold);
    document.getElementById("joinHouseholdBtn").addEventListener("click", joinHousehold);
    return;
  }

  const { household, my_role, members, pending_invites } = data;
  const isOwner = my_role === "owner";

  const membersHtml = members.map(m => `
    <div class="family-member-row" id="family-member-${m.id}">
      <div class="family-member-avatar">${escFam(m.user_name || "?").charAt(0).toUpperCase()}</div>
      <div class="family-member-info">
        <div class="family-member-name">${escFam(m.user_name)} ${m.role === "owner" ? '<span class="family-owner-badge">Owner</span>' : ""}</div>
        <div class="family-member-email">${escFam(m.user_email)}</div>
      </div>
      <div class="family-member-stats">
        <span class="family-stat-income">+${fmtCurrency(m.income_monthly)}</span>
        <span class="family-stat-expense">-${fmtCurrency(m.expense_monthly)}</span>
        <span class="family-stat-label">/mo avg</span>
      </div>
      ${isOwner && m.role !== "owner" ? `
        <button class="btn btn-ghost btn-sm family-remove-btn"
                onclick="removeMember(${m.id})" title="Remove">
          <i data-feather="user-minus"></i>
        </button>` : ""}
    </div>`).join("");

  const invitesHtml = isOwner && pending_invites.length
    ? `<div class="family-section-title">Pending Invites</div>
       ${pending_invites.map(i => `
         <div class="family-invite-row">
           <i data-feather="mail"></i>
           <span>${escFam(i.invitee_email)}</span>
           <code class="family-token">${i.token}</code>
         </div>`).join("")}`
    : "";

  container.innerHTML = `
    <div class="family-card">
      <div class="family-card-header">
        <div>
          <h2>${escFam(household.name)}</h2>
          <span class="family-member-count">${members.length} member${members.length !== 1 ? "s" : ""}</span>
        </div>
        <button class="btn btn-ghost btn-sm" id="leaveHouseholdBtn">
          <i data-feather="log-out"></i> Leave
        </button>
      </div>

      <div class="family-members">${membersHtml}</div>

      ${invitesHtml}

      ${isOwner ? `
        <div class="family-invite-section">
          <div class="family-section-title">Invite a Member</div>
          <div class="family-invite-form">
            <input type="email" id="inviteEmailInput" class="form-control"
                   placeholder="partner@example.com"/>
            <button class="btn btn-primary btn-sm" id="sendInviteBtn">
              <i data-feather="user-plus"></i> Send Invite
            </button>
          </div>
          <div id="inviteResult" style="margin-top:10px"></div>
        </div>` : ""}
    </div>`;

  if (window.feather) feather.replace();

  document.getElementById("leaveHouseholdBtn").addEventListener("click", leaveHousehold);
  if (isOwner) {
    document.getElementById("sendInviteBtn").addEventListener("click", sendInvite);
  }
}

// ---- Actions ----------------------------------------------------------------

async function createHousehold() {
  const name = document.getElementById("householdNameInput").value.trim();
  if (!name) return showToast("Please enter a household name", "error");
  try {
    await api.createHousehold({ name });
    showToast("Household created!", "success");
    loadFamily();
  } catch (err) { showToast(err.message, "error"); }
}

async function joinHousehold() {
  const token = document.getElementById("inviteTokenInput").value.trim();
  if (!token) return showToast("Please paste your invite token", "error");
  try {
    await api.acceptInvite(token);
    showToast("Joined household!", "success");
    loadFamily();
  } catch (err) { showToast(err.message, "error"); }
}

async function sendInvite() {
  const email = document.getElementById("inviteEmailInput").value.trim();
  if (!email) return showToast("Please enter an email address", "error");
  try {
    const res = await api.inviteMember({ email });
    document.getElementById("inviteResult").innerHTML = `
      <div class="family-token-reveal">
        <strong>Share this token with ${escFam(email)}:</strong><br>
        <code class="family-token-big">${res.invite.token}</code>
        <button class="btn btn-ghost btn-sm" onclick="navigator.clipboard.writeText('${res.invite.token}').then(()=>showToast('Copied!','success'))">
          <i data-feather="copy"></i> Copy
        </button>
      </div>`;
    if (window.feather) feather.replace();
    document.getElementById("inviteEmailInput").value = "";
    loadFamily();
  } catch (err) { showToast(err.message, "error"); }
}

async function leaveHousehold() {
  confirmDelete("Leave this household? You can rejoin with an invite link.", async () => {
    try {
      await api.leaveHousehold();
      showToast("You have left the household.", "success");
      loadFamily();
    } catch (err) { showToast(err.message, "error"); }
  });
}

async function removeMember(memberId) {
  confirmDelete("Remove this member from the household?", async () => {
    try {
      await api.removeMember(memberId);
      showToast("Member removed.", "success");
      loadFamily();
    } catch (err) { showToast(err.message, "error"); }
  });
}

function escFam(str) {
  return String(str || "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
